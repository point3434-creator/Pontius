"""Structure-of-arrays regret/strategy storage with a shared-memory backend.

The dict[str] -> Node layout costs ~400-450 B/infoset *per worker* (Python
object + two small ndarrays + dict entry + key string) — at 20M+ infosets
that is the machine's RAM wall, not cores. Here the table is two float64
slabs (regret, strat) of shape [rows, max_actions], allocated in fixed-size
SEGMENTS, plus an int8 action-count array and a key index:

  local backend  — plain numpy segments, one process (run_single, tests)
  shared backend — segments live in multiprocessing.shared_memory: ONE copy
                   machine-wide. The MASTER owns all mutation (row
                   assignment, delta application, discounting, saving);
                   workers attach read-only-by-convention and buffer their
                   sync window privately (WindowOverlay), so worker table
                   RAM is ~zero and 20+ workers fit again.

The key index is an open-addressed hash table over 16-byte BLAKE2b digests
(collision odds at 100M keys ~ 2^-74) stored in one shared block: 24-byte
slots [digest | int32 row | pad], linear probing, master-only inserts,
lock-free reads. A digest of all zeros marks an empty slot.

Checkpoints are a DIRECTORY of raw array dumps (ndarray.tofile) + the index
blob + meta.json — sequential disk speed instead of pickling one multi-GB
object graph. Legacy dict-of-Nodes .pkl checkpoints load transparently and
are converted on the next save.
"""
import hashlib
import json
import os
import shutil
import time
from multiprocessing import shared_memory

import numpy as np

SEG_ROWS = 2_097_152          # rows per segment (~235 MB at width 7)
SLOT = 24                     # index slot: 16B digest + 4B row + 4B pad
EMPTY = b"\x00" * 16
CKPT_FORMAT = 1


def key_digest(key: str) -> bytes:
    return hashlib.blake2b(key.encode(), digest_size=16).digest()


class KeyIndex:
    """Open-addressed digest -> row map in one buffer (shared or local).

    Master-only inserts; readers probe lock-free. No deletions, load factor
    kept under ~0.5 by construction (capacity fixed at init).
    """

    HEADER = 8  # leading u64 key count — FIXED offset (Windows pads the
    #             mapping tail to page size, so nothing may live at the end)

    def __init__(self, capacity_keys, shm_name=None, create=True):
        self.capacity = 1
        while self.capacity < capacity_keys * 2:
            self.capacity *= 2
        nbytes = self.HEADER + self.capacity * SLOT
        if shm_name is None:
            self.shm = None
            self.buf = np.zeros(nbytes, dtype=np.uint8)
        elif create:
            self.shm = shared_memory.SharedMemory(
                name=shm_name, create=True, size=nbytes)
            self.buf = np.frombuffer(self.shm.buf, dtype=np.uint8)
            self.buf[:] = 0
        else:
            self.shm = shared_memory.SharedMemory(name=shm_name)
            self.buf = np.frombuffer(self.shm.buf, dtype=np.uint8)
        self._mv = self.buf.data

    def __len__(self):
        return int(np.frombuffer(self._mv[:8], dtype=np.uint64)[0])

    def is_full(self):
        """Whether another key can be admitted at the fixed 0.5 load cap."""
        return len(self) * 2 >= self.capacity

    def _bump(self):
        n = len(self) + 1
        self.buf[:8] = np.frombuffer(np.uint64(n).tobytes(), dtype=np.uint8)

    def _slot_of(self, digest):
        return int.from_bytes(digest[:8], "little") & (self.capacity - 1)

    def get(self, digest):
        mv = self._mv
        cap = self.capacity
        i = self._slot_of(digest)
        while True:
            off = self.HEADER + i * SLOT
            d = bytes(mv[off:off + 16])
            if d == digest:
                return int.from_bytes(mv[off + 16:off + 20], "little")
            if d == EMPTY:
                return None
            i = (i + 1) & (cap - 1)

    def bulk_load(self, pairs):
        """Vectorized rebuild of a FRESH index from packed (digest16, row4)
        records (uint8 [N, 20]). Same digest->row mapping as sequential
        insert (probe layout may differ; nothing reads layout). The
        per-record Python loop cost ~3-6 us/key — 6-13 MINUTES at 134M
        keys, paid on every checkpoint load (ultracode audit); this is
        rounds of numpy scatter over 4M-key chunks instead.
        """
        assert len(self) == 0, "bulk_load wants an empty index"
        cap = self.capacity
        n = len(pairs)
        slots_view = self.buf[self.HEADER:self.HEADER
                              + cap * SLOT].reshape(cap, SLOT)
        lo = pairs[:, :8].copy().view(np.uint64).reshape(-1)
        home = (lo & np.uint64(cap - 1)).astype(np.int64)
        for start in range(0, n, 4_000_000):  # bound temp memory
            idx = np.arange(start, min(start + 4_000_000, n))
            target = home[idx].copy()
            while len(idx):
                occ = slots_view[target, :16].any(axis=1)
                free_i = np.flatnonzero(~occ)
                if len(free_i):
                    t_free = target[free_i]
                    order = np.argsort(t_free, kind="stable")
                    ts = t_free[order]
                    first = np.concatenate(([True], ts[1:] != ts[:-1]))
                    winners = idx[free_i[order[first]]]
                    slots_view[ts[first], :20] = pairs[winners, :20]
                    placed = np.zeros(len(idx), dtype=bool)
                    placed[free_i[order[first]]] = True
                else:
                    placed = np.zeros(len(idx), dtype=bool)
                idx = idx[~placed]
                target = (target[~placed] + 1) & (cap - 1)
        self.buf[:8] = np.frombuffer(np.uint64(n).tobytes(), dtype=np.uint8)

    def insert(self, digest, row):
        """Master only. Returns the row actually stored (existing on race)."""
        mv = self._mv
        cap = self.capacity
        i = self._slot_of(digest)
        while True:
            off = self.HEADER + i * SLOT
            d = bytes(mv[off:off + 16])
            if d == digest:
                return int.from_bytes(mv[off + 16:off + 20], "little")
            if d == EMPTY:
                if len(self) * 2 >= cap:
                    raise MemoryError(
                        f"key index full ({len(self):,} keys, capacity "
                        f"{cap:,}) — raise --max-infosets")
                mv[off + 16:off + 20] = row.to_bytes(4, "little")
                mv[off:off + 16] = digest  # digest last: readers see complete
                self._bump()
                return row
            i = (i + 1) & (cap - 1)

    def close(self):
        self._mv = None
        self.buf = None
        if self.shm is not None:
            try:
                self.shm.close()
            except BufferError:
                pass  # externally-held views; the OS reclaims at process exit


class FrequencySketch:
    """TinyLFU-style admission gate: a count-min sketch with aging.

    Filters the frontier tail — measured on a real 97.8M-row checkpoint,
    90.6% of infosets were visited at most ~once and 18% never accumulated
    any strategy at all; admitting a line into the table only after
    `min_visits` sightings cuts that waste at fixed memory cost.

    d=2 counter rows, indexed by slicing the SAME 16-byte BLAKE2 digest the
    key index already computed (bytes 0..8 and 8..16) — the gate adds no
    hashing. uint8 counters with conservative update, saturating at 255.
    age() halves everything: recency semantics plus saturation control.
    Lock-free by design: racy increments only under-count (a hand waits one
    more visit), hash collisions only over-count (a noise line admitted
    early) — both benign, so workers share one sketch with no locks.
    Not persisted in checkpoints: after a resume the frontier simply
    re-earns admission under the same rule.
    """

    def __init__(self, cells=2 ** 27, shm_name=None, create=True):
        self.cells = cells
        nbytes = 2 * cells
        if shm_name is None:
            self.shm = None
            self.buf = np.zeros(nbytes, dtype=np.uint8)
        elif create:
            self.shm = shared_memory.SharedMemory(name=shm_name, create=True,
                                                  size=nbytes)
            self.buf = np.frombuffer(self.shm.buf, dtype=np.uint8)
            self.buf[:] = 0
        else:
            self.shm = shared_memory.SharedMemory(name=shm_name)
            self.buf = np.frombuffer(self.shm.buf, dtype=np.uint8,
                                     count=nbytes)

    def bump(self, digest):
        """Record one sighting; return the new min-count estimate."""
        c = self.cells
        i1 = int.from_bytes(digest[:8], "little") % c
        i2 = c + int.from_bytes(digest[8:16], "little") % c
        b = self.buf
        v1, v2 = int(b[i1]), int(b[i2])
        m = v1 if v1 < v2 else v2
        if v1 == m and v1 < 255:  # conservative update: min cells only
            b[i1] = v1 + 1
        if v2 == m and v2 < 255:
            b[i2] = v2 + 1
        return m + 1

    def age(self):
        """Halve all counters (master-only, at a barrier)."""
        np.right_shift(self.buf, 1, out=self.buf)

    def close(self, unlink=False):
        self.buf = None
        if self.shm is not None:
            try:
                self.shm.close()
            except BufferError:
                pass
            if unlink:
                try:
                    self.shm.unlink()
                except FileNotFoundError:
                    pass


class SlabTable:
    """Segmented [rows, width] regret/strat slabs + n_actions, local or shared.

    Master constructs with create=True (allocates segments as rows grow).
    Workers construct with attach_spec=... and call sync_attach() after each
    barrier to map any new segments the master announced.
    """

    def __init__(self, width, max_keys=1_000_000, shared_prefix=None,
                 create=True):
        self.width = width
        self.max_keys = max_keys
        self.prefix = shared_prefix          # None => local numpy backend
        self.create = create
        self.reg_segs = []
        self.strat_segs = []
        self.nact_segs = []
        self._shms = []
        self.rows = 0                        # assigned rows (master truth)
        self.index = KeyIndex(
            max_keys,
            shm_name=None if shared_prefix is None else f"{shared_prefix}_idx",
            create=create)
        if not create:
            self.rows = len(self.index)

    # ---------------------------------------------------------------- storage
    def _seg_names(self, k):
        return (f"{self.prefix}_r{k}", f"{self.prefix}_s{k}",
                f"{self.prefix}_a{k}")

    def _add_segment(self):
        k = len(self.reg_segs)
        shape = (SEG_ROWS, self.width)
        if self.prefix is None:
            self.reg_segs.append(np.zeros(shape))
            self.strat_segs.append(np.zeros(shape))
            self.nact_segs.append(np.zeros(SEG_ROWS, dtype=np.int8))
            return
        rn, sn, an = self._seg_names(k)
        for name, dtype, count, target in (
                (rn, np.float64, SEG_ROWS * self.width, self.reg_segs),
                (sn, np.float64, SEG_ROWS * self.width, self.strat_segs),
                (an, np.int8, SEG_ROWS, self.nact_segs)):
            nbytes = count * np.dtype(dtype).itemsize
            shm = shared_memory.SharedMemory(name=name, create=self.create,
                                             size=nbytes)
            self._shms.append(shm)
            arr = np.frombuffer(shm.buf, dtype=dtype, count=count)
            if self.create:
                arr[:] = 0
            target.append(arr.reshape(shape) if dtype is np.float64 else arr)

    def n_segments(self):
        return len(self.reg_segs)

    def sync_attach(self, n_segments):
        """Worker side: attach any segments the master created since."""
        while len(self.reg_segs) < n_segments:
            self._add_segment()
        self.rows = len(self.index)

    def _loc(self, row):
        return row // SEG_ROWS, row % SEG_ROWS

    # ----------------------------------------------------------------- access
    def lookup(self, key):
        return self.index.get(key_digest(key))

    def row_values(self, row):
        """(regret_row, strat_row, n_actions) — views, do not mutate outside
        the master."""
        s, o = self._loc(row)
        n = int(self.nact_segs[s][o])
        return self.reg_segs[s][o, :n], self.strat_segs[s][o, :n], n

    def assign_row(self, key, n_actions):
        """Master only: row for key, allocating if new."""
        digest = key_digest(key)
        row = self.index.get(digest)
        if row is not None:
            return row
        row = self.rows
        while row >= len(self.reg_segs) * SEG_ROWS:
            self._add_segment()
        s, o = self._loc(row)
        self.nact_segs[s][o] = n_actions
        stored = self.index.insert(digest, row)
        if stored == row:
            self.rows += 1
        return stored

    # ------------------------------------------------------- master mutation
    def apply_pack(self, rows, dreg, dstrat):
        """Add a worker window's deltas (unique rows). Floor separately."""
        for seg in range(len(self.reg_segs)):
            lo, hi = seg * SEG_ROWS, (seg + 1) * SEG_ROWS
            m = (rows >= lo) & (rows < hi)
            if not m.any():
                continue
            off = rows[m] - lo
            w = dreg.shape[1]
            self.reg_segs[seg][off, :w] += dreg[m]
            self.strat_segs[seg][off, :w] += dstrat[m]

    def floor_rows(self, rows, floor):
        for seg in range(len(self.reg_segs)):
            lo, hi = seg * SEG_ROWS, (seg + 1) * SEG_ROWS
            m = (rows >= lo) & (rows < hi)
            if not m.any():
                continue
            off = rows[m] - lo
            # fancy indexing copies: compute then write back
            self.reg_segs[seg][off] = np.maximum(self.reg_segs[seg][off],
                                                 floor)

    def discount(self, factor, floor):
        """Linear-CFR regret scale + gamma=2 strat scale + prune floor."""
        f2 = factor * factor
        full, last = divmod(self.rows, SEG_ROWS)
        for seg in range(len(self.reg_segs)):
            n = SEG_ROWS if seg < full else last
            if n == 0:
                break
            r = self.reg_segs[seg][:n]
            r *= factor
            np.maximum(r, floor, out=r)
            self.strat_segs[seg][:n] *= f2

    def floor_all(self, floor):
        """Raise every stored regret to ``floor`` without changing strategy."""
        full, last = divmod(self.rows, SEG_ROWS)
        for seg in range(len(self.reg_segs)):
            n = SEG_ROWS if seg < full else last
            if n == 0:
                break
            np.maximum(self.reg_segs[seg][:n], floor,
                       out=self.reg_segs[seg][:n])

    # ------------------------------------------------------------ iteration
    def iter_rows(self):
        for row in range(self.rows):
            s, o = self._loc(row)
            n = int(self.nact_segs[s][o])
            yield row, self.reg_segs[s][o, :n], self.strat_segs[s][o, :n]

    def close(self, unlink=False):
        idx_shm = self.index.shm
        self.reg_segs = []
        self.strat_segs = []
        self.nact_segs = []
        self.index.close()
        for shm in self._shms:
            try:
                shm.close()
            except BufferError:
                pass  # externally-held row views; OS reclaims at exit
            if unlink:
                try:
                    shm.unlink()
                except FileNotFoundError:
                    pass
        if unlink and idx_shm is not None:
            try:
                idx_shm.unlink()
            except FileNotFoundError:
                pass

    # ---------------------------------------------------------- checkpointing
    def save_dir(self, path, meta):
        """Raw-dump checkpoint: sequential IO, no object pickling."""
        tmp = path + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        full, last = divmod(self.rows, SEG_ROWS)
        n_segs = full + (1 if last else 0)
        for seg in range(n_segs):
            n = SEG_ROWS if seg < full else last
            np.ascontiguousarray(self.reg_segs[seg][:n]).tofile(
                os.path.join(tmp, f"reg{seg}.bin"))
            np.ascontiguousarray(self.strat_segs[seg][:n]).tofile(
                os.path.join(tmp, f"strat{seg}.bin"))
            np.ascontiguousarray(self.nact_segs[seg][:n]).tofile(
                os.path.join(tmp, f"nact{seg}.bin"))
        # compact index dump: occupied (digest, row) pairs only — small, and
        # loading rehashes so --max-infosets may change between runs
        h = KeyIndex.HEADER
        slots = self.index.buf[h:h + self.index.capacity * SLOT].reshape(
            self.index.capacity, SLOT)
        occupied = slots[~(slots[:, :16] == 0).all(axis=1)]
        np.ascontiguousarray(occupied[:, :20]).tofile(
            os.path.join(tmp, "index.bin"))
        meta = dict(meta, ckpt_format=CKPT_FORMAT, rows=self.rows,
                    width=self.width, seg_rows=SEG_ROWS)
        with open(os.path.join(tmp, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
        # swap: current -> .bak, tmp -> current (rename beats rewriting).
        # TRANSACTIONAL: never delete a dir that may be the only good copy.
        # The old loop rmtree'd .bak at the top of EVERY attempt, so after
        # a partial attempt (current parked at .bak, promote failed) the
        # next retry destroyed the last good checkpoint (2026-08-12
        # review). Now the old backup is removed only while a good CURRENT
        # still exists, and a total failure rolls .bak back into place so
        # a loadable checkpoint always remains.
        bak = path + ".bak"
        try:
            # ~75s of exponential backoff: checkpoint READERS (eval/play/
            # searchab loading this dir) hold files open for minutes on
            # Windows, which blocks directory renames — 2.5s of retries
            # lost that race every time (ultracode audit 2026-08-12)
            for attempt in range(12):
                try:
                    if os.path.exists(path):
                        shutil.rmtree(bak, ignore_errors=True)
                        os.rename(path, bak)
                    os.rename(tmp, path)
                    return
                except PermissionError:
                    time.sleep(0.5 * 1.35 ** attempt)
        finally:
            # rollback runs on EVERY exit — retry exhaustion, an unexpected
            # OSError, or a KeyboardInterrupt landing mid-retry — so the
            # parked last-good checkpoint always returns to `path`
            if not os.path.exists(path) and os.path.isdir(bak):
                try:
                    os.rename(bak, path)
                except OSError:
                    pass
        raise OSError(f"could not swap checkpoint into {path} — new data "
                      f"is intact at {tmp}")

    def preflight_dir(self, path):
        """Validate checkpoint metadata and file sizes before bulk loading.

        A production checkpoint is tens of gigabytes. Configuration and
        capacity errors must be found before reading its multi-gigabyte index
        or allocating/populating slab segments.
        """
        with open(os.path.join(path, "meta.json")) as f:
            meta = json.load(f)
        if meta.get("width") != self.width:
            raise ValueError("checkpoint width mismatch")
        if meta.get("seg_rows") != SEG_ROWS:
            raise ValueError("checkpoint segment size mismatch")
        rows = meta.get("rows")
        if not isinstance(rows, int) or rows < 0:
            raise ValueError("checkpoint has an invalid row count")
        usable = self.index.capacity // 2
        if rows > usable:
            raise MemoryError(f"checkpoint has {rows:,} keys but the index "
                              f"holds at most {usable:,} — "
                              f"raise --max-infosets")
        index_path = os.path.join(path, "index.bin")
        expected_index = rows * 20
        actual_index = os.path.getsize(index_path)
        if actual_index != expected_index:
            raise ValueError(
                f"checkpoint index size mismatch: expected "
                f"{expected_index:,} bytes, found {actual_index:,}")
        full, last = divmod(rows, SEG_ROWS)
        n_segs = full + (1 if last else 0)
        for seg in range(n_segs):
            n = SEG_ROWS if seg < full else last
            for stem, itemsize in (("reg", 8), ("strat", 8), ("nact", 1)):
                expected = n * (self.width if stem != "nact" else 1) * itemsize
                file_path = os.path.join(path, f"{stem}{seg}.bin")
                actual = os.path.getsize(file_path)
                if actual != expected:
                    raise ValueError(
                        f"checkpoint file size mismatch for {file_path}: "
                        f"expected {expected:,} bytes, found {actual:,}")
        return meta

    def load_dir(self, path, meta=None):
        meta = self.preflight_dir(path) if meta is None else meta
        rows = meta["rows"]
        pairs = np.fromfile(os.path.join(path, "index.bin"),
                            dtype=np.uint8).reshape(-1, 20)
        # compare against the REAL usable capacity (power-of-two allocation
        # at load factor 1/2), not the nominal max_keys request
        usable = self.index.capacity // 2
        if len(pairs) > usable:
            raise MemoryError(f"checkpoint has {len(pairs):,} keys but the "
                              f"index holds at most {usable:,} — "
                              f"raise --max-infosets")
        if len(self.index) == 0:
            self.index.bulk_load(pairs)
        else:  # defensive: partially-populated index (not a normal load)
            for rec in pairs:
                digest = rec[:16].tobytes()
                self.index.insert(
                    digest, int.from_bytes(rec[16:20].tobytes(), "little"))
        seg = 0
        loaded = 0
        while loaded < rows:
            n = min(SEG_ROWS, rows - loaded)
            while seg >= len(self.reg_segs):
                self._add_segment()
            self.reg_segs[seg][:n] = np.fromfile(
                os.path.join(path, f"reg{seg}.bin")).reshape(n, self.width)
            self.strat_segs[seg][:n] = np.fromfile(
                os.path.join(path, f"strat{seg}.bin")).reshape(n, self.width)
            self.nact_segs[seg][:n] = np.fromfile(
                os.path.join(path, f"nact{seg}.bin"), dtype=np.int8)
            loaded += n
            seg += 1
        self.rows = rows
        return meta

    def load_legacy_nodes(self, nodes_dict):
        """Migrate a dict[key] -> (regret, strat) from an old .pkl."""
        for key, (reg, strat) in nodes_dict.items():
            row = self.assign_row(key, len(reg))
            s, o = self._loc(row)
            self.reg_segs[s][o, :len(reg)] = reg
            self.strat_segs[s][o, :len(strat)] = strat


class WindowOverlay:
    """A worker's private view of the shared table for one sync window.

    On first touch of a row, current shared values are copied privately; all
    reads/writes in the window hit the copy. The shared slab is frozen
    between barriers (master is the only writer), so the window's delta is
    simply (private - shared). Brand-new keys (no global row yet) live here
    string-keyed until the master assigns rows at the barrier.

    With a FrequencySketch and min_visits > 1, unseen keys must be sighted
    min_visits times before they are admitted as fresh nodes; until then
    they get throwaway scratch arrays (the traversal proceeds, nothing is
    learned or shipped).
    """

    def __init__(self, table, sketch=None, min_visits=1):
        self.table = table
        self.sketch = sketch
        self.min_visits = min_visits
        self.rows = {}      # row -> [reg_copy, strat_copy, n]
        self.fresh = {}     # key -> [reg, strat, n]
        self.n_dropped_full = 0
        self.n_gated = 0

    def node_values(self, key, n_actions):
        """(regret, strat) arrays private to this window."""
        digest = key_digest(key)
        row = self.table.index.get(digest)
        if row is not None:
            ent = self.rows.get(row)
            if ent is None:
                reg, strat, n = self.table.row_values(row)
                ent = [reg.copy(), strat.copy(), n]
                self.rows[row] = ent
            return ent[0], ent[1]
        ent = self.fresh.get(key)
        if ent is None:
            # Once the fixed-size index is full there is no possible barrier
            # admission. Avoid sketch work and, much more importantly, avoid
            # building/serializing large fresh dictionaries that the master
            # can only discard.
            if self.table.index.is_full():
                self.n_dropped_full += 1
                return np.zeros(n_actions), np.zeros(n_actions)
            if (self.sketch is not None and self.min_visits > 1
                    and self.sketch.bump(digest) < self.min_visits):
                # not admitted yet: learn nothing, ship nothing
                self.n_gated += 1
                return np.zeros(n_actions), np.zeros(n_actions)
            ent = [np.zeros(n_actions), np.zeros(n_actions), n_actions]
            self.fresh[key] = ent
        return ent[0], ent[1]

    def collect(self):
        """(pack, fresh) for the barrier; clears the window.

        pack = (rows int64[n], dreg float64[n, w], dstrat float64[n, w])
        fresh = {key: (reg, strat, n_actions)}
        """
        w = self.table.width
        n = len(self.rows)
        rows = np.empty(n, dtype=np.int64)
        dreg = np.zeros((n, w))
        dstrat = np.zeros((n, w))
        for i, (row, (reg, strat, na)) in enumerate(self.rows.items()):
            rows[i] = row
            sreg, sstrat, _ = self.table.row_values(row)
            dreg[i, :na] = reg - sreg
            dstrat[i, :na] = strat - sstrat
        fresh = {k: (v[0], v[1], v[2]) for k, v in self.fresh.items()}
        self.rows = {}
        self.fresh = {}
        return (rows, dreg, dstrat), fresh

    def pop_stats(self):
        stats = {"dropped_full": self.n_dropped_full,
                 "gated": self.n_gated}
        self.n_dropped_full = 0
        self.n_gated = 0
        return stats
