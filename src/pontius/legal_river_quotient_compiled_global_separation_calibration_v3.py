"""ADR-0463 launch-arity overlay for the compiled separation calibration.

The consumed ADR-0458 scientific module remains immutable.  This fresh module
derives one exact replacement of its timed RRNS direct-call function, guards
every campaign launch against signatures parsed from the unchanged literal
CUDA translation unit, and delegates every other scientific definition.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import inspect
import json
from pathlib import Path
import re
from threading import RLock

from . import legal_river_quotient_compiled_global_separation_calibration as _parent


PARENT_SOURCE_PATH = Path(_parent.__file__).resolve()
PARENT_SOURCE_CANONICAL_LF_SHA256 = (
    "d38e96fd445f01a70113a8598094d0449a18271fa4d6ce992c781f0253ae821e"
)
CUDA_SOURCE_SHA256 = (
    "4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7"
)
CUDA_SOURCE = _parent.CUDA_SOURCE
KERNEL_NAMES = _parent.KERNEL_NAMES

_OLD_TIMED_DIRECT_ARGUMENTS = """\
                    "direct_prices_rrns_batch",
                    scan_count * channel_count,
                    (
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        prepared.moduli,"""
_NEW_TIMED_DIRECT_ARGUMENTS = """\
                    "direct_prices_rrns_batch",
                    scan_count * channel_count,
                    (
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.uint64(scan_count),
                        prepared.moduli,"""
_OLD_SELECTED_LEAF_ARGUMENTS = """\
                    "evaluate_selected_leaves_rrns_batch",
                    expected_selected * channel_count,
                    (
                        scratch["selected_leaf_ranks"],
                        np.uint64(expected_selected),
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.uint64(scan_count),
                        prepared.moduli,"""
_NEW_SELECTED_LEAF_ARGUMENTS = """\
                    "evaluate_selected_leaves_rrns_batch",
                    expected_selected * channel_count,
                    (
                        scratch["selected_leaf_ranks"],
                        np.uint64(expected_selected),
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        prepared.moduli,"""

_CUDA_ENTRY_RE = re.compile(
    r'extern\s+"C"\s+__global__\s+void\s+'
    r"(?P<name>[A-Za-z_]\w*)\s*\((?P<parameters>.*?)\)\s*\{",
    re.DOTALL,
)
_PARAMETER_NAME_RE = re.compile(r"([A-Za-z_]\w*)\s*$")
_PATCH_LOCK = RLock()
_ORIGINAL_LAUNCH = _parent._launch


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("launch-arity canonical input must be immutable bytes")
    result = bytearray()
    cursor = 0
    while cursor < len(raw):
        if raw[cursor : cursor + 2] == bytes((13, 10)):
            result.append(10)
            cursor += 2
        else:
            result.append(raw[cursor])
            cursor += 1
    return bytes(result)


def _parent_source_text() -> str:
    raw = PARENT_SOURCE_PATH.read_bytes()
    if sha256(_canonical_lf(raw)).hexdigest() != PARENT_SOURCE_CANONICAL_LF_SHA256:
        raise ValueError("launch-arity parent scientific source differs")
    return _canonical_lf(raw).decode("utf-8")


def effective_scientific_source_text() -> str:
    """Return the exact parent source with the two frozen arity repairs."""

    text = _parent_source_text()
    if text.count(_OLD_TIMED_DIRECT_ARGUMENTS) != 1:
        raise ValueError("timed RRNS direct source-count omission differs")
    if _NEW_TIMED_DIRECT_ARGUMENTS in text:
        raise ValueError("parent unexpectedly contains the successor insertion")
    transformed = text.replace(
        _OLD_TIMED_DIRECT_ARGUMENTS, _NEW_TIMED_DIRECT_ARGUMENTS, 1
    )
    if transformed.count(_OLD_SELECTED_LEAF_ARGUMENTS) != 1:
        raise ValueError("selected-leaf RRNS obsolete source-count differs")
    transformed = transformed.replace(
        _OLD_SELECTED_LEAF_ARGUMENTS, _NEW_SELECTED_LEAF_ARGUMENTS, 1
    )
    if (
        transformed.count(_NEW_TIMED_DIRECT_ARGUMENTS) != 1
        or transformed.count(_NEW_SELECTED_LEAF_ARGUMENTS) != 1
    ):
        raise AssertionError("launch-arity source repair differs")
    return transformed


EFFECTIVE_SCIENTIFIC_SOURCE_SHA256 = sha256(
    effective_scientific_source_text().encode("utf-8")
).hexdigest()


def cuda_kernel_signatures(source_text: str = CUDA_SOURCE) -> dict[str, tuple[str, ...]]:
    """Derive ordered parameter names from the literal CUDA declarations."""

    if not isinstance(source_text, str):
        raise TypeError("CUDA signature source must be text")
    rows: dict[str, tuple[str, ...]] = {}
    for match in _CUDA_ENTRY_RE.finditer(source_text):
        name = match.group("name")
        if name in rows:
            raise ValueError(f"duplicate CUDA entry declaration: {name}")
        raw_parameters = match.group("parameters").strip()
        parameters = [] if not raw_parameters else raw_parameters.split(",")
        names = []
        for declaration in parameters:
            normalized = " ".join(declaration.split())
            found = _PARAMETER_NAME_RE.search(normalized)
            if found is None:
                raise ValueError(f"CUDA parameter declaration differs: {normalized}")
            names.append(found.group(1))
        rows[name] = tuple(names)
    if set(rows) != set(KERNEL_NAMES) or len(rows) != len(KERNEL_NAMES):
        raise ValueError("CUDA entry signature domain differs")
    return {name: rows[name] for name in KERNEL_NAMES}


KERNEL_SIGNATURES = cuda_kernel_signatures()
KERNEL_ARGUMENT_COUNTS = {
    name: len(parameters) for name, parameters in KERNEL_SIGNATURES.items()
}
KERNEL_SIGNATURE_MANIFEST_SHA256 = sha256(
    json.dumps(
        {name: list(parameters) for name, parameters in KERNEL_SIGNATURES.items()},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
).hexdigest()


def launch_arity_contract() -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0463-kernel-launch-arity-contract-v1",
        "parent_scientific_source_canonical_lf_sha256": (
            PARENT_SOURCE_CANONICAL_LF_SHA256
        ),
        "effective_scientific_source_sha256": EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        "literal_cuda_source_sha256": CUDA_SOURCE_SHA256,
        "kernel_count": len(KERNEL_SIGNATURES),
        "kernel_signatures": {
            name: list(parameters)
            for name, parameters in KERNEL_SIGNATURES.items()
        },
        "manifest_sha256": KERNEL_SIGNATURE_MANIFEST_SHA256,
        "timed_direct_source_count_expression": "np.uint64(scan_count)",
        "selected_leaf_extraneous_scan_count_removed": True,
        "complete_differential_source_count_expression": (
            "np.uint64(prepared.source_rows)"
        ),
        "central_pre_driver_guard": True,
    }


def _guarded_launch(
    context: object,
    kernel: str,
    count: int,
    arguments: tuple[object, ...],
) -> None:
    if not isinstance(kernel, str) or kernel not in KERNEL_ARGUMENT_COUNTS:
        raise _parent.CalibrationFailure(
            "kernel_launch_arity_rejected", "unknown CUDA entry at launch"
        )
    if type(arguments) is not tuple:
        raise _parent.CalibrationFailure(
            "kernel_launch_arity_rejected", f"{kernel} arguments are not a tuple"
        )
    expected = KERNEL_ARGUMENT_COUNTS[kernel]
    if len(arguments) != expected:
        raise _parent.CalibrationFailure(
            "kernel_launch_arity_rejected",
            f"{kernel} declares {expected} parameters but received {len(arguments)}",
        )
    _ORIGINAL_LAUNCH(context, kernel, count, arguments)


def _transformed_run_calibration_cell() -> Callable[..., Mapping[str, object]]:
    original = inspect.getsource(_parent._run_calibration_cell)
    if original.count(_OLD_TIMED_DIRECT_ARGUMENTS) != 1:
        raise ValueError("timed calibration-cell source omission differs")
    transformed = original.replace(
        _OLD_TIMED_DIRECT_ARGUMENTS, _NEW_TIMED_DIRECT_ARGUMENTS, 1
    )
    if transformed.count(_OLD_SELECTED_LEAF_ARGUMENTS) != 1:
        raise ValueError("selected-leaf calibration-cell source differs")
    transformed = transformed.replace(
        _OLD_SELECTED_LEAF_ARGUMENTS, _NEW_SELECTED_LEAF_ARGUMENTS, 1
    )
    namespace = dict(vars(_parent))
    namespace["__name__"] = __name__
    namespace["__package__"] = __package__
    namespace["_launch"] = _guarded_launch
    exec(compile(transformed, str(Path(__file__).resolve()), "exec"), namespace)
    function = namespace.get("_run_calibration_cell")
    if not callable(function):
        raise AssertionError("transformed calibration-cell function is absent")
    return function


_RUN_CALIBRATION_CELL = _transformed_run_calibration_cell()


@contextmanager
def _installed_launch_arity_overlay() -> Iterator[None]:
    with _PATCH_LOCK:
        original_launch = _parent._launch
        original_cell = _parent._run_calibration_cell
        _parent._launch = _guarded_launch
        _parent._run_calibration_cell = _RUN_CALIBRATION_CELL
        try:
            yield
        finally:
            _parent._run_calibration_cell = original_cell
            _parent._launch = original_launch


def execute_calibration(*args: object, **kwargs: object) -> Mapping[str, object]:
    with _installed_launch_arity_overlay():
        return _parent.execute_calibration(*args, **kwargs)


def __getattr__(name: str) -> object:
    return getattr(_parent, name)


__all__ = [
    "CUDA_SOURCE",
    "CUDA_SOURCE_SHA256",
    "EFFECTIVE_SCIENTIFIC_SOURCE_SHA256",
    "KERNEL_ARGUMENT_COUNTS",
    "KERNEL_NAMES",
    "KERNEL_SIGNATURE_MANIFEST_SHA256",
    "KERNEL_SIGNATURES",
    "PARENT_SOURCE_CANONICAL_LF_SHA256",
    "cuda_kernel_signatures",
    "effective_scientific_source_text",
    "execute_calibration",
    "launch_arity_contract",
]
