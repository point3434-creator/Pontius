"""Research-only eager CuPy binding of the pinned NumPy reference, float64 throughout."""
import importlib.util
from pathlib import Path
import cupy as cp

spec = importlib.util.spec_from_file_location('gpu_reference',
    Path(__file__).with_name('solver.py'))
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)
reference.np = cp


def normalize(values):
    # CuPy divide lacks NumPy's masked out/where contract. Never divide by zero.
    total = values.sum(axis=1, keepdims=True)
    denominator = cp.where(total > 0, total, 1.)
    return cp.where(total > 0, values / denominator, 1 / values.shape[1])


reference.normalize = normalize
Solver = reference.Solver
