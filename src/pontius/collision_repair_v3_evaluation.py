"""Frozen representative-first collision-repair v3 evaluation from ADR-0300."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from time import perf_counter

from .collision_repair_action_abstraction import (
    ADR0300_COLLISION_REPAIR_SOURCE_ID,
    ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
    CollisionRepairActionAbstractionSource,
)
from .fresh_collision_repair_qualification import (
    ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
    ADR0302_ENVELOPE_ALLOWANCE,
    ADR0302_LP_DUALITY_ALLOWANCE,
    ADR0302_PROBABILITY_ALLOWANCE,
    ADR0302_QUALIFIED_INDICES,
    ADR0302_QUALIFIED_PANEL_SHA256,
    ADR0302_SIMPLEX_PIVOT_CAP,
    ADR0302_SOLVER_TOLERANCE,
    FreshOracleContextBinding,
    FreshTeacherObservation,
    bind_fresh_context_to_oracle,
    build_adr0302_qualified_panel,
)
from .fresh_collision_repair_structures import (
    ADR0301_QUALIFIED_POOL_SHA256,
    ADR0301_REPRESENTATIVE_CONTEXT_COUNT,
    ADR0301_REPRESENTATIVE_SHA256,
    FreshStructureKind,
    FreshWidthFourStructure,
    build_adr0301_fresh_structure,
)
from .no_limit_betting import BettingActionKind
from .reduced_river_sizing_oracle import (
    ReducedRiverSizingContext,
    solve_bounded_normal_form_sizing_teacher,
    solve_reduced_river_sizing,
    two_live_seat_river_opening_state,
)
from .width_four_sizing_power import (
    ReducedSizingLpDimensions,
    width_four_lp_dimensions,
)


def _require_finite_unit_interval(
    value: object,
    *,
    label: str,
    include_zero: bool = False,
) -> float:
    if not isinstance(value, float) or not isfinite(value):
        raise ValueError(f"{label} must be a finite float")
    below_range = value < 0.0 if include_zero else value <= 0.0
    if below_range or value > 1.0:
        bracket = "[0, 1]" if include_zero else "(0, 1]"
        raise ValueError(f"{label} must lie in {bracket}")
    return value


@dataclass(frozen=True, slots=True)
class V3OrderingAllowance:
    """Chip-valued full/candidate/narrow ordering allowance."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips):
            raise ValueError("v3 ordering allowance must be finite")
        if self.chips <= 0.0:
            raise ValueError("v3 ordering allowance must be positive")


@dataclass(frozen=True, slots=True)
class V3MaximumNormalizedLossLimit:
    """Dimensionless per-context normalized-loss ceiling."""

    value: float

    def __post_init__(self) -> None:
        _require_finite_unit_interval(self.value, label="v3 maximum normalized loss")


@dataclass(frozen=True, slots=True)
class V3MeanNormalizedLossLimit:
    """Dimensionless family-mean normalized-loss ceiling."""

    value: float

    def __post_init__(self) -> None:
        _require_finite_unit_interval(self.value, label="v3 mean normalized loss")


@dataclass(frozen=True, slots=True)
class V3AggregateRecoveryFloor:
    """Dimensionless raw-chip aggregate-recovery floor."""

    value: float

    def __post_init__(self) -> None:
        _require_finite_unit_interval(self.value, label="v3 aggregate recovery")


ADR0300_ORDERING_ALLOWANCE = V3OrderingAllowance(1e-9)
ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT = V3MaximumNormalizedLossLimit(0.005)
ADR0300_MEAN_NORMALIZED_LOSS_LIMIT = V3MeanNormalizedLossLimit(0.001)
ADR0300_AGGREGATE_RECOVERY_FLOOR = V3AggregateRecoveryFloor(0.90)
ADR0300_MAXIMUM_V3_RAISES = 7
ADR0300_MAXIMUM_V3_ACTIONS = 9
ADR0300_REPRESENTATIVE_RESULT_SHA256 = (
    "37217f9b4b1dab282dd0c0a998559d10714de6e593b73d2209b45033a75f8c30"
)
ADR0300_QUALIFIED_RESULT_SHA256 = (
    "fdf2261940947020d38ad518ab37c2a8031dc2b8a161157f1e26e862ed0c83c2"
)
ADR0300_EVALUATION_CAMPAIGN_SHA256 = (
    "5e27d5767b35ef43d2a75a9c97aca3d46a3ee966037220299d82c8d571a6dbdf"
)


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


class V3PanelKind(StrEnum):
    REPRESENTATIVE = "representative"
    QUALIFIED = "qualified"


class V3ArmKind(StrEnum):
    FULL_INTEGER = "full_integer"
    COLLISION_REPAIR_V3 = "collision_repair_v3"
    MINIMUM_ALL_IN = "minimum_all_in"


class V3CampaignStopReason(StrEnum):
    REPRESENTATIVE_REJECTED = "representative_rejected"
    QUALIFIED_REJECTED = "qualified_rejected"
    PASSED = "passed"


@dataclass(frozen=True, slots=True)
class V3ArmEvidence:
    kind: V3ArmKind
    bet_sizes: tuple[int, ...]
    value_chips: float
    dimensions: ReducedSizingLpDimensions
    simplex_pivots: int
    probability_residual: float
    chip_objective_error: float
    lp_duality_gap_chips: float
    envelope_violation_chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.kind, V3ArmKind):
            raise TypeError("v3 arm kind must be semantic")
        if not isinstance(self.bet_sizes, tuple) or not self.bet_sizes:
            raise TypeError("v3 arm sizes must be a nonempty immutable tuple")
        if any(
            isinstance(size, bool) or not isinstance(size, int) or size <= 0
            for size in self.bet_sizes
        ):
            raise ValueError("v3 arm sizes must be positive integers")
        if tuple(sorted(set(self.bet_sizes))) != self.bet_sizes:
            raise ValueError("v3 arm sizes must increase strictly")
        if not isinstance(self.value_chips, float) or not isfinite(self.value_chips):
            raise ValueError("v3 arm value must be a finite chip float")
        if not isinstance(self.dimensions, ReducedSizingLpDimensions):
            raise TypeError("v3 arm dimensions must be semantic")
        if (
            isinstance(self.simplex_pivots, bool)
            or not isinstance(self.simplex_pivots, int)
            or self.simplex_pivots < 0
            or self.simplex_pivots > ADR0302_SIMPLEX_PIVOT_CAP
        ):
            raise ValueError("v3 arm pivots exceed ADR-0300")
        for label, value, allowance in (
            (
                "probability residual",
                self.probability_residual,
                ADR0302_PROBABILITY_ALLOWANCE.value,
            ),
            (
                "chip objective error",
                self.chip_objective_error,
                ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips,
            ),
            (
                "LP duality gap",
                self.lp_duality_gap_chips,
                ADR0302_LP_DUALITY_ALLOWANCE.chips,
            ),
            (
                "envelope violation",
                self.envelope_violation_chips,
                ADR0302_ENVELOPE_ALLOWANCE.chips,
            ),
        ):
            if not isinstance(value, float) or not isfinite(value) or value < 0.0:
                raise ValueError(f"v3 arm {label} must be finite and nonnegative")
            if value > allowance:
                raise ValueError(f"v3 arm {label} exceeds ADR-0300")

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "bet_sizes": self.bet_sizes,
            "chip_objective_error": self.chip_objective_error.hex(),
            "dimensions": (
                self.dimensions.variable_count,
                self.dimensions.inequality_count,
            ),
            "envelope_violation_chips": self.envelope_violation_chips.hex(),
            "kind": self.kind.value,
            "lp_duality_gap_chips": self.lp_duality_gap_chips.hex(),
            "probability_residual": self.probability_residual.hex(),
            "simplex_pivots": self.simplex_pivots,
            "value_chips": self.value_chips.hex(),
        }


@dataclass(frozen=True, slots=True)
class V3EvaluationObservation:
    panel_kind: V3PanelKind
    panel_position: int
    pool_context_index: int
    structural_context_digest: str
    oracle_context_digest: str
    binding_digest: str
    abstraction_source_digest: str
    abstraction_digest: str
    payoff_span: int
    exact_legal_action_count: int
    v3_action_count: int
    v3_raise_count: int
    arms: tuple[V3ArmEvidence, ...]
    normalized_full_loss: float

    def __post_init__(self) -> None:
        if not isinstance(self.panel_kind, V3PanelKind):
            raise TypeError("v3 observation panel kind must be semantic")
        for label, value in (
            ("panel position", self.panel_position),
            ("pool context index", self.pool_context_index),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"v3 observation {label} must be nonnegative")
        for label, digest in (
            ("structural context", self.structural_context_digest),
            ("oracle context", self.oracle_context_digest),
            ("binding", self.binding_digest),
            ("abstraction source", self.abstraction_source_digest),
            ("abstraction", self.abstraction_digest),
        ):
            if not _valid_digest(digest):
                raise ValueError(f"v3 observation {label} digest is invalid")
        if self.abstraction_source_digest != ADR0300_COLLISION_REPAIR_SOURCE_SHA256:
            raise ValueError("v3 observation uses the wrong candidate source")
        if (
            isinstance(self.payoff_span, bool)
            or not isinstance(self.payoff_span, int)
            or self.payoff_span <= 0
        ):
            raise ValueError("v3 observation payoff span must be positive")
        for label, value, maximum in (
            ("exact legal action count", self.exact_legal_action_count, None),
            ("v3 action count", self.v3_action_count, ADR0300_MAXIMUM_V3_ACTIONS),
            ("v3 raise count", self.v3_raise_count, ADR0300_MAXIMUM_V3_RAISES),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"v3 observation {label} must be positive")
            if maximum is not None and value > maximum:
                raise ValueError(f"v3 observation {label} exceeds ADR-0300")
        if not isinstance(self.arms, tuple) or any(
            not isinstance(arm, V3ArmEvidence) for arm in self.arms
        ):
            raise TypeError("v3 observation contains a nonsemantic arm")
        if tuple(arm.kind for arm in self.arms) != tuple(V3ArmKind):
            raise ValueError("v3 observation arms must follow the frozen order")
        full, candidate, narrow = self.arms
        if full.value_chips + ADR0300_ORDERING_ALLOWANCE.chips < candidate.value_chips:
            raise ValueError("v3 observation reverses full and candidate values")
        if candidate.value_chips + ADR0300_ORDERING_ALLOWANCE.chips < narrow.value_chips:
            raise ValueError("v3 observation reverses candidate and narrow values")
        if (
            not isinstance(self.normalized_full_loss, float)
            or not isfinite(self.normalized_full_loss)
            or self.normalized_full_loss < 0.0
        ):
            raise ValueError("v3 observation normalized loss must be nonnegative")
        expected_loss = max(0.0, full.value_chips - candidate.value_chips) / self.payoff_span
        if self.normalized_full_loss != expected_loss:
            raise ValueError("v3 observation normalized loss is inconsistent")
        if self.v3_raise_count != len(candidate.bet_sizes):
            raise ValueError("v3 observation raise count differs from candidate arm")
        if self.v3_action_count != self.v3_raise_count + 1:
            raise ValueError("v3 observation action count omits the exact check action")
        if self.exact_legal_action_count != len(full.bet_sizes) + 1:
            raise ValueError("v3 observation exact action count differs from full arm")
        if self.v3_action_count >= self.exact_legal_action_count:
            raise ValueError("v3 observation is not a strict full-arm width reduction")

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "abstraction_digest": self.abstraction_digest,
            "abstraction_source_digest": self.abstraction_source_digest,
            "arms": tuple(arm.canonical_payload for arm in self.arms),
            "binding_digest": self.binding_digest,
            "exact_legal_action_count": self.exact_legal_action_count,
            "normalized_full_loss": self.normalized_full_loss.hex(),
            "oracle_context_digest": self.oracle_context_digest,
            "panel_kind": self.panel_kind.value,
            "panel_position": self.panel_position,
            "payoff_span": self.payoff_span,
            "pool_context_index": self.pool_context_index,
            "structural_context_digest": self.structural_context_digest,
            "v3_action_count": self.v3_action_count,
            "v3_raise_count": self.v3_raise_count,
        }


def _arm(
    *,
    kind: V3ArmKind,
    context: ReducedRiverSizingContext,
    bet_sizes: tuple[int, ...],
) -> V3ArmEvidence:
    solution = solve_reduced_river_sizing(
        context,
        bet_sizes,
        probability_allowance=ADR0302_PROBABILITY_ALLOWANCE,
        chip_allowance=ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
        solver_tolerance=ADR0302_SOLVER_TOLERANCE,
        max_pivots=ADR0302_SIMPLEX_PIVOT_CAP,
    )
    return V3ArmEvidence(
        kind=kind,
        bet_sizes=bet_sizes,
        value_chips=solution.value_chips,
        dimensions=width_four_lp_dimensions(context, bet_sizes),
        simplex_pivots=solution.simplex_pivots,
        probability_residual=solution.max_probability_simplex_residual,
        chip_objective_error=solution.chip_objective_reconstruction_error,
        lp_duality_gap_chips=abs(solution.linear_program_duality_gap),
        envelope_violation_chips=(
            solution.max_envelope_constraint_violation_chips
        ),
    )


def _teacher(
    *,
    context_index: int,
    binding: FreshOracleContextBinding,
) -> FreshTeacherObservation:
    bounded = binding.oracle_context.bounded_two_by_two()
    bet_sizes = (bounded.minimum_bet, bounded.stack)
    compact = solve_reduced_river_sizing(
        bounded,
        bet_sizes,
        probability_allowance=ADR0302_PROBABILITY_ALLOWANCE,
        chip_allowance=ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
        solver_tolerance=ADR0302_SOLVER_TOLERANCE,
        max_pivots=ADR0302_SIMPLEX_PIVOT_CAP,
    )
    teacher = solve_bounded_normal_form_sizing_teacher(
        bounded,
        bet_sizes,
        solver_tolerance=ADR0302_SOLVER_TOLERANCE,
    )
    return FreshTeacherObservation(
        context_index=context_index,
        binding_digest=binding.digest,
        bounded_context_digest=bounded.digest,
        bet_sizes=bet_sizes,
        compact_value_chips=compact.value_chips,
        teacher_value_chips=teacher.value_chips,
        value_difference_chips=abs(compact.value_chips - teacher.value_chips),
        teacher_duality_gap_chips=abs(teacher.duality_gap),
        compact_probability_residual=compact.max_probability_simplex_residual,
        compact_chip_objective_error=compact.chip_objective_reconstruction_error,
        compact_lp_duality_gap_chips=abs(compact.linear_program_duality_gap),
        compact_envelope_violation_chips=(
            compact.max_envelope_constraint_violation_chips
        ),
        compact_simplex_pivots=compact.simplex_pivots,
        teacher_opener_pure_plan_count=teacher.opener_pure_plan_count,
        teacher_responder_pure_plan_count=teacher.responder_pure_plan_count,
    )


@dataclass(frozen=True, slots=True)
class V3FamilyResult:
    panel_kind: V3PanelKind
    panel_digest: str
    observations: tuple[V3EvaluationObservation, ...]
    teacher_observations: tuple[FreshTeacherObservation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.panel_kind, V3PanelKind):
            raise TypeError("v3 family panel kind must be semantic")
        expected_digest = (
            ADR0301_REPRESENTATIVE_SHA256
            if self.panel_kind is V3PanelKind.REPRESENTATIVE
            else ADR0302_QUALIFIED_PANEL_SHA256
        )
        expected_count = (
            ADR0301_REPRESENTATIVE_CONTEXT_COUNT
            if self.panel_kind is V3PanelKind.REPRESENTATIVE
            else len(ADR0302_QUALIFIED_INDICES)
        )
        if self.panel_digest != expected_digest:
            raise ValueError("v3 family panel digest is not sealed")
        if not isinstance(self.observations, tuple) or len(
            self.observations
        ) != expected_count:
            raise TypeError("v3 family has the wrong immutable observation count")
        if any(
            not isinstance(observation, V3EvaluationObservation)
            for observation in self.observations
        ):
            raise TypeError("v3 family contains a nonsemantic observation")
        if tuple(
            observation.panel_position for observation in self.observations
        ) != tuple(range(expected_count)):
            raise ValueError("v3 family positions must be contiguous")
        if any(
            observation.panel_kind is not self.panel_kind
            for observation in self.observations
        ):
            raise ValueError("v3 family observation names the wrong panel")
        pool_indices = tuple(
            observation.pool_context_index for observation in self.observations
        )
        expected_indices = (
            tuple(range(ADR0301_REPRESENTATIVE_CONTEXT_COUNT))
            if self.panel_kind is V3PanelKind.REPRESENTATIVE
            else ADR0302_QUALIFIED_INDICES
        )
        if pool_indices != expected_indices:
            raise ValueError("v3 family pool indices differ from its sealed panel")
        if not isinstance(self.teacher_observations, tuple) or len(
            self.teacher_observations
        ) != expected_count:
            raise TypeError("v3 family has the wrong teacher count")
        if any(
            not isinstance(observation, FreshTeacherObservation)
            for observation in self.teacher_observations
        ):
            raise TypeError("v3 family contains a nonsemantic teacher")
        if tuple(
            observation.context_index for observation in self.teacher_observations
        ) != pool_indices:
            raise ValueError("v3 family teacher indices differ from its panel")
        if tuple(
            observation.binding_digest for observation in self.teacher_observations
        ) != tuple(observation.binding_digest for observation in self.observations):
            raise ValueError("v3 family teacher bindings differ from its panel")
        if self.panel_kind is V3PanelKind.QUALIFIED and self.recovery_denominator_chips <= 0.0:
            raise ValueError("qualified v3 family has no positive recovery denominator")

    @property
    def maximum_normalized_loss(self) -> float:
        return max(observation.normalized_full_loss for observation in self.observations)

    @property
    def mean_normalized_loss(self) -> float:
        return sum(
            observation.normalized_full_loss for observation in self.observations
        ) / len(self.observations)

    @property
    def recovery_numerator_chips(self) -> float:
        return sum(
            observation.arms[1].value_chips - observation.arms[2].value_chips
            for observation in self.observations
        )

    @property
    def recovery_denominator_chips(self) -> float:
        return sum(
            observation.arms[0].value_chips - observation.arms[2].value_chips
            for observation in self.observations
        )

    @property
    def aggregate_recovery(self) -> float | None:
        if self.panel_kind is V3PanelKind.REPRESENTATIVE:
            return None
        return self.recovery_numerator_chips / self.recovery_denominator_chips

    @property
    def passed(self) -> bool:
        loss_pass = (
            self.maximum_normalized_loss
            <= ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT.value
            and self.mean_normalized_loss
            <= ADR0300_MEAN_NORMALIZED_LOSS_LIMIT.value
        )
        if self.panel_kind is V3PanelKind.REPRESENTATIVE:
            return loss_pass
        recovery = self.aggregate_recovery
        assert recovery is not None
        return loss_pass and recovery >= ADR0300_AGGREGATE_RECOVERY_FLOOR.value

    @property
    def digest(self) -> str:
        recovery = self.aggregate_recovery
        payload = {
            "aggregate_recovery": None if recovery is None else recovery.hex(),
            "aggregate_recovery_floor": ADR0300_AGGREGATE_RECOVERY_FLOOR.value.hex(),
            "maximum_normalized_loss": self.maximum_normalized_loss.hex(),
            "maximum_normalized_loss_limit": (
                ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT.value.hex()
            ),
            "mean_normalized_loss": self.mean_normalized_loss.hex(),
            "mean_normalized_loss_limit": (
                ADR0300_MEAN_NORMALIZED_LOSS_LIMIT.value.hex()
            ),
            "observations": tuple(
                observation.canonical_payload for observation in self.observations
            ),
            "ordering_allowance_chips": ADR0300_ORDERING_ALLOWANCE.chips.hex(),
            "panel_digest": self.panel_digest,
            "panel_kind": self.panel_kind.value,
            "recovery_denominator_chips": self.recovery_denominator_chips.hex(),
            "recovery_numerator_chips": self.recovery_numerator_chips.hex(),
            "source_id": ADR0300_COLLISION_REPAIR_SOURCE_ID,
            "source_sha256": ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
            "teacher_observations": tuple(
                observation.canonical_payload
                for observation in self.teacher_observations
            ),
            "version": "collision-repair-v3-family-result-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def verify_against_structure(
        self,
        *,
        structure: FreshWidthFourStructure,
        pool_indices: tuple[int, ...],
    ) -> None:
        expected_structure_kind = (
            FreshStructureKind.REPRESENTATIVE
            if self.panel_kind is V3PanelKind.REPRESENTATIVE
            else FreshStructureKind.QUALIFIED_POOL
        )
        expected_structure_digest = (
            ADR0301_REPRESENTATIVE_SHA256
            if self.panel_kind is V3PanelKind.REPRESENTATIVE
            else ADR0301_QUALIFIED_POOL_SHA256
        )
        if (
            not isinstance(structure, FreshWidthFourStructure)
            or structure.kind is not expected_structure_kind
            or structure.digest != expected_structure_digest
        ):
            raise ValueError("v3 family verification structure is wrong")
        if tuple(
            observation.pool_context_index for observation in self.observations
        ) != pool_indices:
            raise ValueError("v3 family pool indices differ from its panel")
        source = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        )
        for observation, teacher, context_index in zip(
            self.observations,
            self.teacher_observations,
            pool_indices,
            strict=True,
        ):
            structural = structure.contexts[context_index]
            binding = bind_fresh_context_to_oracle(structural)
            context = binding.oracle_context
            if observation.structural_context_digest != structural.digest:
                raise ValueError("v3 family structural context differs")
            if observation.oracle_context_digest != context.digest:
                raise ValueError("v3 family oracle context differs")
            if observation.binding_digest != binding.digest:
                raise ValueError("v3 family conversion binding differs")
            if observation.payoff_span != context.payoff_span:
                raise ValueError("v3 family payoff span differs from its exact game")
            state = two_live_seat_river_opening_state(
                pot=context.pot,
                stack=context.stack,
            )
            abstraction = source.build(
                betting=state,
                decision=state.legal_decision(),
            )
            nonraises = tuple(
                action
                for action in abstraction.actions
                if action.kind is not BettingActionKind.RAISE
            )
            if len(nonraises) != 1 or nonraises[0].kind is not BettingActionKind.CHECK:
                raise ValueError("v3 reduced decision does not retain exactly check")
            v3_sizes = tuple(
                int(action.raise_to)
                for action in abstraction.actions
                if action.kind is BettingActionKind.RAISE
            )
            full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
            narrow_sizes = (context.minimum_bet, context.stack)
            if observation.abstraction_digest != abstraction.digest:
                raise ValueError("v3 family abstraction digest differs")
            if observation.exact_legal_action_count != abstraction.exact_action_count:
                raise ValueError("v3 family exact legal width differs")
            if observation.v3_action_count != len(abstraction.actions):
                raise ValueError("v3 family abstract action width differs")
            if observation.v3_raise_count != len(abstraction.raise_sizes):
                raise ValueError("v3 family abstract raise width differs")
            expected_sizes = (full_sizes, v3_sizes, narrow_sizes)
            if tuple(arm.bet_sizes for arm in observation.arms) != expected_sizes:
                raise ValueError("v3 family arm sizes differ from exact sources")
            if tuple(
                arm.dimensions for arm in observation.arms
            ) != tuple(
                width_four_lp_dimensions(context, sizes) for sizes in expected_sizes
            ):
                raise ValueError("v3 family arm dimensions differ")
            bounded = context.bounded_two_by_two()
            if teacher.binding_digest != binding.digest:
                raise ValueError("v3 family teacher binding differs")
            if teacher.bounded_context_digest != bounded.digest:
                raise ValueError("v3 family teacher bounded context differs")
            if teacher.bet_sizes != (bounded.minimum_bet, bounded.stack):
                raise ValueError("v3 family teacher arm differs")


def _evaluate_family(
    *,
    panel_kind: V3PanelKind,
    structure: FreshWidthFourStructure,
    pool_indices: tuple[int, ...],
    panel_digest: str,
) -> V3FamilyResult:
    source = CollisionRepairActionAbstractionSource(
        source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
    )
    observations: list[V3EvaluationObservation] = []
    teachers: list[FreshTeacherObservation] = []
    for panel_position, context_index in enumerate(pool_indices):
        structural = structure.contexts[context_index]
        binding = bind_fresh_context_to_oracle(structural)
        context = binding.oracle_context
        state = two_live_seat_river_opening_state(
            pot=context.pot,
            stack=context.stack,
        )
        abstraction = source.build(
            betting=state,
            decision=state.legal_decision(),
        )
        nonraises = tuple(
            action
            for action in abstraction.actions
            if action.kind is not BettingActionKind.RAISE
        )
        if len(nonraises) != 1 or nonraises[0].kind is not BettingActionKind.CHECK:
            raise AssertionError("ADR-0300 reduced decision must retain exactly check")
        v3_sizes = tuple(
            int(action.raise_to)
            for action in abstraction.actions
            if action.kind is BettingActionKind.RAISE
        )
        full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
        narrow_sizes = (context.minimum_bet, context.stack)
        arms = (
            _arm(
                kind=V3ArmKind.FULL_INTEGER,
                context=context,
                bet_sizes=full_sizes,
            ),
            _arm(
                kind=V3ArmKind.COLLISION_REPAIR_V3,
                context=context,
                bet_sizes=v3_sizes,
            ),
            _arm(
                kind=V3ArmKind.MINIMUM_ALL_IN,
                context=context,
                bet_sizes=narrow_sizes,
            ),
        )
        observations.append(
            V3EvaluationObservation(
                panel_kind=panel_kind,
                panel_position=panel_position,
                pool_context_index=context_index,
                structural_context_digest=structural.digest,
                oracle_context_digest=context.digest,
                binding_digest=binding.digest,
                abstraction_source_digest=abstraction.source_digest,
                abstraction_digest=abstraction.digest,
                payoff_span=context.payoff_span,
                exact_legal_action_count=abstraction.exact_action_count,
                v3_action_count=len(abstraction.actions),
                v3_raise_count=len(abstraction.raise_sizes),
                arms=arms,
                normalized_full_loss=(
                    max(0.0, arms[0].value_chips - arms[1].value_chips)
                    / context.payoff_span
                ),
            )
        )
        teachers.append(_teacher(context_index=context_index, binding=binding))
    result = V3FamilyResult(
        panel_kind=panel_kind,
        panel_digest=panel_digest,
        observations=tuple(observations),
        teacher_observations=tuple(teachers),
    )
    result.verify_against_structure(
        structure=structure,
        pool_indices=pool_indices,
    )
    return result


@dataclass(frozen=True, slots=True)
class V3EvaluationCampaignResult:
    stop_reason: V3CampaignStopReason
    representative: V3FamilyResult
    qualified: V3FamilyResult | None
    elapsed_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.stop_reason, V3CampaignStopReason):
            raise TypeError("v3 campaign stop reason must be semantic")
        if (
            not isinstance(self.representative, V3FamilyResult)
            or self.representative.panel_kind is not V3PanelKind.REPRESENTATIVE
        ):
            raise TypeError("v3 campaign requires its representative result first")
        if self.stop_reason is V3CampaignStopReason.REPRESENTATIVE_REJECTED:
            if self.representative.passed or self.qualified is not None:
                raise ValueError("v3 campaign representative rejection is inconsistent")
        else:
            if not self.representative.passed:
                raise ValueError("v3 campaign continued after representative failure")
            if (
                not isinstance(self.qualified, V3FamilyResult)
                or self.qualified.panel_kind is not V3PanelKind.QUALIFIED
            ):
                raise TypeError("v3 campaign lacks its qualified result")
            if self.stop_reason is V3CampaignStopReason.PASSED:
                if not self.qualified.passed:
                    raise ValueError("passing v3 campaign has a failed qualified result")
            elif self.qualified.passed:
                raise ValueError("rejected v3 campaign has a passing qualified result")
        if (
            not isinstance(self.elapsed_seconds, float)
            or not isfinite(self.elapsed_seconds)
            or self.elapsed_seconds < 0.0
        ):
            raise ValueError("v3 campaign elapsed time must be nonnegative")

    @property
    def passed(self) -> bool:
        return self.stop_reason is V3CampaignStopReason.PASSED

    @property
    def digest(self) -> str:
        payload = {
            "qualified_digest": (
                None if self.qualified is None else self.qualified.digest
            ),
            "representative_digest": self.representative.digest,
            "stop_reason": self.stop_reason.value,
            "version": "collision-repair-v3-evaluation-campaign-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


def run_adr0300_collision_repair_v3_evaluation() -> V3EvaluationCampaignResult:
    """Execute representative first and never open qualified after a failure."""

    started = perf_counter()
    representative_structure = build_adr0301_fresh_structure(
        kind=FreshStructureKind.REPRESENTATIVE
    )
    representative_indices = tuple(
        range(ADR0301_REPRESENTATIVE_CONTEXT_COUNT)
    )
    representative = _evaluate_family(
        panel_kind=V3PanelKind.REPRESENTATIVE,
        structure=representative_structure,
        pool_indices=representative_indices,
        panel_digest=representative_structure.digest,
    )
    if not representative.passed:
        return V3EvaluationCampaignResult(
            stop_reason=V3CampaignStopReason.REPRESENTATIVE_REJECTED,
            representative=representative,
            qualified=None,
            elapsed_seconds=float(perf_counter() - started),
        )

    qualified_structure = build_adr0301_fresh_structure(
        kind=FreshStructureKind.QUALIFIED_POOL
    )
    qualified_panel = build_adr0302_qualified_panel()
    qualified = _evaluate_family(
        panel_kind=V3PanelKind.QUALIFIED,
        structure=qualified_structure,
        pool_indices=qualified_panel.pool_indices,
        panel_digest=qualified_panel.digest,
    )
    stop_reason = (
        V3CampaignStopReason.PASSED
        if qualified.passed
        else V3CampaignStopReason.QUALIFIED_REJECTED
    )
    return V3EvaluationCampaignResult(
        stop_reason=stop_reason,
        representative=representative,
        qualified=qualified,
        elapsed_seconds=float(perf_counter() - started),
    )


__all__ = [
    "ADR0300_AGGREGATE_RECOVERY_FLOOR",
    "ADR0300_EVALUATION_CAMPAIGN_SHA256",
    "ADR0300_MAXIMUM_NORMALIZED_LOSS_LIMIT",
    "ADR0300_MAXIMUM_V3_ACTIONS",
    "ADR0300_MAXIMUM_V3_RAISES",
    "ADR0300_MEAN_NORMALIZED_LOSS_LIMIT",
    "ADR0300_ORDERING_ALLOWANCE",
    "ADR0300_QUALIFIED_RESULT_SHA256",
    "ADR0300_REPRESENTATIVE_RESULT_SHA256",
    "V3AggregateRecoveryFloor",
    "V3ArmEvidence",
    "V3ArmKind",
    "V3CampaignStopReason",
    "V3EvaluationCampaignResult",
    "V3EvaluationObservation",
    "V3FamilyResult",
    "V3MaximumNormalizedLossLimit",
    "V3MeanNormalizedLossLimit",
    "V3OrderingAllowance",
    "V3PanelKind",
    "run_adr0300_collision_repair_v3_evaluation",
]
