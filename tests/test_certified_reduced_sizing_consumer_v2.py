from __future__ import annotations

import ast
import importlib.util
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import pontius.certified_reduced_sizing_consumer_v2 as consumer
from pontius.certified_reduced_sizing_consumer_v2 import (
    ADR0321_CONSUMER_PROTOCOL_SHA256,
    CallerFallbackDispositionV2,
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
    CertifiedSizingConsumerRejectionReasonV2,
    CertifiedSizingConsumerStageV2,
    KernelRaiseToTotal,
    LegalRaiseSetScope,
    ReducedBetIncrement,
    ReducedSizingResponseModel,
    consume_certified_reduced_sizing_v2,
    verify_adr0321_consumer_source_and_dependencies,
)
from pontius.no_limit_betting import BettingStreet, NoLimitBettingState


_PROBABILITIES = (
    (Fraction(1, 4), Fraction(1, 4)),
    (Fraction(1, 4), Fraction(1, 4)),
)
_SIGNS = ((1, 1), (-1, -1))


def _two_live_state(
    *,
    pot: int = 10,
    actor_stack: int = 20,
    responder_stack: int = 20,
    street_contribution: int = 0,
    street: BettingStreet = BettingStreet.RIVER,
) -> NoLimitBettingState:
    actor_total = pot // 2
    responder_total = pot - actor_total
    if street_contribution > min(actor_total, responder_total):
        raise ValueError("test street contribution exceeds its hand contribution")
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=street,
        starting_stacks=(
            actor_stack + actor_total,
            responder_stack + responder_total,
            2,
            2,
            2,
            2,
        ),
        stacks=(actor_stack, responder_stack, 2, 2, 2, 2),
        total_contributions=(actor_total, responder_total, 0, 0, 0, 0),
        street_contributions=(
            street_contribution,
            street_contribution,
            0,
            0,
            0,
            0,
        ),
        folded=(False, False, True, True, True, True),
        pending_seats=(0, 1),
        last_full_raise_size=2,
        acted_at_bet=(None, None, None, None, None, None),
    )


def _three_live_state() -> NoLimitBettingState:
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=BettingStreet.RIVER,
        starting_stacks=(24, 24, 24, 2, 2, 2),
        stacks=(20, 20, 20, 2, 2, 2),
        total_contributions=(4, 4, 4, 0, 0, 0),
        street_contributions=(0, 0, 0, 0, 0, 0),
        folded=(False, False, False, True, True, True),
        pending_seats=(0, 1, 2),
        last_full_raise_size=2,
        acted_at_bet=(None, None, None, None, None, None),
    )


def _facing_bet_state() -> NoLimitBettingState:
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=BettingStreet.RIVER,
        starting_stacks=(24, 24, 2, 2, 2, 2),
        stacks=(20, 18, 2, 2, 2, 2),
        total_contributions=(4, 6, 0, 0, 0, 0),
        street_contributions=(0, 2, 0, 0, 0, 0),
        folded=(False, False, True, True, True, True),
        pending_seats=(0, 1),
        last_full_raise_size=2,
        acted_at_bet=(None, 0, None, None, None, None),
    )


def _request(
    state: NoLimitBettingState,
    *,
    amounts: tuple[int, ...] | None = None,
    scope: LegalRaiseSetScope | None = None,
    probabilities: tuple[tuple[Fraction, ...], ...] = _PROBABILITIES,
    signs: tuple[tuple[int, ...], ...] = _SIGNS,
    context_id: str = "adr0321-unsealed-toy",
) -> CertifiedReducedSizingRequestV2:
    bounds = state.legal_decision().raise_bounds
    if bounds is None:
        raise ValueError("test request state has no legal raise")
    complete = tuple(range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1))
    selected = complete if amounts is None else amounts
    selected_scope = (
        LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE
        if scope is None and selected == complete
        else LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET
        if scope is None
        else scope
    )
    return CertifiedReducedSizingRequestV2(
        context_id=context_id,
        betting=state,
        response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        legal_raise_scope=selected_scope,
        legal_raise_to_totals=tuple(KernelRaiseToTotal(value) for value in selected),
        joint_probabilities=probabilities,
        showdown_signs=signs,
    )


def _forbidden_backend(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("backend must not be invoked")


class CertifiedReducedSizingConsumerV2SourceTests(unittest.TestCase):
    def test_source_seal_protocol_and_import_boundary_are_exact(self) -> None:
        from pontius.certified_reduced_sizing_consumer_v2_seal import (
            ADR0321_CONSUMER_PROTOCOL_SHA256 as sealed_protocol,
            ADR0321_CONSUMER_SOURCE_MANIFEST,
        )

        source_digest = verify_adr0321_consumer_source_and_dependencies()
        self.assertEqual(
            source_digest,
            ADR0321_CONSUMER_SOURCE_MANIFEST[
                "certified_reduced_sizing_consumer_v2.py"
            ],
        )
        self.assertEqual(ADR0321_CONSUMER_PROTOCOL_SHA256, sealed_protocol)
        with self.assertRaises(TypeError):
            ADR0321_CONSUMER_SOURCE_MANIFEST[  # type: ignore[index]
                "certified_reduced_sizing_consumer_v2.py"
            ] = "0" * 64

        source_path = Path(consumer.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        referenced_names: set[str] = set()
        attributes: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                referenced_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                referenced_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
        forbidden_modules = {
            "linear_program",
            "reduced_river_sizing_oracle",
            "native_simplex_audit_runner",
            "fresh_capacity_filling_qualification",
            "capacity_filling_action_abstraction",
            "collision_repair_action_abstraction",
            "legal_action_abstraction",
        }
        self.assertTrue(imported.isdisjoint(forbidden_modules))
        self.assertNotIn("BettingAction", referenced_names)
        self.assertNotIn("raise_to", referenced_names)
        self.assertNotIn("apply_action", attributes)

        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "consumer.py"
            normalized = source_path.read_bytes().replace(b"\r\n", b"\n")
            copy.write_bytes(normalized.replace(b"\n", b"\r\n"))
            self.assertEqual(
                consumer.canonical_lf_source_sha256(copy),
                source_digest,
            )

        legacy = source_path.with_name("reduced_river_sizing_oracle.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("certified_reduced_sizing_consumer_v2", legacy)

    def test_raise_to_and_increment_are_nominally_distinct(self) -> None:
        self.assertNotEqual(KernelRaiseToTotal(5), ReducedBetIncrement(5))
        with self.assertRaises(TypeError):
            CertifiedReducedSizingRequestV2(
                context_id="wrong-nominal-type",
                betting=_two_live_state(),
                response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
                legal_raise_scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
                legal_raise_to_totals=(ReducedBetIncrement(2),),  # type: ignore[arg-type]
                joint_probabilities=_PROBABILITIES,
                showdown_signs=_SIGNS,
            )

    def test_unsupported_game_shapes_reject_before_backend(self) -> None:
        states = (
            _three_live_state(),
            _facing_bet_state(),
            _two_live_state(pot=9),
            _two_live_state(street=BettingStreet.TURN),
            _two_live_state(actor_stack=20, responder_stack=10),
        )
        for state in states:
            with self.subTest(state=state):
                result = consume_certified_reduced_sizing_v2(
                    _request(state),
                    linprog_function=_forbidden_backend,
                )
                self.assertIsInstance(result, CertifiedReducedSizingRejectedV2)
                assert isinstance(result, CertifiedReducedSizingRejectedV2)
                self.assertEqual(
                    result.reason,
                    CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
                )
                self.assertEqual(result.public_highs_ds_invocation_count, 0)
                self.assertIsNone(result.emitted_action)

    def test_illegal_raise_sets_and_scope_claims_reject_before_backend(self) -> None:
        state = _two_live_state()
        bounds = state.legal_decision().raise_bounds
        assert bounds is not None
        cases = (
            ((bounds.minimum_raise_to, bounds.maximum_raise_to - 1), None),
            ((bounds.minimum_raise_to + 1, bounds.maximum_raise_to), None),
            (
                (bounds.minimum_raise_to, bounds.maximum_raise_to),
                LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
            ),
            (
                tuple(range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1)),
                LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
            ),
            (
                (
                    bounds.minimum_raise_to,
                    bounds.minimum_raise_to,
                    bounds.maximum_raise_to,
                ),
                LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
            ),
        )
        for amounts, scope in cases:
            with self.subTest(amounts=amounts, scope=scope):
                result = consume_certified_reduced_sizing_v2(
                    _request(state, amounts=amounts, scope=scope),
                    linprog_function=_forbidden_backend,
                )
                self.assertIsInstance(result, CertifiedReducedSizingRejectedV2)
                assert isinstance(result, CertifiedReducedSizingRejectedV2)
                self.assertEqual(
                    result.reason,
                    CertifiedSizingConsumerRejectionReasonV2.STALE_OR_ILLEGAL_RAISE_SET,
                )
                self.assertEqual(result.public_highs_ds_invocation_count, 0)

    def test_invalid_exact_range_context_rejects_before_backend(self) -> None:
        result = consume_certified_reduced_sizing_v2(
            _request(
                _two_live_state(),
                amounts=(2, 20),
                probabilities=((Fraction(1, 2),),),
                signs=((1,),),
            ),
            linprog_function=_forbidden_backend,
        )
        self.assertIsInstance(result, CertifiedReducedSizingRejectedV2)
        assert isinstance(result, CertifiedReducedSizingRejectedV2)
        self.assertEqual(
            result.reason,
            CertifiedSizingConsumerRejectionReasonV2.INVALID_EXACT_CONTEXT,
        )
        self.assertEqual(result.public_highs_ds_invocation_count, 0)

    def test_source_and_runtime_drift_reject_before_backend(self) -> None:
        request = _request(_two_live_state(), amounts=(2, 20))
        cases = (
            (
                "verify_adr0321_consumer_source_and_dependencies",
                CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION,
                CertifiedSizingConsumerRejectionReasonV2.SOURCE_DRIFT,
            ),
            (
                "verify_adr0318_source_and_dependencies",
                CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION,
                CertifiedSizingConsumerRejectionReasonV2.SOURCE_DRIFT,
            ),
            (
                "verify_adr0318_runtime_identity",
                CertifiedSizingConsumerStageV2.RUNTIME_VERIFICATION,
                CertifiedSizingConsumerRejectionReasonV2.RUNTIME_DRIFT,
            ),
        )
        for target, stage, reason in cases:
            with self.subTest(target=target), patch.object(
                consumer,
                target,
                side_effect=RuntimeError("synthetic identity drift"),
            ):
                result = consume_certified_reduced_sizing_v2(
                    request,
                    linprog_function=_forbidden_backend,
                )
                self.assertIsInstance(result, CertifiedReducedSizingRejectedV2)
                assert isinstance(result, CertifiedReducedSizingRejectedV2)
                self.assertEqual(result.stage, stage)
                self.assertEqual(result.reason, reason)
                self.assertEqual(result.public_highs_ds_invocation_count, 0)
                self.assertEqual(
                    result.fallback_disposition,
                    CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK,
                )
                self.assertIsNone(result.emitted_action)


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class CertifiedReducedSizingConsumerV2SolverTests(unittest.TestCase):
    def test_complete_scope_accepts_and_human_label_is_not_semantic(self) -> None:
        state = _two_live_state(actor_stack=4, responder_stack=20)
        first = consume_certified_reduced_sizing_v2(
            _request(state, context_id="unsealed-label-a"),
        )
        second = consume_certified_reduced_sizing_v2(
            _request(state, context_id="unsealed-label-b"),
        )
        self.assertIsInstance(first, CertifiedReducedSizingAcceptedV2)
        self.assertIsInstance(second, CertifiedReducedSizingAcceptedV2)
        assert isinstance(first, CertifiedReducedSizingAcceptedV2)
        assert isinstance(second, CertifiedReducedSizingAcceptedV2)
        self.assertEqual(first.legal_raise_scope, LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE)
        self.assertEqual(
            tuple(value.chips for value in first.legal_raise_to_totals),
            (2, 3, 4),
        )
        self.assertEqual(first.request_sha256, second.request_sha256)
        self.assertEqual(first.legal_raise_set_sha256, second.legal_raise_set_sha256)
        self.assertNotEqual(first.context_id, second.context_id)

    def test_nonzero_contribution_maps_totals_to_distinct_increments(self) -> None:
        state = _two_live_state(street_contribution=3)
        result = consume_certified_reduced_sizing_v2(
            _request(state, amounts=(5, 23)),
        )
        self.assertIsInstance(result, CertifiedReducedSizingAcceptedV2)
        assert isinstance(result, CertifiedReducedSizingAcceptedV2)
        self.assertEqual(
            result.legal_raise_to_totals,
            (KernelRaiseToTotal(5), KernelRaiseToTotal(23)),
        )
        self.assertEqual(
            result.reduced_bet_increments,
            (ReducedBetIncrement(2), ReducedBetIncrement(20)),
        )
        self.assertEqual(result.solution.bet_sizes, (2, 20))
        self.assertEqual(result.public_highs_ds_invocation_count, 1)
        self.assertEqual(
            result.fallback_disposition,
            CallerFallbackDispositionV2.NOT_REQUIRED_RESEARCH_RESULT,
        )
        self.assertIsNone(result.emitted_action)

    def test_accepted_record_is_an_exact_view_of_certified_solution(self) -> None:
        request = _request(_two_live_state(), amounts=(2, 20))
        result = consume_certified_reduced_sizing_v2(request)
        self.assertIsInstance(result, CertifiedReducedSizingAcceptedV2)
        assert isinstance(result, CertifiedReducedSizingAcceptedV2)
        solution = result.solution
        self.assertEqual(result.exact_opening_policy, solution.exact_opening_policy)
        self.assertEqual(result.responder_best_actions, solution.responder_best_actions)
        self.assertEqual(
            result.feasible_behavioral_lower_bound_chips,
            solution.feasible_behavioral_lower_bound_chips,
        )
        self.assertEqual(
            result.certified_upper_bound_chips,
            solution.certified_upper_bound_chips,
        )
        self.assertEqual(
            result.signed_certificate_gap_chips,
            solution.signed_certificate_gap_chips,
        )
        self.assertEqual(result.certified_gap_chips, solution.certified_gap_chips)
        self.assertLessEqual(result.certified_gap_chips, 1e-9)
        for digest in (
            result.request_sha256,
            result.public_state_sha256,
            result.legal_raise_set_sha256,
            result.consumer_source_sha256,
        ):
            self.assertEqual(len(digest), 64)

        with self.assertRaisesRegex(ValueError, "different reduced bet increments"):
            replace(
                result,
                reduced_bet_increments=(
                    ReducedBetIncrement(3),
                    ReducedBetIncrement(20),
                ),
            )
        with self.assertRaisesRegex(ValueError, "rebound exact request"):
            replace(
                result,
                legal_raise_to_totals=(
                    KernelRaiseToTotal(3),
                    KernelRaiseToTotal(20),
                ),
            )

    def test_backend_exception_is_typed_once_and_preserves_its_cause(self) -> None:
        def exploding_backend(*args: object, **kwargs: object) -> object:
            del args, kwargs
            raise LookupError("synthetic public backend failure")

        result = consume_certified_reduced_sizing_v2(
            _request(_two_live_state(), amounts=(2, 20)),
            linprog_function=exploding_backend,
        )
        self.assertIsInstance(result, CertifiedReducedSizingRejectedV2)
        assert isinstance(result, CertifiedReducedSizingRejectedV2)
        self.assertEqual(result.stage, CertifiedSizingConsumerStageV2.CERTIFIED_ADAPTER)
        self.assertEqual(
            result.reason,
            CertifiedSizingConsumerRejectionReasonV2.ADAPTER_REJECTED,
        )
        self.assertEqual(result.public_highs_ds_invocation_count, 1)
        self.assertEqual(
            tuple(value.type_name for value in result.exception_chain),
            ("CertifiedSizingAdapterError", "LookupError"),
        )
        self.assertIn("synthetic public backend failure", result.exception_chain[-1].message)
        self.assertIsNone(result.emitted_action)

    def test_corrupt_public_results_reject_after_exactly_one_call(self) -> None:
        import scipy.optimize

        def backend_for(mutation: str):
            def mutated(*args: object, **kwargs: object) -> object:
                result = scipy.optimize.linprog(*args, **kwargs)
                if mutation == "status":
                    result.success = False
                    result.status = 1
                elif mutation == "shape":
                    result.x = result.x[:-1]
                elif mutation == "nan":
                    result.x[0] = float("nan")
                elif mutation == "objective":
                    result.fun += 0.01
                elif mutation == "dual":
                    result.ineqlin.marginals = None
                elif mutation == "certificate":
                    result.ineqlin.marginals[:] = 0.0
                else:  # pragma: no cover - test construction guard
                    raise AssertionError("unknown corruption")
                return result

            return mutated

        for mutation in ("status", "shape", "nan", "objective", "dual", "certificate"):
            with self.subTest(mutation=mutation):
                result = consume_certified_reduced_sizing_v2(
                    _request(_two_live_state(), amounts=(2, 20)),
                    linprog_function=backend_for(mutation),
                )
                self.assertIsInstance(result, CertifiedReducedSizingRejectedV2)
                assert isinstance(result, CertifiedReducedSizingRejectedV2)
                self.assertEqual(
                    result.reason,
                    CertifiedSizingConsumerRejectionReasonV2.ADAPTER_REJECTED,
                )
                self.assertEqual(result.public_highs_ds_invocation_count, 1)
                self.assertIsNone(result.emitted_action)


if __name__ == "__main__":
    unittest.main()
