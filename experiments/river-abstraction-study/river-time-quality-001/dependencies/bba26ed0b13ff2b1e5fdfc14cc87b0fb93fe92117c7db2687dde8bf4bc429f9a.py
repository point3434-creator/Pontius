"""Stateless hierarchically keyed randomness (semantic-event CRN).

The searchmatch ablation showed cross-mode pairing collapses (rho ~ 0.3)
because every draw comes from one mutable cursor: the first control-flow
difference between two continuation modes shifts EVERY later draw. This
module replaces cursors with keys — a random value is a pure function of
WHAT the event is, never of how many draws happened before it:

    value = f(root_seed, scope, namespace, semantic key)

so two runs that differ only in continuation mode (or exploration order,
scheduling, process count) agree on every shared semantic event: decks,
private deals, board runouts, leaf rollout streams, table-action uniforms.

Two levels (benchmarked 2026-08-12 on the project venv, see git message):

  * scope boundaries (evaluation / pair / solve) — BLAKE2b-128 over
    fixed-width unsigned little-endian words. Cold path, once per hand or
    per re-solve; collision-grade hashing.
  * hot draws — a SplitMix64 absorb chain over
    (scope ^ namespace ^ k1 ^ k2 ^ k3), 53-bit uniforms. Measured 2032
    ns/draw vs 3515 for C-blake2b scalar; the numpy bulk-lane variant is
    69 ns/draw and is bit-identical to the scalar chain lane by lane.

Discipline (violations break CRN silently — the gauntlet in
test_searchab.py exists to catch them):

  * continuation MODE never appears in any shared-event key, nor does the
    traverser's bias branch: leaf values are INDEXED by bias enum, the
    rollout seed is shared across the four branches.
  * every key word is a non-negative int < 2**64, encoded fixed-width LE
    at hash boundaries. Never repr/JSON/pickle/Python-hash/dict order.
  * compound events use lanes (per-seat priorities, per-seat selections,
    per-card counters) so one seat's rejection-loop length can never shift
    another seat's draws. Candidate lists are walked in deterministic
    combo-id order.
  * namespaces are full-width 64-bit constants derived from versioned
    names (weak small-int constants would XOR-cancel against small keys);
    test_keyed re-derives them, so editing one is loud.

Leaf rollouts intentionally stay cursor-based (random.Random) — the unit
is keyed by its semantic seed, and draws inside one rollout never need to
be shared with anything else.
"""
import struct
from hashlib import blake2b

import numpy as np

SCHEMA_VERSION = 1

M64 = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15
_MIX1 = 0xBF58476D1CE4E5B9
_MIX2 = 0x94D049BB133111EB
_INV53 = 2.0 ** -53

# --------------------------------------------------------------- namespaces
# blake2b-64 of "pluribus-lite/ns/<name>/v1" (test_keyed re-derives these).
NS_TABLE_ACTION = 0x1CAA46AC7C032234  # table-action
NS_ACTION_TRANSLATION = 0x01246AB58DC30994  # action-translation
NS_SEARCH_PRIVATE_DEAL = 0x8D7B0679CE51255D  # search-private-deal
NS_SEARCH_BOARD_RUNOUT = 0x57F171AA4D28E4FE  # search-board-runout
NS_SEARCH_NODE_ACTION = 0x2E9D3D5F8A4D96A1  # search-node-action
NS_CONTINUATION_CHOICE = 0x5B2748F759D02B49  # continuation-choice
NS_LEAF_ROLLOUT = 0x2FAAEA560480E146  # leaf-rollout
NS_CBV_ROLLOUT = 0xDC64DAFBFF43EA15  # cbv-rollout
NS_DECK_DEAL = 0x65099AF3992A9B18  # deck-deal
NS_TRAIN_ITERATION = 0x9DC4EF580D16DEFE  # train-iteration

# fingerprint chain seeds: separate channels for the translated-abstract
# history (blueprint key space) and the chip-exact real history ('x' tokens)
FP_ABS_INIT = 0x3BC54163D922FFFD  # fp-abstract
FP_REAL_INIT = 0x0B4F48ACF0D26112  # fp-real

NAMESPACES = {
    "table-action": NS_TABLE_ACTION,
    "action-translation": NS_ACTION_TRANSLATION,
    "search-private-deal": NS_SEARCH_PRIVATE_DEAL,
    "search-board-runout": NS_SEARCH_BOARD_RUNOUT,
    "search-node-action": NS_SEARCH_NODE_ACTION,
    "continuation-choice": NS_CONTINUATION_CHOICE,
    "leaf-rollout": NS_LEAF_ROLLOUT,
    "cbv-rollout": NS_CBV_ROLLOUT,
    "deck-deal": NS_DECK_DEAL,
    "train-iteration": NS_TRAIN_ITERATION,
    "fp-abstract": FP_ABS_INIT,
    "fp-real": FP_REAL_INIT,
}

# scope kinds (word 0 of every derivation, alongside the schema version)
KIND_EVAL, KIND_PAIR, KIND_SOLVE, KIND_TRAIN = 1, 2, 3, 4


# ----------------------------------------------------------------- hot path
def mix64(z):
    """SplitMix64 finalizer over a 64-bit word."""
    z = (z ^ (z >> 30)) * _MIX1 & M64
    z = (z ^ (z >> 27)) * _MIX2 & M64
    return z ^ (z >> 31)


def u64(scope, ns, k1=0, k2=0, k3=0):
    """Keyed 64-bit value: pure function of (scope, ns, k1, k2, k3).

    `scope` is a 128-bit scope key from derive_scope(); ns one of the
    NS_* constants; k1..k3 non-negative ints < 2**64 whose meaning the
    call site owns (documented there). Hot path: fixed args, no strings.
    """
    z = (scope & M64) ^ ns
    z = mix64((z + _GOLDEN) & M64)
    z ^= (scope >> 64) & M64
    z = mix64((z + _GOLDEN) & M64)
    z ^= k1
    z = mix64((z + _GOLDEN) & M64)
    z ^= k2
    z = mix64((z + _GOLDEN) & M64)
    z ^= k3
    return mix64((z + _GOLDEN) & M64)


def u01(scope, ns, k1=0, k2=0, k3=0):
    """Keyed uniform in [0, 1) with 53 significant bits."""
    return (u64(scope, ns, k1, k2, k3) >> 11) * _INV53


def u01_lanes(scope, ns, k1, k2, n):
    """n uniforms, lane i bit-identical to u01(scope, ns, k1, k2, i).

    Vectorized SplitMix64 over the lane axis — 69 ns/draw at n=1000 vs
    2 us scalar; use for bulk draws (future dense-solver chance layers).
    """
    z = (scope & M64) ^ ns
    z = mix64((z + _GOLDEN) & M64)
    z ^= (scope >> 64) & M64
    z = mix64((z + _GOLDEN) & M64)
    z ^= k1
    z = mix64((z + _GOLDEN) & M64)
    z ^= k2
    z = mix64((z + _GOLDEN) & M64)
    lanes = np.arange(n, dtype=np.uint64)
    with np.errstate(over="ignore"):
        v = (np.uint64(z) ^ lanes) + np.uint64(_GOLDEN)
        v = (v ^ (v >> np.uint64(30))) * np.uint64(_MIX1)
        v = (v ^ (v >> np.uint64(27))) * np.uint64(_MIX2)
        v = v ^ (v >> np.uint64(31))
    return (v >> np.uint64(11)).astype(np.float64) * _INV53


# ------------------------------------------------------------------- scopes
_PACK6 = struct.Struct("<6Q").pack


def derive_scope(kind, parent, k1=0, k2=0, k3=0):
    """128-bit scope key. Cold path (once per evaluation/pair/solve).

    kind: KIND_* constant. parent: the enclosing scope (0 at the root —
    KIND_EVAL derives from the user seed via k1). k1..k3: identity words
    (deal index, rotation, seat, history fingerprint...). All fixed-width
    unsigned LE into BLAKE2b-128; no strings, no repr.
    """
    if not (0 <= k1 <= M64 and 0 <= k2 <= M64 and 0 <= k3 <= M64):
        raise ValueError("scope key words must be uint64")
    data = _PACK6((SCHEMA_VERSION << 8) | kind, parent & M64,
                  (parent >> 64) & M64, k1, k2, k3)
    return int.from_bytes(blake2b(data, digest_size=16).digest(), "little")


# ------------------------------------------------------- sampling utilities
def pick_from_cdf(u, probs):
    """Inverse-CDF index into a probability vector (last index absorbs
    rounding slack, matching the sampling loops used everywhere else)."""
    acc = 0.0
    last = len(probs) - 1
    for i in range(last):
        acc += probs[i]
        if u < acc:
            return i
    return last


def draw_k(scope, ns, k1, k2, pool, k):
    """k distinct items from `pool` without replacement, keyed.

    Draw c uses key (k1, k2 + c): the caller owns (k1, k2) uniqueness and
    must leave k2..k2+k-1 free. `pool` must arrive in deterministic order
    (sorted card ints everywhere in this project); a copy is consumed.
    u < 1 so int(u * m) <= m - 1: every pick is in range by construction.
    """
    pool = list(pool)
    out = []
    for c in range(k):
        idx = int(u01(scope, ns, k1, k2 + c) * len(pool))
        out.append(pool.pop(idx))
    return out


def unrank_pair(t, m):
    """t-th pair (i, j), i < j, of m items in lexicographic order —
    a single uniform picks an unordered pair with no rejection loop."""
    for i in range(m - 1):
        row = m - 1 - i
        if t < row:
            return i, i + 1 + t
        t -= row
    raise ValueError("pair rank out of range")


# ------------------------------------------------- history fingerprints
# token codes: stable small ints for menu tokens, a tagged wide code for
# off-tree chip-exact raises. 0 is reserved (never a token).
_TC_FOLD, _TC_CALL, _TC_ALLIN, _TC_STREET = 1, 2, 3, 4
_TC_RAISE_BASE = 16  # 'r<i>' -> 16 + i
_TC_OFFTREE_TAG = 1 << 40  # 'x<chips>' -> tag | chips
ACTION_CODE_BASE = 1 << 16  # solve-internal action ids live above tokens


def token_code(tok):
    """Stable integer code for one engine history token."""
    c = tok[0]
    if c == "f":
        return _TC_FOLD
    if c == "c":
        return _TC_CALL
    if c == "a":
        return _TC_ALLIN
    if c == "/":
        return _TC_STREET
    if c == "r":
        return _TC_RAISE_BASE + int(tok[1:])
    if c == "x":
        return _TC_OFFTREE_TAG | int(tok[1:])
    raise ValueError(f"unknown history token {tok!r}")


def action_code(action_id):
    """Code for a solve-internal step by menu action id (the id sequence
    from a fixed root is path-unique: street separators are a
    deterministic function of the actions)."""
    return ACTION_CODE_BASE + action_id


def fp_extend(fp, code):
    """Extend a rolling history fingerprint by one token/action code."""
    return mix64(fp ^ mix64((code + _GOLDEN) & M64))


def fp_history(tokens, init=FP_ABS_INIT):
    """Fingerprint of a whole token sequence (init selects the channel)."""
    fp = init
    for tok in tokens:
        fp = fp_extend(fp, token_code(tok))
    return fp


# ------------------------------------------------------------- card packing
def pack2(a, b):
    """Two card ints (0..51) packed 6 bits each, order-free (12 bits)."""
    if a > b:
        a, b = b, a
    return (b << 6) | a


TAG_EXACT, TAG_BUCKET, TAG_PREFLOP = 0, 1, 2


def hand_key_exact(a, b):
    """Tagged 16-bit hand key for an exact two-card combo (ComboIndex
    interop: tag 2 bits << 14 | payload; bucket/preflop tags reserved)."""
    return (TAG_EXACT << 14) | pack2(a, b)
