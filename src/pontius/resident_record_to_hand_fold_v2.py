"""Topology-owned, finite, non-consuming resident record-to-hand fold."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from functools import lru_cache
from math import fsum
from typing import Any

import numpy as np

from .cupy_sparse_incidence import _cupy_modules
from .open_mode_factor_tt import OpenModeFactorTTWorkspace, _hand_values
from .resident_record_to_hand_fold import (
    RecordToHandBackend,
    ResidentRecordToHandFold,
    validate_record_to_hand_backend,
)


@dataclass(frozen=True, slots=True)
class AbsoluteNegativeReachAllowance:
    """Absolute tolerated negative reach mass."""

    absolute_mass: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.absolute_mass, bool)
            or not isinstance(self.absolute_mass, (int, float))
            or not math.isfinite(float(self.absolute_mass))
            or float(self.absolute_mass) < 0.0
        ):
            raise ValueError("absolute negative-reach allowance is invalid")


@dataclass(frozen=True, slots=True)
class RelativeNegativeReachAllowance:
    """Relative tolerated negative reach against positive row mass only."""

    relative_fraction: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.relative_fraction, bool)
            or not isinstance(self.relative_fraction, (int, float))
            or not math.isfinite(float(self.relative_fraction))
            or float(self.relative_fraction) < 0.0
        ):
            raise ValueError("relative negative-reach allowance is invalid")


@dataclass(frozen=True, slots=True)
class ResidentReachTolerances:
    """Nominally typed absolute and relative reach semantics."""

    absolute: AbsoluteNegativeReachAllowance
    relative: RelativeNegativeReachAllowance

    def __post_init__(self) -> None:
        if type(self.absolute) is not AbsoluteNegativeReachAllowance:
            raise TypeError("resident fold requires AbsoluteNegativeReachAllowance")
        if type(self.relative) is not RelativeNegativeReachAllowance:
            raise TypeError("resident fold requires RelativeNegativeReachAllowance")


@lru_cache(maxsize=1)
def _fold_kernel_v2() -> Any:
    cp, _ = _cupy_modules()
    return cp.RawKernel(
        r"""
        extern "C" __global__
        void pontius_fold_records_to_hands_v2(
            const double* numerators,
            const double* reaches,
            const int* hand_indices,
            const long long records,
            const long long hands,
            const long long total_records,
            double* hand_numerators,
            double* hand_reaches)
        {
            const long long flat =
                (long long)blockDim.x * (long long)blockIdx.x + threadIdx.x;
            if (flat >= total_records) {
                return;
            }
            const long long term = flat / records;
            const int hand = hand_indices[flat - term * records];
            const long long output = term * hands + (long long)hand;
            const double reach = reaches[flat];
            if (reach >= 0.0) {
                atomicAdd(hand_numerators + output, numerators[flat]);
                atomicAdd(hand_reaches + output, reach);
            }
        }
        """,
        "pontius_fold_records_to_hands_v2",
    )


def _topology_hand_indices(
    workspace: OpenModeFactorTTWorkspace,
    target_seat: int,
) -> np.ndarray:
    topology = workspace.topology.base
    hand_counts = topology.hand_counts
    if (
        isinstance(target_seat, bool)
        or not isinstance(target_seat, int)
        or target_seat not in range(len(hand_counts))
    ):
        raise ValueError("resident record fold target seat is outside the topology")
    if target_seat in topology.left.seats:
        half = topology.left
    elif target_seat in topology.right.seats:
        half = topology.right
    else:
        raise ValueError("resident record fold target seat is absent from topology")
    depth = half.seats.index(target_seat)
    matrix = half.indices
    if (
        not isinstance(matrix, np.ndarray)
        or matrix.dtype != np.int32
        or matrix.ndim != 2
        or not matrix.flags.c_contiguous
        or matrix.shape != (half.records, len(half.seats))
    ):
        raise ValueError("resident topology hand index matrix is not contiguous Int32")
    result = np.array(matrix[:, depth], dtype=np.int32, order="C", copy=True)
    hand_count = int(hand_counts[target_seat])
    if np.any(result < 0) or np.any(result >= hand_count):
        raise ValueError("resident topology hand index is outside the target hand axis")
    result.flags.writeable = False
    return result


def _reach_allowances(
    reaches: np.ndarray,
    tolerances: ResidentReachTolerances,
) -> np.ndarray:
    positive_scales = np.max(np.maximum(reaches, 0.0), axis=1)
    return np.maximum(
        float(tolerances.absolute.absolute_mass),
        float(tolerances.relative.relative_fraction) * positive_scales,
    )


def _validate_host_records(
    numerators: np.ndarray,
    reaches: np.ndarray,
    *,
    payoff_span: float,
    tolerances: ResidentReachTolerances,
) -> np.ndarray:
    if not np.all(np.isfinite(numerators)) or not np.all(np.isfinite(reaches)):
        raise FloatingPointError("resident record accumulators must be finite")
    allowances = _reach_allowances(reaches, tolerances)
    minimums = np.min(reaches, axis=1)
    if np.any(minimums < -allowances):
        raise ArithmeticError("resident leaf produced negative reach")
    negative_numerator = np.max(
        np.where(reaches < 0.0, np.abs(numerators), 0.0),
        axis=1,
    )
    if np.any(negative_numerator > payoff_span * allowances):
        raise ArithmeticError(
            "resident leaf produced material numerator at clamped reach"
        )
    return allowances


def _device_all_finite(cp: Any, values: Any) -> bool:
    checked = cp.asnumpy(cp.all(cp.isfinite(values)))
    return bool(np.asarray(checked).item())


def finalize_resident_record_accumulators_v2(
    workspace: OpenModeFactorTTWorkspace,
    *,
    target_seat: int,
    term_keys: tuple[int, ...],
    numerator_records: Any,
    reach_records: Any,
    payoff_span: float,
    reach_tolerances: ResidentReachTolerances,
    backend: RecordToHandBackend = "host_numpy",
    zero_reach_value: float = 0.0,
) -> ResidentRecordToHandFold:
    """Fold records using only topology-owned mapping and explicit units."""

    selected = validate_record_to_hand_backend(backend)
    if (
        isinstance(payoff_span, bool)
        or not isinstance(payoff_span, (int, float))
        or not math.isfinite(float(payoff_span))
        or float(payoff_span) <= 0.0
    ):
        raise ValueError("resident fold payoff span must be finite and positive")
    if type(reach_tolerances) is not ResidentReachTolerances:
        raise TypeError("resident fold requires ResidentReachTolerances")
    if not np.isfinite(zero_reach_value):
        raise ValueError("resident zero-reach value must be finite")
    if not term_keys or len(set(term_keys)) != len(term_keys):
        raise ValueError("resident record fold requires unique term keys")
    indices = _topology_hand_indices(workspace, target_seat)
    if not hasattr(numerator_records, "shape") or not hasattr(reach_records, "shape"):
        raise TypeError("resident record accumulators must be arrays")
    if numerator_records.shape != reach_records.shape:
        raise ValueError("resident numerator and reach records differ")
    if len(numerator_records.shape) != 2:
        raise ValueError("resident record accumulators must be a matrix")
    term_count, record_count = map(int, numerator_records.shape)
    if record_count != len(indices) or record_count <= 0:
        raise ValueError("resident record axis differs from the topology")
    if term_count != len(term_keys):
        raise ValueError("resident record rows differ from term keys")

    if isinstance(numerator_records, np.ndarray) or isinstance(reach_records, np.ndarray):
        if not (
            isinstance(numerator_records, np.ndarray)
            and isinstance(reach_records, np.ndarray)
            and numerator_records.dtype == np.float64
            and reach_records.dtype == np.float64
            and numerator_records.flags.c_contiguous
            and reach_records.flags.c_contiguous
        ):
            raise ValueError("resident host record matrices must be contiguous Float64")
        _validate_host_records(
            numerator_records,
            reach_records,
            payoff_span=float(payoff_span),
            tolerances=reach_tolerances,
        )

    cp, _ = _cupy_modules()
    if numerator_records.dtype != cp.float64 or reach_records.dtype != cp.float64:
        raise ValueError("resident device record matrices must use Float64")
    if not numerator_records.flags.c_contiguous or not reach_records.flags.c_contiguous:
        raise ValueError("resident device record matrices must be C-contiguous")
    if not _device_all_finite(cp, numerator_records) or not _device_all_finite(
        cp, reach_records
    ):
        raise FloatingPointError("resident record accumulators must be finite")

    download_started = time.perf_counter()
    if selected == "host_numpy":
        host_numerators = cp.asnumpy(numerator_records)
        host_reaches = cp.asnumpy(reach_records)
        cp.cuda.runtime.deviceSynchronize()
        download_ms = (time.perf_counter() - download_started) * 1000.0
        _validate_host_records(
            host_numerators,
            host_reaches,
            payoff_span=float(payoff_span),
            tolerances=reach_tolerances,
        )
        fold_started = time.perf_counter()
        values = []
        for key, raw_numerators, raw_reaches in zip(
            term_keys,
            host_numerators,
            host_reaches,
            strict=True,
        ):
            valid = raw_reaches >= 0.0
            accepted_numerators = np.where(valid, raw_numerators, 0.0)
            accepted_reaches = np.where(valid, raw_reaches, 0.0)
            numerators = np.bincount(
                indices,
                weights=accepted_numerators,
                minlength=workspace.topology.base.hand_counts[target_seat],
            ).astype(np.float64, copy=False)
            reaches = np.bincount(
                indices,
                weights=accepted_reaches,
                minlength=workspace.topology.base.hand_counts[target_seat],
            ).astype(np.float64, copy=False)
            values.append(
                (
                    key,
                    _hand_values(
                        workspace=workspace,
                        target=target_seat,
                        numerators=numerators,
                        reaches=reaches,
                        total_numerator=fsum(float(value) for value in numerators),
                        total_reach=fsum(float(value) for value in reaches),
                        zero_reach_value=zero_reach_value,
                    ),
                )
            )
        fold_ms = (time.perf_counter() - fold_started) * 1000.0
        return ResidentRecordToHandFold(
            values=tuple(values),
            backend=selected,
            device_hand_fold_gpu_ms=0.0,
            device_to_host_ms=download_ms,
            host_hand_fold_ms=fold_ms,
            host_hand_finalize_ms=0.0,
            device_to_host_bytes=int(host_numerators.nbytes + host_reaches.nbytes),
            device_fold_scratch_numeric_bytes=0,
        )

    device_indices = cp.ascontiguousarray(cp.asarray(indices), dtype=cp.int32)
    fold_begin = cp.cuda.Event()
    fold_end = cp.cuda.Event()
    fold_begin.record()
    minimums = cp.min(reach_records, axis=1)
    positive_scales = cp.max(cp.maximum(reach_records, 0.0), axis=1)
    negative_numerator_maxima = cp.max(
        cp.where(reach_records < 0.0, cp.abs(numerator_records), 0.0),
        axis=1,
    )
    hand_count = int(workspace.topology.base.hand_counts[target_seat])
    hand_numerators = cp.zeros((term_count, hand_count), dtype=cp.float64)
    hand_reaches = cp.zeros((term_count, hand_count), dtype=cp.float64)
    total_records = term_count * record_count
    threads = 256
    blocks = (total_records + threads - 1) // threads
    _fold_kernel_v2()(
        (blocks,),
        (threads,),
        (
            numerator_records,
            reach_records,
            device_indices,
            np.int64(record_count),
            np.int64(hand_count),
            np.int64(total_records),
            hand_numerators,
            hand_reaches,
        ),
    )
    fold_end.record()
    fold_end.synchronize()
    fold_gpu_ms = float(cp.cuda.get_elapsed_time(fold_begin, fold_end))

    download_started = time.perf_counter()
    host_numerators = cp.asnumpy(hand_numerators)
    host_reaches = cp.asnumpy(hand_reaches)
    host_minimums = cp.asnumpy(minimums)
    host_positive_scales = cp.asnumpy(positive_scales)
    host_negative_numerator_maxima = cp.asnumpy(negative_numerator_maxima)
    cp.cuda.runtime.deviceSynchronize()
    download_ms = (time.perf_counter() - download_started) * 1000.0
    allowances = np.maximum(
        float(reach_tolerances.absolute.absolute_mass),
        float(reach_tolerances.relative.relative_fraction) * host_positive_scales,
    )
    if np.any(host_minimums < -allowances):
        raise ArithmeticError("resident leaf produced negative reach")
    if np.any(host_negative_numerator_maxima > float(payoff_span) * allowances):
        raise ArithmeticError(
            "resident leaf produced material numerator at clamped reach"
        )

    finalize_started = time.perf_counter()
    values = []
    for key, numerators, reaches in zip(
        term_keys,
        host_numerators,
        host_reaches,
        strict=True,
    ):
        values.append(
            (
                key,
                _hand_values(
                    workspace=workspace,
                    target=target_seat,
                    numerators=numerators,
                    reaches=reaches,
                    total_numerator=fsum(float(value) for value in numerators),
                    total_reach=fsum(float(value) for value in reaches),
                    zero_reach_value=zero_reach_value,
                ),
            )
        )
    finalize_ms = (time.perf_counter() - finalize_started) * 1000.0
    downloaded = int(
        host_numerators.nbytes
        + host_reaches.nbytes
        + host_minimums.nbytes
        + host_positive_scales.nbytes
        + host_negative_numerator_maxima.nbytes
    )
    scratch = int(
        device_indices.nbytes
        + minimums.nbytes
        + positive_scales.nbytes
        + negative_numerator_maxima.nbytes
        + hand_numerators.nbytes
        + hand_reaches.nbytes
    )
    return ResidentRecordToHandFold(
        values=tuple(values),
        backend=selected,
        device_hand_fold_gpu_ms=fold_gpu_ms,
        device_to_host_ms=download_ms,
        host_hand_fold_ms=0.0,
        host_hand_finalize_ms=finalize_ms,
        device_to_host_bytes=downloaded,
        device_fold_scratch_numeric_bytes=scratch,
    )


__all__ = [
    "AbsoluteNegativeReachAllowance",
    "RelativeNegativeReachAllowance",
    "ResidentReachTolerances",
    "finalize_resident_record_accumulators_v2",
]
