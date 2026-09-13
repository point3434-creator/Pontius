"""Information abstraction: bucketing strategically similar card situations.

Preflop is lossless (169 classes — see cards.preflop_class). Postflop we
follow the distribution-aware school (Johanson et al.; Ganzfried & Sandholm):
a hand on a given board is described by its *equity distribution* over future
run-outs, summarized as a sorted-quantile vector, and hands are k-means
clustered in that space. Sorted-quantile features make Euclidean k-means
equivalent to 2-Wasserstein (earth-mover's) clustering of the underlying
distributions — the metric the potential-aware abstraction literature uses —
and are markedly less noisy than fixed-bin histograms at the same budget.

Streets:
  flop  — quantiles of equity over turn+river run-outs, stratified over turns
  turn  — quantiles of equity over all remaining rivers (enumerated)
  river — exact equity vs all 990 opponent holes, binned directly (no k-means)

Per-run-out equity is estimated against a *matched* set of opponent holes
(a random perfect matching of the remaining cards): every card is used at
most once, which balances the finite population and cuts variance vs the
same number of independent draws.

Bucket assignment is deterministic — the feature RNG is seeded from a stable
CRC32 digest of the canonical form, so it survives Python upgrades and spawn
boundaries — and cached. Caches carry a fingerprint of the centroid build and
are silently discarded when the abstraction is rebuilt.
"""
import hashlib
import itertools
import json
import os
import pickle
import random
import time
import zlib

import numpy as np

from .cards import preflop_class
from .evaluator import hand_rank

FEATURE_DIM = 20          # quantiles per feature vector (flop/turn)
FEATURE_VERSION = 2       # bump when features/sampling change: forces rebuild
HIST_BINS = FEATURE_DIM   # legacy alias
_QS = np.linspace(0.025, 0.975, FEATURE_DIM)
_SUIT_PERMS = list(itertools.permutations(range(4)))


# --------------------------------------------------------------- canonical form
def canonical_key(hole, board):
    """Suit-isomorphic canonical id for (hole, board).

    Any consistent relabeling of suits maps to the same key, collapsing e.g.
    all four single-suit flush draws onto one entry.
    """
    flop = sorted(board[:3])
    turn = board[3:4]
    river = board[4:5]
    best = None
    for perm in _SUIT_PERMS:
        h = tuple(sorted((c // 4) * 4 + perm[c % 4] for c in hole))
        f = tuple(sorted((c // 4) * 4 + perm[c % 4] for c in flop))
        t = tuple((c // 4) * 4 + perm[c % 4] for c in turn)
        r = tuple((c // 4) * 4 + perm[c % 4] for c in river)
        cand = (h, f, t, r)
        if best is None or cand < best:
            best = cand
    return best


def stable_seed(key) -> int:
    """CRC32 of the canonical key. Unlike built-in hash(), this is identical
    across Python versions, builds, and platforms — the persisted caches and
    centroid builds depend on that."""
    flat = bytearray()
    for part in key:
        flat.extend(part)
        flat.append(255)  # street separator (cards are 0..51)
    return zlib.crc32(bytes(flat))


# ------------------------------------------------------------------- equity
def _river_equity_ref(hole, board5):
    """Reference exact river equity: O(990) hand_rank calls per query.

    Kept verbatim as the oracle for the table-based river_equity below —
    test_abstraction proves bit-identity (river buckets feed infoset keys,
    so even 1-ulp drift would invalidate the blueprint)."""
    dead = set(hole) | set(board5)
    remaining = [c for c in range(52) if c not in dead]
    ours = hand_rank(list(hole) + list(board5))
    wins = ties = total = 0
    for i in range(len(remaining)):
        for j in range(i + 1, len(remaining)):
            theirs = hand_rank([remaining[i], remaining[j]] + list(board5))
            if ours > theirs:
                wins += 1
            elif ours == theirs:
                ties += 1
            total += 1
    return (wins + 0.5 * ties) / total


# Per-board rank tables: ranking all C(47,2)=1081 two-card holes once serves
# every equity query on that board with a few binary searches instead of 990
# hand_rank calls (range-vs-board workloads hit one board ~1000x). Per-process
# and FIFO-bounded like the turn cache: ~48KB/board, so the cap costs ~12MB
# per process, ~250MB across 20 workers — same ballpark as RAW_MEMO.
RIVER_TABLE_CAP = 256
_RIVER_TABLES = {}

# board-independent C(47,2) structure, so table assembly is pure numpy:
# pair p -> its two positions in the 47-card list, and position k -> the 46
# pairs touching it (row order = ascending other-position, ties impossible)
_PAIR_POS = np.array(list(itertools.combinations(range(47), 2)),
                     dtype=np.int64)
_TOUCH_POS = np.array([np.flatnonzero((_PAIR_POS == k).any(axis=1))
                       for k in range(47)])


def _river_table(board5):
    """(52x52 pair rank, sorted all-pair ranks, per-card sorted ranks) for a
    complete board. hand_rank is a pure function of the card *set* (both
    backends), so the table is keyed on the sorted board."""
    key = tuple(sorted(board5))
    tbl = _RIVER_TABLES.get(key)
    if tbl is not None:
        return tbl
    cards47 = [c for c in range(52) if c not in set(key)]
    hr = hand_rank
    ranks = np.array([hr(p + key) for p in itertools.combinations(cards47, 2)],
                     dtype=np.int64)
    arr47 = np.array(cards47, dtype=np.int64)
    a, b = arr47[_PAIR_POS[:, 0]], arr47[_PAIR_POS[:, 1]]
    pair_rank = np.zeros((52, 52), dtype=np.int64)
    pair_rank[a, b] = ranks
    pair_rank[b, a] = ranks
    touched = np.sort(ranks[_TOUCH_POS], axis=1)  # (47, 46) rows
    per_card = {c: touched[k] for k, c in enumerate(cards47)}
    all_ranks = np.sort(ranks)
    if len(_RIVER_TABLES) >= RIVER_TABLE_CAP:
        _RIVER_TABLES.pop(next(iter(_RIVER_TABLES)))  # FIFO eviction
    tbl = _RIVER_TABLES[key] = (pair_rank, all_ranks, per_card)
    return tbl


def river_equity(hole, board5):
    """Exact equity vs a uniform random opponent hole on a complete board.

    Wins/ties are counted from the per-board table by inclusion-exclusion:
    all 1081 pairs, minus the 46 pairs using each hole card; the (h1,h2)
    pair itself ranks equal to ours, so it never enters the win count and
    re-enters the tie count once. The integer counts are exactly those of
    _river_equity_ref, so the returned float is bit-identical to it."""
    pair_rank, all_ranks, per_card = _river_table(board5)
    r = pair_rank[hole[0], hole[1]]
    lo = int(np.searchsorted(all_ranks, r, side="left"))
    eq = int(np.searchsorted(all_ranks, r, side="right")) - lo
    c1 = per_card[hole[0]]
    lo1 = int(np.searchsorted(c1, r, side="left"))
    eq1 = int(np.searchsorted(c1, r, side="right")) - lo1
    c2 = per_card[hole[1]]
    lo2 = int(np.searchsorted(c2, r, side="left"))
    eq2 = int(np.searchsorted(c2, r, side="right")) - lo2
    wins = lo - lo1 - lo2
    ties = eq - eq1 - eq2 + 1
    return (wins + 0.5 * ties) / 990  # C(45,2) opponent pairs


def _matched_equity(hole, board5, pool, n_opp, rng):
    """Equity vs ~n_opp opponent holes drawn as random perfect matchings of
    `pool` (each matching uses every card at most once — negatively
    correlated draws, lower variance than independent sampling)."""
    ours = hand_rank(list(hole) + board5)
    score = 0.0
    seen = 0
    pool = pool[:]
    while seen < n_opp:
        rng.shuffle(pool)
        pairs = min(len(pool) // 2, n_opp - seen)
        for i in range(pairs):
            theirs = hand_rank([pool[2 * i], pool[2 * i + 1]] + board5)
            if ours > theirs:
                score += 1.0
            elif ours == theirs:
                score += 0.5
        seen += pairs
    return score / seen


def equity_feature(hole, board, n_runouts=48, n_opp=22, bins=FEATURE_DIM,
                   rng=None, _canon=None):
    """Feature for k-means: equity quantile vector (flop/turn), [equity] (river).

    Deterministic per canonical hand when rng is None: the computation runs on
    the *canonical form* of the cards with an rng seeded from its stable
    digest, so all suit-isomorphic twins produce the identical feature vector,
    reproducible across processes, runs, and Python versions.
    """
    if rng is None:
        key = _canon if _canon is not None else canonical_key(hole, board)
        rng = random.Random(stable_seed(key))
        hole = list(key[0])
        board = list(key[1]) + list(key[2]) + list(key[3])
    board = list(board)
    if len(board) == 5:
        return np.array([river_equity(hole, board)], dtype=np.float32)

    dead = set(hole) | set(board)
    remaining = [c for c in range(52) if c not in dead]
    equities = []
    if len(board) == 4:  # turn -> enumerate every river exactly once
        for rc in remaining:
            pool = [c for c in remaining if c != rc]
            equities.append(_matched_equity(hole, board + [rc], pool,
                                            n_opp, rng))
    else:  # flop -> run-outs stratified over the turn card
        m = len(remaining)
        perm = rng.sample(remaining, m)
        for i in range(n_runouts):
            turn_c = perm[i % m]
            j = rng.randrange(m - 1)
            river_c = remaining[j]
            if river_c == turn_c:
                river_c = remaining[m - 1]
            pool = [c for c in remaining if c != turn_c and c != river_c]
            equities.append(_matched_equity(hole, board + [turn_c, river_c],
                                            pool, n_opp, rng))
    qs = _QS if bins == FEATURE_DIM else np.linspace(0.025, 0.975, bins)
    return np.quantile(np.asarray(equities, dtype=np.float64),
                       qs).astype(np.float32)


# ------------------------------------------------------------------- k-means
def kmeans(X, k, iters=30, seed=0, device=None, n_init=3):
    """k-means with proper k-means++ init (d^2 sampling, running-min update),
    scatter-based centroid updates, and best-of-n_init restarts. Uses CUDA
    when torch sees a GPU."""
    import torch

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    Xt = torch.as_tensor(X, dtype=torch.float32, device=device)
    n = Xt.shape[0]
    k = min(k, n)

    best_C, best_inertia = None, float("inf")
    for trial in range(max(1, n_init)):
        g = torch.Generator(device="cpu").manual_seed(seed + 9973 * trial)
        C = torch.empty((k, Xt.shape[1]), dtype=torch.float32, device=device)
        C[0] = Xt[int(torch.randint(n, (1,), generator=g))]
        d2 = ((Xt - C[0]) ** 2).sum(dim=1)  # running min sq-distance
        for j in range(1, k):
            probs = (d2 / (d2.sum() + 1e-12)).cpu()
            C[j] = Xt[int(torch.multinomial(probs, 1, generator=g))]
            d2 = torch.minimum(d2, ((Xt - C[j]) ** 2).sum(dim=1))

        for _ in range(iters):
            assign = torch.cdist(Xt, C).argmin(dim=1)
            sums = torch.zeros_like(C)
            sums.index_add_(0, assign, Xt)
            counts = torch.bincount(assign, minlength=k)
            live = counts > 0
            C[live] = sums[live] / counts[live].unsqueeze(1).float()
            n_dead = int((~live).sum())
            if n_dead:  # dead clusters: reseed on random points
                ridx = torch.randint(n, (n_dead,), generator=g).to(device)
                C[~live] = Xt[ridx]

        assign = torch.cdist(Xt, C).argmin(dim=1)
        inertia = float(((Xt - C[assign]) ** 2).sum())
        if inertia < best_inertia:
            best_inertia, best_C = inertia, C.clone()
    return best_C.cpu().numpy()


# ------------------------------------------------------------- runtime lookup
class BucketAssigner:
    """Maps (hole, board) -> bucket id using saved centroids, with caching.

    Preflop returns the lossless 169-class id. Flop/turn compute the equity
    feature (deterministic per canonical hand) and take the nearest centroid;
    the river bins exact equity directly (meta 'river_bins'). Lookup layers:
    a bounded raw-tuple memo (skips the 24-permutation canonicalization on
    repeat visits), then the canonical cache (flop unbounded — its space is
    ~1.3M keys — turn bounded FIFO). River results go in the raw memo only —
    its canonical space is ~2.4B keys, a persistent cache never pays off —
    while the exact equity itself comes from the module-level per-board rank
    table, shared across all holes on a board.
    """

    STREET_OF_LEN = {0: 0, 3: 1, 4: 2, 5: 3}
    # per-PROCESS caches: at 20 workers these multiply 20x, so keep them lean
    TURN_CACHE_CAP = 300_000
    RAW_MEMO_CAP = 300_000

    def __init__(self, bucket_dir="buckets"):
        self.bucket_dir = bucket_dir
        self.centroids = {}
        self.meta = {}
        for street in ("flop", "turn", "river"):
            path = os.path.join(bucket_dir, f"{street}_centroids.npy")
            if os.path.exists(path):
                self.centroids[street] = np.load(path)
        meta_path = os.path.join(bucket_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                self.meta = json.load(f)
        self.river_bins = self.meta.get("river_bins")
        self.build_id = self._compute_build_id()

        self.cache_flop = {}
        self.cache_turn = {}
        self.raw_memo = {}
        self._new_entries = {}  # canonical additions since last pop (for sync)
        self.cache_path = os.path.join(bucket_dir, "assign_cache.pkl")
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "rb") as f:
                    blob = pickle.load(f)
                if (isinstance(blob, dict) and "build_id" in blob
                        and blob["build_id"] == self.build_id):
                    self.cache_flop = blob.get("flop", {})
                    self.cache_turn = blob.get("turn", {})
                # legacy or mismatched caches are dropped silently: their
                # entries were computed under a different abstraction
            except Exception:
                pass

    def _compute_build_id(self):
        """Fingerprint of the centroid build + interpreter-stable settings."""
        if not self.centroids and self.river_bins is None:
            return None
        h = hashlib.sha1()
        h.update(json.dumps(self.meta, sort_keys=True).encode())
        for street in ("flop", "turn", "river"):
            arr = self.centroids.get(street)
            if arr is not None:
                h.update(street.encode())
                h.update(np.ascontiguousarray(arr).tobytes())
        return h.hexdigest()

    def _street_params(self, name):
        per = self.meta.get("streets", {}).get(name, {})
        return (per.get("n_runouts", self.meta.get("n_runouts", 48)),
                per.get("n_opp", self.meta.get("n_opp", 22)),
                per.get("bins", self.meta.get("bins", FEATURE_DIM)))

    def num_buckets(self, street_index: int) -> int:
        if street_index == 0:
            return 169
        name = ("flop", "turn", "river")[street_index - 1]
        if name == "river" and self.river_bins:
            return self.river_bins
        return len(self.centroids[name])

    def bucket(self, hole, board) -> int:
        street = self.STREET_OF_LEN[len(board)]
        if street == 0:
            return preflop_class(hole)
        raw = (hole[0], hole[1]) + tuple(board)
        hit = self.raw_memo.get(raw)
        if hit is not None:
            return hit

        if street == 3 and self.river_bins:
            eq = river_equity(hole, board)
            b = min(int(eq * self.river_bins), self.river_bins - 1)
            self._memo_raw(raw, b)
            return b

        name = ("flop", "turn", "river")[street - 1]
        cache = self.cache_flop if street == 1 else self.cache_turn
        key = canonical_key(hole, board)
        b = cache.get(key)
        if b is None:
            n_runouts, n_opp, bins = self._street_params(name)
            feat = equity_feature(hole, board, n_runouts=n_runouts,
                                  n_opp=n_opp, bins=bins, _canon=key)
            cent = self.centroids[name]
            b = int(np.argmin(((cent - feat[None, :]) ** 2).sum(axis=1)))
            self._store(street, key, b)
        self._memo_raw(raw, b)
        return b

    def _memo_raw(self, raw, b):
        if len(self.raw_memo) >= self.RAW_MEMO_CAP:
            self.raw_memo.clear()
        self.raw_memo[raw] = b

    def _store(self, street, key, b):
        cache = self.cache_flop if street == 1 else self.cache_turn
        if cache is self.cache_turn and len(cache) >= self.TURN_CACHE_CAP:
            cache.pop(next(iter(cache)))  # FIFO eviction
        cache[key] = b
        self._new_entries[key] = (street, b)

    # ------------------------------------------------- multi-process cache sync
    def pop_new_entries(self):
        """Canonical cache entries added since the last call (for shipping to
        other workers). Cheap: keys + small ints."""
        out = self._new_entries
        self._new_entries = {}
        return out

    def apply_new_entries(self, entries):
        """Fold in entries computed by other workers."""
        for key, (street, b) in entries.items():
            cache = self.cache_flop if street == 1 else self.cache_turn
            if cache is self.cache_turn and len(cache) >= self.TURN_CACHE_CAP:
                cache.pop(next(iter(cache)))
            cache[key] = b

    # -------------------------------------------------------------- persistence
    def save_cache(self):
        os.makedirs(self.bucket_dir, exist_ok=True)
        blob = {"build_id": self.build_id, "flop": self.cache_flop,
                "turn": self.cache_turn}
        tmp = self.cache_path + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump(blob, f, protocol=pickle.HIGHEST_PROTOCOL)
        # a concurrent reader (eval/searchab loading the cache) blocks
        # os.replace on Windows — retry, and give up QUIETLY: the cache is
        # a pure accelerator, never worth killing a training master over
        for attempt in range(8):
            try:
                os.replace(tmp, self.cache_path)
                return
            except PermissionError:
                time.sleep(0.25 * (attempt + 1))
        print(f"WARNING: bucket cache save skipped (reader holding "
              f"{self.cache_path}); will retry at the next save")
