"""Exact delta-aware policy recertification for the river microgame.

This module does not treat nearby ranges as interchangeable.  It compiles one
fixed policy into probability-free per-deal coefficients, verifies an exact
source-to-target range delta, and applies that delta only to the affected
private-hand best-response aggregates.  The result is mathematically the same
fixed-policy value and exploitability calculation as a full tree evaluation.

Delta discovery still scans the union of source and target support.  It can be
performed once and amortized across many independently compiled policy cache
entries.  Applying a verified delta costs work proportional to the changed
deals and affected private-hand decision cones, not the full range support.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import fsum

from .evaluation import EvaluationResult, Policy, policy_distribution
from .river import (
    BET,
    CALL,
    CHECK,
    FOLD,
    RAISE,
    HoleCards,
    RiverDeal,
    RiverHoldem,
    RiverState,
    format_card,
)


@dataclass(frozen=True, slots=True)
class RiverRangeChange:
    """One exact probability change in a normalized joint river range."""

    deal: RiverDeal
    source_probability: float
    target_probability: float

    @property
    def probability_delta(self) -> float:
        return self.target_probability - self.source_probability

    @property
    def kind(self) -> str:
        if self.source_probability == 0.0:
            return "added"
        if self.target_probability == 0.0:
            return "removed"
        return "reweighted"


@dataclass(frozen=True, slots=True)
class RiverRangeDelta:
    """A provenance-bound, lossless delta between two normalized ranges."""

    structural_digest: str
    source_provenance_digest: str
    target_provenance_digest: str
    changes: tuple[RiverRangeChange, ...]

    @classmethod
    def between(cls, source: RiverHoldem, target: RiverHoldem) -> RiverRangeDelta:
        """Discover every changed joint-deal probability exactly once."""

        if not isinstance(source, RiverHoldem) or not isinstance(target, RiverHoldem):
            raise TypeError("range deltas require RiverHoldem source and target games")
        if source.structural_digest != target.structural_digest:
            raise ValueError("range deltas require identical game structure")

        source_distribution = source.joint_distribution()
        target_distribution = target.joint_distribution()
        changes = tuple(
            RiverRangeChange(
                deal=deal,
                source_probability=source_distribution.get(deal, 0.0),
                target_probability=target_distribution.get(deal, 0.0),
            )
            for deal in sorted(set(source_distribution) | set(target_distribution))
            if source_distribution.get(deal, 0.0)
            != target_distribution.get(deal, 0.0)
        )
        if abs(fsum(change.probability_delta for change in changes)) > 1e-12:
            raise AssertionError("normalized range delta does not conserve probability mass")
        if (not changes) != (
            source.provenance_digest == target.provenance_digest
        ):
            raise AssertionError("range delta and provenance identity disagree")
        return cls(
            structural_digest=source.structural_digest,
            source_provenance_digest=source.provenance_digest,
            target_provenance_digest=target.provenance_digest,
            changes=changes,
        )

    @property
    def total_variation(self) -> float:
        return 0.5 * fsum(abs(change.probability_delta) for change in self.changes)

    @property
    def added_deals(self) -> int:
        return sum(change.kind == "added" for change in self.changes)

    @property
    def removed_deals(self) -> int:
        return sum(change.kind == "removed" for change in self.changes)

    @property
    def reweighted_deals(self) -> int:
        return sum(change.kind == "reweighted" for change in self.changes)

    def validate(self, source: RiverHoldem, target: RiverHoldem) -> None:
        """Reject use with anything except the games that produced this delta."""

        if source.structural_digest != self.structural_digest:
            raise ValueError("delta structure does not match the compiled source")
        if target.structural_digest != self.structural_digest:
            raise ValueError("delta structure does not match the target")
        if source.provenance_digest != self.source_provenance_digest:
            raise ValueError("delta source provenance does not match the compiled source")
        if target.provenance_digest != self.target_provenance_digest:
            raise ValueError("delta target provenance does not match the target")


@dataclass(frozen=True, slots=True)
class RiverRecertificationDiagnostics:
    """Auditable work counts for one exact incremental recertification."""

    changed_deals: int
    added_deals: int
    removed_deals: int
    reweighted_deals: int
    affected_player0_hands: int
    affected_player1_hands: int
    newly_compiled_deals: int
    source_deals: int
    target_deals: int
    total_variation: float


@dataclass(frozen=True, slots=True)
class RiverRecertificationResult:
    evaluation: EvaluationResult
    diagnostics: RiverRecertificationDiagnostics


@dataclass(frozen=True, slots=True)
class _DealPolicyCoefficients:
    """Probability-free value coefficients contributed by one joint deal."""

    player0_hand: HoleCards
    player1_hand: HoleCards
    fixed_policy_u0: float
    player0_check: float
    player0_bet_without_raise: float
    player0_raise_fold: float
    player0_raise_call: float
    player1_check_base: float
    player1_fold: float
    player1_call: float
    player1_raise: float


_PLAYER0_ZERO = (0.0, 0.0, 0.0, 0.0)
_PLAYER1_ZERO = (0.0, 0.0, 0.0)


def _compile_deal(
    game: RiverHoldem,
    deal: RiverDeal,
    policy: Policy,
    distributions: dict[tuple[str, tuple[str, ...]], dict[str, float]],
) -> _DealPolicyCoefficients:
    """Compile a deal using the same state and policy contracts as full evaluation."""

    def distribution(state: RiverState, player: int) -> dict[str, float]:
        actions = tuple(state.legal_actions())
        key = state.information_state_key(player)
        cache_key = (key, actions)
        result = distributions.get(cache_key)
        if result is None:
            result = policy_distribution(policy, key, actions)
            distributions[cache_key] = result
        return result

    dealt = game.initial_state().apply_action(deal)
    player0_root = distribution(dealt, 0)
    check_u0 = dealt.apply_action(CHECK).returns()[0]

    facing_bet = dealt.apply_action(BET)
    player1_response = distribution(facing_bet, 1)
    fold_u0 = facing_bet.apply_action(FOLD).returns()[0]
    call_u0 = facing_bet.apply_action(CALL).returns()[0]

    bet_without_raise = (
        player1_response[FOLD] * fold_u0
        + player1_response[CALL] * call_u0
    )
    raise_fold = 0.0
    raise_call = 0.0
    player1_raise = 0.0
    fixed_bet_u0 = bet_without_raise

    if game.raise_to is not None:
        facing_raise = facing_bet.apply_action(RAISE)
        player0_response = distribution(facing_raise, 0)
        raise_fold_u0 = facing_raise.apply_action(FOLD).returns()[0]
        raise_call_u0 = facing_raise.apply_action(CALL).returns()[0]
        raise_probability = player1_response[RAISE]
        raise_fold = raise_probability * raise_fold_u0
        raise_call = raise_probability * raise_call_u0
        fixed_raise_u0 = (
            player0_response[FOLD] * raise_fold_u0
            + player0_response[CALL] * raise_call_u0
        )
        fixed_bet_u0 += raise_probability * fixed_raise_u0
        player1_raise = player0_root[BET] * (-fixed_raise_u0)

    fixed_u0 = (
        player0_root[CHECK] * check_u0
        + player0_root[BET] * fixed_bet_u0
    )
    return _DealPolicyCoefficients(
        player0_hand=deal.player0,
        player1_hand=deal.player1,
        fixed_policy_u0=fixed_u0,
        player0_check=check_u0,
        player0_bet_without_raise=bet_without_raise,
        player0_raise_fold=raise_fold,
        player0_raise_call=raise_call,
        player1_check_base=player0_root[CHECK] * (-check_u0),
        player1_fold=player0_root[BET] * (-fold_u0),
        player1_call=player0_root[BET] * (-call_u0),
        player1_raise=player1_raise,
    )


def _player0_hand_value(values: tuple[float, float, float, float], has_raise: bool) -> float:
    check, bet_without_raise, raise_fold, raise_call = values
    bet = bet_without_raise
    if has_raise:
        bet += max(raise_fold, raise_call)
    return max(check, bet)


def _player1_hand_value(values: tuple[float, float, float], has_raise: bool) -> float:
    fold, call, raise_value = values
    return max(fold, call, raise_value) if has_raise else max(fold, call)


def _evaluation(
    fixed_u0: float,
    player0_best_response: float,
    player1_best_response: float,
) -> EvaluationResult:
    utilities = (fixed_u0, -fixed_u0)
    best_responses = (player0_best_response, player1_best_response)
    deviation_gains = (
        max(0.0, player0_best_response - fixed_u0),
        max(0.0, player1_best_response + fixed_u0),
    )
    nash_conv = fsum(deviation_gains)
    return EvaluationResult(
        utilities=utilities,
        best_response_values=best_responses,
        deviation_gains=deviation_gains,
        nash_conv=nash_conv,
        exploitability=nash_conv / 2.0,
    )


class RiverPolicyEvaluationCache:
    """Compiled exact evaluator for one policy and one source range.

    The cache is intentionally source-relative.  Every recertification validates
    both provenance digests and applies a complete delta from that immutable
    source; unchecked approximate or chained range reuse is not exposed.
    """

    def __init__(self, source: RiverHoldem, policy: Policy) -> None:
        if not isinstance(source, RiverHoldem):
            raise TypeError("RiverPolicyEvaluationCache requires a RiverHoldem game")
        self._source = source
        self._policy: Policy = {
            key: dict(distribution) for key, distribution in policy.items()
        }
        self._has_raise = source.raise_to is not None
        distributions: dict[tuple[str, tuple[str, ...]], dict[str, float]] = {}
        self._coefficients = {
            deal: _compile_deal(source, deal, self._policy, distributions)
            for deal, _ in source.deals
        }

        player0: dict[HoleCards, list[float]] = {}
        player1: dict[HoleCards, list[float]] = {}
        fixed_terms = []
        player1_check_terms = []
        for deal, probability in source.deals:
            coefficients = self._coefficients[deal]
            fixed_terms.append(probability * coefficients.fixed_policy_u0)
            player1_check_terms.append(probability * coefficients.player1_check_base)

            values0 = player0.setdefault(coefficients.player0_hand, [0.0] * 4)
            values0[0] += probability * coefficients.player0_check
            values0[1] += probability * coefficients.player0_bet_without_raise
            values0[2] += probability * coefficients.player0_raise_fold
            values0[3] += probability * coefficients.player0_raise_call

            values1 = player1.setdefault(coefficients.player1_hand, [0.0] * 3)
            values1[0] += probability * coefficients.player1_fold
            values1[1] += probability * coefficients.player1_call
            values1[2] += probability * coefficients.player1_raise

        self._player0 = {hand: tuple(values) for hand, values in player0.items()}
        self._player1 = {hand: tuple(values) for hand, values in player1.items()}
        self._player0_optima = {
            hand: _player0_hand_value(values, self._has_raise)
            for hand, values in self._player0.items()
        }
        self._player1_optima = {
            hand: _player1_hand_value(values, self._has_raise)
            for hand, values in self._player1.items()
        }
        self._fixed_u0 = fsum(fixed_terms)
        self._player1_check_base = fsum(player1_check_terms)
        self._player0_best_response = fsum(self._player0_optima.values())
        self._player1_best_response = self._player1_check_base + fsum(
            self._player1_optima.values()
        )
        self._source_evaluation = _evaluation(
            self._fixed_u0,
            self._player0_best_response,
            self._player1_best_response,
        )

    @property
    def source(self) -> RiverHoldem:
        return self._source

    @property
    def source_evaluation(self) -> EvaluationResult:
        return self._source_evaluation

    @property
    def compiled_deals(self) -> int:
        return len(self._coefficients)

    def recertify(
        self,
        target: RiverHoldem,
        delta: RiverRangeDelta | None = None,
    ) -> RiverRecertificationResult:
        """Exactly evaluate the compiled policy under a verified target range."""

        if not isinstance(target, RiverHoldem):
            raise TypeError("recertification target must be a RiverHoldem game")
        verified_delta = (
            RiverRangeDelta.between(self._source, target)
            if delta is None
            else delta
        )
        verified_delta.validate(self._source, target)

        updated_player0: dict[HoleCards, list[float]] = {}
        updated_player1: dict[HoleCards, list[float]] = {}
        fixed_deltas = []
        player1_check_deltas = []
        newly_compiled = 0
        distributions: dict[tuple[str, tuple[str, ...]], dict[str, float]] = {}

        for change in verified_delta.changes:
            coefficients = self._coefficients.get(change.deal)
            if coefficients is None:
                coefficients = _compile_deal(
                    target,
                    change.deal,
                    self._policy,
                    distributions,
                )
                newly_compiled += 1
            probability_delta = change.probability_delta
            fixed_deltas.append(probability_delta * coefficients.fixed_policy_u0)
            player1_check_deltas.append(
                probability_delta * coefficients.player1_check_base
            )

            values0 = updated_player0.get(coefficients.player0_hand)
            if values0 is None:
                values0 = list(
                    self._player0.get(coefficients.player0_hand, _PLAYER0_ZERO)
                )
                updated_player0[coefficients.player0_hand] = values0
            values0[0] += probability_delta * coefficients.player0_check
            values0[1] += probability_delta * coefficients.player0_bet_without_raise
            values0[2] += probability_delta * coefficients.player0_raise_fold
            values0[3] += probability_delta * coefficients.player0_raise_call

            values1 = updated_player1.get(coefficients.player1_hand)
            if values1 is None:
                values1 = list(
                    self._player1.get(coefficients.player1_hand, _PLAYER1_ZERO)
                )
                updated_player1[coefficients.player1_hand] = values1
            values1[0] += probability_delta * coefficients.player1_fold
            values1[1] += probability_delta * coefficients.player1_call
            values1[2] += probability_delta * coefficients.player1_raise

        player0_best_response = self._player0_best_response
        for hand, values in updated_player0.items():
            player0_best_response += _player0_hand_value(
                tuple(values), self._has_raise
            ) - self._player0_optima.get(hand, 0.0)

        player1_best_response = self._player1_best_response + fsum(
            player1_check_deltas
        )
        for hand, values in updated_player1.items():
            player1_best_response += _player1_hand_value(
                tuple(values), self._has_raise
            ) - self._player1_optima.get(hand, 0.0)

        evaluation = _evaluation(
            self._fixed_u0 + fsum(fixed_deltas),
            player0_best_response,
            player1_best_response,
        )
        return RiverRecertificationResult(
            evaluation=evaluation,
            diagnostics=RiverRecertificationDiagnostics(
                changed_deals=len(verified_delta.changes),
                added_deals=verified_delta.added_deals,
                removed_deals=verified_delta.removed_deals,
                reweighted_deals=verified_delta.reweighted_deals,
                affected_player0_hands=len(updated_player0),
                affected_player1_hands=len(updated_player1),
                newly_compiled_deals=newly_compiled,
                source_deals=len(self._source.deals),
                target_deals=len(target.deals),
                total_variation=verified_delta.total_variation,
            ),
        )


def make_support_swap_perturbation(
    game: RiverHoldem,
    *,
    player: int,
) -> tuple[RiverHoldem, dict[str, object]]:
    """Replace the rarest feasible deal with an unseen private hand.

    The opponent hand and probability mass are held fixed.  Candidate deals are
    chosen to occupy the removed deal's sorted position when possible, which
    keeps floating-point normalization order stable and makes the intended
    sparse two-deal delta mechanically checkable.
    """

    if player not in (0, 1):
        raise ValueError("player must be zero or one")
    distribution = game.joint_distribution()
    source_deals = tuple(sorted(distribution))
    source_hands = set(game.marginal_distribution(player))
    board = set(game.board)
    selected: tuple[RiverDeal, RiverDeal] | None = None

    for removed in sorted(source_deals, key=lambda deal: (distribution[deal], deal)):
        opponent = removed.hand(1 - player)
        available = tuple(
            card for card in range(52) if card not in board and card not in opponent
        )
        removed_index = source_deals.index(removed)
        common = tuple(deal for deal in source_deals if deal != removed)
        fallback: RiverDeal | None = None
        for candidate_hand in combinations(available, 2):
            if candidate_hand in source_hands:
                continue
            candidate = (
                RiverDeal(candidate_hand, opponent)
                if player == 0
                else RiverDeal(opponent, candidate_hand)
            )
            if candidate in distribution:
                continue
            if fallback is None:
                fallback = candidate
            insertion_index = sum(deal < candidate for deal in common)
            if insertion_index == removed_index:
                selected = (removed, candidate)
                break
        if selected is None and fallback is not None:
            selected = (removed, fallback)
        if selected is not None:
            break
    if selected is None:
        raise ValueError("could not construct a compatible unseen support deal")

    removed, added = selected
    moved_probability = distribution[removed]
    target_weights = {
        deal: (moved_probability if deal == added else distribution[deal])
        for deal in sorted((set(distribution) - {removed}) | {added})
    }
    target = RiverHoldem.from_joint_weights(
        board=game.board,
        pot=game.pot,
        stacks=game.stacks,
        bet_size=game.bet_size,
        raise_to=game.raise_to,
        joint_weights=target_weights,
    )
    delta = RiverRangeDelta.between(game, target)
    return target, {
        "player": player,
        "removed_deal": {
            "player0": [format_card(card) for card in removed.player0],
            "player1": [format_card(card) for card in removed.player1],
        },
        "added_deal": {
            "player0": [format_card(card) for card in added.player0],
            "player1": [format_card(card) for card in added.player1],
        },
        "moved_probability_mass": moved_probability,
        "actual_root_joint_total_variation": delta.total_variation,
        "delta_deals": len(delta.changes),
        "added_deals": delta.added_deals,
        "removed_deals": delta.removed_deals,
        "reweighted_deals": delta.reweighted_deals,
        "new_private_hand": [format_card(card) for card in added.hand(player)],
        "new_private_hand_was_absent": added.hand(player) not in source_hands,
    }
