"""Isolated h32 resident sparse pass for an NVTX-filtered Nsight invocation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from . import h32_tier_b_opponent_batch_differential as batch_v1
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, _cupy_modules


def run_profile_workload(
    config_path: Path,
    *,
    direction: str,
    metadata_output: Path,
) -> dict[str, object]:
    """Launch exactly one two-SpMM sparse pass inside the named NVTX range."""

    from .h32_resident_sparse_ncu_profile import (
        parse_h32_resident_sparse_ncu_profile_config,
    )

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_resident_sparse_ncu_profile_config(config)
    if direction not in parsed["directions"]:
        raise ValueError("resident sparse profile direction is not frozen")
    live = parsed["live"]
    target = next(
        row
        for row in live["targets"]
        if row["target"] == parsed["representative_target"]
    )
    board = batch_v1.science.parse_cards(*target["board"])
    source, _, sparse, _ = batch_v1.science._build_case(
        parsed=live,
        board=board,
        hand_count=int(live["hands_per_player"]),
        family=str(target["range_family"]),
    )
    source_digest = batch_v1.science._belief_digest(source)
    if source_digest != parsed["expected_source_belief_sha256"]:
        raise ArithmeticError("resident sparse profile source belief differs")

    cp, _ = _cupy_modules()
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    operator = getattr(gpu, direction)
    width = int(parsed["feature_width"])
    feature_count = int(operator.cpu.source_records) * width
    features = cp.linspace(
        0.25,
        1.25,
        feature_count,
        dtype=cp.float64,
    ).reshape(operator.cpu.source_records, width)

    for _ in range(int(parsed["workload_warmups"])):
        incidence = operator.source_matrix @ features
        compatible = operator.query_matrix @ incidence
        cp.cuda.runtime.deviceSynchronize()
        del incidence, compatible

    range_name = parsed["nvtx_ranges"][direction]
    begin = cp.cuda.Event()
    end = cp.cuda.Event()
    cp.cuda.nvtx.RangePush(range_name)
    begin.record()
    incidence = operator.source_matrix @ features
    compatible = operator.query_matrix @ incidence
    end.record()
    end.synchronize()
    cp.cuda.nvtx.RangePop()

    checksum_started = time.perf_counter()
    checksum = float(cp.asnumpy(cp.sum(compatible, dtype=cp.float64)))
    cp.cuda.runtime.deviceSynchronize()
    pool = cp.get_default_memory_pool()
    metadata = {
        "direction": direction,
        "nvtx_range": range_name,
        "feature_width": width,
        "source_belief_sha256": source_digest,
        "source_records": int(operator.cpu.source_records),
        "query_records": int(operator.cpu.query_records),
        "incidence_entries": int(operator.cpu.incidence_entries),
        "source_nnz": int(operator.cpu.source_nnz),
        "query_nnz": int(operator.cpu.query_nnz),
        "source_matrix_shape": list(map(int, operator.source_matrix.shape)),
        "query_matrix_shape": list(map(int, operator.query_matrix.shape)),
        "features_numeric_bytes": int(features.nbytes),
        "incidence_numeric_bytes": int(incidence.nbytes),
        "compatible_numeric_bytes": int(compatible.nbytes),
        "event_elapsed_ms_diagnostic": float(
            cp.cuda.get_elapsed_time(begin, end)
        ),
        "checksum": checksum,
        "checksum_download_ms": (time.perf_counter() - checksum_started) * 1000.0,
        "gpu_pool_used_bytes": int(pool.used_bytes()),
        "gpu_pool_total_bytes": int(pool.total_bytes()),
        "finite": bool(np.isfinite(checksum)),
    }
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--direction", required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    args = parser.parse_args()
    run_profile_workload(
        args.config,
        direction=args.direction,
        metadata_output=args.metadata_output,
    )


if __name__ == "__main__":
    main()
