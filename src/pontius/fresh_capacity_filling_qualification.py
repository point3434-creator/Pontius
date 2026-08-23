"""Candidate-blind qualification of ADR-0309's sealed v4 pools."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from time import perf_counter
from typing import Any

from .fresh_capacity_filling_structures import (
    ADR0305_V4_QUALIFIED_A_SHA256,
    ADR0305_V4_QUALIFIED_B_SHA256,
    ADR0305_V4_QUALIFIED_CONTEXT_COUNT,
    CapacityFillingStructureKind,
    CapacityFillingWidthFourContext,
    FreshCapacityFillingStructure,
    build_adr0305_v4_structure,
)
from .reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ExactDealProbability,
    ProbabilitySimplexAllowance,
    ReducedRiverSizingContext,
    solve_bounded_normal_form_sizing_teacher,
    solve_reduced_river_sizing,
)
from .sizing_power_diagnostic import (
    ChipClassificationGuard,
    NormalizedSizingOpportunityFloor,
    QualificationStopReason,
    SizingPowerClassification,
    classify_sizing_opportunity,
)
from .width_four_sizing_power import (
    ReducedSizingLpDimensions,
    width_four_lp_dimensions,
)

ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE = 1e-11
ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP = 4096
ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT = 24
ADR0305_V4_QUALIFICATION_OPPORTUNITY_FLOOR = NormalizedSizingOpportunityFloor(1e-4)
ADR0305_V4_QUALIFICATION_CLASSIFICATION_GUARD = ChipClassificationGuard(1e-8)
ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE = ProbabilitySimplexAllowance(1e-9)
ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE = ChipObjectiveAllowance(1e-9)

# ADR-0310 records the stopped candidate-blind invocation. Qualified A passed,
# but its panel remains provisional because qualified B hit the numerical kill
# criterion before either panel could become an evaluation panel.
ADR0310_QUALIFIED_A_OPENED_CONTEXT_COUNT = 73
ADR0310_QUALIFIED_A_INDICES = (
    0,
    3,
    4,
    8,
    10,
    13,
    14,
    17,
    28,
    30,
    34,
    35,
    42,
    43,
    52,
    53,
    55,
    56,
    58,
    63,
    64,
    69,
    70,
    72,
)
ADR0310_QUALIFIED_A_RESULT_SHA256 = (
    "ff16b19045880646699f11cc3eb6ea8a6d2d69db7391d62ae5649c36aafd576d"
)
ADR0310_QUALIFIED_A_PROVISIONAL_PANEL_SHA256 = (
    "c2a737abadb726219c2a55d5d785258abc790da44947d89c5a80fbcd80f2e45d"
)
ADR0310_QUALIFIED_A_TEACHER_CONTROL_SHA256 = (
    "11c59dc8cb9d76f309fdf7b512bb8a4660f6109cdb9341522bfd59da5fa43da6"
)
ADR0310_QUALIFIED_A_CAMPAIGN_SHA256 = (
    "c292dd30782d26a43ef71038f7f2fd55cabfa1004f6f049b8476e69df3f7462d"
)
ADR0310_QUALIFIED_B_FAILURE_CONTEXT_INDEX = 21
ADR0310_QUALIFIED_B_COMPLETED_CONTEXT_COUNT = 21
ADR0310_QUALIFIED_B_COMPLETED_INDICES = tuple(range(21))
ADR0310_QUALIFIED_B_COMPLETED_QUALIFYING_INDICES = (
    0,
    1,
    2,
    4,
    6,
    7,
    8,
    10,
    11,
    16,
    20,
)
ADR0310_QUALIFIED_B_FAILURE_SHA256 = (
    "03c5dc4f00c0429d3c615352a1d52f9c64dec0d3b4c4cf72f6d7cc171e3a26fe"
)


def _require_positive_allowance(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")
    return value


@dataclass(frozen=True, slots=True)
class CapacityFillingLpDualityGapAllowance:
    """Chip-valued compact-LP primal-dual gap allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(
            self.chips,
            label="capacity-filling LP duality allowance",
        )


@dataclass(frozen=True, slots=True)
class CapacityFillingEnvelopeViolationAllowance:
    """Chip-valued lower-envelope feasibility allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(
            self.chips,
            label="capacity-filling envelope allowance",
        )


@dataclass(frozen=True, slots=True)
class CapacityFillingTeacherAgreementAllowance:
    """Chip-valued compact-versus-normal-form agreement allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(
            self.chips,
            label="capacity-filling teacher agreement allowance",
        )


@dataclass(frozen=True, slots=True)
class CapacityFillingTeacherDualityAllowance:
    """Chip-valued normal-form primal-dual gap allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(
            self.chips,
            label="capacity-filling teacher duality allowance",
        )


ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE = CapacityFillingLpDualityGapAllowance(1e-9)
ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE = CapacityFillingEnvelopeViolationAllowance(1e-9)
ADR0305_V4_QUALIFICATION_TEACHER_AGREEMENT_ALLOWANCE = CapacityFillingTeacherAgreementAllowance(
    1e-9
)
ADR0305_V4_QUALIFICATION_TEACHER_DUALITY_ALLOWANCE = CapacityFillingTeacherDualityAllowance(1e-9)


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _qualified_pool_digest(kind: CapacityFillingStructureKind) -> str:
    if kind is CapacityFillingStructureKind.QUALIFIED_A:
        return ADR0305_V4_QUALIFIED_A_SHA256
    if kind is CapacityFillingStructureKind.QUALIFIED_B:
        return ADR0305_V4_QUALIFIED_B_SHA256
    raise ValueError("capacity-filling qualification excludes representative values")


def _context_payload(context: Any) -> dict[str, object]:
    return {
        "board": context.board,
        "context_id": context.context_id,
        "joint_probabilities": tuple(
            tuple((probability.numerator, probability.denominator) for probability in row)
            for row in context.joint_probabilities
        ),
        "minimum_bet": context.minimum_bet,
        "opener_hands": context.opener_hands,
        "pot": context.pot,
        "responder_hands": context.responder_hands,
        "stack": context.stack,
    }


def _structural_context_digest(context: CapacityFillingWidthFourContext) -> str:
    payload = {
        "context": context.canonical_payload,
        "version": "capacity-filling-structural-context-identity-v1",
    }
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class CapacityFillingOracleContextBinding:
    """Exact one-to-one binding from a v4 structure to the sizing oracle."""

    structural_context: CapacityFillingWidthFourContext
    oracle_context: ReducedRiverSizingContext

    def __post_init__(self) -> None:
        if not isinstance(self.structural_context, CapacityFillingWidthFourContext):
            raise TypeError("capacity-filling binding requires a structural context")
        if not isinstance(self.oracle_context, ReducedRiverSizingContext):
            raise TypeError("capacity-filling binding requires an exact oracle context")
        if _context_payload(self.structural_context) != _context_payload(self.oracle_context):
            raise ValueError("capacity-filling conversion changed a context field")
        if self.structural_context.payoff_span != self.oracle_context.payoff_span:
            raise ValueError("capacity-filling conversion changed payoff span")
        if self.structural_context.showdown_signs != self.oracle_context.showdown_signs:
            raise ValueError("capacity-filling conversion changed showdown")

    @property
    def structural_context_digest(self) -> str:
        return _structural_context_digest(self.structural_context)

    @property
    def digest(self) -> str:
        payload = {
            "context": _context_payload(self.oracle_context),
            "oracle_context_sha256": self.oracle_context.digest,
            "structural_context_sha256": self.structural_context_digest,
            "version": "capacity-filling-structural-oracle-binding-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


def bind_capacity_filling_context_to_oracle(
    context: CapacityFillingWidthFourContext,
) -> CapacityFillingOracleContextBinding:
    """Convert every exact field and immediately prove semantic identity."""

    if not isinstance(context, CapacityFillingWidthFourContext):
        raise TypeError("capacity-filling conversion requires a structural context")
    oracle = ReducedRiverSizingContext(
        context_id=context.context_id,
        board=context.board,
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        opener_hands=context.opener_hands,
        responder_hands=context.responder_hands,
        joint_probabilities=tuple(
            tuple(
                ExactDealProbability(
                    probability.numerator,
                    probability.denominator,
                )
                for probability in row
            )
            for row in context.joint_probabilities
        ),
    )
    return CapacityFillingOracleContextBinding(
        structural_context=context,
        oracle_context=oracle,
    )


@dataclass(frozen=True, slots=True)
class CapacityFillingQualificationObservation:
    context_index: int
    structural_context_digest: str
    oracle_context_digest: str
    binding_digest: str
    full_value_chips: float
    narrow_value_chips: float
    payoff_span: int
    classification: SizingPowerClassification
    full_bet_sizes: tuple[int, ...]
    narrow_bet_sizes: tuple[int, ...]
    full_dimensions: ReducedSizingLpDimensions
    narrow_dimensions: ReducedSizingLpDimensions
    full_simplex_pivots: int
    narrow_simplex_pivots: int
    max_probability_residual: float
    max_chip_objective_error: float
    max_lp_duality_gap_chips: float
    max_envelope_violation_chips: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index not in range(ADR0305_V4_QUALIFIED_CONTEXT_COUNT)
        ):
            raise ValueError("capacity-filling observation index lies outside its pool")
        for label, digest in (
            ("structural context", self.structural_context_digest),
            ("oracle context", self.oracle_context_digest),
            ("binding", self.binding_digest),
        ):
            if not _valid_digest(digest):
                raise ValueError(f"capacity-filling observation {label} digest is invalid")
        for label, value in (
            ("full value", self.full_value_chips),
            ("narrow value", self.narrow_value_chips),
            ("probability residual", self.max_probability_residual),
            ("chip objective error", self.max_chip_objective_error),
            ("LP duality gap", self.max_lp_duality_gap_chips),
            ("envelope violation", self.max_envelope_violation_chips),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"capacity-filling observation {label} must be finite")
        if (
            isinstance(self.payoff_span, bool)
            or not isinstance(self.payoff_span, int)
            or self.payoff_span <= 0
        ):
            raise ValueError("capacity-filling payoff span must be positive")
        if not isinstance(self.classification, SizingPowerClassification):
            raise TypeError("capacity-filling classification must be semantic")
        for label, sizes in (
            ("full", self.full_bet_sizes),
            ("narrow", self.narrow_bet_sizes),
        ):
            if not isinstance(sizes, tuple) or not sizes:
                raise TypeError(f"capacity-filling {label} sizes must be immutable")
            if any(
                isinstance(size, bool) or not isinstance(size, int) or size <= 0 for size in sizes
            ):
                raise ValueError(f"capacity-filling {label} sizes must be positive")
            if tuple(sorted(set(sizes))) != sizes:
                raise ValueError(f"capacity-filling {label} sizes must increase")
        if not isinstance(
            self.full_dimensions,
            ReducedSizingLpDimensions,
        ) or not isinstance(self.narrow_dimensions, ReducedSizingLpDimensions):
            raise TypeError("capacity-filling LP dimensions must be semantic")
        for label, pivots in (
            ("full", self.full_simplex_pivots),
            ("narrow", self.narrow_simplex_pivots),
        ):
            if isinstance(pivots, bool) or not isinstance(pivots, int) or pivots < 0:
                raise ValueError(f"capacity-filling {label} pivots must be nonnegative")
            if pivots > ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP:
                raise ValueError(f"capacity-filling {label} pivots exceed the frozen cap")
        for label, value, allowance in (
            (
                "probability residual",
                self.max_probability_residual,
                ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE.value,
            ),
            (
                "chip objective error",
                self.max_chip_objective_error,
                ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE.chips,
            ),
            (
                "LP duality gap",
                self.max_lp_duality_gap_chips,
                ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE.chips,
            ),
            (
                "envelope violation",
                self.max_envelope_violation_chips,
                ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE.chips,
            ),
        ):
            if value < 0.0 or value > allowance:
                raise ValueError(f"capacity-filling {label} exceeds the frozen allowance")

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "binding_digest": self.binding_digest,
            "classification": self.classification.value,
            "context_index": self.context_index,
            "full_bet_sizes": self.full_bet_sizes,
            "full_dimensions": (
                self.full_dimensions.variable_count,
                self.full_dimensions.inequality_count,
            ),
            "full_simplex_pivots": self.full_simplex_pivots,
            "full_value_chips": self.full_value_chips.hex(),
            "max_chip_objective_error": self.max_chip_objective_error.hex(),
            "max_envelope_violation_chips": (self.max_envelope_violation_chips.hex()),
            "max_lp_duality_gap_chips": self.max_lp_duality_gap_chips.hex(),
            "max_probability_residual": self.max_probability_residual.hex(),
            "narrow_bet_sizes": self.narrow_bet_sizes,
            "narrow_dimensions": (
                self.narrow_dimensions.variable_count,
                self.narrow_dimensions.inequality_count,
            ),
            "narrow_simplex_pivots": self.narrow_simplex_pivots,
            "narrow_value_chips": self.narrow_value_chips.hex(),
            "oracle_context_digest": self.oracle_context_digest,
            "payoff_span": self.payoff_span,
            "structural_context_digest": self.structural_context_digest,
        }


class CapacityFillingQualificationArm(StrEnum):
    """The exact value-owning arm active at a qualification failure."""

    FULL_INTEGER = "full_integer"
    MINIMUM_ALL_IN = "minimum_all_in"


@dataclass(frozen=True, slots=True)
class CapacityFillingQualificationNumericalFailure(Exception):
    """Digest-bound stop state for a solver failure before panel selection."""

    pool_kind: CapacityFillingStructureKind
    pool_digest: str
    context_index: int
    structural_context_digest: str
    oracle_context_digest: str
    binding_digest: str
    arm: CapacityFillingQualificationArm
    bet_sizes: tuple[int, ...]
    dimensions: ReducedSizingLpDimensions
    completed_observations: tuple[CapacityFillingQualificationObservation, ...]
    completed_qualified_indices: tuple[int, ...]
    cause_type: str
    cause_message: str

    def __post_init__(self) -> None:
        if self.pool_digest != _qualified_pool_digest(self.pool_kind):
            raise ValueError("capacity-filling failure pool identity is not sealed")
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index not in range(ADR0305_V4_QUALIFIED_CONTEXT_COUNT)
        ):
            raise ValueError("capacity-filling failure index lies outside its pool")
        for label, digest in (
            ("structural context", self.structural_context_digest),
            ("oracle context", self.oracle_context_digest),
            ("binding", self.binding_digest),
        ):
            if not _valid_digest(digest):
                raise ValueError(f"capacity-filling failure {label} digest is invalid")
        if not isinstance(self.arm, CapacityFillingQualificationArm):
            raise TypeError("capacity-filling failure arm must be semantic")
        if (
            not isinstance(self.bet_sizes, tuple)
            or not self.bet_sizes
            or any(
                isinstance(size, bool) or not isinstance(size, int) or size <= 0
                for size in self.bet_sizes
            )
            or tuple(sorted(set(self.bet_sizes))) != self.bet_sizes
        ):
            raise ValueError("capacity-filling failure bet sizes must increase")
        if not isinstance(self.dimensions, ReducedSizingLpDimensions):
            raise TypeError("capacity-filling failure dimensions must be semantic")
        if not isinstance(self.completed_observations, tuple) or any(
            not isinstance(observation, CapacityFillingQualificationObservation)
            for observation in self.completed_observations
        ):
            raise TypeError("capacity-filling failure prefix must be semantic")
        if tuple(observation.context_index for observation in self.completed_observations) != tuple(
            range(self.context_index)
        ):
            raise ValueError("capacity-filling failure prefix is not contiguous")
        expected_qualified = tuple(
            observation.context_index
            for observation in self.completed_observations
            if observation.classification is SizingPowerClassification.QUALIFYING
        )
        if self.completed_qualified_indices != expected_qualified:
            raise ValueError("capacity-filling failure qualifier prefix drifted")
        if any(
            observation.classification is SizingPowerClassification.AMBIGUOUS
            for observation in self.completed_observations
        ):
            raise ValueError("capacity-filling failure continued after ambiguity")
        if len(self.completed_qualified_indices) >= (ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT):
            raise ValueError("capacity-filling failure continued after its target")
        for label, value in (
            ("cause type", self.cause_type),
            ("cause message", self.cause_message),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"capacity-filling failure {label} must be nonempty")

    @property
    def completed_context_count(self) -> int:
        return len(self.completed_observations)

    @property
    def solver_call_number(self) -> int:
        arm_offset = 1 if self.arm is CapacityFillingQualificationArm.FULL_INTEGER else 2
        return 2 * self.completed_context_count + arm_offset

    @property
    def digest(self) -> str:
        payload = {
            "arm": self.arm.value,
            "bet_sizes": self.bet_sizes,
            "binding_digest": self.binding_digest,
            "cause_message": self.cause_message,
            "cause_type": self.cause_type,
            "completed_observations": tuple(
                observation.canonical_payload for observation in self.completed_observations
            ),
            "completed_qualified_indices": self.completed_qualified_indices,
            "context_index": self.context_index,
            "dimensions": (
                self.dimensions.variable_count,
                self.dimensions.inequality_count,
            ),
            "oracle_context_digest": self.oracle_context_digest,
            "pool_digest": self.pool_digest,
            "pool_kind": self.pool_kind.value,
            "solver_call_number": self.solver_call_number,
            "structural_context_digest": self.structural_context_digest,
            "version": "capacity-filling-qualification-numerical-failure-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def __str__(self) -> str:
        return (
            f"capacity-filling {self.pool_kind.value} context "
            f"{self.context_index} {self.arm.value} failed: "
            f"{self.cause_type}: {self.cause_message}"
        )


@dataclass(frozen=True, slots=True)
class CapacityFillingQualifiedPanel:
    pool_kind: CapacityFillingStructureKind
    pool_digest: str
    pool_indices: tuple[int, ...]
    structural_context_digests: tuple[str, ...]
    oracle_context_digests: tuple[str, ...]
    binding_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.pool_digest != _qualified_pool_digest(self.pool_kind):
            raise ValueError("capacity-filling panel pool identity is not sealed")
        if (
            not isinstance(self.pool_indices, tuple)
            or len(self.pool_indices) != ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT
        ):
            raise TypeError("capacity-filling panel requires 24 immutable indices")
        if any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index not in range(ADR0305_V4_QUALIFIED_CONTEXT_COUNT)
            for index in self.pool_indices
        ):
            raise ValueError("capacity-filling panel index lies outside its pool")
        if tuple(sorted(self.pool_indices)) != self.pool_indices or len(
            set(self.pool_indices)
        ) != len(self.pool_indices):
            raise ValueError("capacity-filling panel indices must increase strictly")
        for label, digests in (
            ("structural", self.structural_context_digests),
            ("oracle", self.oracle_context_digests),
            ("binding", self.binding_digests),
        ):
            if not isinstance(digests, tuple) or len(digests) != len(self.pool_indices):
                raise TypeError(f"capacity-filling panel {label} digests must align")
            if any(not _valid_digest(digest) for digest in digests):
                raise ValueError(f"capacity-filling panel {label} digest is invalid")

    @property
    def digest(self) -> str:
        payload = {
            "binding_digests": self.binding_digests,
            "oracle_context_digests": self.oracle_context_digests,
            "pool_digest": self.pool_digest,
            "pool_indices": self.pool_indices,
            "pool_kind": self.pool_kind.value,
            "structural_context_digests": self.structural_context_digests,
            "version": "capacity-filling-qualified-panel-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class CapacityFillingQualificationResult:
    pool_kind: CapacityFillingStructureKind
    pool_digest: str
    stop_reason: QualificationStopReason
    observations: tuple[CapacityFillingQualificationObservation, ...]
    qualified_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.pool_digest != _qualified_pool_digest(self.pool_kind):
            raise ValueError("capacity-filling result pool identity is not sealed")
        if not isinstance(self.stop_reason, QualificationStopReason):
            raise TypeError("capacity-filling stop reason must be semantic")
        if not isinstance(self.observations, tuple) or not self.observations:
            raise TypeError("capacity-filling result requires immutable observations")
        if any(
            not isinstance(observation, CapacityFillingQualificationObservation)
            for observation in self.observations
        ):
            raise TypeError("capacity-filling result has a nonsemantic observation")
        if tuple(observation.context_index for observation in self.observations) != tuple(
            range(len(self.observations))
        ):
            raise ValueError("capacity-filling observations must be a contiguous prefix")
        expected_qualified = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.QUALIFYING
        )
        if self.qualified_indices != expected_qualified:
            raise ValueError("capacity-filling qualified indices disagree with values")
        ambiguous = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.AMBIGUOUS
        )
        if self.stop_reason is QualificationStopReason.AMBIGUOUS:
            if ambiguous != (len(self.observations) - 1,):
                raise ValueError("capacity-filling result did not stop at ambiguity")
            if len(self.qualified_indices) >= ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT:
                raise ValueError("ambiguous result already reached its target")
        elif ambiguous:
            raise ValueError("non-ambiguous result contains an ambiguity")
        if self.stop_reason is QualificationStopReason.TARGET_REACHED:
            if len(self.qualified_indices) != ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT:
                raise ValueError("target-reached result lacks 24 qualifiers")
            if self.qualified_indices[-1] != len(self.observations) - 1:
                raise ValueError("target-reached result opened a later value")
        elif self.stop_reason is QualificationStopReason.POOL_EXHAUSTED:
            if len(self.observations) != ADR0305_V4_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("exhausted result did not open its full pool")
            if len(self.qualified_indices) >= ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT:
                raise ValueError("exhausted result already reached its target")

    @property
    def opened_context_count(self) -> int:
        return len(self.observations)

    @property
    def digest(self) -> str:
        payload = {
            "chip_classification_guard": (
                ADR0305_V4_QUALIFICATION_CLASSIFICATION_GUARD.chips.hex()
            ),
            "chip_objective_allowance": (
                ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE.chips.hex()
            ),
            "envelope_allowance_chips": (ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE.chips.hex()),
            "lp_duality_allowance_chips": (
                ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE.chips.hex()
            ),
            "observations": tuple(
                observation.canonical_payload for observation in self.observations
            ),
            "opportunity_floor": (ADR0305_V4_QUALIFICATION_OPPORTUNITY_FLOOR.value.hex()),
            "pool_digest": self.pool_digest,
            "pool_kind": self.pool_kind.value,
            "probability_allowance": (ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE.value.hex()),
            "qualified_indices": self.qualified_indices,
            "simplex_pivot_cap": ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
            "solver_tolerance": (ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE.hex()),
            "stop_reason": self.stop_reason.value,
            "version": "capacity-filling-qualification-result-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def verify_against_pool(self, *, pool: FreshCapacityFillingStructure) -> None:
        if (
            not isinstance(pool, FreshCapacityFillingStructure)
            or pool.kind is not self.pool_kind
            or pool.digest != self.pool_digest
        ):
            raise ValueError("capacity-filling verification pool differs from result")
        for observation, structural_context in zip(
            self.observations,
            pool.contexts[: len(self.observations)],
            strict=True,
        ):
            binding = bind_capacity_filling_context_to_oracle(structural_context)
            context = binding.oracle_context
            if observation.structural_context_digest != binding.structural_context_digest:
                raise ValueError("capacity-filling structural prefix drifted")
            if observation.oracle_context_digest != context.digest:
                raise ValueError("capacity-filling oracle prefix drifted")
            if observation.binding_digest != binding.digest:
                raise ValueError("capacity-filling binding prefix drifted")
            if observation.payoff_span != context.payoff_span:
                raise ValueError("capacity-filling payoff span differs from game")
            full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
            narrow_sizes = (context.minimum_bet, context.stack)
            if observation.full_bet_sizes != full_sizes:
                raise ValueError("capacity-filling full arm differs from game")
            if observation.narrow_bet_sizes != narrow_sizes:
                raise ValueError("capacity-filling narrow arm differs from game")
            if observation.full_dimensions != width_four_lp_dimensions(
                context,
                full_sizes,
            ):
                raise ValueError("capacity-filling full LP dimensions differ")
            if observation.narrow_dimensions != width_four_lp_dimensions(
                context,
                narrow_sizes,
            ):
                raise ValueError("capacity-filling narrow LP dimensions differ")
            expected = classify_sizing_opportunity(
                full_value_chips=observation.full_value_chips,
                narrow_value_chips=observation.narrow_value_chips,
                payoff_span=context.payoff_span,
                opportunity_floor=ADR0305_V4_QUALIFICATION_OPPORTUNITY_FLOOR,
                classification_guard=(ADR0305_V4_QUALIFICATION_CLASSIFICATION_GUARD),
            )
            if observation.classification is not expected:
                raise ValueError("capacity-filling classification differs from values")
            if (
                observation.full_value_chips
                + ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE.chips
                < observation.narrow_value_chips
            ):
                raise ValueError("capacity-filling full value fell below narrow")

    def qualified_panel(
        self,
        *,
        pool: FreshCapacityFillingStructure,
    ) -> CapacityFillingQualifiedPanel:
        if self.stop_reason is not QualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached result has a panel")
        self.verify_against_pool(pool=pool)
        return self._panel_identity()

    def _panel_identity(self) -> CapacityFillingQualifiedPanel:
        if self.stop_reason is not QualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached result has a panel")
        selected = tuple(self.observations[index] for index in self.qualified_indices)
        return CapacityFillingQualifiedPanel(
            pool_kind=self.pool_kind,
            pool_digest=self.pool_digest,
            pool_indices=self.qualified_indices,
            structural_context_digests=tuple(
                observation.structural_context_digest for observation in selected
            ),
            oracle_context_digests=tuple(
                observation.oracle_context_digest for observation in selected
            ),
            binding_digests=tuple(observation.binding_digest for observation in selected),
        )


@dataclass(frozen=True, slots=True)
class CapacityFillingTeacherObservation:
    context_index: int
    binding_digest: str
    bounded_context_digest: str
    bet_sizes: tuple[int, ...]
    compact_value_chips: float
    teacher_value_chips: float
    value_difference_chips: float
    teacher_duality_gap_chips: float
    compact_probability_residual: float
    compact_chip_objective_error: float
    compact_lp_duality_gap_chips: float
    compact_envelope_violation_chips: float
    compact_simplex_pivots: int
    teacher_opener_pure_plan_count: int
    teacher_responder_pure_plan_count: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index not in range(ADR0305_V4_QUALIFIED_CONTEXT_COUNT)
        ):
            raise ValueError("capacity-filling teacher index lies outside its pool")
        if not _valid_digest(self.binding_digest):
            raise ValueError("capacity-filling teacher binding digest is invalid")
        if not _valid_digest(self.bounded_context_digest):
            raise ValueError("capacity-filling bounded-context digest is invalid")
        if (
            not isinstance(self.bet_sizes, tuple)
            or len(self.bet_sizes) != 2
            or any(
                isinstance(size, bool) or not isinstance(size, int) or size <= 0
                for size in self.bet_sizes
            )
            or self.bet_sizes[0] >= self.bet_sizes[1]
        ):
            raise ValueError("capacity-filling teacher sizes must be minimum/all-in")
        for label, value in (
            ("compact value", self.compact_value_chips),
            ("teacher value", self.teacher_value_chips),
            ("value difference", self.value_difference_chips),
            ("teacher duality gap", self.teacher_duality_gap_chips),
            ("probability residual", self.compact_probability_residual),
            ("chip objective error", self.compact_chip_objective_error),
            ("LP duality gap", self.compact_lp_duality_gap_chips),
            ("envelope violation", self.compact_envelope_violation_chips),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"capacity-filling teacher {label} must be finite")
        if self.value_difference_chips != abs(self.compact_value_chips - self.teacher_value_chips):
            raise ValueError("capacity-filling teacher difference is inconsistent")
        for label, value, allowance in (
            (
                "value difference",
                self.value_difference_chips,
                ADR0305_V4_QUALIFICATION_TEACHER_AGREEMENT_ALLOWANCE.chips,
            ),
            (
                "teacher duality gap",
                self.teacher_duality_gap_chips,
                ADR0305_V4_QUALIFICATION_TEACHER_DUALITY_ALLOWANCE.chips,
            ),
            (
                "probability residual",
                self.compact_probability_residual,
                ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE.value,
            ),
            (
                "chip objective error",
                self.compact_chip_objective_error,
                ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE.chips,
            ),
            (
                "LP duality gap",
                self.compact_lp_duality_gap_chips,
                ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE.chips,
            ),
            (
                "envelope violation",
                self.compact_envelope_violation_chips,
                ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE.chips,
            ),
        ):
            if value < 0.0 or value > allowance:
                raise ValueError(f"capacity-filling teacher {label} exceeds its allowance")
        if (
            isinstance(self.compact_simplex_pivots, bool)
            or not isinstance(self.compact_simplex_pivots, int)
            or self.compact_simplex_pivots < 0
            or self.compact_simplex_pivots > ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP
        ):
            raise ValueError("capacity-filling teacher pivots exceed the frozen cap")
        if self.teacher_opener_pure_plan_count != 9:
            raise ValueError("capacity-filling teacher opener plan count drifted")
        if self.teacher_responder_pure_plan_count != 16:
            raise ValueError("capacity-filling teacher responder plan count drifted")

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "binding_digest": self.binding_digest,
            "bet_sizes": self.bet_sizes,
            "bounded_context_digest": self.bounded_context_digest,
            "compact_chip_objective_error": (self.compact_chip_objective_error.hex()),
            "compact_envelope_violation_chips": (self.compact_envelope_violation_chips.hex()),
            "compact_lp_duality_gap_chips": (self.compact_lp_duality_gap_chips.hex()),
            "compact_probability_residual": (self.compact_probability_residual.hex()),
            "compact_simplex_pivots": self.compact_simplex_pivots,
            "compact_value_chips": self.compact_value_chips.hex(),
            "context_index": self.context_index,
            "teacher_duality_gap_chips": self.teacher_duality_gap_chips.hex(),
            "teacher_opener_pure_plan_count": self.teacher_opener_pure_plan_count,
            "teacher_responder_pure_plan_count": (self.teacher_responder_pure_plan_count),
            "teacher_value_chips": self.teacher_value_chips.hex(),
            "value_difference_chips": self.value_difference_chips.hex(),
        }


@dataclass(frozen=True, slots=True)
class CapacityFillingTeacherControl:
    pool_kind: CapacityFillingStructureKind
    panel_digest: str
    observations: tuple[CapacityFillingTeacherObservation, ...]

    def __post_init__(self) -> None:
        _qualified_pool_digest(self.pool_kind)
        if not _valid_digest(self.panel_digest):
            raise ValueError("capacity-filling teacher panel digest is invalid")
        if (
            not isinstance(self.observations, tuple)
            or len(self.observations) != ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT
        ):
            raise TypeError("capacity-filling teacher requires 24 observations")
        if any(
            not isinstance(observation, CapacityFillingTeacherObservation)
            for observation in self.observations
        ):
            raise TypeError("capacity-filling teacher contains a wrong observation")
        indices = tuple(observation.context_index for observation in self.observations)
        if tuple(sorted(indices)) != indices or len(set(indices)) != len(indices):
            raise ValueError("capacity-filling teacher indices must increase")

    @property
    def digest(self) -> str:
        payload = {
            "envelope_allowance_chips": (ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE.chips.hex()),
            "lp_duality_allowance_chips": (
                ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE.chips.hex()
            ),
            "observations": tuple(
                observation.canonical_payload for observation in self.observations
            ),
            "panel_digest": self.panel_digest,
            "pool_kind": self.pool_kind.value,
            "probability_allowance": (ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE.value.hex()),
            "simplex_pivot_cap": ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
            "solver_tolerance": (ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE.hex()),
            "teacher_agreement_allowance_chips": (
                ADR0305_V4_QUALIFICATION_TEACHER_AGREEMENT_ALLOWANCE.chips.hex()
            ),
            "teacher_duality_allowance_chips": (
                ADR0305_V4_QUALIFICATION_TEACHER_DUALITY_ALLOWANCE.chips.hex()
            ),
            "version": "capacity-filling-teacher-control-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def verify_against_pool(
        self,
        *,
        pool: FreshCapacityFillingStructure,
        result: CapacityFillingQualificationResult,
    ) -> None:
        panel = result.qualified_panel(pool=pool)
        if self.pool_kind is not panel.pool_kind:
            raise ValueError("capacity-filling teacher names the wrong family")
        if self.panel_digest != panel.digest:
            raise ValueError("capacity-filling teacher names the wrong panel")
        for observation, context_index, binding_digest in zip(
            self.observations,
            panel.pool_indices,
            panel.binding_digests,
            strict=True,
        ):
            binding = bind_capacity_filling_context_to_oracle(pool.contexts[context_index])
            bounded = binding.oracle_context.bounded_two_by_two()
            expected_sizes = (bounded.minimum_bet, bounded.stack)
            if observation.context_index != context_index:
                raise ValueError("capacity-filling teacher index differs from panel")
            if observation.binding_digest != binding_digest:
                raise ValueError("capacity-filling teacher binding differs from panel")
            if observation.bounded_context_digest != bounded.digest:
                raise ValueError("capacity-filling bounded teacher context drifted")
            if observation.bet_sizes != expected_sizes:
                raise ValueError("capacity-filling teacher arm differs from game")


@dataclass(frozen=True, slots=True)
class CapacityFillingQualificationCampaignResult:
    qualification: CapacityFillingQualificationResult
    teacher_control: CapacityFillingTeacherControl | None
    elapsed_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.qualification, CapacityFillingQualificationResult):
            raise TypeError("capacity-filling campaign qualification must be semantic")
        target_reached = self.qualification.stop_reason is QualificationStopReason.TARGET_REACHED
        if target_reached != isinstance(
            self.teacher_control,
            CapacityFillingTeacherControl,
        ):
            raise ValueError("capacity-filling teacher state disagrees with result")
        if target_reached:
            assert self.teacher_control is not None
            panel = self.qualification._panel_identity()
            if self.teacher_control.pool_kind is not panel.pool_kind:
                raise ValueError("capacity-filling campaign teacher family drifted")
            if self.teacher_control.panel_digest != panel.digest:
                raise ValueError("capacity-filling campaign teacher panel drifted")
            if (
                tuple(
                    observation.context_index for observation in self.teacher_control.observations
                )
                != panel.pool_indices
            ):
                raise ValueError("capacity-filling campaign teacher indices drifted")
            if (
                tuple(
                    observation.binding_digest for observation in self.teacher_control.observations
                )
                != panel.binding_digests
            ):
                raise ValueError("capacity-filling campaign teacher bindings drifted")
        if (
            not isinstance(self.elapsed_seconds, float)
            or not isfinite(self.elapsed_seconds)
            or self.elapsed_seconds < 0.0
        ):
            raise ValueError("capacity-filling elapsed time must be nonnegative")

    @property
    def passed(self) -> bool:
        return self.teacher_control is not None

    @property
    def digest(self) -> str:
        payload = {
            "pool_kind": self.qualification.pool_kind.value,
            "qualification_digest": self.qualification.digest,
            "teacher_control_digest": (
                None if self.teacher_control is None else self.teacher_control.digest
            ),
            "version": "capacity-filling-qualification-campaign-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def verify_against_pool(self, *, pool: FreshCapacityFillingStructure) -> None:
        self.qualification.verify_against_pool(pool=pool)
        if self.teacher_control is not None:
            self.teacher_control.verify_against_pool(
                pool=pool,
                result=self.qualification,
            )


def _run_qualification(
    *,
    pool: FreshCapacityFillingStructure,
) -> CapacityFillingQualificationResult:
    _qualified_pool_digest(pool.kind)
    observations: list[CapacityFillingQualificationObservation] = []
    qualified_indices: list[int] = []
    for context_index, structural_context in enumerate(pool.contexts):
        binding = bind_capacity_filling_context_to_oracle(structural_context)
        context = binding.oracle_context
        full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
        narrow_sizes = (context.minimum_bet, context.stack)
        try:
            full = solve_reduced_river_sizing(
                context,
                full_sizes,
                probability_allowance=(ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE),
                chip_allowance=(ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE),
                solver_tolerance=ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE,
                max_pivots=ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
            )
        except Exception as error:
            raise CapacityFillingQualificationNumericalFailure(
                pool_kind=pool.kind,
                pool_digest=pool.digest,
                context_index=context_index,
                structural_context_digest=binding.structural_context_digest,
                oracle_context_digest=context.digest,
                binding_digest=binding.digest,
                arm=CapacityFillingQualificationArm.FULL_INTEGER,
                bet_sizes=full_sizes,
                dimensions=width_four_lp_dimensions(context, full_sizes),
                completed_observations=tuple(observations),
                completed_qualified_indices=tuple(qualified_indices),
                cause_type=type(error).__name__,
                cause_message=str(error),
            ) from error
        try:
            narrow = solve_reduced_river_sizing(
                context,
                narrow_sizes,
                probability_allowance=(ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE),
                chip_allowance=(ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE),
                solver_tolerance=ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE,
                max_pivots=ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
            )
        except Exception as error:
            raise CapacityFillingQualificationNumericalFailure(
                pool_kind=pool.kind,
                pool_digest=pool.digest,
                context_index=context_index,
                structural_context_digest=binding.structural_context_digest,
                oracle_context_digest=context.digest,
                binding_digest=binding.digest,
                arm=CapacityFillingQualificationArm.MINIMUM_ALL_IN,
                bet_sizes=narrow_sizes,
                dimensions=width_four_lp_dimensions(context, narrow_sizes),
                completed_observations=tuple(observations),
                completed_qualified_indices=tuple(qualified_indices),
                cause_type=type(error).__name__,
                cause_message=str(error),
            ) from error
        if (
            full.value_chips + ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE.chips
            < narrow.value_chips
        ):
            raise AssertionError(
                f"capacity-filling {pool.kind.value} context {context_index}: "
                "full value fell below narrow"
            )
        classification = classify_sizing_opportunity(
            full_value_chips=full.value_chips,
            narrow_value_chips=narrow.value_chips,
            payoff_span=context.payoff_span,
            opportunity_floor=ADR0305_V4_QUALIFICATION_OPPORTUNITY_FLOOR,
            classification_guard=ADR0305_V4_QUALIFICATION_CLASSIFICATION_GUARD,
        )
        observations.append(
            CapacityFillingQualificationObservation(
                context_index=context_index,
                structural_context_digest=binding.structural_context_digest,
                oracle_context_digest=context.digest,
                binding_digest=binding.digest,
                full_value_chips=full.value_chips,
                narrow_value_chips=narrow.value_chips,
                payoff_span=context.payoff_span,
                classification=classification,
                full_bet_sizes=full_sizes,
                narrow_bet_sizes=narrow_sizes,
                full_dimensions=width_four_lp_dimensions(context, full_sizes),
                narrow_dimensions=width_four_lp_dimensions(context, narrow_sizes),
                full_simplex_pivots=full.simplex_pivots,
                narrow_simplex_pivots=narrow.simplex_pivots,
                max_probability_residual=max(
                    full.max_probability_simplex_residual,
                    narrow.max_probability_simplex_residual,
                ),
                max_chip_objective_error=max(
                    full.chip_objective_reconstruction_error,
                    narrow.chip_objective_reconstruction_error,
                ),
                max_lp_duality_gap_chips=max(
                    abs(full.linear_program_duality_gap),
                    abs(narrow.linear_program_duality_gap),
                ),
                max_envelope_violation_chips=max(
                    full.max_envelope_constraint_violation_chips,
                    narrow.max_envelope_constraint_violation_chips,
                ),
            )
        )
        if classification is SizingPowerClassification.AMBIGUOUS:
            return CapacityFillingQualificationResult(
                pool_kind=pool.kind,
                pool_digest=pool.digest,
                stop_reason=QualificationStopReason.AMBIGUOUS,
                observations=tuple(observations),
                qualified_indices=tuple(qualified_indices),
            )
        if classification is SizingPowerClassification.QUALIFYING:
            qualified_indices.append(context_index)
            if len(qualified_indices) == ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT:
                return CapacityFillingQualificationResult(
                    pool_kind=pool.kind,
                    pool_digest=pool.digest,
                    stop_reason=QualificationStopReason.TARGET_REACHED,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified_indices),
                )
    return CapacityFillingQualificationResult(
        pool_kind=pool.kind,
        pool_digest=pool.digest,
        stop_reason=QualificationStopReason.POOL_EXHAUSTED,
        observations=tuple(observations),
        qualified_indices=tuple(qualified_indices),
    )


def _run_teacher_control(
    *,
    pool: FreshCapacityFillingStructure,
    result: CapacityFillingQualificationResult,
) -> CapacityFillingTeacherControl:
    panel = result.qualified_panel(pool=pool)
    observations: list[CapacityFillingTeacherObservation] = []
    for context_index in result.qualified_indices:
        binding = bind_capacity_filling_context_to_oracle(pool.contexts[context_index])
        bounded = binding.oracle_context.bounded_two_by_two()
        sizes = (bounded.minimum_bet, bounded.stack)
        compact = solve_reduced_river_sizing(
            bounded,
            sizes,
            probability_allowance=ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE,
            max_pivots=ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
        )
        teacher = solve_bounded_normal_form_sizing_teacher(
            bounded,
            sizes,
            solver_tolerance=ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE,
        )
        observations.append(
            CapacityFillingTeacherObservation(
                context_index=context_index,
                binding_digest=binding.digest,
                bounded_context_digest=bounded.digest,
                bet_sizes=sizes,
                compact_value_chips=compact.value_chips,
                teacher_value_chips=teacher.value_chips,
                value_difference_chips=abs(compact.value_chips - teacher.value_chips),
                teacher_duality_gap_chips=abs(teacher.duality_gap),
                compact_probability_residual=(compact.max_probability_simplex_residual),
                compact_chip_objective_error=(compact.chip_objective_reconstruction_error),
                compact_lp_duality_gap_chips=abs(compact.linear_program_duality_gap),
                compact_envelope_violation_chips=(compact.max_envelope_constraint_violation_chips),
                compact_simplex_pivots=compact.simplex_pivots,
                teacher_opener_pure_plan_count=teacher.opener_pure_plan_count,
                teacher_responder_pure_plan_count=(teacher.responder_pure_plan_count),
            )
        )
    return CapacityFillingTeacherControl(
        pool_kind=pool.kind,
        panel_digest=panel.digest,
        observations=tuple(observations),
    )


def _run_owned_campaign(
    *,
    kind: CapacityFillingStructureKind,
) -> CapacityFillingQualificationCampaignResult:
    started = perf_counter()
    pool = build_adr0305_v4_structure(kind=kind)
    if pool.digest != _qualified_pool_digest(kind):
        raise AssertionError("capacity-filling qualified pool identity drifted")
    result = _run_qualification(pool=pool)
    result.verify_against_pool(pool=pool)
    if result.stop_reason is not QualificationStopReason.TARGET_REACHED:
        return CapacityFillingQualificationCampaignResult(
            qualification=result,
            teacher_control=None,
            elapsed_seconds=float(perf_counter() - started),
        )
    teacher = _run_teacher_control(pool=pool, result=result)
    teacher.verify_against_pool(pool=pool, result=result)
    campaign = CapacityFillingQualificationCampaignResult(
        qualification=result,
        teacher_control=teacher,
        elapsed_seconds=float(perf_counter() - started),
    )
    campaign.verify_against_pool(pool=pool)
    return campaign


def run_adr0305_v4_qualified_a() -> CapacityFillingQualificationCampaignResult:
    """Open qualified A only, under the frozen candidate-blind protocol."""

    campaign = _run_owned_campaign(kind=CapacityFillingStructureKind.QUALIFIED_A)
    if campaign.digest != ADR0310_QUALIFIED_A_CAMPAIGN_SHA256:
        raise AssertionError("ADR-0310 qualified-A campaign identity drifted")
    return campaign


def run_adr0305_v4_qualified_b(
    *,
    qualified_a: CapacityFillingQualificationCampaignResult,
) -> CapacityFillingQualificationCampaignResult:
    """Open B only after a verified target-reaching A result is supplied."""

    if not isinstance(qualified_a, CapacityFillingQualificationCampaignResult):
        raise TypeError("qualified B requires a semantic qualified-A campaign")
    if qualified_a.qualification.pool_kind is not CapacityFillingStructureKind.QUALIFIED_A:
        raise ValueError("qualified B requires the qualified-A family first")
    qualified_a_pool = build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_A)
    qualified_a.verify_against_pool(pool=qualified_a_pool)
    if not qualified_a.passed:
        raise ValueError("qualified B remains unopened after a failed qualified A")
    if qualified_a.digest != ADR0310_QUALIFIED_A_CAMPAIGN_SHA256:
        raise ValueError("qualified B requires ADR-0310's exact qualified-A pass")
    return _run_owned_campaign(kind=CapacityFillingStructureKind.QUALIFIED_B)


__all__ = [
    "ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE",
    "ADR0305_V4_QUALIFICATION_CLASSIFICATION_GUARD",
    "ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE",
    "ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE",
    "ADR0305_V4_QUALIFICATION_OPPORTUNITY_FLOOR",
    "ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE",
    "ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP",
    "ADR0305_V4_QUALIFICATION_SOLVER_TOLERANCE",
    "ADR0305_V4_QUALIFICATION_TEACHER_AGREEMENT_ALLOWANCE",
    "ADR0305_V4_QUALIFICATION_TEACHER_DUALITY_ALLOWANCE",
    "ADR0305_V4_QUALIFIED_PANEL_CONTEXT_COUNT",
    "ADR0310_QUALIFIED_A_CAMPAIGN_SHA256",
    "ADR0310_QUALIFIED_A_INDICES",
    "ADR0310_QUALIFIED_A_OPENED_CONTEXT_COUNT",
    "ADR0310_QUALIFIED_A_PROVISIONAL_PANEL_SHA256",
    "ADR0310_QUALIFIED_A_RESULT_SHA256",
    "ADR0310_QUALIFIED_A_TEACHER_CONTROL_SHA256",
    "ADR0310_QUALIFIED_B_COMPLETED_CONTEXT_COUNT",
    "ADR0310_QUALIFIED_B_COMPLETED_INDICES",
    "ADR0310_QUALIFIED_B_COMPLETED_QUALIFYING_INDICES",
    "ADR0310_QUALIFIED_B_FAILURE_CONTEXT_INDEX",
    "ADR0310_QUALIFIED_B_FAILURE_SHA256",
    "CapacityFillingEnvelopeViolationAllowance",
    "CapacityFillingLpDualityGapAllowance",
    "CapacityFillingOracleContextBinding",
    "CapacityFillingQualificationArm",
    "CapacityFillingQualificationCampaignResult",
    "CapacityFillingQualificationNumericalFailure",
    "CapacityFillingQualificationObservation",
    "CapacityFillingQualificationResult",
    "CapacityFillingQualifiedPanel",
    "CapacityFillingTeacherAgreementAllowance",
    "CapacityFillingTeacherControl",
    "CapacityFillingTeacherDualityAllowance",
    "CapacityFillingTeacherObservation",
    "bind_capacity_filling_context_to_oracle",
    "run_adr0305_v4_qualified_a",
    "run_adr0305_v4_qualified_b",
]
