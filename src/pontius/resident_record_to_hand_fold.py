"""Host and device record-to-hand finalization for resident leaf contractions."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import fsum
import time
from typing import Any, Literal

import numpy as np

from .cupy_sparse_incidence import _cupy_modules
from .open_mode_factor_tt import OpenModeFactorTTWorkspace, _hand_values


RecordToHandBackend = Literal["host_numpy", "gpu_cupy"]


@dataclass(frozen=True, slots=True)
class ResidentRecordToHandFold:
    """Final hand vectors and an explicit placement/timing ledger."""

    values: tuple[tuple[int, Any], ...]
    backend: RecordToHandBackend
    device_hand_fold_gpu_ms: float
    device_to_host_ms: float
    host_hand_fold_ms: float
    host_hand_finalize_ms: float
    device_to_host_bytes: int
    device_fold_scratch_numeric_bytes: int


def validate_record_to_hand_backend(value: str) -> RecordToHandBackend:
    """Fail closed on an unknown fold placement."""

    if value not in ("host_numpy", "gpu_cupy"):
        raise ValueError("record-to-hand backend must be host_numpy or gpu_cupy")
    return value  # type: ignore[return-value]


@lru_cache(maxsize=1)
def _fold_kernel() -> Any:
    cp, _ = _cupy_modules()
    return cp.RawKernel(
        r"""
        extern "C" __global__
        void pontius_fold_records_to_hands(
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
            atomicAdd(hand_numerators + output, numerators[flat]);
            atomicAdd(hand_reaches + output, reaches[flat]);
        }
        """,
        "pontius_fold_records_to_hands",
    )


def finalize_resident_record_accumulators(
    workspace: OpenModeFactorTTWorkspace,
    *,
    target_seat: int,
    term_keys: tuple[int, ...],
    numerator_records: Any,
    reach_records: Any,
    host_hand_indices: np.ndarray,
    device_hand_indices: Any,
    backend: RecordToHandBackend = "host_numpy",
    zero_reach_value: float = 0.0,
    negative_reach_relative_allowance: float = 1e-10,
) -> ResidentRecordToHandFold:
    """Fold query records by target hand without changing leaf semantics.

    The device arm validates and clamps each record before grouping, matching
    the accepted host arm. Only the reassociation of Float64 additions differs.
    """

    selected = validate_record_to_hand_backend(backend)
    cp, _ = _cupy_modules()
    if not term_keys:
        raise ValueError("resident record fold requires at least one term")
    if numerator_records.shape != reach_records.shape:
        raise ValueError("resident numerator and reach records differ")
    if len(numerator_records.shape) != 2:
        raise ValueError("resident record accumulators must be a matrix")
    term_count, record_count = map(int, numerator_records.shape)
    if term_count != len(term_keys):
        raise ValueError("resident record rows differ from term keys")
    if host_hand_indices.shape != (record_count,):
        raise ValueError("resident host hand index differs from record axis")
    if host_hand_indices.dtype != np.int32:
        raise ValueError("resident host hand index must use Int32")
    if not np.isfinite(zero_reach_value):
        raise ValueError("resident zero-reach value must be finite")
    if (
        not np.isfinite(negative_reach_relative_allowance)
        or negative_reach_relative_allowance < 0.0
    ):
        raise ValueError("resident negative-reach allowance is invalid")

    hand_count = int(workspace.topology.base.hand_counts[target_seat])
    if selected == "host_numpy":
        download_started = time.perf_counter()
        host_numerators = cp.asnumpy(numerator_records)
        host_reaches = cp.asnumpy(reach_records)
        cp.cuda.runtime.deviceSynchronize()
        download_ms = (time.perf_counter() - download_started) * 1000.0

        fold_started = time.perf_counter()
        values = []
        for key, numerators_by_record, reaches_by_record in zip(
            term_keys,
            host_numerators,
            host_reaches,
            strict=True,
        ):
            scale = max(1.0, float(np.max(np.abs(reaches_by_record))))
            minimum = float(np.min(reaches_by_record))
            if minimum < -negative_reach_relative_allowance * scale:
                raise ArithmeticError("resident leaf produced negative reach")
            if minimum < 0.0:
                reaches_by_record = np.maximum(reaches_by_record, 0.0)
            numerators = np.bincount(
                host_hand_indices,
                weights=numerators_by_record,
                minlength=hand_count,
            ).astype(np.float64, copy=False)
            reaches = np.bincount(
                host_hand_indices,
                weights=reaches_by_record,
                minlength=hand_count,
            ).astype(np.float64, copy=False)
            values.append(
                (
                    key,
                    _hand_values(
                        workspace=workspace,
                        target=target_seat,
                        numerators=numerators,
                        reaches=reaches,
                        total_numerator=fsum(
                            float(value) for value in numerators_by_record
                        ),
                        total_reach=fsum(float(value) for value in reaches_by_record),
                        zero_reach_value=zero_reach_value,
                    ),
                )
            )
        fold_ms = (time.perf_counter() - fold_started) * 1000.0
        record_bytes = int(host_numerators.nbytes + host_reaches.nbytes)
        return ResidentRecordToHandFold(
            values=tuple(values),
            backend=selected,
            device_hand_fold_gpu_ms=0.0,
            device_to_host_ms=download_ms,
            host_hand_fold_ms=fold_ms,
            host_hand_finalize_ms=0.0,
            device_to_host_bytes=record_bytes,
            device_fold_scratch_numeric_bytes=0,
        )

    indices = cp.ascontiguousarray(device_hand_indices, dtype=cp.int32)
    if indices.shape != (record_count,):
        raise ValueError("resident device hand index differs from record axis")
    fold_begin = cp.cuda.Event()
    fold_end = cp.cuda.Event()
    fold_begin.record()
    minimums = cp.min(reach_records, axis=1)
    scales = cp.maximum(1.0, cp.max(cp.abs(reach_records), axis=1))
    cp.maximum(reach_records, 0.0, out=reach_records)
    hand_numerators = cp.zeros((term_count, hand_count), dtype=cp.float64)
    hand_reaches = cp.zeros((term_count, hand_count), dtype=cp.float64)
    total_records = term_count * record_count
    threads = 256
    blocks = (total_records + threads - 1) // threads
    _fold_kernel()(
        (blocks,),
        (threads,),
        (
            numerator_records,
            reach_records,
            indices,
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
    host_scales = cp.asnumpy(scales)
    cp.cuda.runtime.deviceSynchronize()
    download_ms = (time.perf_counter() - download_started) * 1000.0

    finalize_started = time.perf_counter()
    values = []
    for index, (key, numerators, reaches) in enumerate(
        zip(term_keys, host_numerators, host_reaches, strict=True)
    ):
        if float(host_minimums[index]) < (
            -negative_reach_relative_allowance * float(host_scales[index])
        ):
            raise ArithmeticError("resident leaf produced negative reach")
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
        + host_scales.nbytes
    )
    scratch = int(
        indices.nbytes
        + minimums.nbytes
        + scales.nbytes
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
