"""Pontius exact-game research laboratory."""

from .cfr import TabularCFR
from .coalition import (
    CoalitionEvaluationResult,
    MultiplayerAcceptanceAssessment,
    assess_multiplayer_candidate,
    evaluate_coalition_threats,
)
from .cuda_dll_bootstrap import configure_cuda_dll_directory
from .dependency_tape import CompiledPolicyDependencyTape
from .evaluation import EvaluationResult, evaluate_profile, expected_utilities
from .full_width_belief import FullWidthOneSeatBelief
from .full_width_reference_policy import ImmutableFullWidthReferencePolicy
from .holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from .immutable_blueprint import ImmutableBlueprintActionSource
from .kuhn import KuhnPoker
from .legal_decision_spine import LegalDecisionSpine
from .no_limit_betting import (
    BettingAction,
    BettingActionKind,
    BettingStreet,
    ContributionLayer,
    LegalBettingDecision,
    NoLimitBettingState,
    RaiseBounds,
    SidePot,
)
from .reference_hand_replay import ReferenceHandSpec, replay_reference_hand
from .river import RiverHoldem
from .river_incremental import RiverPolicyEvaluationCache, RiverRangeDelta
from .river_multi_size import MultiSizeRiverHoldem
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem

# Configure only a complete repository-pinned Windows bundle. This performs
# no CUDA import or DLL load, so the CPU laboratory remains CUDA-optional.
configure_cuda_dll_directory()

__all__ = [
    "BettingAction",
    "BettingActionKind",
    "BettingStreet",
    "CoalitionEvaluationResult",
    "CompiledPolicyDependencyTape",
    "ContributionLayer",
    "EvaluationResult",
    "FullWidthOneSeatBelief",
    "ImmutableBlueprintActionSource",
    "ImmutableFullWidthReferencePolicy",
    "KuhnPoker",
    "LegalBettingDecision",
    "LegalDecisionSpine",
    "MultiSizeRiverHoldem",
    "MultiplayerAcceptanceAssessment",
    "MultiwayRiverDeal",
    "MultiwayRiverHoldem",
    "NoLimitBettingState",
    "OneSeatCardState",
    "RaiseBounds",
    "ReferenceHandSpec",
    "RiverHoldem",
    "RiverPolicyEvaluationCache",
    "RiverRangeDelta",
    "SidePot",
    "SixSeatHoldemDeal",
    "TabularCFR",
    "assess_multiplayer_candidate",
    "evaluate_coalition_threats",
    "evaluate_profile",
    "expected_utilities",
    "replay_reference_hand",
]
