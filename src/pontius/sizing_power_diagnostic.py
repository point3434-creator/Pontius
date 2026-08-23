"""Candidate-blind reduced sizing-power pools frozen by ADR-0295."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite

from .action_abstraction_confirmation import (
    ADR0293_GENERATOR_VERSION,
    ADR0293_POTS,
    ADR0293_STACKS,
    _DigestStream,
    _private_pairs,
    _showdown_signs,
    _shuffled_deck,
    _structurally_admissible,
)
from .reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ExactDealProbability,
    ProbabilitySimplexAllowance,
    ReducedRiverSizingContext,
    solve_reduced_river_sizing,
)

ADR0295_GENERATOR_VERSION = "candidate-blind-sizing-power-pools-v1"
ADR0295_BASELINE_COMMIT = "2a7e5f470ca509e3c6dda1f300251fb8c3e9e4a3"
ADR0295_BATCH_COUNT = 3
ADR0295_POOL_CONTEXT_COUNT = 96
ADR0295_QUALIFIED_CONTEXT_COUNT = 12
ADR0295_POOL_SHA256 = (
    "37d6e5ee5ce23b5473b1a3cf7cf521a9e40673a0b514ff2368dc02c5e325eda2",
    "7590e8490266315bc3bfcf5757fb6e1cdea232151cb0dd0000b90dbe66aedde6",
    "6ac85b6314e4d8bd1124775e2d65899fcc1dd059a6bc649dce42bc3d860ebac8",
)
ADR0295_POOL_CANDIDATE_ATTEMPTS = (180, 181, 175)


def _seed_for_batch(batch_index: int) -> str:
    if (
        isinstance(batch_index, bool)
        or not isinstance(batch_index, int)
        or batch_index not in range(ADR0295_BATCH_COUNT)
    ):
        raise ValueError("sizing-power batch index must identify one of three batches")
    return (
        "pontius|adr-0295|candidate-blind-power-v1|"
        f"baseline={ADR0295_BASELINE_COMMIT}|batch={batch_index}"
    )


@dataclass(frozen=True, slots=True)
class NormalizedSizingOpportunityFloor:
    """Dimensionless material-opportunity threshold, not a solver tolerance."""

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, float) or not isfinite(self.value):
            raise ValueError("normalized sizing-opportunity floor must be a finite float")
        if not 0.0 < self.value < 1.0:
            raise ValueError("normalized sizing-opportunity floor must lie in (0, 1)")


@dataclass(frozen=True, slots=True)
class ChipClassificationGuard:
    """Chip-valued ambiguity guard, distinct from normalized opportunity."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips):
            raise ValueError("chip classification guard must be a finite float")
        if self.chips <= 0.0:
            raise ValueError("chip classification guard must be positive")


class SizingPowerClassification(StrEnum):
    QUALIFYING = "qualifying"
    NONQUALIFYING = "nonqualifying"
    AMBIGUOUS = "ambiguous"


class QualificationStopReason(StrEnum):
    TARGET_REACHED = "target_reached"
    POOL_EXHAUSTED = "pool_exhausted"
    AMBIGUOUS = "ambiguous"


def classify_sizing_opportunity(
    *,
    full_value_chips: float,
    narrow_value_chips: float,
    payoff_span: int,
    opportunity_floor: NormalizedSizingOpportunityFloor,
    classification_guard: ChipClassificationGuard,
) -> SizingPowerClassification:
    """Classify one full-versus-narrow gap without any candidate policy."""

    if not isinstance(opportunity_floor, NormalizedSizingOpportunityFloor):
        raise TypeError("sizing opportunity requires its normalized semantic floor")
    if not isinstance(classification_guard, ChipClassificationGuard):
        raise TypeError("sizing opportunity requires its chip semantic guard")
    if (
        not isinstance(full_value_chips, float)
        or not isfinite(full_value_chips)
        or not isinstance(narrow_value_chips, float)
        or not isfinite(narrow_value_chips)
    ):
        raise ValueError("sizing-opportunity values must be finite floats")
    if (
        isinstance(payoff_span, bool)
        or not isinstance(payoff_span, int)
        or payoff_span <= 0
    ):
        raise ValueError("sizing-opportunity payoff span must be a positive integer")
    gap = full_value_chips - narrow_value_chips
    threshold = opportunity_floor.value * payoff_span
    if abs(gap - threshold) <= classification_guard.chips:
        return SizingPowerClassification.AMBIGUOUS
    if gap > threshold + classification_guard.chips:
        return SizingPowerClassification.QUALIFYING
    return SizingPowerClassification.NONQUALIFYING


@dataclass(frozen=True, slots=True)
class SizingPowerPool:
    batch_index: int
    seed: str
    candidate_attempts: int
    contexts: tuple[ReducedRiverSizingContext, ...]

    def __post_init__(self) -> None:
        expected_seed = _seed_for_batch(self.batch_index)
        if self.seed != expected_seed:
            raise ValueError("sizing-power pool seed differs from ADR-0295")
        if (
            isinstance(self.candidate_attempts, bool)
            or not isinstance(self.candidate_attempts, int)
            or self.candidate_attempts < ADR0295_POOL_CONTEXT_COUNT
        ):
            raise ValueError("sizing-power raw candidate-attempt count is invalid")
        if not isinstance(self.contexts, tuple) or len(
            self.contexts
        ) != ADR0295_POOL_CONTEXT_COUNT:
            raise TypeError("sizing-power pool must contain 96 immutable contexts")
        if any(
            not isinstance(context, ReducedRiverSizingContext)
            for context in self.contexts
        ):
            raise TypeError("sizing-power pool contains a nonsemantic context")
        expected_ids = tuple(
            f"adr0295-power-b{self.batch_index}-c{index:02d}"
            for index in range(ADR0295_POOL_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("sizing-power pool ids or ordering differ from ADR-0295")
        if len({context.digest for context in self.contexts}) != len(self.contexts):
            raise ValueError("sizing-power pool repeats a context")
        if any(
            not _structurally_admissible(context.showdown_signs)
            for context in self.contexts
        ):
            raise ValueError("sizing-power pool contains an inadmissible sign matrix")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "batch_index": self.batch_index,
            "candidate_attempts": self.candidate_attempts,
            "contexts": tuple(
                {
                    "board": context.board,
                    "context_id": context.context_id,
                    "joint_probabilities": tuple(
                        tuple(
                            (probability.numerator, probability.denominator)
                            for probability in row
                        )
                        for row in context.joint_probabilities
                    ),
                    "minimum_bet": context.minimum_bet,
                    "opener_hands": context.opener_hands,
                    "pot": context.pot,
                    "responder_hands": context.responder_hands,
                    "stack": context.stack,
                }
                for context in self.contexts
            ),
            "dependency_generator_version": ADR0293_GENERATOR_VERSION,
            "generator_version": ADR0295_GENERATOR_VERSION,
            "seed": self.seed,
        }
        return json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class QualifiedSizingPowerPanel:
    pool_digest: str
    pool_indices: tuple[int, ...]
    context_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.pool_digest, str)
            or len(self.pool_digest) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.pool_digest
            )
        ):
            raise ValueError("qualified sizing-power pool digest must be SHA-256")
        if not isinstance(self.pool_indices, tuple) or len(
            self.pool_indices
        ) != ADR0295_QUALIFIED_CONTEXT_COUNT:
            raise TypeError("qualified sizing-power panel requires 12 immutable indices")
        if any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index not in range(ADR0295_POOL_CONTEXT_COUNT)
            for index in self.pool_indices
        ):
            raise ValueError("qualified sizing-power index lies outside its pool")
        if tuple(sorted(self.pool_indices)) != self.pool_indices or len(
            set(self.pool_indices)
        ) != len(self.pool_indices):
            raise ValueError("qualified sizing-power indices must increase strictly")
        if not isinstance(self.context_digests, tuple) or len(
            self.context_digests
        ) != len(self.pool_indices):
            raise TypeError("qualified sizing-power context digests must align with indices")
        if any(
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            for digest in self.context_digests
        ):
            raise ValueError("qualified sizing-power context digest is invalid")

    @property
    def digest(self) -> str:
        payload = {
            "context_digests": self.context_digests,
            "pool_digest": self.pool_digest,
            "pool_indices": self.pool_indices,
            "version": "qualified-candidate-blind-sizing-power-panel-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class SizingPowerObservation:
    context_index: int
    context_digest: str
    full_value_chips: float
    narrow_value_chips: float
    payoff_span: int
    classification: SizingPowerClassification
    max_probability_residual: float
    max_chip_objective_error: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.context_index, bool)
            or not isinstance(self.context_index, int)
            or self.context_index not in range(ADR0295_POOL_CONTEXT_COUNT)
        ):
            raise ValueError("sizing-power observation index lies outside its pool")
        if (
            not isinstance(self.context_digest, str)
            or len(self.context_digest) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.context_digest
            )
        ):
            raise ValueError("sizing-power observation context digest is invalid")
        for label, value in (
            ("full value", self.full_value_chips),
            ("narrow value", self.narrow_value_chips),
            ("probability residual", self.max_probability_residual),
            ("chip objective error", self.max_chip_objective_error),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"sizing-power observation {label} must be finite")
        if (
            isinstance(self.payoff_span, bool)
            or not isinstance(self.payoff_span, int)
            or self.payoff_span <= 0
        ):
            raise ValueError("sizing-power observation payoff span must be positive")
        if not isinstance(self.classification, SizingPowerClassification):
            raise TypeError("sizing-power observation classification must be semantic")
        if self.max_probability_residual < 0.0 or self.max_chip_objective_error < 0.0:
            raise ValueError("sizing-power observation errors must be nonnegative")


@dataclass(frozen=True, slots=True)
class SizingPowerQualificationResult:
    batch_index: int
    pool_digest: str
    stop_reason: QualificationStopReason
    observations: tuple[SizingPowerObservation, ...]
    qualified_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        _seed_for_batch(self.batch_index)
        if (
            not isinstance(self.pool_digest, str)
            or len(self.pool_digest) != 64
            or any(
                character not in "0123456789abcdef" for character in self.pool_digest
            )
        ):
            raise ValueError("sizing-power result pool digest is invalid")
        if not isinstance(self.stop_reason, QualificationStopReason):
            raise TypeError("sizing-power stop reason must be semantic")
        if not isinstance(self.observations, tuple) or not self.observations:
            raise TypeError("sizing-power result requires immutable observations")
        if any(
            not isinstance(observation, SizingPowerObservation)
            for observation in self.observations
        ):
            raise TypeError("sizing-power result contains a nonsemantic observation")
        if tuple(observation.context_index for observation in self.observations) != tuple(
            range(len(self.observations))
        ):
            raise ValueError("sizing-power observations must be a contiguous prefix")
        expected_qualified = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.QUALIFYING
        )
        if self.qualified_indices != expected_qualified:
            raise ValueError("sizing-power qualified indices disagree with observations")
        ambiguous_indices = tuple(
            observation.context_index
            for observation in self.observations
            if observation.classification is SizingPowerClassification.AMBIGUOUS
        )
        if self.stop_reason is QualificationStopReason.AMBIGUOUS:
            if ambiguous_indices != (len(self.observations) - 1,):
                raise ValueError("ambiguous sizing result must stop at its first ambiguity")
            if len(self.qualified_indices) >= ADR0295_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("ambiguous sizing result already reached its target")
        elif ambiguous_indices:
            raise ValueError("non-ambiguous sizing result contains an ambiguity")
        if self.stop_reason is QualificationStopReason.TARGET_REACHED:
            if len(self.qualified_indices) != ADR0295_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("target-reached sizing result lacks 12 qualifiers")
            if self.qualified_indices[-1] != len(self.observations) - 1:
                raise ValueError("target-reached sizing result opened a later value")
        elif self.stop_reason is QualificationStopReason.POOL_EXHAUSTED:
            if len(self.observations) != ADR0295_POOL_CONTEXT_COUNT:
                raise ValueError("pool-exhausted sizing result did not open the full pool")
            if len(self.qualified_indices) >= ADR0295_QUALIFIED_CONTEXT_COUNT:
                raise ValueError("pool-exhausted sizing result already reached its target")

    @property
    def opened_context_count(self) -> int:
        return len(self.observations)

    @property
    def digest(self) -> str:
        payload = {
            "batch_index": self.batch_index,
            "observations": tuple(
                {
                    "classification": observation.classification.value,
                    "context_digest": observation.context_digest,
                    "context_index": observation.context_index,
                    "full_value_chips": observation.full_value_chips.hex(),
                    "max_chip_objective_error": observation.max_chip_objective_error.hex(),
                    "max_probability_residual": observation.max_probability_residual.hex(),
                    "narrow_value_chips": observation.narrow_value_chips.hex(),
                    "payoff_span": observation.payoff_span,
                }
                for observation in self.observations
            ),
            "pool_digest": self.pool_digest,
            "qualified_indices": self.qualified_indices,
            "stop_reason": self.stop_reason.value,
            "version": "candidate-blind-sizing-power-result-v1",
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
        pool: SizingPowerPool,
    ) -> QualifiedSizingPowerPanel:
        if self.stop_reason is not QualificationStopReason.TARGET_REACHED:
            raise ValueError("only a target-reached result has a qualified panel")
        if (
            not isinstance(pool, SizingPowerPool)
            or pool.batch_index != self.batch_index
            or pool.digest != self.pool_digest
        ):
            raise ValueError("qualified-panel pool differs from its sizing result")
        expected_prefix = tuple(
            context.digest for context in pool.contexts[: len(self.observations)]
        )
        observed_prefix = tuple(
            observation.context_digest for observation in self.observations
        )
        if observed_prefix != expected_prefix:
            raise ValueError("sizing result observations differ from their pool prefix")
        return qualify_sizing_power_panel(
            pool=pool,
            pool_indices=self.qualified_indices,
        )


def build_adr0295_sizing_power_pool(*, batch_index: int) -> SizingPowerPool:
    """Build one frozen structural pool without solving any betting arm."""

    seed = _seed_for_batch(batch_index)
    stream = _DigestStream(seed)
    contexts: list[ReducedRiverSizingContext] = []
    candidate_attempts = 0
    while len(contexts) < ADR0295_POOL_CONTEXT_COUNT:
        candidate_attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs(deck[5:11])
        responder_hands = _private_pairs(deck[11:17])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible(signs):
            continue
        pot = ADR0293_POTS[stream.randbelow(len(ADR0293_POTS))]
        stack = ADR0293_STACKS[stream.randbelow(len(ADR0293_STACKS))]
        weights = tuple(1 + stream.randbelow(9) for _ in range(9))
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                ExactDealProbability(weights[row * 3 + column], denominator)
                for column in range(3)
            )
            for row in range(3)
        )
        contexts.append(
            ReducedRiverSizingContext(
                context_id=(
                    f"adr0295-power-b{batch_index}-c{len(contexts):02d}"
                ),
                board=board,
                pot=pot,
                stack=stack,
                minimum_bet=2,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
            )
        )
    return SizingPowerPool(
        batch_index=batch_index,
        seed=seed,
        candidate_attempts=candidate_attempts,
        contexts=tuple(contexts),
    )


def qualify_sizing_power_panel(
    *,
    pool: SizingPowerPool,
    pool_indices: tuple[int, ...],
) -> QualifiedSizingPowerPanel:
    """Bind caller-classified indices without accepting values or policies."""

    if not isinstance(pool, SizingPowerPool):
        raise TypeError("qualification requires a semantic sizing-power pool")
    if not isinstance(pool_indices, tuple):
        raise TypeError("qualified sizing-power indices must be immutable")
    if len(pool_indices) != ADR0295_QUALIFIED_CONTEXT_COUNT:
        raise ValueError("qualification requires exactly 12 pool indices")
    if any(
        isinstance(index, bool)
        or not isinstance(index, int)
        or index not in range(ADR0295_POOL_CONTEXT_COUNT)
        for index in pool_indices
    ):
        raise ValueError("qualified sizing-power index lies outside its pool")
    if tuple(sorted(pool_indices)) != pool_indices or len(set(pool_indices)) != len(
        pool_indices
    ):
        raise ValueError("qualified sizing-power indices must increase strictly")
    return QualifiedSizingPowerPanel(
        pool_digest=pool.digest,
        pool_indices=pool_indices,
        context_digests=tuple(pool.contexts[index].digest for index in pool_indices),
    )


def run_candidate_blind_sizing_power_qualification(
    *,
    pool: SizingPowerPool,
    opportunity_floor: NormalizedSizingOpportunityFloor,
    classification_guard: ChipClassificationGuard,
    probability_allowance: ProbabilitySimplexAllowance,
    chip_allowance: ChipObjectiveAllowance,
) -> SizingPowerQualificationResult:
    """Own all value openings and stop immediately at target or ambiguity."""

    if not isinstance(pool, SizingPowerPool):
        raise TypeError("candidate-blind qualification requires a semantic pool")
    if not isinstance(opportunity_floor, NormalizedSizingOpportunityFloor):
        raise TypeError("candidate-blind qualification requires its opportunity floor")
    if not isinstance(classification_guard, ChipClassificationGuard):
        raise TypeError("candidate-blind qualification requires its classification guard")
    if not isinstance(probability_allowance, ProbabilitySimplexAllowance):
        raise TypeError("candidate-blind qualification requires its probability allowance")
    if not isinstance(chip_allowance, ChipObjectiveAllowance):
        raise TypeError("candidate-blind qualification requires its chip allowance")
    observations: list[SizingPowerObservation] = []
    qualified_indices: list[int] = []
    for context_index, context in enumerate(pool.contexts):
        full, narrow = tuple(
            solve_reduced_river_sizing(
                context,
                sizes,
                probability_allowance=probability_allowance,
                chip_allowance=chip_allowance,
            )
            for sizes in (
                tuple(range(context.minimum_bet, context.stack + 1)),
                (context.minimum_bet, context.stack),
            )
        )
        if full.value_chips + chip_allowance.chips < narrow.value_chips:
            raise AssertionError("full sizing value fell materially below narrow value")
        classification = classify_sizing_opportunity(
            full_value_chips=full.value_chips,
            narrow_value_chips=narrow.value_chips,
            payoff_span=context.payoff_span,
            opportunity_floor=opportunity_floor,
            classification_guard=classification_guard,
        )
        observations.append(
            SizingPowerObservation(
                context_index=context_index,
                context_digest=context.digest,
                full_value_chips=full.value_chips,
                narrow_value_chips=narrow.value_chips,
                payoff_span=context.payoff_span,
                classification=classification,
                max_probability_residual=max(
                    full.max_probability_simplex_residual,
                    narrow.max_probability_simplex_residual,
                ),
                max_chip_objective_error=max(
                    full.chip_objective_reconstruction_error,
                    narrow.chip_objective_reconstruction_error,
                ),
            )
        )
        if classification is SizingPowerClassification.AMBIGUOUS:
            return SizingPowerQualificationResult(
                batch_index=pool.batch_index,
                pool_digest=pool.digest,
                stop_reason=QualificationStopReason.AMBIGUOUS,
                observations=tuple(observations),
                qualified_indices=tuple(qualified_indices),
            )
        if classification is SizingPowerClassification.QUALIFYING:
            qualified_indices.append(context_index)
            if len(qualified_indices) == ADR0295_QUALIFIED_CONTEXT_COUNT:
                return SizingPowerQualificationResult(
                    batch_index=pool.batch_index,
                    pool_digest=pool.digest,
                    stop_reason=QualificationStopReason.TARGET_REACHED,
                    observations=tuple(observations),
                    qualified_indices=tuple(qualified_indices),
                )
    return SizingPowerQualificationResult(
        batch_index=pool.batch_index,
        pool_digest=pool.digest,
        stop_reason=QualificationStopReason.POOL_EXHAUSTED,
        observations=tuple(observations),
        qualified_indices=tuple(qualified_indices),
    )


__all__ = [
    "ADR0295_BASELINE_COMMIT",
    "ADR0295_BATCH_COUNT",
    "ADR0295_GENERATOR_VERSION",
    "ADR0295_POOL_CANDIDATE_ATTEMPTS",
    "ADR0295_POOL_CONTEXT_COUNT",
    "ADR0295_POOL_SHA256",
    "ADR0295_QUALIFIED_CONTEXT_COUNT",
    "ChipClassificationGuard",
    "NormalizedSizingOpportunityFloor",
    "QualificationStopReason",
    "QualifiedSizingPowerPanel",
    "SizingPowerClassification",
    "SizingPowerObservation",
    "SizingPowerPool",
    "SizingPowerQualificationResult",
    "build_adr0295_sizing_power_pool",
    "classify_sizing_opportunity",
    "qualify_sizing_power_panel",
    "run_candidate_blind_sizing_power_qualification",
]
