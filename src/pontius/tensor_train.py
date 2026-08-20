"""Small deterministic Float64 tensor-train decomposition primitives."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class TensorTrain:
    """One open-boundary tensor train with immutable contiguous cores."""

    shape: tuple[int, ...]
    cores: tuple[FloatArray, ...]
    decomposition_singular_values: tuple[FloatArray, ...]

    def __post_init__(self) -> None:
        if len(self.shape) < 2 or any(size <= 0 for size in self.shape):
            raise ValueError("tensor train requires at least two positive modes")
        if len(self.cores) != len(self.shape):
            raise ValueError("tensor train requires one core per mode")
        if len(self.decomposition_singular_values) != len(self.shape) - 1:
            raise ValueError("tensor train requires one singular spectrum per bond")
        previous_rank = 1
        canonical_cores = []
        for mode, (size, supplied) in enumerate(zip(self.shape, self.cores, strict=True)):
            core = np.array(supplied, dtype=np.float64, order="C", copy=True)
            if core.ndim != 3 or core.shape[0] != previous_rank or core.shape[1] != size:
                raise ValueError(f"invalid tensor-train core shape at mode {mode}")
            if not np.all(np.isfinite(core)):
                raise ValueError("tensor-train cores must be finite")
            previous_rank = core.shape[2]
            core.flags.writeable = False
            canonical_cores.append(core)
        if previous_rank != 1:
            raise ValueError("last tensor-train rank must equal one")
        spectra = []
        for supplied in self.decomposition_singular_values:
            values = np.array(supplied, dtype=np.float64, order="C", copy=True)
            if values.ndim != 1 or not np.all(np.isfinite(values)) or np.any(values < 0.0):
                raise ValueError("tensor-train singular values must be finite vectors")
            values.flags.writeable = False
            spectra.append(values)
        object.__setattr__(self, "cores", tuple(canonical_cores))
        object.__setattr__(self, "decomposition_singular_values", tuple(spectra))

    @classmethod
    def from_dense(
        cls,
        tensor: object,
        *,
        maximum_rank: int | None = None,
    ) -> TensorTrain:
        values = np.ascontiguousarray(tensor, dtype=np.float64)
        if values.ndim < 2 or any(size <= 0 for size in values.shape):
            raise ValueError("TT-SVD requires a tensor with at least two positive modes")
        if not np.all(np.isfinite(values)):
            raise ValueError("TT-SVD input must be finite")
        if maximum_rank is not None and (
            isinstance(maximum_rank, bool) or maximum_rank <= 0
        ):
            raise ValueError("maximum TT rank must be a positive integer or None")

        shape = tuple(int(size) for size in values.shape)
        cores = []
        spectra = []
        unfolding = values.copy()
        previous_rank = 1
        for mode, size in enumerate(shape[:-1]):
            matrix = unfolding.reshape(previous_rank * size, -1)
            left, singular, right = np.linalg.svd(matrix, full_matrices=False)
            spectra.append(singular)
            rank = len(singular)
            if maximum_rank is not None:
                rank = min(rank, maximum_rank)
            cores.append(left[:, :rank].reshape(previous_rank, size, rank))
            unfolding = singular[:rank, None] * right[:rank]
            previous_rank = rank
        cores.append(unfolding.reshape(previous_rank, shape[-1], 1))
        return cls(
            shape=shape,
            cores=tuple(cores),
            decomposition_singular_values=tuple(spectra),
        )

    @property
    def ranks(self) -> tuple[int, ...]:
        return (1, *(core.shape[2] for core in self.cores))

    @property
    def storage_bytes(self) -> int:
        return sum(core.nbytes for core in self.cores)

    def to_dense(self) -> FloatArray:
        result = self.cores[0][0]
        for core in self.cores[1:]:
            result = np.tensordot(result, core, axes=((-1,), (0,)))
        return np.ascontiguousarray(result[..., 0], dtype=np.float64)


def unfolding_numerical_ranks(
    tensor: object,
    *,
    relative_threshold: float,
) -> tuple[int, ...]:
    values = np.ascontiguousarray(tensor, dtype=np.float64)
    if values.ndim < 2 or not np.all(np.isfinite(values)):
        raise ValueError("unfolding ranks require a finite tensor of order at least two")
    if not np.isfinite(relative_threshold) or not 0.0 <= relative_threshold < 1.0:
        raise ValueError("relative rank threshold must lie in [0, 1)")
    ranks = [1]
    for split in range(1, values.ndim):
        matrix = values.reshape(
            int(np.prod(values.shape[:split])),
            int(np.prod(values.shape[split:])),
        )
        singular = np.linalg.svd(matrix, compute_uv=False)
        threshold = relative_threshold * singular[0] if len(singular) else 0.0
        ranks.append(max(1, int(np.count_nonzero(singular > threshold))))
    ranks.append(1)
    return tuple(ranks)


def tensor_errors(reference: object, candidate: object) -> dict[str, float]:
    first = np.ascontiguousarray(reference, dtype=np.float64)
    second = np.ascontiguousarray(candidate, dtype=np.float64)
    if first.shape != second.shape:
        raise ValueError("tensor error operands must have identical shapes")
    difference = first - second
    denominator = float(np.linalg.norm(first.ravel()))
    return {
        "maximum_absolute_error": float(np.max(np.abs(difference))),
        "relative_frobenius_error": (
            float(np.linalg.norm(difference.ravel())) / denominator
            if denominator > 0.0
            else float(np.linalg.norm(difference.ravel()))
        ),
    }
