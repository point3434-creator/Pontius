"""Owned candidate-blind qualification of ADR-0302's sealed fresh pool."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from time import perf_counter
from typing import Any

from .fresh_collision_repair_structures import (
    ADR0301_QUALIFIED_POOL_CONTEXT_COUNT,
    ADR0301_QUALIFIED_POOL_SHA256,
    FreshStructureKind,
    FreshWidthFourContext,
    FreshWidthFourStructure,
    build_adr0301_fresh_structure,
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

ADR0302_SOLVER_TOLERANCE = 1e-11
ADR0302_SIMPLEX_PIVOT_CAP = 4096
ADR0302_QUALIFIED_CONTEXT_COUNT = 24
ADR0302_OPPORTUNITY_FLOOR = NormalizedSizingOpportunityFloor(1e-4)
ADR0302_CLASSIFICATION_GUARD = ChipClassificationGuard(1e-8)
ADR0302_PROBABILITY_ALLOWANCE = ProbabilitySimplexAllowance(1e-9)
ADR0302_CHIP_OBJECTIVE_ALLOWANCE = ChipObjectiveAllowance(1e-9)
ADR0302_OPENED_CONTEXT_COUNT = 60
ADR0302_QUALIFIED_INDICES = (
    0,
    5,
    10,
    13,
    15,
    21,
    22,
    23,
    24,
    25,
    31,
    33,
    34,
    37,
    40,
    41,
    42,
    43,
    45,
    48,
    52,
    53,
    55,
    59,
)
ADR0302_QUALIFICATION_RESULT_SHA256 = (
    "c5be094e616043644a13ebbd477565ff548593a9d7d1f70dac0ae5340cbe0c23"
)
ADR0302_QUALIFIED_PANEL_SHA256 = (
    "05f00a99ccec22bfea07abd405b1089414a89bce9a4c4e704efceb132ea1cf29"
)
ADR0302_TEACHER_CONTROL_SHA256 = (
    "b88b47f2260da31bdb7e49a0d454309327483ded0ff6ea7b17d77bd2cf914ada"
)
ADR0302_CAMPAIGN_SHA256 = (
    "3ada7c7a68002eb2fa3d0e6ca904f0df771f17e8270fd09ef10cedef1772d8fe"
)


def _require_positive_allowance(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")
    return value


@dataclass(frozen=True, slots=True)
class FreshLpDualityGapAllowance:
    """Chip-valued compact-LP primal-dual gap allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(self.chips, label="fresh LP duality allowance")


@dataclass(frozen=True, slots=True)
class FreshEnvelopeViolationAllowance:
    """Chip-valued lower-envelope feasibility allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(self.chips, label="fresh envelope allowance")


@dataclass(frozen=True, slots=True)
class FreshTeacherAgreementAllowance:
    """Chip-valued compact-versus-normal-form agreement allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(self.chips, label="fresh teacher agreement")


@dataclass(frozen=True, slots=True)
class FreshTeacherDualityAllowance:
    """Chip-valued normal-form primal-dual gap allowance."""

    chips: float

    def __post_init__(self) -> None:
        _require_positive_allowance(self.chips, label="fresh teacher duality allowance")


ADR0302_LP_DUALITY_ALLOWANCE = FreshLpDualityGapAllowance(1e-9)
ADR0302_ENVELOPE_ALLOWANCE = FreshEnvelopeViolationAllowance(1e-9)
ADR0302_TEACHER_AGREEMENT_ALLOWANCE = FreshTeacherAgreementAllowance(1e-9)
ADR0302_TEACHER_DUALITY_ALLOWANCE = FreshTeacherDualityAllowance(1e-9)


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _context_payload(context: Any) -> dict[str, object]:
    probabilities = context.joint_probabilities
    return {
        "board": context.board,
        "context_id": context.context_id,
        "joint_probabilities": tuple(
            tuple(
                (probability.numerator, probability.denominator)
                for probability in row
            )
            for row in probabilities
        ),
        "minimum_bet": context.minimum_bet,
        "opener_hands": context.opener_hands,
        "pot": context.pot,
        "responder_hands": context.responder_hands,
        "stack": context.stack,
    }


@dataclass(frozen=True, slots=True)
class FreshOracleContextBinding:
    """Exact one-to-one binding from a value-free record to the sizing oracle."""

    structural_context: FreshWidthFourContext
    oracle_context: ReducedRiverSizingContext

    def __post_init__(self) -> None:
        if not isinstance(self.structural_context, FreshWidthFourContext):
            raise TypeError("fresh binding requires a structural context")
        if not isinstance(self.oracle_context, ReducedRiverSizingContext):
            raise TypeError("fresh binding requires an exact oracle context")
        if _context_payload(self.structural_context) != _context_payload(
            self.oracle_context
        ):
            raise ValueError("fresh structural-to-oracle conversion changed a field")
        if self.structural_context.payoff_span != self.oracle_context.payoff_span:
            raise ValueError("fresh structural-to-oracle conversion changed payoff span")
        if self.structural_context.showdown_signs != self.oracle_context.showdown_signs:
            raise ValueError("fresh structural-to-oracle conversion changed showdown")

    @property
    def digest(self) -> str:
        payload = {
            "context": _context_payload(self.oracle_context),
            "oracle_context_sha256": self.oracle_context.digest,
            "structural_context_sha256": self.structural_context.digest,
            "version": "fresh-structural-oracle-binding-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


def bind_fresh_context_to_oracle(
    context: FreshWidthFourContext,
) -> FreshOracleContextBinding:
    """Convert every exact field and immediately prove semantic identity."""

    if not isinstance(context, FreshWidthFourContext):
        raise TypeError("fresh conversion requires a structural context")
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
    return FreshOracleContextBinding(
        structural_context=context,
        oracle_context=oracle,
    )


@dataclass(frozen=True, slots=True)
class FreshQualificationObservation:
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
            or self.context_index not in range(ADR0301_QUALIFIED_POOL_CONTEXT_COUNT)
        ):
            raise ValueError("fresh observation index lies outside its pool")
        for label, digest in (
            ("structural context", self.structural_context_digest),
            ("oracle context", self.oracle_context_digest),
            ("binding", self.binding_digest),
        ):
            if not _valid_digest(digest):
                raise ValueError(f"fresh observation {label} digest is invalid")
        for label, value in (
            ("full value", self.full_value_chips),
            ("narrow value", self.narrow_value_chips),
            ("probability residual", self.max_probability_residual),
            ("chip objective error", self.max_chip_objective_error),
            ("LP duality gap", self.max_lp_duality_gap_chips),
            ("envelope violation", self.max_envelope_violation_chips),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"fresh observation {label} must be finite")
        if (
            isinstance(self.payoff_span, bool)
            or not isinstance(self.payoff_span, int)
            or self.payoff_span <= 0
        ):
            raise ValueError("fresh observation payoff span must be positive")
        if not isinstance(self.classification, SizingPowerClassification):
            raise TypeError("fresh observation classification must be semantic")
        for label, sizes in (
            ("full", self.full_bet_sizes),
            ("narrow", self.narrow_bet_sizes),
        ):
            if not isinstance(sizes, tuple) or not sizes:
                raise TypeError(f"fresh observation {label} sizes must be immutable")
            if any(
                isinstance(size, bool) or not isinstance(size, int) or size <= 0
                for size in sizes
            ):
                raise ValueError(f"fresh observation {label} sizes must be positive")
            if tuple(sorted(set(sizes))) != sizes:
                raise ValueError(f"fresh observation {label} sizes must increase")
        if not isinstance(self.full_dimensions, ReducedSizingLpDimensions) or not isinstance(
            self.narrow_dimensions,
            ReducedSizingLpDimensions,
        ):
            raise TypeError("fresh observation LP dimensions must be semantic")
        for label, pivots in (
            ("full", self.full_simplex_pivots),
            ("narrow", self.narrow_simplex_pivots),
        ):
            if isinstance(pivots, bool) or not isinstance(pivots, int) or pivots < 0:
                raise ValueError(f"fresh {label} pivot count must be nonnegative")
            if pivots > ADR0302_SIMPLEX_PIVOT_CAP:
                raise ValueError(f"fresh {label} pivot count exceeds ADR-0300")
        if not (
            0.0
            <= self.max_probability_residual
            <= ADR0302_PROBABILITY_ALLOWANCE.value
        ):
            raise ValueError("fresh probability residual exceeds ADR-0300")
        if not (
            0.0
            <= self.max_chip_objective_error
            <= ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips
        ):
            raise ValueError("fresh chip objective error exceeds ADR-0300")
        if not (
            0.0
            <= self.max_lp_duality_gap_chips
            <= ADR0302_LP_DUALITY_ALLOWANCE.chips
        ):
            raise ValueError("fresh LP duality gap exceeds ADR-0300")
        if not (
            0.0
            <= self.max_envelope_violation_chips
            <= ADR0302_ENVELOPE_ALLOWANCE.chips
        ):
            raise ValueError("fresh envelope violation exceeds ADR-0300")


@dataclass(frozen=True, slots=True)
class FreshQualifiedPanel:
    pool_digest: str
    pool_indices: tuple[int, ...]
    structural_context_digests: tuple[str, ...]
    oracle_context_digests: tuple[str, ...]
    binding_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.pool_digest != ADR0301_QUALIFIED_POOL_SHA256:
            raise ValueError("fresh panel pool digest is not sealed")
        if not isinstance(self.pool_indices, tuple) or len(
            self.pool_indices
        ) != ADR0302_QUALIFIED_CONTEXT_COUNT:
            raise TypeError("fresh panel requires 24 immutable indices")
        if any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index not in range(ADR0301_QUALIFIED_POOL_CONTEXT_COUNT)
            for index in self.pool_indices
        ):
            raise ValueError("fresh panel index lies outside its pool")
        if tuple(sorted(self.pool_indices)) != self.pool_indices or len(
            set(self.pool_indices)
        ) != len(self.pool_indices):
            raise ValueError("fresh panel indices must increase strictly")
        for label, digests in (
            ("structural", self.structural_context_digests),
            ("oracle", self.oracle_context_digests),
            ("binding", self.binding_digests),
        ):
            if not isinstance(digests, tuple) or len(digests) != len(
                self.pool_indices
            ):
                raise TypeError(f"fresh panel {label} digests must align")
            if any(not _valid_digest(digest) for digest in digests):
                raise ValueError(f"fresh panel {label} digest is invalid")

    @property
    def digest(self) -> str:
        payload = {
            "binding_digests": self.binding_digests,
            "oracle_context_digests": self.oracle_context_digests,
            "pool_digest": self.pool_digest,
            "pool_indices": self.pool_indices,
            "structural_context_digests": self.structural_context_digests,
            "version": "fresh-collision-repair-qualified-panel-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class FreshQualificationResult:
    pool_digest: str
    stop_reason: QualificationStopReason
    observations: tuple[FreshQualificationObservation, ...]
    qualified_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.pool_digest != ADR0301_QUALIFIED_POOL_SHA256:
            raise ValueError("fresh qualification pool digest is not sealed")
        if not isinstance(self.stop_reason, QualificationStopReason):
            raise TypeError("fresh qualification stop reason must be semantic")
        if not isinstance(self.observations, tuple) or not self.observations:
            raise TypeError("fresh qualification requires immutable observations")
        if any(
            not isinstance(observation, FreshQualificationObservation)
            for observation in self.observations
        ):
            raise TypeError("fresh qualification contains a nonsemantic observation")
        if tuple(
            observation.context_index for observation in self.observations
        ) != tuple(range(len(self.observations))):
            raise ValueError("fresh observations must be a contiguous pool prefix")
        expected_qualified = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.QUALIFYING
        )
        if self.qualified_indices != expected_qualified:
            raise ValueError("fresh qualified indices disagree with observations")
        ambiguous = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.AMBIGUOUS
        )
        if self.stop_reason is QualificationStopReason.AMBIGUOUS:
            if ambiguous != (len(self.observations) - 1,):
                raise ValueError("fresh qualification must stop at first ambiguity")
            if len(self.qualified_indices) >= ADR0302_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("ambiguous fresh result already reached its target")
        elif ambiguous:
            raise ValueError("non-ambiguous fresh result contains an ambiguity")
        if self.stop_reason is QualificationStopReason.TARGET_REACHED:
            if len(self.qualified_indices) != ADR0302_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("target-reached fresh result lacks 24 qualifiers")
            if self.qualified_indices[-1] != len(self.observations) - 1:
                raise ValueError("target-reached fresh result opened a later value")
        elif self.stop_reason is QualificationStopReason.POOL_EXHAUSTED:
            if len(self.observations) != ADR0301_QUALIFIED_POOL_CONTEXT_COUNT:
                raise ValueError("exhausted fresh result did not open its full pool")
            if len(self.qualified_indices) >= ADR0302_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("exhausted fresh result already reached its target")

    @property
    def opened_context_count(self) -> int:
        return len(self.observations)

    @property
    def digest(self) -> str:
        payload = {
            "chip_classification_guard": ADR0302_CLASSIFICATION_GUARD.chips.hex(),
            "chip_objective_allowance": ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips.hex(),
            "envelope_allowance_chips": ADR0302_ENVELOPE_ALLOWANCE.chips.hex(),
            "lp_duality_allowance_chips": ADR0302_LP_DUALITY_ALLOWANCE.chips.hex(),
            "observations": tuple(
                {
                    "binding_digest": observation.binding_digest,
                    "classification": observation.classification.value,
                    "context_index": observation.context_index,
                    "full_dimensions": (
                        observation.full_dimensions.variable_count,
                        observation.full_dimensions.inequality_count,
                    ),
                    "full_bet_sizes": observation.full_bet_sizes,
                    "full_simplex_pivots": observation.full_simplex_pivots,
                    "full_value_chips": observation.full_value_chips.hex(),
                    "max_chip_objective_error": (
                        observation.max_chip_objective_error.hex()
                    ),
                    "max_envelope_violation_chips": (
                        observation.max_envelope_violation_chips.hex()
                    ),
                    "max_lp_duality_gap_chips": (
                        observation.max_lp_duality_gap_chips.hex()
                    ),
                    "max_probability_residual": (
                        observation.max_probability_residual.hex()
                    ),
                    "narrow_dimensions": (
                        observation.narrow_dimensions.variable_count,
                        observation.narrow_dimensions.inequality_count,
                    ),
                    "narrow_bet_sizes": observation.narrow_bet_sizes,
                    "narrow_simplex_pivots": observation.narrow_simplex_pivots,
                    "narrow_value_chips": observation.narrow_value_chips.hex(),
                    "oracle_context_digest": observation.oracle_context_digest,
                    "payoff_span": observation.payoff_span,
                    "structural_context_digest": (
                        observation.structural_context_digest
                    ),
                }
                for observation in self.observations
            ),
            "opportunity_floor": ADR0302_OPPORTUNITY_FLOOR.value.hex(),
            "pool_digest": self.pool_digest,
            "probability_allowance": ADR0302_PROBABILITY_ALLOWANCE.value.hex(),
            "qualified_indices": self.qualified_indices,
            "simplex_pivot_cap": ADR0302_SIMPLEX_PIVOT_CAP,
            "solver_tolerance": ADR0302_SOLVER_TOLERANCE.hex(),
            "stop_reason": self.stop_reason.value,
            "version": "fresh-collision-repair-qualification-result-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def verify_against_pool(self, *, pool: FreshWidthFourStructure) -> None:
        if (
            not isinstance(pool, FreshWidthFourStructure)
            or pool.kind is not FreshStructureKind.QUALIFIED_POOL
            or pool.digest != self.pool_digest
        ):
            raise ValueError("fresh verification pool differs from its result")
        for observation, structural_context in zip(
            self.observations,
            pool.contexts[: len(self.observations)],
            strict=True,
        ):
            binding = bind_fresh_context_to_oracle(structural_context)
            context = binding.oracle_context
            if observation.structural_context_digest != structural_context.digest:
                raise ValueError("fresh result structural prefix differs from its pool")
            if observation.oracle_context_digest != context.digest:
                raise ValueError("fresh result oracle prefix differs from conversion")
            if observation.binding_digest != binding.digest:
                raise ValueError("fresh result binding prefix differs from conversion")
            if observation.payoff_span != structural_context.payoff_span:
                raise ValueError("fresh result payoff span differs from its game")
            full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
            narrow_sizes = (context.minimum_bet, context.stack)
            if observation.full_bet_sizes != full_sizes:
                raise ValueError("fresh result full arm differs from its game")
            if observation.narrow_bet_sizes != narrow_sizes:
                raise ValueError("fresh result narrow arm differs from its game")
            if observation.full_dimensions != width_four_lp_dimensions(
                context,
                full_sizes,
            ):
                raise ValueError("fresh result full LP dimensions differ")
            if observation.narrow_dimensions != width_four_lp_dimensions(
                context,
                narrow_sizes,
            ):
                raise ValueError("fresh result narrow LP dimensions differ")
            expected = classify_sizing_opportunity(
                full_value_chips=observation.full_value_chips,
                narrow_value_chips=observation.narrow_value_chips,
                payoff_span=context.payoff_span,
                opportunity_floor=ADR0302_OPPORTUNITY_FLOOR,
                classification_guard=ADR0302_CLASSIFICATION_GUARD,
            )
            if observation.classification is not expected:
                raise ValueError("fresh result classification differs from values")
            if (
                observation.full_value_chips
                + ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips
                < observation.narrow_value_chips
            ):
                raise ValueError("fresh result reverses full and narrow values")

    def qualified_panel(
        self,
        *,
        pool: FreshWidthFourStructure,
    ) -> FreshQualifiedPanel:
        if self.stop_reason is not QualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached fresh result has a panel")
        self.verify_against_pool(pool=pool)
        return self._panel_identity()

    def _panel_identity(self) -> FreshQualifiedPanel:
        if self.stop_reason is not QualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached fresh result has a panel")
        selected = tuple(self.observations[index] for index in self.qualified_indices)
        return FreshQualifiedPanel(
            pool_digest=self.pool_digest,
            pool_indices=self.qualified_indices,
            structural_context_digests=tuple(
                observation.structural_context_digest for observation in selected
            ),
            oracle_context_digests=tuple(
                observation.oracle_context_digest for observation in selected
            ),
            binding_digests=tuple(
                observation.binding_digest for observation in selected
            ),
        )


@dataclass(frozen=True, slots=True)
class FreshTeacherObservation:
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
            or self.context_index not in range(ADR0301_QUALIFIED_POOL_CONTEXT_COUNT)
        ):
            raise ValueError("fresh teacher index lies outside its pool")
        if not _valid_digest(self.binding_digest):
            raise ValueError("fresh teacher binding digest is invalid")
        if not _valid_digest(self.bounded_context_digest):
            raise ValueError("fresh teacher bounded-context digest is invalid")
        if (
            not isinstance(self.bet_sizes, tuple)
            or len(self.bet_sizes) != 2
            or any(
                isinstance(size, bool) or not isinstance(size, int) or size <= 0
                for size in self.bet_sizes
            )
            or self.bet_sizes[0] >= self.bet_sizes[1]
        ):
            raise ValueError("fresh teacher sizes must be exact minimum/all-in")
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
                raise ValueError(f"fresh teacher {label} must be finite")
        if self.value_difference_chips != abs(
            self.compact_value_chips - self.teacher_value_chips
        ):
            raise ValueError("fresh teacher value difference is inconsistent")
        for label, value, allowance in (
            (
                "value difference",
                self.value_difference_chips,
                ADR0302_TEACHER_AGREEMENT_ALLOWANCE.chips,
            ),
            (
                "teacher duality gap",
                self.teacher_duality_gap_chips,
                ADR0302_TEACHER_DUALITY_ALLOWANCE.chips,
            ),
            (
                "probability residual",
                self.compact_probability_residual,
                ADR0302_PROBABILITY_ALLOWANCE.value,
            ),
            (
                "chip objective error",
                self.compact_chip_objective_error,
                ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips,
            ),
            (
                "LP duality gap",
                self.compact_lp_duality_gap_chips,
                ADR0302_LP_DUALITY_ALLOWANCE.chips,
            ),
            (
                "envelope violation",
                self.compact_envelope_violation_chips,
                ADR0302_ENVELOPE_ALLOWANCE.chips,
            ),
        ):
            if value < 0.0 or value > allowance:
                raise ValueError(f"fresh teacher {label} exceeds ADR-0300")
        if (
            isinstance(self.compact_simplex_pivots, bool)
            or not isinstance(self.compact_simplex_pivots, int)
            or self.compact_simplex_pivots < 0
            or self.compact_simplex_pivots > ADR0302_SIMPLEX_PIVOT_CAP
        ):
            raise ValueError("fresh teacher compact pivots exceed ADR-0300")
        if self.teacher_opener_pure_plan_count != 9:
            raise ValueError("fresh teacher opener plan count differs from exact work")
        if self.teacher_responder_pure_plan_count != 16:
            raise ValueError("fresh teacher responder plan count differs from exact work")

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "binding_digest": self.binding_digest,
            "bet_sizes": self.bet_sizes,
            "bounded_context_digest": self.bounded_context_digest,
            "compact_chip_objective_error": (
                self.compact_chip_objective_error.hex()
            ),
            "compact_envelope_violation_chips": (
                self.compact_envelope_violation_chips.hex()
            ),
            "compact_lp_duality_gap_chips": (
                self.compact_lp_duality_gap_chips.hex()
            ),
            "compact_probability_residual": (
                self.compact_probability_residual.hex()
            ),
            "compact_simplex_pivots": self.compact_simplex_pivots,
            "compact_value_chips": self.compact_value_chips.hex(),
            "context_index": self.context_index,
            "teacher_duality_gap_chips": self.teacher_duality_gap_chips.hex(),
            "teacher_opener_pure_plan_count": self.teacher_opener_pure_plan_count,
            "teacher_responder_pure_plan_count": (
                self.teacher_responder_pure_plan_count
            ),
            "teacher_value_chips": self.teacher_value_chips.hex(),
            "value_difference_chips": self.value_difference_chips.hex(),
        }


@dataclass(frozen=True, slots=True)
class FreshTeacherControl:
    panel_digest: str
    observations: tuple[FreshTeacherObservation, ...]

    def __post_init__(self) -> None:
        if not _valid_digest(self.panel_digest):
            raise ValueError("fresh teacher panel digest is invalid")
        if not isinstance(self.observations, tuple) or len(
            self.observations
        ) != ADR0302_QUALIFIED_CONTEXT_COUNT:
            raise TypeError("fresh teacher requires 24 immutable observations")
        if any(
            not isinstance(observation, FreshTeacherObservation)
            for observation in self.observations
        ):
            raise TypeError("fresh teacher contains a nonsemantic observation")
        indices = tuple(observation.context_index for observation in self.observations)
        if tuple(sorted(indices)) != indices or len(set(indices)) != len(indices):
            raise ValueError("fresh teacher indices must increase strictly")

    @property
    def digest(self) -> str:
        payload = {
            "envelope_allowance_chips": ADR0302_ENVELOPE_ALLOWANCE.chips.hex(),
            "lp_duality_allowance_chips": ADR0302_LP_DUALITY_ALLOWANCE.chips.hex(),
            "observations": tuple(
                observation.canonical_payload for observation in self.observations
            ),
            "panel_digest": self.panel_digest,
            "probability_allowance": ADR0302_PROBABILITY_ALLOWANCE.value.hex(),
            "simplex_pivot_cap": ADR0302_SIMPLEX_PIVOT_CAP,
            "solver_tolerance": ADR0302_SOLVER_TOLERANCE.hex(),
            "teacher_agreement_allowance_chips": (
                ADR0302_TEACHER_AGREEMENT_ALLOWANCE.chips.hex()
            ),
            "teacher_duality_allowance_chips": (
                ADR0302_TEACHER_DUALITY_ALLOWANCE.chips.hex()
            ),
            "version": "fresh-collision-repair-teacher-control-v1",
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
        pool: FreshWidthFourStructure,
        result: FreshQualificationResult,
    ) -> None:
        panel = result.qualified_panel(pool=pool)
        if self.panel_digest != panel.digest:
            raise ValueError("fresh teacher control names the wrong qualified panel")
        for observation, context_index, binding_digest in zip(
            self.observations,
            panel.pool_indices,
            panel.binding_digests,
            strict=True,
        ):
            binding = bind_fresh_context_to_oracle(pool.contexts[context_index])
            bounded = binding.oracle_context.bounded_two_by_two()
            expected_sizes = (bounded.minimum_bet, bounded.stack)
            if observation.context_index != context_index:
                raise ValueError("fresh teacher control index differs from its panel")
            if observation.binding_digest != binding_digest:
                raise ValueError("fresh teacher control binding differs from its panel")
            if observation.bounded_context_digest != bounded.digest:
                raise ValueError("fresh teacher bounded context differs from conversion")
            if observation.bet_sizes != expected_sizes:
                raise ValueError("fresh teacher arm differs from minimum/all-in")


@dataclass(frozen=True, slots=True)
class FreshQualificationCampaignResult:
    qualification: FreshQualificationResult
    teacher_control: FreshTeacherControl | None
    elapsed_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.qualification, FreshQualificationResult):
            raise TypeError("fresh campaign qualification must be semantic")
        target_reached = (
            self.qualification.stop_reason is QualificationStopReason.TARGET_REACHED
        )
        if target_reached != isinstance(self.teacher_control, FreshTeacherControl):
            raise ValueError("fresh campaign teacher state disagrees with qualification")
        if target_reached:
            assert self.teacher_control is not None
            panel = self.qualification._panel_identity()
            if self.teacher_control.panel_digest != panel.digest:
                raise ValueError("fresh campaign teacher names the wrong panel")
            if tuple(
                observation.context_index
                for observation in self.teacher_control.observations
            ) != panel.pool_indices:
                raise ValueError("fresh campaign teacher indices differ from its panel")
            if tuple(
                observation.binding_digest
                for observation in self.teacher_control.observations
            ) != panel.binding_digests:
                raise ValueError("fresh campaign teacher bindings differ from its panel")
        if (
            not isinstance(self.elapsed_seconds, float)
            or not isfinite(self.elapsed_seconds)
            or self.elapsed_seconds < 0.0
        ):
            raise ValueError("fresh campaign elapsed time must be nonnegative")

    @property
    def passed(self) -> bool:
        return self.teacher_control is not None

    @property
    def digest(self) -> str:
        payload = {
            "qualification_digest": self.qualification.digest,
            "teacher_control_digest": (
                None if self.teacher_control is None else self.teacher_control.digest
            ),
            "version": "fresh-collision-repair-qualification-campaign-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


def _run_qualification(
    *,
    pool: FreshWidthFourStructure,
) -> FreshQualificationResult:
    observations: list[FreshQualificationObservation] = []
    qualified_indices: list[int] = []
    for context_index, structural_context in enumerate(pool.contexts):
        binding = bind_fresh_context_to_oracle(structural_context)
        context = binding.oracle_context
        full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
        narrow_sizes = (context.minimum_bet, context.stack)
        full = solve_reduced_river_sizing(
            context,
            full_sizes,
            probability_allowance=ADR0302_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0302_SOLVER_TOLERANCE,
            max_pivots=ADR0302_SIMPLEX_PIVOT_CAP,
        )
        narrow = solve_reduced_river_sizing(
            context,
            narrow_sizes,
            probability_allowance=ADR0302_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0302_SOLVER_TOLERANCE,
            max_pivots=ADR0302_SIMPLEX_PIVOT_CAP,
        )
        if (
            full.value_chips + ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips
            < narrow.value_chips
        ):
            raise AssertionError(
                f"ADR-0302 context {context_index}: full value fell below narrow"
            )
        classification = classify_sizing_opportunity(
            full_value_chips=full.value_chips,
            narrow_value_chips=narrow.value_chips,
            payoff_span=context.payoff_span,
            opportunity_floor=ADR0302_OPPORTUNITY_FLOOR,
            classification_guard=ADR0302_CLASSIFICATION_GUARD,
        )
        observations.append(
            FreshQualificationObservation(
                context_index=context_index,
                structural_context_digest=structural_context.digest,
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
            return FreshQualificationResult(
                pool_digest=pool.digest,
                stop_reason=QualificationStopReason.AMBIGUOUS,
                observations=tuple(observations),
                qualified_indices=tuple(qualified_indices),
            )
        if classification is SizingPowerClassification.QUALIFYING:
            qualified_indices.append(context_index)
            if len(qualified_indices) == ADR0302_QUALIFIED_CONTEXT_COUNT:
                return FreshQualificationResult(
                    pool_digest=pool.digest,
                    stop_reason=QualificationStopReason.TARGET_REACHED,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified_indices),
                )
    return FreshQualificationResult(
        pool_digest=pool.digest,
        stop_reason=QualificationStopReason.POOL_EXHAUSTED,
        observations=tuple(observations),
        qualified_indices=tuple(qualified_indices),
    )


def _run_teacher_control(
    *,
    pool: FreshWidthFourStructure,
    result: FreshQualificationResult,
) -> FreshTeacherControl:
    panel = result.qualified_panel(pool=pool)
    observations: list[FreshTeacherObservation] = []
    for context_index in result.qualified_indices:
        binding = bind_fresh_context_to_oracle(pool.contexts[context_index])
        bounded = binding.oracle_context.bounded_two_by_two()
        sizes = (bounded.minimum_bet, bounded.stack)
        compact = solve_reduced_river_sizing(
            bounded,
            sizes,
            probability_allowance=ADR0302_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0302_SOLVER_TOLERANCE,
            max_pivots=ADR0302_SIMPLEX_PIVOT_CAP,
        )
        teacher = solve_bounded_normal_form_sizing_teacher(
            bounded,
            sizes,
            solver_tolerance=ADR0302_SOLVER_TOLERANCE,
        )
        observations.append(
            FreshTeacherObservation(
                context_index=context_index,
                binding_digest=binding.digest,
                bounded_context_digest=bounded.digest,
                bet_sizes=sizes,
                compact_value_chips=compact.value_chips,
                teacher_value_chips=teacher.value_chips,
                value_difference_chips=abs(
                    compact.value_chips - teacher.value_chips
                ),
                teacher_duality_gap_chips=abs(teacher.duality_gap),
                compact_probability_residual=(
                    compact.max_probability_simplex_residual
                ),
                compact_chip_objective_error=(
                    compact.chip_objective_reconstruction_error
                ),
                compact_lp_duality_gap_chips=abs(
                    compact.linear_program_duality_gap
                ),
                compact_envelope_violation_chips=(
                    compact.max_envelope_constraint_violation_chips
                ),
                compact_simplex_pivots=compact.simplex_pivots,
                teacher_opener_pure_plan_count=teacher.opener_pure_plan_count,
                teacher_responder_pure_plan_count=(
                    teacher.responder_pure_plan_count
                ),
            )
        )
    return FreshTeacherControl(
        panel_digest=panel.digest,
        observations=tuple(observations),
    )


def run_adr0302_fresh_qualification() -> FreshQualificationCampaignResult:
    """Own the only fresh qualification invocation and its exact stop state."""

    started = perf_counter()
    pool = build_adr0301_fresh_structure(kind=FreshStructureKind.QUALIFIED_POOL)
    if pool.digest != ADR0301_QUALIFIED_POOL_SHA256:
        raise AssertionError("ADR-0302 qualified pool identity drifted")
    result = _run_qualification(pool=pool)
    result.verify_against_pool(pool=pool)
    if result.stop_reason is not QualificationStopReason.TARGET_REACHED:
        return FreshQualificationCampaignResult(
            qualification=result,
            teacher_control=None,
            elapsed_seconds=float(perf_counter() - started),
        )
    teacher = _run_teacher_control(pool=pool, result=result)
    teacher.verify_against_pool(pool=pool, result=result)
    campaign = FreshQualificationCampaignResult(
        qualification=result,
        teacher_control=teacher,
        elapsed_seconds=float(perf_counter() - started),
    )
    return campaign


def build_adr0302_qualified_panel() -> FreshQualifiedPanel:
    """Rebuild the sealed panel identity without reopening any sizing value."""

    pool = build_adr0301_fresh_structure(kind=FreshStructureKind.QUALIFIED_POOL)
    bindings = tuple(
        bind_fresh_context_to_oracle(pool.contexts[index])
        for index in ADR0302_QUALIFIED_INDICES
    )
    panel = FreshQualifiedPanel(
        pool_digest=pool.digest,
        pool_indices=ADR0302_QUALIFIED_INDICES,
        structural_context_digests=tuple(
            binding.structural_context.digest for binding in bindings
        ),
        oracle_context_digests=tuple(
            binding.oracle_context.digest for binding in bindings
        ),
        binding_digests=tuple(binding.digest for binding in bindings),
    )
    if panel.digest != ADR0302_QUALIFIED_PANEL_SHA256:
        raise AssertionError("ADR-0302 qualified panel identity drifted")
    return panel


__all__ = [
    "ADR0302_CAMPAIGN_SHA256",
    "ADR0302_CHIP_OBJECTIVE_ALLOWANCE",
    "ADR0302_CLASSIFICATION_GUARD",
    "ADR0302_ENVELOPE_ALLOWANCE",
    "ADR0302_LP_DUALITY_ALLOWANCE",
    "ADR0302_OPENED_CONTEXT_COUNT",
    "ADR0302_OPPORTUNITY_FLOOR",
    "ADR0302_PROBABILITY_ALLOWANCE",
    "ADR0302_QUALIFICATION_RESULT_SHA256",
    "ADR0302_QUALIFIED_CONTEXT_COUNT",
    "ADR0302_QUALIFIED_INDICES",
    "ADR0302_QUALIFIED_PANEL_SHA256",
    "ADR0302_SIMPLEX_PIVOT_CAP",
    "ADR0302_SOLVER_TOLERANCE",
    "ADR0302_TEACHER_AGREEMENT_ALLOWANCE",
    "ADR0302_TEACHER_CONTROL_SHA256",
    "ADR0302_TEACHER_DUALITY_ALLOWANCE",
    "FreshEnvelopeViolationAllowance",
    "FreshLpDualityGapAllowance",
    "FreshOracleContextBinding",
    "FreshQualificationCampaignResult",
    "FreshQualificationObservation",
    "FreshQualificationResult",
    "FreshQualifiedPanel",
    "FreshTeacherAgreementAllowance",
    "FreshTeacherControl",
    "FreshTeacherDualityAllowance",
    "FreshTeacherObservation",
    "bind_fresh_context_to_oracle",
    "build_adr0302_qualified_panel",
    "run_adr0302_fresh_qualification",
]
