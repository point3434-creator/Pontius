"""Read-only, strategy-only checkpoint views for evaluation.

A playing policy reads `strat` and `n_actions`. It never reads `reg`. But
`SlabTable.load_dir` materialises the whole training structure, and at
`blueprint_day4_compact` scale (160,147,115 rows, width 7) that is:

    reg 8.352 + strat 8.352 + nact 0.149 + key index 12.000 = 28.85 GiB

The key index dominates and is the part that cannot be paged out. `KeyIndex`
is open-addressed at load factor <= 0.5 with SLOT = 24 B, so 160.1M keys
force 2^29 slots: 12 GiB of RAM to index 3.2 GiB of records, built in-process
by `bulk_load` (measured 83 s at 134M keys, paid once per reader -- and once
per `searchab` WORKER). Everything else is file-backed and evictable.

This module replaces that index with a sorted array on disk, memory-mapped:

    strat 8.352 + nact 0.149 + sidecar 2.999 = 11.50 GiB, all file-backed

which is what makes two checkpoints resident at once (the day4 compaction
certificate: raw 18.30 + compact 11.50 = 29.8 GiB, against the ~68 GB
HANDOFF calls impossible on this box) and what makes the eight-agent mixed
league of the strength protocol possible at all.

Format, safety rules, and verification tiers are pinned in ROADMAP.md under
"EVAL-ONLY CHECKPOINT LOADER -- SPEC". The two rules worth repeating here:

  FROZEN SOURCES ONLY. A memmap holds a Windows file handle for the life of
  the process, and open handles are exactly what blocks `save_dir`'s rename.
  Checking TRAINING.lock at map time does not fix that -- training can start
  afterwards -- so v1 refuses trainer-managed paths categorically instead of
  racing them.

  LOOKUP NEVER ASSUMES `hi` IS UNIQUE. `keys_lo` exists so that a non-member
  query cannot false-hit a stranger's row; the current hash compares all 16
  digest bytes and neither may this.
"""
import bisect
import hashlib
import json
import os
import random
import shutil
import sys
import time

import numpy as np

from .table import SEG_ROWS, key_digest

SIDECAR_FORMAT = 1
SIDECAR_SUFFIX = ".evalidx"
SPOT_RECORDS = 4096

# The exact paths train_blueprint.py:369 writes and SlabTable.save_dir swaps.
# Frozen artifacts (blueprint_dayN_ckpt, *_compact) fall outside this set.
MUTABLE_BASENAMES = frozenset({"blueprint_ckpt", "blueprint_ckpt_rescue"})
MUTABLE_SUFFIXES = (".tmp", ".bak")

SIDECAR_FILES = ("keys_hi.bin", "keys_lo.bin", "rows.bin", "starts.bin")


class SidecarError(Exception):
    """Sidecar is absent, ineligible, stale, or malformed. Fatal by default:
    a present-but-invalid sidecar must never silently degrade into a
    28.85 GiB full load."""


class SidecarUnavailable(SidecarError):
    """The eval loader cannot serve this source, and that is not an error --
    nothing is wrong, the fast path simply does not apply. These are the
    ONLY conditions loader='auto' may recover from."""


class SidecarMissing(SidecarUnavailable):
    """No sidecar has been built for this checkpoint."""


class SourceNotFrozen(SidecarUnavailable):
    """A trainer-managed path, which v1 refuses to map at all. Recoverable
    for a READER (fall back to the full loader), never for the builder:
    play.py and eval_blueprint.py default to resolve_checkpoint(), which
    returns the live blueprint_ckpt, and they must keep working there."""


# --------------------------------------------------------------- frozen rule
def is_mutable_checkpoint(path):
    base = os.path.basename(os.path.abspath(path).rstrip("\\/"))
    return base in MUTABLE_BASENAMES or base.endswith(MUTABLE_SUFFIXES)


def require_frozen(path):
    """v1 refuses trainer-managed checkpoints outright -- see module docstring."""
    if is_mutable_checkpoint(path):
        raise SourceNotFrozen(
            f"{path} is a trainer-managed checkpoint; eval sidecars are "
            f"restricted to frozen artifacts (blueprint_dayN_ckpt, *_compact). "
            f"A long-lived mmap of a live dir blocks checkpoint renames, and "
            f"a lock check cannot fix that race. Freeze a copy first.")


def sidecar_path(ckpt_path):
    return os.path.abspath(ckpt_path).rstrip("\\/") + SIDECAR_SUFFIX


# ------------------------------------------------------------- build helpers
def choose_prefix_bits(n_records):
    """~32 records per prefix bucket, so a lookup narrows to ~2 cache lines.

    Dynamic so small historical checkpoints do not carry a fixed 32 MiB
    starts.bin: at 254.8M / 160.1M / 134.2M / 53.9M records this gives
    p = 23 / 22 / 22 / 21 -> 33.6 / 16.8 / 16.8 / 8.4 MB.
    """
    if n_records < 1:
        return 8
    import math
    p = int(round(math.log2(max(n_records / 32.0, 1.0))))
    return max(8, min(24, p))


def split_records(records):
    """(digest16|row4) uint8 [N, 20] -> (hi u64, lo u64, row u32), little-endian.

    hi/lo are the same halves table.py already slots on
    (`int.from_bytes(digest[:8], "little")`) -- no new digest convention.
    """
    records = np.ascontiguousarray(records, dtype=np.uint8)
    if records.ndim != 2 or records.shape[1] != 20:
        raise SidecarError(f"index records must be [N, 20] uint8, "
                           f"got {records.shape}")
    hi = records[:, 0:8].copy().view("<u8").reshape(-1)
    lo = records[:, 8:16].copy().view("<u8").reshape(-1)
    row = records[:, 16:20].copy().view("<u4").reshape(-1)
    return hi, lo, row


def build_index_arrays(records, rows, prefix_bits=None,
                       allow_nonbijective=False):
    """Sort (digest, row) records and validate the checkpoint's own contract.

    Takes an ARRAY rather than a path so tests can feed crafted inputs --
    equal-hi/different-lo pairs cannot be produced from real BLAKE2 output.

    Strict by default. `table.py:487` already requires index.bin == rows x 20
    and normal SlabTable construction yields a bijection between stored
    digests and rows; the permissive note at compact_blueprint.py:138 is
    recovery behavior, not a licence for malformed mappings.
    """
    hi, lo, row = split_records(records)
    n = len(hi)
    defects = {}

    if n != rows:
        msg = (f"index has {n:,} records but meta.json declares {rows:,} rows")
        if n > rows or not allow_nonbijective:
            raise SidecarError(msg)
        defects["record_count"] = n
        print(f"  WARNING (--allow-nonbijective): {msg}")

    if n:
        bad = int((row >= rows).sum())
        if bad:
            raise SidecarError(f"{bad:,} records reference a row outside "
                               f"[0, {rows:,}) -- reads past the slabs")

    order = np.lexsort((lo, hi))
    hi, lo, row = hi[order], lo[order], row[order]

    if n > 1:  # duplicate full digest: corruption, never legitimate
        dup = (hi[1:] == hi[:-1]) & (lo[1:] == lo[:-1])
        n_dup = int(dup.sum())
        if n_dup:
            raise SidecarError(f"{n_dup:,} duplicate digests in the index")

    if n:  # rows must be a permutation of 0..rows-1
        seen = np.zeros(rows, dtype=bool)
        seen[row] = True
        n_missing = int(rows - seen.sum())
        n_duprow = int(n - np.unique(row).size)
        if n_duprow or n_missing:
            msg = (f"row mapping is not a bijection: {n_duprow:,} duplicate "
                   f"rows, {n_missing:,} rows unreferenced")
            if n_duprow or not allow_nonbijective:
                raise SidecarError(msg)
            defects["missing_rows"] = n_missing
            print(f"  WARNING (--allow-nonbijective): {msg}")

    p = choose_prefix_bits(n) if prefix_bits is None else int(prefix_bits)
    shift = np.uint64(64 - p)
    edges = (np.arange(1 << p, dtype=np.uint64) << shift)
    starts = np.empty((1 << p) + 1, dtype="<u4")
    starts[:-1] = np.searchsorted(hi, edges, side="left").astype("<u4")
    starts[-1] = n  # (1 << p) << shift would overflow uint64 to 0
    return {"hi": hi.astype("<u8", copy=False),
            "lo": lo.astype("<u8", copy=False),
            "row": row.astype("<u4", copy=False),
            "starts": starts, "prefix_bits": p, "records": n,
            "defects": defects}


def process_memory():
    """Windows process counters via psapi -- no third-party dependency.

    Returns bytes for peak_working_set / working_set / peak_commit / commit
    and a raw page_faults count. The pilot needs all of these: with the eval
    loader most of the footprint is file-backed, so WORKING SET (resident,
    evictable) and COMMIT (private, cannot be paged out) answer different
    questions, and page faults are the cost the mmap design trades RAM for.
    """
    if os.name != "nt":
        return {}
    import ctypes
    from ctypes import wintypes

    class _PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]

    # argtypes/restype are NOT optional here: HANDLE is 64-bit and ctypes
    # defaults to c_int, which truncates the pseudo-handle and fails the call
    cur = ctypes.windll.kernel32.GetCurrentProcess
    cur.argtypes, cur.restype = [], wintypes.HANDLE
    gpmi = ctypes.windll.psapi.GetProcessMemoryInfo
    gpmi.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD]
    gpmi.restype = wintypes.BOOL
    c = _PMC()
    c.cb = ctypes.sizeof(c)
    if not gpmi(cur(), ctypes.byref(c), c.cb):
        return {}
    return {"peak_working_set": int(c.PeakWorkingSetSize),
            "working_set": int(c.WorkingSetSize),
            "peak_commit": int(c.PeakPagefileUsage),
            "commit": int(c.PagefileUsage),
            "page_faults": int(c.PageFaultCount)}


def _sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_ckpt_meta(path):
    with open(os.path.join(path, "meta.json")) as f:
        return json.load(f)


def build_eval_index(src, dst=None, prefix_bits=None, allow_nonbijective=False,
                     ignore_training_lock=False, log=print):
    """Offline sidecar build. NOT streaming -- np.lexsort over 160M records
    needs a ~1.28 GB int64 permutation plus temporaries (peak measured and
    recorded in ROADMAP). One-time per frozen checkpoint."""
    require_frozen(src)
    lock = os.path.join(os.path.dirname(os.path.abspath(src)), "TRAINING.lock")
    if os.path.exists(lock) and not ignore_training_lock:
        raise SidecarError(
            f"{lock} exists -- building a multi-GB sidecar competes with the "
            f"trainer for RAM and IO on a box that has OOM'd. Pass "
            f"ignore_training_lock=True to freeze a sibling anyway.")

    meta = load_ckpt_meta(src)
    rows, width = meta["rows"], meta["width"]
    if meta.get("seg_rows") != SEG_ROWS:
        raise SidecarError(f"segment size {meta.get('seg_rows')} != {SEG_ROWS}")
    index_path = os.path.join(src, "index.bin")

    t0 = time.time()
    log(f"hashing {index_path} ({os.path.getsize(index_path):,} B)")
    index_sha = _sha256_file(index_path)
    records = np.fromfile(index_path, dtype=np.uint8).reshape(-1, 20)
    log(f"  {len(records):,} records read ({time.time() - t0:.0f}s); sorting")

    t1 = time.time()
    built = build_index_arrays(records, rows, prefix_bits, allow_nonbijective)
    del records
    log(f"  sorted ({time.time() - t1:.0f}s): prefix_bits="
        f"{built['prefix_bits']}, {built['records'] / max(1 << built['prefix_bits'], 1):.1f}"
        f" records/bucket")

    dst = sidecar_path(src) if dst is None else dst
    tmp = dst + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    for name, arr in (("keys_hi.bin", built["hi"]), ("keys_lo.bin", built["lo"]),
                      ("rows.bin", built["row"]), ("starts.bin", built["starts"])):
        np.ascontiguousarray(arr).tofile(os.path.join(tmp, name))
    sidecar_sha = {name: _sha256_file(os.path.join(tmp, name))
                   for name in SIDECAR_FILES}

    out = {
        "sidecar_format": SIDECAR_FORMAT,
        "byte_order": "little",
        "prefix_bits": built["prefix_bits"],
        "records": built["records"],
        "rows": rows,
        "width": width,
        "seg_rows": SEG_ROWS,
        "verdict_grade": not built["defects"],
        "defects": built["defects"],
        "built": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": {
            "path": os.path.abspath(src),          # PROVENANCE ONLY, never a gate
            "iteration": meta.get("iteration"),
            "bucket_build_id": meta.get("bucket_build_id"),
            "config": meta.get("config"),
            "index_bytes": os.path.getsize(index_path),
            "index_sha256": index_sha,
        },
        "sidecar_sha256": sidecar_sha,
    }
    # measured, not asserted: the builder is offline, not streaming --
    # np.lexsort needs a full int64 permutation plus temporaries
    mem = process_memory()
    out["build_peak_working_set"] = mem.get("peak_working_set")
    out["build_seconds"] = round(time.time() - t0, 1)
    total = sum(os.path.getsize(os.path.join(tmp, f)) for f in os.listdir(tmp))
    with open(os.path.join(tmp, "meta.json"), "w") as f:
        json.dump(out, f, indent=2)

    shutil.rmtree(dst, ignore_errors=True)
    os.rename(tmp, dst)
    log(f"{dst} | {built['records']:,} records | {total / 2**30:.2f} GiB | "
        f"{out['build_seconds']:.0f}s total"
        + (f" | peak working set {mem['peak_working_set'] / 2**30:.2f} GiB"
           if mem else ""))
    if not out["verdict_grade"]:
        log("  NOT VERDICT GRADE -- built with --allow-nonbijective")
    return out


# ------------------------------------------------------------------ the view
class EvalTable:
    """Strategy-only, read-only view of a frozen dir checkpoint.

    Duck-types the three members BlueprintPolicy touches (`rows`, `lookup`,
    `row_values`); nothing else in the codebase reaches through `_slab`.
    `reg` is never mapped -- anything needing regrets memmaps the files
    directly, as analyze_table.py:169 already does.
    """

    def __init__(self, path, sidecar=None, verify="fast", track_rows=False):
        if sys.byteorder != "little":
            raise SidecarError("sidecar format is little-endian only")
        require_frozen(path)
        self.path = os.path.abspath(path)
        self.meta = load_ckpt_meta(self.path)
        self.rows = int(self.meta["rows"])
        self.width = int(self.meta["width"])
        self.seg_rows = int(self.meta.get("seg_rows", SEG_ROWS))

        self.sidecar = sidecar_path(self.path) if sidecar is None else sidecar
        smeta_path = os.path.join(self.sidecar, "meta.json")
        if not os.path.isfile(smeta_path):
            raise SidecarMissing(
                f"no eval sidecar at {self.sidecar} -- build one with\n"
                f"    python build_eval_index.py {self.path}")
        with open(smeta_path) as f:
            self.smeta = json.load(f)
        self._validate_meta()

        self._strat_maps = {}
        self._nact_maps = {}
        self.prefix_bits = int(self.smeta["prefix_bits"])
        self._shift = 64 - self.prefix_bits
        self._records = int(self.smeta["records"])
        self._hi_a = self._map(("keys_hi.bin", "<u8", self._records))
        self._lo_a = self._map(("keys_lo.bin", "<u8", self._records))
        self._row_a = self._map(("rows.bin", "<u4", self._records))
        self._starts_a = self._map(
            ("starts.bin", "<u4", (1 << self.prefix_bits) + 1))
        # Python ints straight out of the buffer: bisect over a numpy array
        # boxes a scalar per probe. cast('B') first -- memoryview.cast only
        # accepts a byte source.
        self._hi = memoryview(self._hi_a).cast("B").cast("Q")
        self._lo = memoryview(self._lo_a).cast("B").cast("Q")
        self._row = memoryview(self._row_a).cast("B").cast("I")
        self._starts = memoryview(self._starts_a).cast("B").cast("I")

        self.touched = self.touched_pos = self.touched_bucket = None
        if verify == "full":
            verify_sidecar(self.path, self.sidecar, full=True, table=self)
        elif verify == "fast":
            self._spot_check()
        elif verify not in (None, "none"):
            raise ValueError(f"unknown verify mode {verify!r}")

        # pilot instrumentation. One byte per slot (not one bit): bit
        # twiddling in the lookup path would contaminate the timing the pilot
        # exists to measure. Allocated AFTER verification so the loader's own
        # self-check is not counted as work. These arrays are themselves ~0.5
        # GB at day4-raw scale, so they PERTURB the memory measurement -- run
        # the pilot once with and once without, per ROADMAP.
        if track_rows:
            self.touched = bytearray(self.rows)
            self.touched_pos = bytearray(self._records)
            self.touched_bucket = bytearray(1 << self.prefix_bits)

    # ------------------------------------------------------------- validation
    def _validate_meta(self):
        s = self.smeta
        if s.get("sidecar_format") != SIDECAR_FORMAT:
            raise SidecarError(f"sidecar format {s.get('sidecar_format')} != "
                               f"{SIDECAR_FORMAT}")
        if s.get("byte_order") != "little":
            raise SidecarError("sidecar is not little-endian")
        for field in ("rows", "width", "seg_rows"):
            want = self.meta.get(field) if field != "seg_rows" else \
                self.meta.get("seg_rows", SEG_ROWS)
            if s.get(field) != want:
                raise SidecarError(f"sidecar {field}={s.get(field)} but "
                                   f"checkpoint says {want} -- stale sidecar")
        src = s.get("source", {})
        for field in ("iteration", "bucket_build_id"):
            if src.get(field) != self.meta.get(field):
                raise SidecarError(
                    f"sidecar was built from {field}={src.get(field)!r}, "
                    f"checkpoint has {self.meta.get(field)!r} -- stale sidecar")
        index_path = os.path.join(self.path, "index.bin")
        if src.get("index_bytes") != os.path.getsize(index_path):
            raise SidecarError("source index.bin size changed since build")
        p = int(s["prefix_bits"])
        n = int(s["records"])
        for name, itemsize, count in (("keys_hi.bin", 8, n), ("keys_lo.bin", 8, n),
                                      ("rows.bin", 4, n),
                                      ("starts.bin", 4, (1 << p) + 1)):
            f = os.path.join(self.sidecar, name)
            if not os.path.isfile(f):
                raise SidecarError(f"sidecar file missing: {f}")
            actual = os.path.getsize(f)
            if actual != itemsize * count:
                raise SidecarError(f"{name}: expected {itemsize * count:,} B, "
                                   f"found {actual:,}")

    def _spot_check(self, count=SPOT_RECORDS):
        """PROBABILISTIC verification -- not exact identity verification.

        Samples records from the SOURCE index.bin and requires this table to
        resolve each to the recorded row. Deterministic: the sample is seeded
        from the recorded source SHA-256, spread across the whole index, and
        always includes the first and last record plus a spread of prefix
        bucket edges. ~80 KB of IO. Full identity is `--verify`.
        """
        n = self._records
        if n == 0:
            return
        sha = self.smeta["source"]["index_sha256"]
        rng = random.Random(int(sha[:16], 16))
        positions = {0, n - 1}
        positions.update(rng.randrange(n) for _ in range(count))
        index_path = os.path.join(self.path, "index.bin")
        with open(index_path, "rb") as f:
            for pos in sorted(positions):
                f.seek(pos * 20)
                rec = f.read(20)
                digest = rec[:16]
                want = int.from_bytes(rec[16:20], "little")
                got = self.lookup_digest(digest)
                if got != want:
                    raise SidecarError(
                        f"spot check failed at source record {pos}: sidecar "
                        f"says row {got}, index.bin says {want}")
        # bucket-edge containment on a bounded sample of buckets
        nb = 1 << self.prefix_bits
        for b in {0, nb - 1} | {rng.randrange(nb) for _ in range(256)}:
            lo_i, hi_i = self._starts[b], self._starts[b + 1]
            if lo_i > hi_i or hi_i > n:
                raise SidecarError(f"starts[] not monotonic at bucket {b}")
            if lo_i < hi_i:
                if (self._hi[lo_i] >> self._shift) != b:
                    raise SidecarError(f"record {lo_i} is outside bucket {b}")
                if (self._hi[hi_i - 1] >> self._shift) != b:
                    raise SidecarError(f"record {hi_i - 1} outside bucket {b}")

    # ---------------------------------------------------------------- mapping
    def _map(self, spec):
        name, dtype, count = spec
        return np.memmap(os.path.join(self.sidecar, name), dtype=dtype,
                         mode="r", shape=(count,))

    def _strat_seg(self, s):
        m = self._strat_maps.get(s)
        if m is None:
            n = min(self.seg_rows, self.rows - s * self.seg_rows)
            m = np.memmap(os.path.join(self.path, f"strat{s}.bin"),
                          dtype="<f8", mode="r", shape=(n, self.width))
            self._strat_maps[s] = m
        return m

    def _nact_seg(self, s):
        m = self._nact_maps.get(s)
        if m is None:
            n = min(self.seg_rows, self.rows - s * self.seg_rows)
            m = np.memmap(os.path.join(self.path, f"nact{s}.bin"),
                          dtype=np.int8, mode="r", shape=(n,))
            self._nact_maps[s] = m
        return m

    # ----------------------------------------------------------------- lookup
    def lookup_digest(self, digest):
        hi = int.from_bytes(digest[0:8], "little")
        lo = int.from_bytes(digest[8:16], "little")
        b = hi >> self._shift
        i = self._starts[b]
        end = self._starts[b + 1]
        j = bisect.bisect_left(self._hi, hi, i, end)
        if self.touched_bucket is not None:
            self.touched_bucket[b] = 1
            if j < self._records:  # landing slot; the bisect probed near it
                self.touched_pos[j] = 1
        # walk: hi is NOT assumed unique (~7e-4 per 160M-key checkpoint), and
        # a non-member sharing hi must not false-hit a stranger's row
        while j < end and self._hi[j] == hi:
            if self._lo[j] == lo:
                row = self._row[j]
                if self.touched is not None:
                    self.touched[row] = 1
                return row
            j += 1
        return None

    def lookup(self, key):
        return self.lookup_digest(key_digest(key))

    def row_values(self, row):
        """(None, strat_view, n) -- the regret slot is never read by a policy."""
        s, o = divmod(row, self.seg_rows)
        n = int(self._nact_seg(s)[o])
        return None, self._strat_seg(s)[o, :n], n

    def distinct_touched(self):
        if self.touched is None:
            return None
        return int(np.count_nonzero(np.frombuffer(self.touched, dtype=np.uint8)))

    def footprint(self, page=4096):
        """Distinct rows and distinct 4 KiB PAGES touched since load.

        Rows touched is not itself the working set -- what the OS keeps
        resident is pages. At width 7 a strat row is 56 B, so ~73 rows share
        a page and scattered access inflates the resident bytes far above
        rows x 56. Index pages are a LOWER BOUND: only the bisect's landing
        slot is recorded, while the probe itself reads neighbours (usually
        the same one or two pages, since a bucket holds ~32 records).
        """
        if self.touched is None:
            return None
        u8 = np.uint8
        rows_hit = np.flatnonzero(np.frombuffer(self.touched, dtype=u8))
        seg, off = np.divmod(rows_hit.astype(np.int64), self.seg_rows)
        tag = seg << np.int64(40)  # segment-qualified page ids
        strat_pages = np.unique(tag + (off * self.width * 8) // page).size
        nact_pages = np.unique(tag + off // page).size
        pos = np.flatnonzero(np.frombuffer(self.touched_pos, dtype=u8))
        buck = np.flatnonzero(np.frombuffer(self.touched_bucket, dtype=u8))
        hi_pages = np.unique(pos // (page // 8)).size
        row_pages = np.unique(pos // (page // 4)).size
        start_pages = np.unique(buck // (page // 4)).size
        idx_pages = 2 * hi_pages + row_pages + start_pages  # hi and lo parallel
        return {
            "rows_touched": int(rows_hit.size),
            "rows_total": self.rows,
            "buckets_touched": int(buck.size),
            "buckets_total": 1 << self.prefix_bits,
            "strat_pages": int(strat_pages),
            "nact_pages": int(nact_pages),
            "index_pages_min": int(idx_pages),
            "resident_bytes_min": int((strat_pages + nact_pages + idx_pages)
                                      * page),
        }

    def close(self):
        """Drop every mapping so Windows releases the file handles."""
        self._hi = self._lo = self._row = self._starts = None
        self._hi_a = self._lo_a = self._row_a = self._starts_a = None
        self._strat_maps.clear()
        self._nact_maps.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def verify_sidecar(src, sidecar=None, full=False, table=None, log=print):
    """Full-tier verification: source hash, sidecar hashes, sorted order,
    starts[] offsets, and the COMPLETE mapping (re-derived from the source
    and compared bit-for-bit). Mandatory once per production sidecar and
    again before the day4 certificate; ordinary loads use the fast tier."""
    sidecar = sidecar_path(src) if sidecar is None else sidecar
    with open(os.path.join(sidecar, "meta.json")) as f:
        smeta = json.load(f)
    if not full:
        (table or EvalTable(src, sidecar, verify="none"))._spot_check()
        return smeta

    index_path = os.path.join(src, "index.bin")
    log(f"verify: hashing source index.bin")
    got = _sha256_file(index_path)
    want = smeta["source"]["index_sha256"]
    if got != want:
        raise SidecarError(f"source index.bin SHA-256 {got} != recorded {want}")
    for name, want in smeta["sidecar_sha256"].items():
        got = _sha256_file(os.path.join(sidecar, name))
        if got != want:
            raise SidecarError(f"{name} SHA-256 {got} != recorded {want}")

    log("verify: re-deriving the sorted mapping from source")
    meta = load_ckpt_meta(src)
    records = np.fromfile(index_path, dtype=np.uint8).reshape(-1, 20)
    ref = build_index_arrays(records, meta["rows"], smeta["prefix_bits"],
                            allow_nonbijective=not smeta.get("verdict_grade",
                                                             True))
    del records
    for name, key, dtype in (("keys_hi.bin", "hi", "<u8"),
                             ("keys_lo.bin", "lo", "<u8"),
                             ("rows.bin", "row", "<u4"),
                             ("starts.bin", "starts", "<u4")):
        on_disk = np.fromfile(os.path.join(sidecar, name), dtype=dtype)
        if not np.array_equal(on_disk, ref[key]):
            raise SidecarError(f"{name} does not match a fresh rebuild")
    mem = process_memory()
    log(f"verify: OK -- {ref['records']:,} records, "
        f"prefix_bits={ref['prefix_bits']}"
        + (f" | peak working set {mem['peak_working_set'] / 2**30:.2f} GiB"
           if mem else ""))
    return smeta
