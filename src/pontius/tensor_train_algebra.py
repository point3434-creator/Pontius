"""Exact tensor-train algebra and deterministic Float64 TT rounding."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .tensor_train import TensorTrain


@dataclass(frozen=True, slots=True)
class TensorTrainRounding:
    """A rounded TT plus auditable rank and discarded-norm diagnostics."""

    train: TensorTrain
    input_ranks: tuple[int, ...]
    output_ranks: tuple[int, ...]
    relative_tolerance: float
    maximum_rank: int | None
    source_frobenius_norm: float
    discarded_frobenius_bound: float
    relative_discarded_bound: float


def multiply_mode_vector(
    train: TensorTrain,
    mode: int,
    vector: object,
) -> TensorTrain:
    """Multiply one tensor mode pointwise by a finite unary vector."""

    if mode not in range(len(train.shape)):
        raise ValueError("TT mode is outside the train shape")
    values = np.ascontiguousarray(vector, dtype=np.float64)
    if values.shape != (train.shape[mode],) or not np.all(np.isfinite(values)):
        raise ValueError("TT mode multiplier must be a matching finite vector")
    cores = list(train.cores)
    cores[mode] = np.ascontiguousarray(
        cores[mode] * values[None, :, None],
        dtype=np.float64,
    )
    return TensorTrain(
        shape=train.shape,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            np.empty(0, dtype=np.float64) for _ in range(len(train.shape) - 1)
        ),
    )


def add_tensor_trains(first: TensorTrain, second: TensorTrain) -> TensorTrain:
    """Return the exact block-structured TT sum without rank truncation."""

    if first.shape != second.shape:
        raise ValueError("tensor-train addition requires identical mode shapes")
    dimensions = len(first.shape)
    cores = [
        np.ascontiguousarray(
            np.concatenate((first.cores[0], second.cores[0]), axis=2),
            dtype=np.float64,
        )
    ]
    for mode in range(1, dimensions - 1):
        left = first.cores[mode]
        right = second.cores[mode]
        combined = np.zeros(
            (
                left.shape[0] + right.shape[0],
                first.shape[mode],
                left.shape[2] + right.shape[2],
            ),
            dtype=np.float64,
            order="C",
        )
        combined[: left.shape[0], :, : left.shape[2]] = left
        combined[left.shape[0] :, :, left.shape[2] :] = right
        cores.append(combined)
    cores.append(
        np.ascontiguousarray(
            np.concatenate((first.cores[-1], second.cores[-1]), axis=0),
            dtype=np.float64,
        )
    )
    return TensorTrain(
        shape=first.shape,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            np.empty(0, dtype=np.float64) for _ in range(dimensions - 1)
        ),
    )


def sum_tensor_trains(trains: tuple[TensorTrain, ...]) -> TensorTrain:
    """Return an exact direct sum of one or more identically shaped TTs."""

    if not trains:
        raise ValueError("tensor-train sum requires at least one operand")
    result = trains[0]
    for train in trains[1:]:
        result = add_tensor_trains(result, train)
    return result


def round_tensor_train(
    train: TensorTrain,
    *,
    relative_tolerance: float,
    maximum_rank: int | None = None,
) -> TensorTrainRounding:
    """Left-orthogonalize and truncate by a right-to-left TT-SVD sweep."""

    if (
        not math.isfinite(relative_tolerance)
        or relative_tolerance < 0.0
        or relative_tolerance >= 1.0
    ):
        raise ValueError("TT rounding tolerance must lie in [0, 1)")
    if maximum_rank is not None and (
        isinstance(maximum_rank, bool) or maximum_rank <= 0
    ):
        raise ValueError("TT rounding maximum rank must be positive or None")

    cores = [np.array(core, dtype=np.float64, order="C", copy=True) for core in train.cores]
    dimensions = len(cores)
    for mode in range(dimensions - 1):
        previous_rank, size, next_rank = cores[mode].shape
        matrix = cores[mode].reshape(previous_rank * size, next_rank)
        orthogonal, transfer = np.linalg.qr(matrix, mode="reduced")
        new_rank = orthogonal.shape[1]
        cores[mode] = orthogonal.reshape(previous_rank, size, new_rank)
        cores[mode + 1] = np.tensordot(
            transfer,
            cores[mode + 1],
            axes=((1,), (0,)),
        )

    source_norm = float(np.linalg.norm(cores[-1].ravel()))
    per_bond_tolerance = (
        relative_tolerance * source_norm / math.sqrt(dimensions - 1)
    )
    spectra: list[np.ndarray | None] = [None] * (dimensions - 1)
    discarded_squared = 0.0
    for mode in range(dimensions - 1, 0, -1):
        previous_rank, size, next_rank = cores[mode].shape
        matrix = cores[mode].reshape(previous_rank, size * next_rank)
        left, singular, right = np.linalg.svd(matrix, full_matrices=False)
        spectra[mode - 1] = singular.copy()
        tolerance_rank = _minimum_retained_rank(singular, per_bond_tolerance)
        retained_rank = tolerance_rank
        if maximum_rank is not None:
            retained_rank = min(retained_rank, maximum_rank)
        retained_rank = max(1, retained_rank)
        discarded_squared += float(
            np.dot(singular[retained_rank:], singular[retained_rank:])
        )
        cores[mode] = right[:retained_rank].reshape(
            retained_rank,
            size,
            next_rank,
        )
        weighted_left = left[:, :retained_rank] * singular[:retained_rank]
        cores[mode - 1] = np.tensordot(
            cores[mode - 1],
            weighted_left,
            axes=((2,), (0,)),
        )

    rounded = TensorTrain(
        shape=train.shape,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            spectrum if spectrum is not None else np.empty(0, dtype=np.float64)
            for spectrum in spectra
        ),
    )
    discarded_bound = math.sqrt(discarded_squared)
    return TensorTrainRounding(
        train=rounded,
        input_ranks=train.ranks,
        output_ranks=rounded.ranks,
        relative_tolerance=relative_tolerance,
        maximum_rank=maximum_rank,
        source_frobenius_norm=source_norm,
        discarded_frobenius_bound=discarded_bound,
        relative_discarded_bound=(
            discarded_bound / source_norm if source_norm > 0.0 else discarded_bound
        ),
    )


def _minimum_retained_rank(singular: np.ndarray, tolerance: float) -> int:
    if len(singular) <= 1:
        return 1
    tail_squared = np.cumsum((singular[::-1] * singular[::-1]))[::-1]
    limit_squared = tolerance * tolerance
    for retained in range(1, len(singular)):
        if float(tail_squared[retained]) <= limit_squared:
            return retained
    return len(singular)
