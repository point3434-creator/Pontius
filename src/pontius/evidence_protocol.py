"""Repository-wide evidence defaults for GPU numerical identity."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal


DigestGatePurpose = Literal[
    "immutable_input_identity",
    "serialized_object_identity",
    "immediate_restore_reexport_identity",
    "explicit_bitwise_determinism_experiment",
]


@dataclass(frozen=True, slots=True)
class GPUNumericalIdentityTolerances:
    """Default semantic-identity ceilings for re-derived Float64 GPU work."""

    maximum_accumulator_absolute_error: float = 1e-12
    maximum_policy_probability_error: float = 1e-12
    maximum_policy_mean_information_set_total_variation: float = 1e-13
    maximum_quality_absolute_error: float = 1e-10


DEFAULT_GPU_NUMERICAL_IDENTITY = GPUNumericalIdentityTolerances()


def validate_gpu_numerical_identity(
    *,
    maximum_accumulator_absolute_error: float,
    maximum_policy_probability_error: float,
    policy_mean_information_set_total_variation: float,
    maximum_quality_absolute_error: float,
    tolerances: GPUNumericalIdentityTolerances = DEFAULT_GPU_NUMERICAL_IDENTITY,
) -> None:
    """Reject nonfinite or above-ceiling cross-run semantic differences."""

    observed = {
        "accumulator": maximum_accumulator_absolute_error,
        "policy_probability": maximum_policy_probability_error,
        "policy_mean_tv": policy_mean_information_set_total_variation,
        "quality": maximum_quality_absolute_error,
    }
    ceilings = {
        "accumulator": tolerances.maximum_accumulator_absolute_error,
        "policy_probability": tolerances.maximum_policy_probability_error,
        "policy_mean_tv": (
            tolerances.maximum_policy_mean_information_set_total_variation
        ),
        "quality": tolerances.maximum_quality_absolute_error,
    }
    for name, value in observed.items():
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"GPU numerical identity {name} error must be finite and nonnegative")
        if value > ceilings[name]:
            raise ValueError(f"GPU numerical identity {name} error exceeds its frozen ceiling")


def validate_digest_gate_purpose(purpose: str) -> DigestGatePurpose:
    """Permit bitwise gates only where byte identity is the actual contract."""

    allowed = {
        "immutable_input_identity",
        "serialized_object_identity",
        "immediate_restore_reexport_identity",
        "explicit_bitwise_determinism_experiment",
    }
    if purpose not in allowed:
        raise ValueError(
            "bitwise digest is diagnostic for ordinary cross-run GPU semantic identity"
        )
    return purpose  # type: ignore[return-value]
