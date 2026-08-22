"""Pontius exact-game research laboratory."""

from .cuda_dll_bootstrap import configure_cuda_dll_directory
from .cfr import TabularCFR
from .coalition import (
    CoalitionEvaluationResult,
    MultiplayerAcceptanceAssessment,
    assess_multiplayer_candidate,
    evaluate_coalition_threats,
)
from .dependency_tape import CompiledPolicyDependencyTape
from .evaluation import EvaluationResult, evaluate_profile, expected_utilities
from .kuhn import KuhnPoker
from .river import RiverHoldem
from .river_incremental import RiverPolicyEvaluationCache, RiverRangeDelta
from .river_multi_size import MultiSizeRiverHoldem
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem

# Configure only a complete repository-pinned Windows bundle. This performs
# no CUDA import or DLL load, so the CPU laboratory remains CUDA-optional.
configure_cuda_dll_directory()

__all__ = [
    "CompiledPolicyDependencyTape",
    "CoalitionEvaluationResult",
    "EvaluationResult",
    "KuhnPoker",
    "MultiSizeRiverHoldem",
    "MultiplayerAcceptanceAssessment",
    "MultiwayRiverDeal",
    "MultiwayRiverHoldem",
    "RiverHoldem",
    "RiverPolicyEvaluationCache",
    "RiverRangeDelta",
    "TabularCFR",
    "assess_multiplayer_candidate",
    "evaluate_profile",
    "evaluate_coalition_threats",
    "expected_utilities",
]
