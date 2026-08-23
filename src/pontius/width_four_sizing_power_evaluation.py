"""Owned ADR-0297 value boundary for the sealed width-four structural pools."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from time import perf_counter

from .reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ProbabilitySimplexAllowance,
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
    ADR0297_BATCH_COUNT,
    ADR0297_POOL_CONTEXT_COUNT,
    ADR0297_POOL_SHA256,
    ADR0297_QUALIFIED_CONTEXT_COUNT,
    ReducedSizingLpDimensions,
    WidthFourSizingPowerPool,
    build_adr0297_width_four_pool,
    width_four_lp_dimensions,
)

ADR0297_SOLVER_TOLERANCE = 1e-11
ADR0297_SIMPLEX_PIVOT_CAP = 4096
ADR0297_OPPORTUNITY_FLOOR = NormalizedSizingOpportunityFloor(1e-4)
ADR0297_CLASSIFICATION_GUARD = ChipClassificationGuard(1e-8)
ADR0297_PROBABILITY_ALLOWANCE = ProbabilitySimplexAllowance(1e-9)
ADR0297_CHIP_OBJECTIVE_ALLOWANCE = ChipObjectiveAllowance(1e-9)


@dataclass(frozen=True, slots=True)
class LinearProgramDualityGapAllowance:
    """Chip-valued LP primal-dual objective-gap allowance."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips):
            raise ValueError("LP duality-gap allowance must be a finite float")
        if self.chips <= 0.0:
            raise ValueError("LP duality-gap allowance must be positive")


@dataclass(frozen=True, slots=True)
class EnvelopeConstraintViolationAllowance:
    """Chip-valued lower-envelope inequality-feasibility allowance."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips):
            raise ValueError("envelope constraint allowance must be a finite float")
        if self.chips <= 0.0:
            raise ValueError("envelope constraint allowance must be positive")


@dataclass(frozen=True, slots=True)
class TeacherChipAgreementAllowance:
    """Chip-valued compact-versus-normal-form agreement allowance."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips):
            raise ValueError("teacher agreement allowance must be a finite float")
        if self.chips <= 0.0:
            raise ValueError("teacher agreement allowance must be positive")


@dataclass(frozen=True, slots=True)
class TeacherDualityGapAllowance:
    """Chip-valued normal-form teacher primal-dual gap allowance."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips):
            raise ValueError("teacher duality allowance must be a finite float")
        if self.chips <= 0.0:
            raise ValueError("teacher duality allowance must be positive")


ADR0297_LP_DUALITY_ALLOWANCE = LinearProgramDualityGapAllowance(1e-9)
ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE = EnvelopeConstraintViolationAllowance(1e-9)
ADR0297_TEACHER_AGREEMENT_ALLOWANCE = TeacherChipAgreementAllowance(1e-9)
ADR0297_TEACHER_DUALITY_ALLOWANCE = TeacherDualityGapAllowance(1e-9)


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True, slots=True)
class WidthFourQualifiedPanel:
    batch_index: int
    pool_digest: str
    pool_indices: tuple[int, ...]
    context_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.batch_index, bool)
            or not isinstance(self.batch_index, int)
            or self.batch_index not in range(ADR0297_BATCH_COUNT)
        ):
            raise ValueError("width-four panel batch is invalid")
        if not _valid_digest(self.pool_digest):
            raise ValueError("width-four panel pool digest is invalid")
        if self.pool_digest != ADR0297_POOL_SHA256[self.batch_index]:
            raise ValueError("width-four panel pool digest is not sealed")
        if not isinstance(self.pool_indices, tuple) or len(
            self.pool_indices
        ) != ADR0297_QUALIFIED_CONTEXT_COUNT:
            raise TypeError("width-four panel requires 12 immutable indices")
        if any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index not in range(ADR0297_POOL_CONTEXT_COUNT)
            for index in self.pool_indices
        ):
            raise ValueError("width-four panel index lies outside its pool")
        if tuple(sorted(self.pool_indices)) != self.pool_indices or len(
            set(self.pool_indices)
        ) != len(self.pool_indices):
            raise ValueError("width-four panel indices must increase strictly")
        if not isinstance(self.context_digests, tuple) or len(
            self.context_digests
        ) != len(self.pool_indices):
            raise TypeError("width-four panel context digests must align with indices")
        if any(not _valid_digest(digest) for digest in self.context_digests):
            raise ValueError("width-four panel context digest is invalid")

    @property
    def digest(self) -> str:
        payload = {
            "batch_index": self.batch_index,
            "context_digests": self.context_digests,
            "pool_digest": self.pool_digest,
            "pool_indices": self.pool_indices,
            "version": "candidate-blind-width4-qualified-panel-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class WidthFourSizingPowerObservation:
    context_index: int
    context_digest: str
    full_value_chips: float
    narrow_value_chips: float
    payoff_span: int
    classification: SizingPowerClassification
    full_dimensions: ReducedSizingLpDimensions
    narrow_dimensions: ReducedSizingLpDimensions
    full_simplex_pivots: int
    narrow_simplex_pivots: int
    max_probability_residual: float
    max_chip_objective_error: float
    max_lp_duality_gap: float
    max_envelope_constraint_violation_chips: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index not in range(ADR0297_POOL_CONTEXT_COUNT)
        ):
            raise ValueError("width-four observation index lies outside its pool")
        if not _valid_digest(self.context_digest):
            raise ValueError("width-four observation context digest is invalid")
        for label, value in (
            ("full value", self.full_value_chips),
            ("narrow value", self.narrow_value_chips),
            ("probability residual", self.max_probability_residual),
            ("chip objective error", self.max_chip_objective_error),
            ("LP duality gap", self.max_lp_duality_gap),
            (
                "envelope constraint violation",
                self.max_envelope_constraint_violation_chips,
            ),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"width-four observation {label} must be finite")
        if (
            isinstance(self.payoff_span, bool)
            or not isinstance(self.payoff_span, int)
            or self.payoff_span <= 0
        ):
            raise ValueError("width-four observation payoff span must be positive")
        if not isinstance(self.classification, SizingPowerClassification):
            raise TypeError("width-four observation classification must be semantic")
        if not isinstance(self.full_dimensions, ReducedSizingLpDimensions) or not isinstance(
            self.narrow_dimensions,
            ReducedSizingLpDimensions,
        ):
            raise TypeError("width-four observation LP dimensions must be semantic")
        for label, pivots in (
            ("full", self.full_simplex_pivots),
            ("narrow", self.narrow_simplex_pivots),
        ):
            if isinstance(pivots, bool) or not isinstance(pivots, int) or pivots < 0:
                raise ValueError(f"width-four {label} pivot count must be nonnegative")
            if pivots > ADR0297_SIMPLEX_PIVOT_CAP:
                raise ValueError(f"width-four {label} pivot count exceeds ADR-0297")
        if not 0.0 <= self.max_probability_residual <= ADR0297_PROBABILITY_ALLOWANCE.value:
            raise ValueError("width-four probability residual exceeds ADR-0297")
        if not 0.0 <= self.max_chip_objective_error <= ADR0297_CHIP_OBJECTIVE_ALLOWANCE.chips:
            raise ValueError("width-four chip objective error exceeds ADR-0297")
        if not 0.0 <= self.max_lp_duality_gap <= ADR0297_LP_DUALITY_ALLOWANCE.chips:
            raise ValueError("width-four LP duality gap exceeds ADR-0297")
        if not (
            0.0
            <= self.max_envelope_constraint_violation_chips
            <= ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE.chips
        ):
            raise ValueError("width-four envelope constraint violation exceeds ADR-0297")


@dataclass(frozen=True, slots=True)
class WidthFourSizingPowerBatchResult:
    batch_index: int
    pool_digest: str
    stop_reason: QualificationStopReason
    observations: tuple[WidthFourSizingPowerObservation, ...]
    qualified_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.batch_index, bool)
            or not isinstance(self.batch_index, int)
            or self.batch_index not in range(ADR0297_BATCH_COUNT)
        ):
            raise ValueError("width-four result batch is invalid")
        if self.pool_digest != ADR0297_POOL_SHA256[self.batch_index]:
            raise ValueError("width-four result pool digest is not sealed")
        if not isinstance(self.stop_reason, QualificationStopReason):
            raise TypeError("width-four stop reason must be semantic")
        if not isinstance(self.observations, tuple) or not self.observations:
            raise TypeError("width-four result requires immutable observations")
        if any(
            not isinstance(observation, WidthFourSizingPowerObservation)
            for observation in self.observations
        ):
            raise TypeError("width-four result contains a nonsemantic observation")
        if tuple(observation.context_index for observation in self.observations) != tuple(
            range(len(self.observations))
        ):
            raise ValueError("width-four observations must be a contiguous prefix")
        expected_qualified = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.QUALIFYING
        )
        if self.qualified_indices != expected_qualified:
            raise ValueError("width-four qualified indices disagree with observations")
        ambiguous_indices = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.AMBIGUOUS
        )
        if self.stop_reason is QualificationStopReason.AMBIGUOUS:
            if ambiguous_indices != (len(self.observations) - 1,):
                raise ValueError("width-four result must stop at its first ambiguity")
            if len(self.qualified_indices) >= ADR0297_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("ambiguous width-four result already reached its target")
        elif ambiguous_indices:
            raise ValueError("non-ambiguous width-four result contains an ambiguity")
        if self.stop_reason is QualificationStopReason.TARGET_REACHED:
            if len(self.qualified_indices) != ADR0297_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("target-reached width-four result lacks 12 qualifiers")
            if self.qualified_indices[-1] != len(self.observations) - 1:
                raise ValueError("target-reached width-four result opened a later value")
        elif self.stop_reason is QualificationStopReason.POOL_EXHAUSTED:
            if len(self.observations) != ADR0297_POOL_CONTEXT_COUNT:
                raise ValueError("exhausted width-four result did not open its full pool")
            if len(self.qualified_indices) >= ADR0297_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("exhausted width-four result already reached its target")

    @property
    def opened_context_count(self) -> int:
        return len(self.observations)

    @property
    def digest(self) -> str:
        payload = {
            "batch_index": self.batch_index,
            "classification_guard_chips": ADR0297_CLASSIFICATION_GUARD.chips.hex(),
            "chip_objective_allowance": ADR0297_CHIP_OBJECTIVE_ALLOWANCE.chips.hex(),
            "envelope_constraint_allowance_chips": (
                ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE.chips.hex()
            ),
            "lp_duality_allowance_chips": ADR0297_LP_DUALITY_ALLOWANCE.chips.hex(),
            "observations": tuple(
                {
                    "classification": observation.classification.value,
                    "context_digest": observation.context_digest,
                    "context_index": observation.context_index,
                    "full_dimensions": (
                        observation.full_dimensions.variable_count,
                        observation.full_dimensions.inequality_count,
                    ),
                    "full_simplex_pivots": observation.full_simplex_pivots,
                    "full_value_chips": observation.full_value_chips.hex(),
                    "max_chip_objective_error": observation.max_chip_objective_error.hex(),
                    "max_envelope_constraint_violation_chips": (
                        observation.max_envelope_constraint_violation_chips.hex()
                    ),
                    "max_lp_duality_gap": observation.max_lp_duality_gap.hex(),
                    "max_probability_residual": observation.max_probability_residual.hex(),
                    "narrow_dimensions": (
                        observation.narrow_dimensions.variable_count,
                        observation.narrow_dimensions.inequality_count,
                    ),
                    "narrow_simplex_pivots": observation.narrow_simplex_pivots,
                    "narrow_value_chips": observation.narrow_value_chips.hex(),
                    "payoff_span": observation.payoff_span,
                }
                for observation in self.observations
            ),
            "opportunity_floor": ADR0297_OPPORTUNITY_FLOOR.value.hex(),
            "pool_digest": self.pool_digest,
            "probability_allowance": ADR0297_PROBABILITY_ALLOWANCE.value.hex(),
            "qualified_indices": self.qualified_indices,
            "simplex_pivot_cap": ADR0297_SIMPLEX_PIVOT_CAP,
            "solver_tolerance": ADR0297_SOLVER_TOLERANCE.hex(),
            "stop_reason": self.stop_reason.value,
            "version": "candidate-blind-width4-sizing-power-result-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def qualified_panel(
        self,
        *,
        pool: WidthFourSizingPowerPool,
    ) -> WidthFourQualifiedPanel:
        if self.stop_reason is not QualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached width-four result has a panel")
        if (
            not isinstance(pool, WidthFourSizingPowerPool)
            or pool.batch_index != self.batch_index
            or pool.digest != self.pool_digest
        ):
            raise ValueError("width-four panel pool differs from its result")
        self.verify_against_pool(pool=pool)
        return WidthFourQualifiedPanel(
            batch_index=self.batch_index,
            pool_digest=self.pool_digest,
            pool_indices=self.qualified_indices,
            context_digests=tuple(
                pool.contexts[index].digest for index in self.qualified_indices
            ),
        )

    def verify_against_pool(self, *, pool: WidthFourSizingPowerPool) -> None:
        if (
            not isinstance(pool, WidthFourSizingPowerPool)
            or pool.batch_index != self.batch_index
            or pool.digest != self.pool_digest
        ):
            raise ValueError("width-four verification pool differs from its result")
        for observation, context in zip(
            self.observations,
            pool.contexts[: len(self.observations)],
            strict=True,
        ):
            if observation.context_digest != context.digest:
                raise ValueError(
                    "width-four result observations differ from their pool prefix"
                )
            if observation.payoff_span != context.payoff_span:
                raise ValueError("width-four result payoff span differs from its game")
            full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
            narrow_sizes = (context.minimum_bet, context.stack)
            if observation.full_dimensions != width_four_lp_dimensions(
                context,
                full_sizes,
            ):
                raise ValueError("width-four result full LP dimensions differ")
            if observation.narrow_dimensions != width_four_lp_dimensions(
                context,
                narrow_sizes,
            ):
                raise ValueError("width-four result narrow LP dimensions differ")
            expected_classification = classify_sizing_opportunity(
                full_value_chips=observation.full_value_chips,
                narrow_value_chips=observation.narrow_value_chips,
                payoff_span=context.payoff_span,
                opportunity_floor=ADR0297_OPPORTUNITY_FLOOR,
                classification_guard=ADR0297_CLASSIFICATION_GUARD,
            )
            if observation.classification is not expected_classification:
                raise ValueError("width-four result classification differs from values")
            if (
                observation.full_value_chips
                + ADR0297_CHIP_OBJECTIVE_ALLOWANCE.chips
                < observation.narrow_value_chips
            ):
                raise ValueError("width-four result reverses full and narrow values")


@dataclass(frozen=True, slots=True)
class WidthFourTeacherControl:
    batch_index: int
    panel_digest: str
    maximum_value_difference_chips: float
    maximum_teacher_duality_gap_chips: float
    maximum_compact_probability_residual: float
    maximum_compact_chip_objective_error: float
    maximum_compact_lp_duality_gap: float
    maximum_compact_envelope_constraint_violation_chips: float
    maximum_compact_simplex_pivots: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.batch_index, bool)
            or not isinstance(self.batch_index, int)
            or self.batch_index not in range(ADR0297_BATCH_COUNT)
        ):
            raise ValueError("width-four teacher batch is invalid")
        if not _valid_digest(self.panel_digest):
            raise ValueError("width-four teacher panel digest is invalid")
        for label, value, allowance in (
            (
                "value difference",
                self.maximum_value_difference_chips,
                ADR0297_TEACHER_AGREEMENT_ALLOWANCE.chips,
            ),
            (
                "teacher duality gap",
                self.maximum_teacher_duality_gap_chips,
                ADR0297_TEACHER_DUALITY_ALLOWANCE.chips,
            ),
            (
                "compact probability residual",
                self.maximum_compact_probability_residual,
                ADR0297_PROBABILITY_ALLOWANCE.value,
            ),
            (
                "compact chip objective error",
                self.maximum_compact_chip_objective_error,
                ADR0297_CHIP_OBJECTIVE_ALLOWANCE.chips,
            ),
            (
                "compact LP duality gap",
                self.maximum_compact_lp_duality_gap,
                ADR0297_LP_DUALITY_ALLOWANCE.chips,
            ),
            (
                "compact envelope constraint violation",
                self.maximum_compact_envelope_constraint_violation_chips,
                ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE.chips,
            ),
        ):
            if not isinstance(value, float) or not isfinite(value) or value < 0.0:
                raise ValueError(f"width-four teacher {label} must be nonnegative")
            if value > allowance:
                raise ValueError(f"width-four teacher {label} exceeds ADR-0297")
        if (
            isinstance(self.maximum_compact_simplex_pivots, bool)
            or not isinstance(self.maximum_compact_simplex_pivots, int)
            or self.maximum_compact_simplex_pivots < 0
            or self.maximum_compact_simplex_pivots > ADR0297_SIMPLEX_PIVOT_CAP
        ):
            raise ValueError("width-four teacher compact pivots exceed ADR-0297")

    @property
    def digest(self) -> str:
        payload = {
            "batch_index": self.batch_index,
            "maximum_compact_chip_objective_error": self.maximum_compact_chip_objective_error.hex(),
            "envelope_constraint_allowance_chips": (
                ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE.chips.hex()
            ),
            "lp_duality_allowance_chips": ADR0297_LP_DUALITY_ALLOWANCE.chips.hex(),
            "maximum_compact_envelope_constraint_violation_chips": (
                self.maximum_compact_envelope_constraint_violation_chips.hex()
            ),
            "maximum_compact_lp_duality_gap": self.maximum_compact_lp_duality_gap.hex(),
            "maximum_compact_probability_residual": self.maximum_compact_probability_residual.hex(),
            "maximum_compact_simplex_pivots": self.maximum_compact_simplex_pivots,
            "maximum_teacher_duality_gap_chips": self.maximum_teacher_duality_gap_chips.hex(),
            "maximum_value_difference_chips": self.maximum_value_difference_chips.hex(),
            "panel_digest": self.panel_digest,
            "simplex_pivot_cap": ADR0297_SIMPLEX_PIVOT_CAP,
            "solver_tolerance": ADR0297_SOLVER_TOLERANCE.hex(),
            "teacher_agreement_allowance_chips": (
                ADR0297_TEACHER_AGREEMENT_ALLOWANCE.chips.hex()
            ),
            "teacher_duality_allowance_chips": (
                ADR0297_TEACHER_DUALITY_ALLOWANCE.chips.hex()
            ),
            "version": "candidate-blind-width4-teacher-control-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


class WidthFourCampaignStopReason(StrEnum):
    PASSED_ALL_BATCHES = "passed_all_batches"
    BATCH_REJECTED = "batch_rejected"


@dataclass(frozen=True, slots=True)
class WidthFourSizingPowerCampaignResult:
    stop_reason: WidthFourCampaignStopReason
    batch_results: tuple[WidthFourSizingPowerBatchResult, ...]
    teacher_controls: tuple[WidthFourTeacherControl, ...]
    elapsed_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.stop_reason, WidthFourCampaignStopReason):
            raise TypeError("width-four campaign stop reason must be semantic")
        if not isinstance(self.batch_results, tuple) or not self.batch_results:
            raise TypeError("width-four campaign requires immutable batch results")
        if any(
            not isinstance(result, WidthFourSizingPowerBatchResult)
            for result in self.batch_results
        ):
            raise TypeError("width-four campaign contains a nonsemantic batch result")
        if not isinstance(self.teacher_controls, tuple) or any(
            not isinstance(control, WidthFourTeacherControl)
            for control in self.teacher_controls
        ):
            raise TypeError("width-four campaign teacher controls must be semantic")
        if tuple(result.batch_index for result in self.batch_results) != tuple(
            range(len(self.batch_results))
        ):
            raise ValueError("width-four campaign batches must be a contiguous prefix")
        target_batches = tuple(
            result.batch_index
            for result in self.batch_results
            if result.stop_reason is QualificationStopReason.TARGET_REACHED
        )
        if tuple(control.batch_index for control in self.teacher_controls) != target_batches:
            raise ValueError("width-four teacher controls disagree with target batches")
        if self.stop_reason is WidthFourCampaignStopReason.PASSED_ALL_BATCHES:
            if len(self.batch_results) != ADR0297_BATCH_COUNT or len(
                target_batches
            ) != ADR0297_BATCH_COUNT:
                raise ValueError("passing width-four campaign lacks three target batches")
        else:
            if self.batch_results[-1].stop_reason is QualificationStopReason.TARGET_REACHED:
                raise ValueError("rejected width-four campaign ends in a target batch")
            if any(
                result.stop_reason is not QualificationStopReason.TARGET_REACHED
                for result in self.batch_results[:-1]
            ):
                raise ValueError("width-four campaign continued after an earlier failure")
        if (
            not isinstance(self.elapsed_seconds, float)
            or not isfinite(self.elapsed_seconds)
            or self.elapsed_seconds < 0.0
        ):
            raise ValueError("width-four campaign elapsed time must be nonnegative")

    @property
    def passed(self) -> bool:
        return self.stop_reason is WidthFourCampaignStopReason.PASSED_ALL_BATCHES

    @property
    def digest(self) -> str:
        payload = {
            "batch_result_digests": tuple(result.digest for result in self.batch_results),
            "stop_reason": self.stop_reason.value,
            "teacher_control_digests": tuple(
                control.digest for control in self.teacher_controls
            ),
            "version": "candidate-blind-width4-sizing-power-campaign-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


def _run_width_four_batch(
    *,
    pool: WidthFourSizingPowerPool,
) -> WidthFourSizingPowerBatchResult:
    observations: list[WidthFourSizingPowerObservation] = []
    qualified_indices: list[int] = []
    for context_index, context in enumerate(pool.contexts):
        full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
        narrow_sizes = (context.minimum_bet, context.stack)
        full = solve_reduced_river_sizing(
            context,
            full_sizes,
            probability_allowance=ADR0297_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0297_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0297_SOLVER_TOLERANCE,
            max_pivots=ADR0297_SIMPLEX_PIVOT_CAP,
        )
        narrow = solve_reduced_river_sizing(
            context,
            narrow_sizes,
            probability_allowance=ADR0297_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0297_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0297_SOLVER_TOLERANCE,
            max_pivots=ADR0297_SIMPLEX_PIVOT_CAP,
        )
        if full.value_chips + ADR0297_CHIP_OBJECTIVE_ALLOWANCE.chips < narrow.value_chips:
            raise AssertionError(
                f"ADR-0297 batch {pool.batch_index} context {context_index}: "
                "full sizing value fell materially below narrow value"
            )
        classification = classify_sizing_opportunity(
            full_value_chips=full.value_chips,
            narrow_value_chips=narrow.value_chips,
            payoff_span=context.payoff_span,
            opportunity_floor=ADR0297_OPPORTUNITY_FLOOR,
            classification_guard=ADR0297_CLASSIFICATION_GUARD,
        )
        observations.append(
            WidthFourSizingPowerObservation(
                context_index=context_index,
                context_digest=context.digest,
                full_value_chips=full.value_chips,
                narrow_value_chips=narrow.value_chips,
                payoff_span=context.payoff_span,
                classification=classification,
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
                max_lp_duality_gap=max(
                    abs(full.linear_program_duality_gap),
                    abs(narrow.linear_program_duality_gap),
                ),
                max_envelope_constraint_violation_chips=max(
                    full.max_envelope_constraint_violation_chips,
                    narrow.max_envelope_constraint_violation_chips,
                ),
            )
        )
        if classification is SizingPowerClassification.AMBIGUOUS:
            return WidthFourSizingPowerBatchResult(
                batch_index=pool.batch_index,
                pool_digest=pool.digest,
                stop_reason=QualificationStopReason.AMBIGUOUS,
                observations=tuple(observations),
                qualified_indices=tuple(qualified_indices),
            )
        if classification is SizingPowerClassification.QUALIFYING:
            qualified_indices.append(context_index)
            if len(qualified_indices) == ADR0297_QUALIFIED_CONTEXT_COUNT:
                return WidthFourSizingPowerBatchResult(
                    batch_index=pool.batch_index,
                    pool_digest=pool.digest,
                    stop_reason=QualificationStopReason.TARGET_REACHED,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified_indices),
                )
    return WidthFourSizingPowerBatchResult(
        batch_index=pool.batch_index,
        pool_digest=pool.digest,
        stop_reason=QualificationStopReason.POOL_EXHAUSTED,
        observations=tuple(observations),
        qualified_indices=tuple(qualified_indices),
    )


def _run_teacher_control(
    *,
    pool: WidthFourSizingPowerPool,
    result: WidthFourSizingPowerBatchResult,
) -> WidthFourTeacherControl:
    panel = result.qualified_panel(pool=pool)
    value_differences: list[float] = []
    teacher_gaps: list[float] = []
    compact_probability_residuals: list[float] = []
    compact_chip_errors: list[float] = []
    compact_lp_gaps: list[float] = []
    compact_envelope_constraint_violations: list[float] = []
    compact_pivots: list[int] = []
    for context_index in result.qualified_indices:
        bounded = pool.contexts[context_index].bounded_two_by_two()
        sizes = (bounded.minimum_bet, bounded.stack)
        compact = solve_reduced_river_sizing(
            bounded,
            sizes,
            probability_allowance=ADR0297_PROBABILITY_ALLOWANCE,
            chip_allowance=ADR0297_CHIP_OBJECTIVE_ALLOWANCE,
            solver_tolerance=ADR0297_SOLVER_TOLERANCE,
            max_pivots=ADR0297_SIMPLEX_PIVOT_CAP,
        )
        teacher = solve_bounded_normal_form_sizing_teacher(
            bounded,
            sizes,
            solver_tolerance=ADR0297_SOLVER_TOLERANCE,
        )
        value_differences.append(abs(compact.value_chips - teacher.value_chips))
        teacher_gaps.append(abs(teacher.duality_gap))
        compact_probability_residuals.append(
            compact.max_probability_simplex_residual
        )
        compact_chip_errors.append(compact.chip_objective_reconstruction_error)
        compact_lp_gaps.append(abs(compact.linear_program_duality_gap))
        compact_envelope_constraint_violations.append(
            compact.max_envelope_constraint_violation_chips
        )
        compact_pivots.append(compact.simplex_pivots)
    return WidthFourTeacherControl(
        batch_index=pool.batch_index,
        panel_digest=panel.digest,
        maximum_value_difference_chips=max(value_differences),
        maximum_teacher_duality_gap_chips=max(teacher_gaps),
        maximum_compact_probability_residual=max(compact_probability_residuals),
        maximum_compact_chip_objective_error=max(compact_chip_errors),
        maximum_compact_lp_duality_gap=max(compact_lp_gaps),
        maximum_compact_envelope_constraint_violation_chips=max(
            compact_envelope_constraint_violations
        ),
        maximum_compact_simplex_pivots=max(compact_pivots),
    )


def _validate_panel_diversity(
    *,
    pool: WidthFourSizingPowerPool,
    result: WidthFourSizingPowerBatchResult,
) -> None:
    selected = tuple(pool.contexts[index] for index in result.qualified_indices)
    if len({context.pot for context in selected}) < 3:
        raise AssertionError(f"ADR-0297 batch {pool.batch_index}: panel lacks pot diversity")
    if len({context.stack for context in selected}) < 3:
        raise AssertionError(
            f"ADR-0297 batch {pool.batch_index}: panel lacks stack diversity"
        )
    if len({context.showdown_signs for context in selected}) < 8:
        raise AssertionError(
            f"ADR-0297 batch {pool.batch_index}: panel lacks sign-matrix diversity"
        )


def run_adr0297_width_four_campaign() -> WidthFourSizingPowerCampaignResult:
    """Own the complete frozen invocation and stop before every later failed batch."""

    started = perf_counter()
    pools = tuple(
        build_adr0297_width_four_pool(batch_index=batch_index)
        for batch_index in range(ADR0297_BATCH_COUNT)
    )
    if tuple(pool.digest for pool in pools) != ADR0297_POOL_SHA256:
        raise AssertionError("ADR-0297 campaign pool identity differs from ADR-0298")
    batch_results: list[WidthFourSizingPowerBatchResult] = []
    teacher_controls: list[WidthFourTeacherControl] = []
    panel_digests: set[str] = set()
    result_digests: set[str] = set()
    for pool in pools:
        result = _run_width_four_batch(pool=pool)
        result.verify_against_pool(pool=pool)
        batch_results.append(result)
        if result.stop_reason is not QualificationStopReason.TARGET_REACHED:
            return WidthFourSizingPowerCampaignResult(
                stop_reason=WidthFourCampaignStopReason.BATCH_REJECTED,
                batch_results=tuple(batch_results),
                teacher_controls=tuple(teacher_controls),
                elapsed_seconds=float(perf_counter() - started),
            )
        _validate_panel_diversity(pool=pool, result=result)
        control = _run_teacher_control(pool=pool, result=result)
        teacher_controls.append(control)
        if result.digest in result_digests:
            raise AssertionError("ADR-0297 campaign repeats a batch-result digest")
        if control.panel_digest in panel_digests:
            raise AssertionError("ADR-0297 campaign repeats a qualified-panel digest")
        result_digests.add(result.digest)
        panel_digests.add(control.panel_digest)
    return WidthFourSizingPowerCampaignResult(
        stop_reason=WidthFourCampaignStopReason.PASSED_ALL_BATCHES,
        batch_results=tuple(batch_results),
        teacher_controls=tuple(teacher_controls),
        elapsed_seconds=float(perf_counter() - started),
    )


__all__ = [
    "ADR0297_CHIP_OBJECTIVE_ALLOWANCE",
    "ADR0297_CLASSIFICATION_GUARD",
    "ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE",
    "ADR0297_LP_DUALITY_ALLOWANCE",
    "ADR0297_OPPORTUNITY_FLOOR",
    "ADR0297_PROBABILITY_ALLOWANCE",
    "ADR0297_SIMPLEX_PIVOT_CAP",
    "ADR0297_SOLVER_TOLERANCE",
    "ADR0297_TEACHER_AGREEMENT_ALLOWANCE",
    "ADR0297_TEACHER_DUALITY_ALLOWANCE",
    "EnvelopeConstraintViolationAllowance",
    "LinearProgramDualityGapAllowance",
    "TeacherChipAgreementAllowance",
    "TeacherDualityGapAllowance",
    "WidthFourCampaignStopReason",
    "WidthFourQualifiedPanel",
    "WidthFourSizingPowerBatchResult",
    "WidthFourSizingPowerCampaignResult",
    "WidthFourSizingPowerObservation",
    "WidthFourTeacherControl",
    "run_adr0297_width_four_campaign",
]
