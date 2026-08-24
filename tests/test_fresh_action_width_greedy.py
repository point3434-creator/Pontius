from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_greedy as greedy
from pontius.certified_reduced_sizing_consumer_v2 import (
    ADR0321_CONSUMER_PROTOCOL_SHA256,
    _bind_request,
    canonical_lf_source_sha256,
)
from pontius.certified_reduced_sizing_consumer_v2_seal import (
    ADR0321_CONSUMER_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_greedy import (
    ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
    ADR0323_GREEDY_ARM_COUNT,
    ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH,
    ADR0323_GREEDY_EXECUTED_CALL_COUNT,
    ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH,
    ADR0323_GREEDY_TRANSITION_COUNT,
    ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH,
    ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT,
    ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT,
    ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR,
    CertifiedGreedyTeacherExcessInterval,
    ClosedFiniteBlockPhase,
    ConservativeAggregateRecoveryInterval,
    GreedyCertifiedValueEvidence,
    GreedyRunnerException,
    GreedyRunnerRejected,
    GreedyRunnerStage,
    GreedyWidthGateResult,
    MaximumNormalizedFullRegretLimit,
    MaximumNormalizedTeacherExcessLimit,
    MeanNormalizedFullRegretLimit,
    MeanNormalizedTeacherExcessLimit,
    MinimumAggregateRecoveryFloor,
    OpponentResponseAction,
    OwnRaiseBlockIdentity,
    build_adr0323_closed_finite_block_greedy_schedule,
    build_closed_finite_block_candidate,
    canonical_greedy_result_bytes,
    certified_closed_finite_block_price,
    certified_greedy_teacher_excess,
    closed_finite_block_greedy_protocol_sha256,
    conservative_aggregate_recovery,
    normalize_full_regret,
    retain_greedy_result,
    run_adr0323_closed_finite_block_greedy_development,
    run_and_retain_adr0323_closed_finite_block_greedy_development,
    select_greedy_candidate,
    verify_adr0329_greedy_schedule,
    verify_adr0329_greedy_source_and_dependencies,
)
from pontius.fresh_action_width_greedy_seal import (
    ADR0329_GREEDY_PROTOCOL_SHA256,
    ADR0329_GREEDY_SCHEDULE_SHA256,
    ADR0329_GREEDY_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_qualification import (
    CertifiedChipRegretInterval,
    CertifiedChipValueInterval,
)
from pontius.fresh_action_width_structures import PrivateRangeWidth


_ROOT = Path(__file__).parents[1]


def _forbidden_consumer(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("value-free greedy construction reached the consumer")


def _evidence(
    task: greedy.GreedySubsetTask,
    lower: float,
    upper: float,
) -> GreedyCertifiedValueEvidence:
    bound = _bind_request(task.request)
    signed_gap = upper - lower
    result = GreedyCertifiedValueEvidence(
        task_sha256=task.digest,
        request_sha256=bound.request_sha256,
        public_state_sha256=bound.public_state_sha256,
        legal_raise_set_sha256=bound.legal_raise_set_sha256,
        linear_program_sha256=bound.linear_program_sha256,
        response_row_set_sha256=task.response_row_set.digest,
        consumer_source_sha256=ADR0321_CONSUMER_SOURCE_MANIFEST[
            "certified_reduced_sizing_consumer_v2.py"
        ],
        consumer_protocol_sha256=ADR0321_CONSUMER_PROTOCOL_SHA256,
        public_highs_ds_invocation_count=1,
        raise_to_totals=tuple(
            value.chips for value in bound.legal_raise_to_totals
        ),
        reduced_bet_increments=tuple(
            value.chips for value in bound.reduced_bet_increments
        ),
        feasible_behavioral_lower_bound_chips=lower,
        certified_upper_bound_chips=upper,
        signed_certificate_gap_chips=signed_gap,
        certified_gap_chips=max(0.0, signed_gap),
    )
    result.verify_task(task)
    return result


class FreshActionWidthGreedyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with patch.object(
            greedy,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_consumer,
        ):
            cls.schedule = build_adr0323_closed_finite_block_greedy_schedule()

    def test_source_protocol_and_schedule_are_sealed(self) -> None:
        self.assertEqual(
            verify_adr0329_greedy_source_and_dependencies(),
            ADR0329_GREEDY_SOURCE_MANIFEST["fresh_action_width_greedy.py"],
        )
        self.assertEqual(
            closed_finite_block_greedy_protocol_sha256(),
            ADR0329_GREEDY_PROTOCOL_SHA256,
        )
        self.assertEqual(self.schedule.digest, ADR0329_GREEDY_SCHEDULE_SHA256)
        verify_adr0329_greedy_schedule(self.schedule)
        source_root = _ROOT / "src" / "pontius"
        actual = {
            name: canonical_lf_source_sha256(source_root / name)
            for name in ADR0329_GREEDY_SOURCE_MANIFEST
        }
        self.assertEqual(actual, ADR0329_GREEDY_SOURCE_MANIFEST)

    def test_complete_adaptive_graph_is_value_free_and_exact(self) -> None:
        self.assertEqual(len(self.schedule.tasks), ADR0323_GREEDY_ARM_COUNT)
        self.assertEqual(
            self.schedule.arm_counts_by_width,
            ADR0323_GREEDY_ARM_COUNTS_BY_WIDTH,
        )
        self.assertEqual(
            len(self.schedule.transitions),
            ADR0323_GREEDY_TRANSITION_COUNT,
        )
        self.assertEqual(
            self.schedule.transition_counts_by_target_width,
            ADR0323_GREEDY_TRANSITION_COUNTS_BY_TARGET_WIDTH,
        )
        self.assertEqual(
            self.schedule.executed_candidate_counts_by_target_width,
            ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH,
        )
        self.assertEqual(len({task.digest for task in self.schedule.tasks}), 2_479)
        self.assertEqual(
            len({transition.digest for transition in self.schedule.transitions}),
            7_848,
        )

        executed = 0
        observed_by_width = {3: 0, 4: 0, 5: 0, 6: 0}
        for panel_position in range(16):
            incumbent = self.schedule.initial_task(panel_position)
            executed += 1
            for target_width in range(3, 7):
                outgoing = self.schedule.outgoing(incumbent)
                self.assertEqual(
                    [value.candidate_position for value in outgoing],
                    list(range(len(outgoing))),
                )
                self.assertEqual(
                    [value.proposed_raise_to_total.chips for value in outgoing],
                    sorted(value.proposed_raise_to_total.chips for value in outgoing),
                )
                observed_by_width[target_width] += len(outgoing)
                executed += len(outgoing)
                incumbent = outgoing[0].augmented
        self.assertEqual(executed, ADR0323_GREEDY_EXECUTED_CALL_COUNT)
        self.assertEqual(
            tuple(sorted(observed_by_width.items())),
            ADR0323_GREEDY_EXECUTED_CANDIDATE_COUNTS_BY_TARGET_WIDTH,
        )

    def test_response_closure_is_semantic_not_a_row_count_coincidence(self) -> None:
        for task in self.schedule.tasks:
            self.assertEqual(
                task.response_row_set.row_count,
                task.raise_width.count * 4 * 2,
            )
            grouped = {
                (
                    row.raise_to_total.chips,
                    row.responder_private_type_index,
                ): set()
                for row in task.response_row_set.rows
            }
            for row in task.response_row_set.rows:
                grouped[
                    (row.raise_to_total.chips, row.responder_private_type_index)
                ].add(row.action)
            self.assertTrue(
                all(
                    actions
                    == {OpponentResponseAction.FOLD, OpponentResponseAction.CALL}
                    for actions in grouped.values()
                )
            )

        transition = self.schedule.transitions[0]
        self.assertEqual(len(transition.own_block.response_rows), 8)
        self.assertEqual(
            set(transition.incumbent.response_row_set.rows)
            | set(transition.own_block.response_rows),
            set(transition.augmented.response_row_set.rows),
        )
        corrupted_rows = list(transition.own_block.response_rows)
        corrupted_rows[-1] = replace(
            corrupted_rows[-1],
            action=OpponentResponseAction.FOLD,
        )
        with self.assertRaisesRegex(ValueError, "complete fold/call"):
            OwnRaiseBlockIdentity(
                context_semantic_digest=(
                    transition.own_block.context_semantic_digest
                ),
                raise_to_total=transition.own_block.raise_to_total,
                reduced_bet_increment=(
                    transition.own_block.reduced_bet_increment
                ),
                responder_private_range_width=(
                    transition.own_block.responder_private_range_width
                ),
                response_rows=tuple(corrupted_rows),
            )
        with self.assertRaisesRegex(ValueError, "phase order"):
            replace(
                transition,
                phase_order=(
                    ClosedFiniteBlockPhase.OWN_BLOCK_PROPOSAL,
                    ClosedFiniteBlockPhase.CERTIFIED_SOLVE,
                    ClosedFiniteBlockPhase.OPPONENT_RESPONSE_CLOSURE,
                ),
            )
        self.assertEqual(
            transition.phase_order,
            ADR0323_CLOSED_FINITE_BLOCK_PHASE_ORDER,
        )

    def test_standalone_identities_and_schedule_reject_well_shaped_drift(self) -> None:
        row_set = self.schedule.initial_task(0).response_row_set
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            replace(
                row_set,
                reduced_bet_increments=(
                    row_set.reduced_bet_increments[0],
                    row_set.reduced_bet_increments[0],
                ),
            )

        own_block = self.schedule.transitions[0].own_block
        with self.assertRaisesRegex(ValueError, "frozen h4"):
            replace(
                own_block,
                responder_private_range_width=PrivateRangeWidth(3),
            )

        tasks = list(self.schedule.tasks)
        tasks[1] = replace(tasks[1], subset_index=10_000)
        with self.assertRaisesRegex(ValueError, "ordered anchored-subset family"):
            replace(self.schedule, tasks=tuple(tasks))

    def test_selection_uses_lower_endpoint_then_exact_smaller_raise(self) -> None:
        incumbent_task = self.schedule.initial_task(0)
        transitions = self.schedule.outgoing(incumbent_task)[:3]
        incumbent = _evidence(incumbent_task, 0.0, 0.0)
        values = ((1.0, 1.1), (1.0, 9.0), (1.0, 2.0))
        candidates = tuple(
            build_closed_finite_block_candidate(
                transition=transition,
                incumbent=incumbent,
                augmented=_evidence(transition.augmented, lower, upper),
            )
            for transition, (lower, upper) in zip(
                transitions,
                values,
                strict=True,
            )
        )
        self.assertEqual(select_greedy_candidate(candidates), candidates[0])
        stronger = replace(
            candidates[2],
            augmented=_evidence(transitions[2].augmented, 1.01, 1.02),
            price=certified_closed_finite_block_price(
                incumbent=incumbent.value,
                augmented=CertifiedChipValueInterval(1.01, 1.02),
            ),
        )
        self.assertEqual(
            select_greedy_candidate((*candidates[:2], stronger)),
            stronger,
        )

    def test_interval_directions_payoff_span_and_aggregate_order(self) -> None:
        price = certified_closed_finite_block_price(
            incumbent=CertifiedChipValueInterval(1.0, 2.0),
            augmented=CertifiedChipValueInterval(3.0, 5.0),
        )
        self.assertEqual(
            (price.signed_lower_chips, price.signed_upper_chips),
            (1.0, 4.0),
        )
        excess = certified_greedy_teacher_excess(
            teacher=CertifiedChipValueInterval(10.0, 12.0),
            greedy=CertifiedChipValueInterval(7.0, 8.0),
        )
        self.assertEqual(
            (excess.signed_lower_chips, excess.signed_upper_chips),
            (2.0, 5.0),
        )
        normalized = normalize_full_regret(
            CertifiedChipRegretInterval(2.0, 4.0, 2.0, 4.0),
            payoff_span_chips=40,
        )
        self.assertEqual((normalized.lower, normalized.upper), (0.05, 0.1))

        recovery = conservative_aggregate_recovery(
            full_values=(
                CertifiedChipValueInterval(10.0, 10.0),
                CertifiedChipValueInterval(100.0, 100.0),
            ),
            baseline_values=(
                CertifiedChipValueInterval(0.0, 0.0),
                CertifiedChipValueInterval(0.0, 0.0),
            ),
            greedy_values=(
                CertifiedChipValueInterval(9.0, 9.0),
                CertifiedChipValueInterval(50.0, 50.0),
            ),
        )
        self.assertEqual(recovery.lower, 59.0 / 110.0)
        self.assertNotEqual(recovery.lower, (0.9 + 0.5) / 2.0)

    def test_gate_controls_are_nominally_distinct(self) -> None:
        controls = (
            ADR0323_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT,
            ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT,
            ADR0323_MINIMUM_AGGREGATE_RECOVERY_FLOOR,
            ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT,
            ADR0323_MEAN_NORMALIZED_TEACHER_EXCESS_LIMIT,
        )
        self.assertEqual(
            tuple(type(value) for value in controls),
            (
                MaximumNormalizedFullRegretLimit,
                MeanNormalizedFullRegretLimit,
                MinimumAggregateRecoveryFloor,
                MaximumNormalizedTeacherExcessLimit,
                MeanNormalizedTeacherExcessLimit,
            ),
        )
        self.assertEqual(
            tuple(value.value for value in controls),
            (0.005, 0.001, 0.90, 0.001, 0.0002),
        )
        self.assertIsNot(
            type(ADR0323_MEAN_NORMALIZED_FULL_REGRET_LIMIT),
            type(ADR0323_MAXIMUM_NORMALIZED_TEACHER_EXCESS_LIMIT),
        )
        self.assertIsNot(CertifiedGreedyTeacherExcessInterval, CertifiedChipRegretInterval)

    def test_source_excludes_revoked_action_and_transfer_paths(self) -> None:
        source_path = _ROOT / "src" / "pontius" / "fresh_action_width_greedy.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        forbidden_fragments = (
            "action_abstraction",
            "capacity_filling",
            "collision_repair",
            "historical",
            "multi_size_policy_bridge",
            "resolver",
            "blueprint",
            "preparation_bank",
        )
        self.assertFalse(
            any(
                fragment in name
                for fragment in forbidden_fragments
                for name in imported
            )
        )
        self.assertNotIn("BettingAction", source)
        self.assertNotIn("apply_action", source)
        self.assertNotIn("transfer_seed_from_mechanism_commit", source)
        consumer_calls = tuple(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "consume_certified_reduced_sizing_v2"
        )
        self.assertEqual(len(consumer_calls), 2)

    def test_width_gate_booleans_cannot_disagree_with_frozen_limits(self) -> None:
        recovery = ConservativeAggregateRecoveryInterval(
            lower=0.91,
            upper=0.92,
            achieved_gain_lower_chips=91.0,
            achieved_gain_upper_chips=92.0,
            available_gain_lower_chips=100.0,
            available_gain_upper_chips=100.0,
        )
        gate = GreedyWidthGateResult(
            raise_width=self.schedule.tasks_for_context(0)[1].raise_width,
            maximum_normalized_full_regret_upper=0.004,
            mean_normalized_full_regret_lower=0.0008,
            mean_normalized_full_regret_upper=0.0009,
            aggregate_recovery=recovery,
            maximum_normalized_teacher_excess_upper=0.0008,
            mean_normalized_teacher_excess_lower=0.0001,
            mean_normalized_teacher_excess_upper=0.00015,
            maximum_full_regret_pass=True,
            mean_full_regret_pass=True,
            aggregate_recovery_pass=True,
            maximum_teacher_excess_pass=True,
            mean_teacher_excess_pass=True,
        )
        self.assertTrue(gate.passes)
        with self.assertRaisesRegex(ValueError, "booleans"):
            replace(gate, aggregate_recovery_pass=False)

    def test_preflight_failure_is_typed_zero_call_and_cannot_reach_consumer(self) -> None:
        with (
            patch.object(
                greedy,
                "verify_adr0329_greedy_source_and_dependencies",
                side_effect=RuntimeError("synthetic source drift"),
            ),
            patch.object(
                greedy,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_consumer,
            ),
        ):
            result = run_adr0323_closed_finite_block_greedy_development()
        self.assertIsInstance(result, GreedyRunnerRejected)
        self.assertEqual(result.stage, GreedyRunnerStage.SOURCE_PREFLIGHT)
        self.assertEqual(result.known_public_highs_ds_invocation_count, 0)
        self.assertTrue(result.invocation_count_complete)

    def test_execution_failure_requires_exact_sealed_provenance(self) -> None:
        result = GreedyRunnerRejected(
            stage=GreedyRunnerStage.EXECUTION,
            reason="synthetic execution rejection",
            pool_sha256=self.schedule.pool_sha256,
            qualification_result_sha256=(
                self.schedule.qualification_result_sha256
            ),
            panel_sha256=self.schedule.panel_sha256,
            exhaustive_teacher_result_sha256=(
                self.schedule.exhaustive_teacher_result_sha256
            ),
            schedule_sha256=self.schedule.digest,
            greedy_source_sha256=ADR0329_GREEDY_SOURCE_MANIFEST[
                "fresh_action_width_greedy.py"
            ],
            completed_contexts=(),
            current_task=self.schedule.initial_task(0),
            current_transition=None,
            known_public_highs_ds_invocation_count=0,
            invocation_count_complete=True,
            exception_chain=(
                GreedyRunnerException(
                    module="tests.synthetic",
                    type_name="SyntheticError",
                    message="sealed fixture",
                ),
            ),
        )
        with self.assertRaisesRegex(ValueError, "another seal"):
            replace(result, schedule_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "another seal"):
            replace(result, greedy_source_sha256="f" * 64)

    def test_canonical_no_clobber_retention_and_pre_run_reservation(self) -> None:
        result = GreedyRunnerRejected(
            stage=GreedyRunnerStage.SOURCE_PREFLIGHT,
            reason="synthetic preflight rejection",
            pool_sha256=None,
            qualification_result_sha256=None,
            panel_sha256=None,
            exhaustive_teacher_result_sha256=None,
            schedule_sha256=None,
            greedy_source_sha256=None,
            completed_contexts=(),
            current_task=None,
            current_transition=None,
            known_public_highs_ds_invocation_count=0,
            invocation_count_complete=True,
            exception_chain=(
                GreedyRunnerException(
                    module="tests.synthetic",
                    type_name="SyntheticError",
                    message="sealed fixture",
                ),
            ),
        )
        rendered = canonical_greedy_result_bytes(result)
        self.assertTrue(rendered.endswith(b"\n"))
        self.assertFalse(rendered.endswith(b"\n\n"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "greedy.json"
            digest, byte_count = retain_greedy_result(result, output_path=output)
            self.assertEqual(output.read_bytes(), rendered)
            self.assertEqual(digest, hashlib.sha256(rendered).hexdigest())
            self.assertEqual(byte_count, len(rendered))
            with self.assertRaises(FileExistsError):
                retain_greedy_result(result, output_path=output)

            reserved = Path(directory) / "reserved.json"

            def _reserved_runner() -> GreedyRunnerRejected:
                self.assertTrue(reserved.with_suffix(".json.partial").exists())
                return result

            with patch.object(
                greedy,
                "run_adr0323_closed_finite_block_greedy_development",
                side_effect=_reserved_runner,
            ):
                returned = run_and_retain_adr0323_closed_finite_block_greedy_development(
                    output_path=reserved
                )
            self.assertEqual(returned, result)
            self.assertEqual(reserved.read_bytes(), rendered)
            self.assertFalse(reserved.with_suffix(".json.partial").exists())


if __name__ == "__main__":
    unittest.main()
