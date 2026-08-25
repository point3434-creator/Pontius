"""Value-unopened legal-h4 population for factorized-affine confirmation.

The four contexts are derived only from the clean ADR-0358 preregistration
commit, before its target result existed.  Construction fixes cards, exact
dyadic joint ranges, the legal six-seat betting state, source policies, the
downstream direction classes, and the complete successor evidence contract.
It does not call a best response, CFR, a master, a selector, or an affine
consumer and it does not import any ADR-0358 result owner or artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

from .evaluation import Policy, collect_information_sets
from .legal_decision_spine_v2 import public_betting_state_sha256
from .legal_river_continuation import LegalHeadsUpRiverContinuation
from .no_limit_betting import CALL, CHECK, FOLD, BettingStreet, NoLimitBettingState
from .river import RiverDeal, format_card, make_hole, parse_card, parse_cards


ADR0360_MECHANISM_SOURCE_COMMIT = "23c7f023e686b8b84bc1145381c5fe7ba99dc8d4"
ADR0360_CONFIRMATION_CONTEXT_COUNT = 4
ADR0360_CONFIRMATION_PRIVATE_WIDTH = 4
ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR = 64
ADR0360_CONFIRMATION_SEED = (
    "pontius|adr-0360|legal-h4-factorized-affine-confirmation|"
    f"mechanism-commit={ADR0360_MECHANISM_SOURCE_COMMIT}"
)
ADR0360_CONFIRMATION_SEED_SHA256 = sha256(
    ADR0360_CONFIRMATION_SEED.encode("ascii")
).hexdigest()

_SOURCE_POLICY_VERSION = "adr0360-context-bound-dyadic-key-rotated-policy-v1"
_POPULATION_VERSION = "adr0360-fresh-legal-h4-factorized-affine-population-v1"
_SEMANTIC_KEY_VERSION = "legal-h4-confirmation-semantic-key-v1"
_DECK = tuple(format_card(card) for card in range(52))
_SOURCE_TEMPLATES = MappingProxyType(
    {
        2: (0.25, 0.75),
        3: (0.25, 0.25, 0.5),
        4: (0.125, 0.25, 0.125, 0.5),
    }
)


ADR0360_CONFIRMATION_PROTOCOL = MappingProxyType(
    {
        "acting_player": 0,
        "candidate_selection": (
            "first_four_sha256_permutations_without_outcome_filtering_skipping_"
            "replacement_or_reseed"
        ),
        "claims_policy": (
            "finite_fresh_h4_factorized_affine_mechanism_confirmation_only_no_"
            "full_width_action_clock_action_quality_strategy_strength_multiway_"
            "or_cross_street_claim"
        ),
        "cardinality_columns": (
            "total_function_certificate_authority",
            "reachable_support_reporting_only",
        ),
        "confirmation_context_count": ADR0360_CONFIRMATION_CONTEXT_COUNT,
        "direction_classes_in_order": (
            "one_step_dcfr_regret_vertex_per_public_history",
            "one_step_dcfr_regret_vertex_per_public_history",
            "one_step_dcfr_regret_vertex_per_public_history",
            "converged_one_seat_row_growth_proposal",
        ),
        "direction_count_per_context": 4,
        "direction_regret_endpoint_rule": (
            "dcfr_variant_warm_mass_1_one_step_then_per_sorted_public_history_"
            "maximize_2_times_postdiscount_regret_minus_source_probability_"
            "with_legal_action_order_tie_break"
        ),
        "direction_regret_public_histories_in_order": (
            "p0:raise-to-2/p1:raise-to-4",
            "p0:raise-to-3/p1:raise-to-4",
            "root",
        ),
        "direction_generation_stage": (
            "inside_the_exclusive_confirmation_terminal_after_source_seal_and_"
            "before_factorized_sections"
        ),
        "evidence_stage": (
            "source_sealed_before_any_fresh_legal_h4_confirmation_target_value"
        ),
        "expected_sections": 32,
        "failure_interpretation": (
            "any_context_direction_target_semantic_infrastructure_or_byte_"
            "failure_rejects_the_complete_confirmation_without_drop_reseed_"
            "retry_gate_repair_or_partial_pass"
        ),
        "fan_piece_guard": 256,
        "identity_authority": "total_function_only",
        "maximum_artifact_bytes": 8_388_608,
        "maximum_campaign_seconds": 600.0,
        "maximum_explicit_tree_nodes": 100_000,
        "maximum_section_subject_seconds": 60.0,
        "maximum_subject_seconds": 360.0,
        "point_authority": "two_pass_factorized_directional_face",
        "population_version": _POPULATION_VERSION,
        "private_width": ADR0360_CONFIRMATION_PRIVATE_WIDTH,
        "ray_authority": "exact_selector_normal_fan",
        "required_raw_section_fields": (
            "fan.complete_cells_segments_points_and_tie_measures",
            "cell_gain_rows.complete_tapes_domains_intercepts_and_slopes",
            "samples.every_scale_state_active_row_and_complete_face",
            "samples.face.every_information_set_factor_parent_action_support_"
            "local_slope_extrema_and_work_field",
            "source_face.complete_factors_tapes_cardinalities_algebra_and_work",
            "pieces.complete_domains_witnesses_tapes_affine_rows_states_and_"
            "cardinalities",
            "selector_window.complete_float_hex_switch_identity_and_call_counts",
            "epigraph.every_fan_row_by_every_point_exact_residual",
        ),
        "response_tape_materialization_limit": 0,
        "result_path_policy": "exclusive_absent_path_retain_first_terminal_only",
        "row_growth_guard": 0.25,
        "row_growth_acceptance": (
            "converged",
            "candidate_feasible",
            "exact_candidate_feasible",
            "exact_converged",
            "all_response_rows_exactly_rebound",
            "maximum_master_duality_gap_at_most_1e-8",
            "maximum_master_constraint_violation_at_most_1e-8",
        ),
        "row_growth_max_iterations": 128,
        "row_growth_primitive": "audit_one_seat_row_growth_v1",
        "row_growth_tolerance": 1e-10,
        "selector_margin_allowance": 1e-12,
        "source_policy_version": _SOURCE_POLICY_VERSION,
        "target_players": (0, 1),
        "tie_dispatch": (
            "exact_source_tie_to_factorized_maximum_envelope_singleton_to_"
            "selector_window_v2_or_fail_closed"
        ),
        "weight_denominator": ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR,
    }
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _card_sort_key(card: str) -> int:
    return parse_card(card)


def _canonical_hole_strings(cards: tuple[str, str]) -> tuple[str, str]:
    first, second = sorted(cards, key=_card_sort_key)
    return first, second


def _candidate_deck(candidate_ordinal: int) -> tuple[str, ...]:
    if isinstance(candidate_ordinal, bool) or not isinstance(candidate_ordinal, int):
        raise TypeError("confirmation candidate ordinal must be an integer")
    if candidate_ordinal < 0:
        raise ValueError("confirmation candidate ordinal must be nonnegative")
    prefix = (
        f"{ADR0360_CONFIRMATION_SEED}|candidate={candidate_ordinal}|card="
    )
    return tuple(
        sorted(
            _DECK,
            key=lambda card: (
                sha256(f"{prefix}{card}".encode("ascii")).digest(),
                card,
            ),
        )
    )


def _candidate_weights(candidate_ordinal: int) -> tuple[tuple[int, ...], ...]:
    weights = [1] * 16
    for allocation in range(48):
        digest = sha256(
            (
                f"{ADR0360_CONFIRMATION_SEED}|candidate={candidate_ordinal}|"
                f"weight-allocation={allocation}"
            ).encode("ascii")
        ).digest()
        weights[int.from_bytes(digest[:8], "big") % len(weights)] += 1
    if sum(weights) != ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR:
        raise AssertionError("confirmation weight construction lost dyadic mass")
    return tuple(
        tuple(weights[row * 4 : (row + 1) * 4]) for row in range(4)
    )


def checked_to_confirmation_river() -> NoLimitBettingState:
    """Reproduce the legal two-live-seat checked-to river entry state."""

    state = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=(6,) * 6,
        small_blind=1,
        big_blind=2,
    )
    for expected_seat, action in (
        (3, FOLD),
        (4, FOLD),
        (5, FOLD),
        (0, FOLD),
        (1, CALL),
        (2, CHECK),
    ):
        if state.acting_seat != expected_seat:
            raise AssertionError("confirmation preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if state.street is not street:
            raise AssertionError("confirmation street order drifted")
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    if state.acting_seat != 1:
        raise AssertionError("confirmation first river actor drifted")
    state = state.apply_action(CHECK)
    state.assert_invariants()
    return state


def _semantic_payload(
    *,
    board: tuple[str, ...],
    root_hands: tuple[tuple[str, str], ...],
    responder_hands: tuple[tuple[str, str], ...],
    joint_weight_numerators: tuple[tuple[int, ...], ...],
    joint_weight_denominator: int,
) -> dict[str, object]:
    probabilities = tuple(
        tuple(Fraction(value, joint_weight_denominator) for value in row)
        for row in joint_weight_numerators
    )
    return {
        "betting_state_sha256": public_betting_state_sha256(
            checked_to_confirmation_river()
        ),
        "board": list(board),
        "joint_probabilities": [
            [
                {
                    "denominator": probability.denominator,
                    "numerator": probability.numerator,
                }
                for probability in row
            ]
            for row in probabilities
        ],
        "responder_hands": [list(hand) for hand in responder_hands],
        "root_hands": [list(hand) for hand in root_hands],
        "version": _SEMANTIC_KEY_VERSION,
    }


@dataclass(frozen=True, slots=True)
class FreshLegalH4ConfirmationContext:
    """One structural, target-value-unopened h4 confirmation context."""

    context_id: str
    candidate_ordinal: int
    board: tuple[str, ...]
    root_hands: tuple[tuple[str, str], ...]
    responder_hands: tuple[tuple[str, str], ...]
    joint_weight_numerators: tuple[tuple[int, ...], ...]
    joint_weight_denominator: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.candidate_ordinal, bool)
            or not isinstance(self.candidate_ordinal, int)
        ):
            raise TypeError("confirmation candidate ordinal must be an integer")
        expected_id = f"adr0360-legal-h4-confirmation-{self.candidate_ordinal:02d}"
        if self.context_id != expected_id or self.candidate_ordinal < 0:
            raise ValueError("confirmation context identity drifted")
        if len(self.board) != 5:
            raise ValueError("confirmation board must contain five cards")
        if len(self.root_hands) != ADR0360_CONFIRMATION_PRIVATE_WIDTH:
            raise ValueError("confirmation root private width drifted")
        if len(self.responder_hands) != ADR0360_CONFIRMATION_PRIVATE_WIDTH:
            raise ValueError("confirmation responder private width drifted")
        cards = (
            *self.board,
            *(card for hand in self.root_hands for card in hand),
            *(card for hand in self.responder_hands for card in hand),
        )
        parsed = tuple(parse_card(card) for card in cards)
        if len(set(parsed)) != 21:
            raise ValueError("confirmation context cards are not collision-free")
        if tuple(format_card(card) for card in parsed) != cards:
            raise ValueError("confirmation context cards are not canonical tokens")
        if self.board != tuple(sorted(self.board, key=_card_sort_key)):
            raise ValueError("confirmation board is not canonical")
        for hand in (*self.root_hands, *self.responder_hands):
            if len(hand) != 2 or hand != _canonical_hole_strings(hand):
                raise ValueError("confirmation private hand is not canonical")
        if (
            self.joint_weight_denominator
            != ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR
        ):
            raise ValueError("confirmation weight denominator drifted")
        if (
            len(self.joint_weight_numerators) != 4
            or any(len(row) != 4 for row in self.joint_weight_numerators)
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for row in self.joint_weight_numerators
                for value in row
            )
        ):
            raise ValueError("confirmation joint weights are not positive h4 rows")
        if (
            sum(value for row in self.joint_weight_numerators for value in row)
            != self.joint_weight_denominator
        ):
            raise ValueError("confirmation joint weights do not sum to their denominator")

    @property
    def semantic_payload(self) -> dict[str, object]:
        return _semantic_payload(
            board=self.board,
            root_hands=self.root_hands,
            responder_hands=self.responder_hands,
            joint_weight_numerators=self.joint_weight_numerators,
            joint_weight_denominator=self.joint_weight_denominator,
        )

    @property
    def semantic_digest(self) -> str:
        return _canonical_sha256(self.semantic_payload)

    def build_game(self) -> LegalHeadsUpRiverContinuation:
        deals = tuple(
            (
                RiverDeal(make_hole(*root), make_hole(*responder)),
                float(self.joint_weight_numerators[root_index][responder_index]),
            )
            for root_index, root in enumerate(self.root_hands)
            for responder_index, responder in enumerate(self.responder_hands)
        )
        return LegalHeadsUpRiverContinuation(
            board=parse_cards(*self.board),
            base_state=checked_to_confirmation_river(),
            deals=deals,
        )


def _context_from_candidate(candidate_ordinal: int) -> FreshLegalH4ConfirmationContext:
    deck = _candidate_deck(candidate_ordinal)
    board = tuple(sorted(deck[:5], key=_card_sort_key))
    root_cards = deck[5:13]
    responder_cards = deck[13:21]
    roots = tuple(
        _canonical_hole_strings((root_cards[index], root_cards[index + 1]))
        for index in range(0, 8, 2)
    )
    responders = tuple(
        _canonical_hole_strings(
            (responder_cards[index], responder_cards[index + 1])
        )
        for index in range(0, 8, 2)
    )
    return FreshLegalH4ConfirmationContext(
        context_id=f"adr0360-legal-h4-confirmation-{candidate_ordinal:02d}",
        candidate_ordinal=candidate_ordinal,
        board=board,
        root_hands=roots,
        responder_hands=responders,
        joint_weight_numerators=_candidate_weights(candidate_ordinal),
        joint_weight_denominator=ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR,
    )


def _rotated(values: tuple[float, ...], offset: int) -> tuple[float, ...]:
    index = offset % len(values)
    return (*values[index:], *values[:index])


def legal_h4_confirmation_source_policy(
    context: FreshLegalH4ConfirmationContext,
    game: LegalHeadsUpRiverContinuation | None = None,
) -> Policy:
    """Build the deterministic full-support source without evaluating utility."""

    if not isinstance(context, FreshLegalH4ConfirmationContext):
        raise TypeError("confirmation source requires its nominal context type")
    if game is None:
        game = context.build_game()
    if game.provenance_digest != context.build_game().provenance_digest:
        raise ValueError("confirmation source game does not match its context")
    policy: Policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            try:
                template = _SOURCE_TEMPLATES[len(actions)]
            except KeyError as exc:
                raise ValueError(
                    "confirmation source found an unexpected action width"
                ) from exc
            digest = sha256(
                (
                    f"{_SOURCE_POLICY_VERSION}|context={context.semantic_digest}|"
                    f"player={player}|{key}"
                ).encode("utf-8")
            ).digest()
            probabilities = _rotated(template, int.from_bytes(digest[:2], "big"))
            policy[key] = dict(zip(actions, probabilities, strict=True))
    return policy


def policy_sha256(policy: Mapping[str, Mapping[object, float]]) -> str:
    return _canonical_sha256(
        [
            {
                "actions": [
                    {
                        "action": str(action),
                        "probability_hex": float(probability).hex(),
                    }
                    for action, probability in sorted(
                        policy[key].items(), key=lambda item: str(item[0])
                    )
                ],
                "information_key": key,
            }
            for key in sorted(policy)
        ]
    )


def _development_semantic_digest() -> str:
    from .legal_h4_selector_fixture import (
        BOARD,
        JOINT_WEIGHT_DENOMINATOR,
        JOINT_WEIGHT_NUMERATORS,
        RESPONDER_HANDS,
        ROOT_HANDS,
    )

    payload = _semantic_payload(
        board=tuple(sorted(BOARD, key=_card_sort_key)),
        root_hands=tuple(_canonical_hole_strings(hand) for hand in ROOT_HANDS),
        responder_hands=tuple(_canonical_hole_strings(hand) for hand in RESPONDER_HANDS),
        joint_weight_numerators=JOINT_WEIGHT_NUMERATORS,
        joint_weight_denominator=JOINT_WEIGHT_DENOMINATOR,
    )
    return _canonical_sha256(payload)


@dataclass(frozen=True, slots=True)
class FreshLegalH4ConfirmationPopulation:
    """Exact ordered value-unopened population and exclusion identity."""

    version: str
    mechanism_source_commit: str
    seed: str
    development_semantic_digest: str
    contexts: tuple[FreshLegalH4ConfirmationContext, ...]

    def __post_init__(self) -> None:
        if self.version != _POPULATION_VERSION:
            raise ValueError("confirmation population version drifted")
        if self.mechanism_source_commit != ADR0360_MECHANISM_SOURCE_COMMIT:
            raise ValueError("confirmation mechanism source commit drifted")
        if self.seed != ADR0360_CONFIRMATION_SEED:
            raise ValueError("confirmation seed drifted")
        if self.development_semantic_digest != _development_semantic_digest():
            raise ValueError("confirmation development exclusion drifted")
        if (
            not isinstance(self.contexts, tuple)
            or len(self.contexts) != ADR0360_CONFIRMATION_CONTEXT_COUNT
            or any(
                not isinstance(context, FreshLegalH4ConfirmationContext)
                for context in self.contexts
            )
        ):
            raise TypeError("confirmation population must contain four contexts")
        if tuple(context.candidate_ordinal for context in self.contexts) != tuple(
            range(ADR0360_CONFIRMATION_CONTEXT_COUNT)
        ):
            raise ValueError("confirmation population is not the first four candidates")
        digests = tuple(context.semantic_digest for context in self.contexts)
        if len(set(digests)) != len(digests):
            raise ValueError("confirmation population repeats a semantic context")
        if self.development_semantic_digest in digests:
            raise ValueError("confirmation population overlaps the development fixture")

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "contexts": [
                {
                    "candidate_ordinal": context.candidate_ordinal,
                    "context_id": context.context_id,
                    "semantic_digest": context.semantic_digest,
                    "semantic_payload": context.semantic_payload,
                    "source_policy_sha256": policy_sha256(
                        legal_h4_confirmation_source_policy(context)
                    ),
                }
                for context in self.contexts
            ],
            "development_semantic_digest": self.development_semantic_digest,
            "mechanism_source_commit": self.mechanism_source_commit,
            "protocol_sha256": ADR0360_CONFIRMATION_PROTOCOL_SHA256,
            "seed": self.seed,
            "version": self.version,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.canonical_payload)

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


ADR0360_CONFIRMATION_PROTOCOL_SHA256 = _canonical_sha256(
    dict(ADR0360_CONFIRMATION_PROTOCOL)
)


def build_adr0360_confirmation_population() -> FreshLegalH4ConfirmationPopulation:
    """Return the first four candidates; never filter, skip, or replace one."""

    return FreshLegalH4ConfirmationPopulation(
        version=_POPULATION_VERSION,
        mechanism_source_commit=ADR0360_MECHANISM_SOURCE_COMMIT,
        seed=ADR0360_CONFIRMATION_SEED,
        development_semantic_digest=_development_semantic_digest(),
        contexts=tuple(
            _context_from_candidate(candidate_ordinal)
            for candidate_ordinal in range(ADR0360_CONFIRMATION_CONTEXT_COUNT)
        ),
    )


__all__ = [
    "ADR0360_CONFIRMATION_CONTEXT_COUNT",
    "ADR0360_CONFIRMATION_PRIVATE_WIDTH",
    "ADR0360_CONFIRMATION_PROTOCOL",
    "ADR0360_CONFIRMATION_PROTOCOL_SHA256",
    "ADR0360_CONFIRMATION_SEED",
    "ADR0360_CONFIRMATION_SEED_SHA256",
    "ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR",
    "ADR0360_MECHANISM_SOURCE_COMMIT",
    "FreshLegalH4ConfirmationContext",
    "FreshLegalH4ConfirmationPopulation",
    "build_adr0360_confirmation_population",
    "checked_to_confirmation_river",
    "legal_h4_confirmation_source_policy",
    "policy_sha256",
]
