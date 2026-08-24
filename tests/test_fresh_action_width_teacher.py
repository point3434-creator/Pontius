from __future__ import annotations

import ast
import json
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.fresh_action_width_teacher as teacher
from pontius.certified_reduced_sizing_consumer_v2 import (
    CertifiedReducedSizingAcceptedV2,
    CertifiedReducedSizingRejectedV2,
    CertifiedReducedSizingRequestV2,
    KernelRaiseToTotal,
    LegalRaiseSetScope,
    ReducedSizingResponseModel,
    canonical_lf_source_sha256,
    consume_certified_reduced_sizing_v2,
)
from pontius.fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    CertifiedChipValueInterval,
)
from pontius.fresh_action_width_qualification_result import (
    ADR0323_QUALIFICATION_RESULT_SHA256,
    ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
    ADR0323_QUALIFIED_PANEL_SHA256,
    ADR0323_QUALIFIED_POOL_INDICES,
)
from pontius.fresh_action_width_structures import RaiseActionWidth
from pontius.fresh_action_width_teacher import (
    ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
    ADR0323_EXHAUSTIVE_TEACHER_SUBSET_TASK_COUNT,
    ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
    ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
    ExhaustiveTeacherArm,
    ExhaustiveTeacherFailure,
    ExhaustiveTeacherFailureKind,
    ExhaustiveTeacherFailureStage,
    ExhaustiveTeacherRunnerRejected,
    ExhaustiveTeacherRunnerStage,
    ExhaustiveTeacherSchedule,
    ExhaustiveTeacherTask,
    TeacherEquivalenceAllowance,
    TeacherRunnerException,
    TeacherSubsetCandidate,
    build_adr0323_exhaustive_teacher_schedule,
    build_teacher_subset_observation,
    canonical_exhaustive_teacher_result_bytes,
    exhaustive_teacher_protocol_sha256,
    normalize_teacher_regret,
    reduce_teacher_width,
    retain_exhaustive_teacher_result,
    run_adr0323_exhaustive_development_teacher,
    run_and_retain_adr0323_exhaustive_development_teacher,
    verify_adr0327_teacher_source_and_dependencies,
)
from pontius.fresh_action_width_teacher_seal import (
    ADR0327_EXHAUSTIVE_TEACHER_PROTOCOL_SHA256,
    ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
    ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST,
    ADR0327_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
    ADR0327_EXHAUSTIVE_TEACHER_TASK_COUNT,
)
from pontius.no_limit_betting import BettingStreet, NoLimitBettingState


_PROBABILITIES = (
    (Fraction(1, 4), Fraction(1, 4)),
    (Fraction(1, 4), Fraction(1, 4)),
)
_SIGNS = ((1, 1), (-1, -1))


def _two_live_toy_state() -> NoLimitBettingState:
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=BettingStreet.RIVER,
        starting_stacks=(9, 9, 2, 2, 2, 2),
        stacks=(4, 4, 2, 2, 2, 2),
        total_contributions=(5, 5, 0, 0, 0, 0),
        street_contributions=(0, 0, 0, 0, 0, 0),
        folded=(False, False, True, True, True, True),
        pending_seats=(0, 1),
        last_full_raise_size=2,
        acted_at_bet=(None, None, None, None, None, None),
    )


def _toy_request(
    *,
    scope: LegalRaiseSetScope,
    amounts: tuple[int, ...],
    label: str,
) -> CertifiedReducedSizingRequestV2:
    return CertifiedReducedSizingRequestV2(
        context_id=label,
        betting=_two_live_toy_state(),
        response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
        legal_raise_scope=scope,
        legal_raise_to_totals=tuple(KernelRaiseToTotal(value) for value in amounts),
        joint_probabilities=_PROBABILITIES,
        showdown_signs=_SIGNS,
    )


def _forbidden_call(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("the sealed development teacher must remain value-unopened")


class FreshActionWidthTeacherSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with patch.object(
            teacher,
            "consume_certified_reduced_sizing_v2",
            side_effect=_forbidden_call,
        ):
            cls.schedule = build_adr0323_exhaustive_teacher_schedule()

        full_request = _toy_request(
            scope=LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
            amounts=(2, 3, 4),
            label="adr0327-source-only-full-toy",
        )
        subset_request = _toy_request(
            scope=LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET,
            amounts=(2, 4),
            label="adr0327-source-only-subset-toy",
        )
        full = consume_certified_reduced_sizing_v2(full_request)
        subset = consume_certified_reduced_sizing_v2(subset_request)
        if not isinstance(full, CertifiedReducedSizingAcceptedV2) or not isinstance(
            subset,
            CertifiedReducedSizingAcceptedV2,
        ):
            raise AssertionError("teacher schema toys must be accepted")
        cls.full_toy = full
        cls.subset_toy = subset
        cls.full_task = ExhaustiveTeacherTask(
            ordinal=0,
            panel_position=0,
            pool_index=0,
            context_semantic_digest=sha256(b"teacher-toy-context").hexdigest(),
            arm=ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE,
            raise_width=None,
            subset_index=None,
            request=full_request,
        )
        cls.subset_task = ExhaustiveTeacherTask(
            ordinal=1,
            panel_position=0,
            pool_index=0,
            context_semantic_digest=cls.full_task.context_semantic_digest,
            arm=ExhaustiveTeacherArm.ANCHORED_SUBSET,
            raise_width=RaiseActionWidth(2),
            subset_index=0,
            request=subset_request,
        )

    def test_source_manifest_protocol_and_import_boundary_are_exact(self) -> None:
        root = Path(teacher.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST), actual)
        self.assertEqual(
            actual["fresh_action_width_teacher.py"],
            verify_adr0327_teacher_source_and_dependencies(),
        )
        self.assertEqual(
            ADR0327_EXHAUSTIVE_TEACHER_PROTOCOL_SHA256,
            exhaustive_teacher_protocol_sha256(),
        )
        self.assertEqual(
            ADR0327_EXHAUSTIVE_TEACHER_SCHEDULE_SHA256,
            self.schedule.digest,
        )
        self.assertEqual(
            ADR0323_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
            ADR0327_EXHAUSTIVE_TEACHER_SUBSET_COUNTS,
        )
        self.assertEqual(
            ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
            ADR0327_EXHAUSTIVE_TEACHER_TASK_COUNT,
        )
        with self.assertRaises(TypeError):
            ADR0327_EXHAUSTIVE_TEACHER_SOURCE_MANIFEST[  # type: ignore[index]
                "fresh_action_width_teacher.py"
            ] = "0" * 64

        tree = ast.parse(Path(teacher.__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        names: set[str] = set()
        attributes: set[str] = set()
        consumer_calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "consume_certified_reduced_sizing_v2"
            ):
                consumer_calls += 1
        forbidden = {
            "action_abstraction_confirmation",
            "capacity_filling_action_abstraction",
            "collision_repair_action_abstraction",
            "fresh_capacity_filling_qualification",
            "fresh_collision_repair_qualification",
            "legal_action_abstraction",
            "linear_program",
            "reduced_river_sizing_oracle",
            "sizing_power_diagnostic",
            "width_four_sizing_power_evaluation",
        }
        self.assertTrue(imported.isdisjoint(forbidden))
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("apply_action", attributes)
        self.assertEqual(2, consumer_calls)

    def test_value_free_schedule_is_complete_unique_and_ordered(self) -> None:
        schedule = self.schedule
        self.assertEqual(ADR0323_QUALIFICATION_RESULT_SHA256, schedule.qualification_result_sha256)
        self.assertEqual(ADR0323_QUALIFIED_PANEL_SHA256, schedule.panel_sha256)
        self.assertEqual(ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT, len(schedule.tasks))
        self.assertEqual(
            ADR0323_EXHAUSTIVE_TEACHER_SUBSET_TASK_COUNT,
            len(schedule.tasks) - len(ADR0323_QUALIFIED_POOL_INDICES),
        )
        self.assertEqual(len(schedule.tasks), len({task.digest for task in schedule.tasks}))
        self.assertEqual(
            len(schedule.tasks),
            len({task.request_sha256 for task in schedule.tasks}),
        )
        for panel_position, (pool_index, context_digest) in enumerate(
            zip(
                ADR0323_QUALIFIED_POOL_INDICES,
                ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
                strict=True,
            )
        ):
            context_tasks = tuple(
                task
                for task in schedule.tasks
                if task.panel_position == panel_position
            )
            self.assertIs(
                ExhaustiveTeacherArm.COMPLETE_INTEGER_UNIVERSE,
                context_tasks[0].arm,
            )
            self.assertEqual(pool_index, context_tasks[0].pool_index)
            self.assertEqual(context_digest, context_tasks[0].context_semantic_digest)
            self.assertEqual(
                tuple(range(context_tasks[0].raise_to_totals[0], context_tasks[0].raise_to_totals[-1] + 1)),
                context_tasks[0].raise_to_totals,
            )
            observed = tuple(
                (task.raise_width.count, task.subset_index)
                for task in context_tasks[1:]
                if task.raise_width is not None
            )
            self.assertEqual(tuple(sorted(observed)), observed)

    def test_teacher_envelope_uses_conservative_directions_and_strict_dominance(self) -> None:
        width = RaiseActionWidth(2)
        overlap = reduce_teacher_width(
            (
                TeacherSubsetCandidate(0, (2, 4), CertifiedChipValueInterval(0.0, 0.5)),
                TeacherSubsetCandidate(1, (2, 5), CertifiedChipValueInterval(0.5, 0.6)),
            ),
            raise_width=width,
            equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
        )
        self.assertEqual(CertifiedChipValueInterval(0.5, 0.6), overlap.value)
        self.assertEqual((0, 1), overlap.nondominated_subset_indices)
        self.assertIsNone(overlap.unique_best_subset_index)

        unique = reduce_teacher_width(
            (
                TeacherSubsetCandidate(0, (2, 4), CertifiedChipValueInterval(0.0, 0.4)),
                TeacherSubsetCandidate(1, (2, 5), CertifiedChipValueInterval(0.5, 0.6)),
            ),
            raise_width=width,
            equivalence_allowance=ADR0323_TEACHER_EQUIVALENCE_ALLOWANCE,
        )
        self.assertEqual((1,), unique.nondominated_subset_indices)
        self.assertEqual(1, unique.unique_best_subset_index)

    def test_equivalence_is_reporting_only_and_may_be_empty(self) -> None:
        candidates = (
            TeacherSubsetCandidate(0, (2, 4), CertifiedChipValueInterval(0.0, 1.0)),
            TeacherSubsetCandidate(1, (2, 5), CertifiedChipValueInterval(0.5, 1.5)),
        )
        narrow = reduce_teacher_width(
            candidates,
            raise_width=RaiseActionWidth(2),
            equivalence_allowance=TeacherEquivalenceAllowance(1e-8),
        )
        wide = reduce_teacher_width(
            candidates,
            raise_width=RaiseActionWidth(2),
            equivalence_allowance=TeacherEquivalenceAllowance(2.0),
        )
        self.assertEqual((), narrow.equivalent_subset_indices)
        self.assertEqual((0, 1), wide.equivalent_subset_indices)
        self.assertEqual(narrow.value, wide.value)
        self.assertEqual(narrow.nondominated_subset_indices, wide.nondominated_subset_indices)
        self.assertEqual(narrow.unique_best_subset_index, wide.unique_best_subset_index)
        with self.assertRaises(TypeError):
            reduce_teacher_width(
                candidates,
                raise_width=RaiseActionWidth(2),
                equivalence_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,  # type: ignore[arg-type]
            )

    def test_subset_regret_and_normalization_use_payoff_span(self) -> None:
        observation = build_teacher_subset_observation(
            task=self.subset_task,
            full=self.full_toy,
            accepted=self.subset_toy,
            payoff_span_chips=18,
        )
        self.assertAlmostEqual(
            observation.regret.nonnegative_lower_chips / 18,
            observation.normalized_regret.lower,
        )
        self.assertAlmostEqual(
            observation.regret.nonnegative_upper_chips / 18,
            observation.normalized_regret.upper,
        )
        self.assertNotEqual(
            TeacherEquivalenceAllowance(1e-8),
            ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        with self.assertRaises(ValueError):
            normalize_teacher_regret(observation.regret, payoff_span_chips=0)

        other_probabilities = (
            (Fraction(1, 2), Fraction(1, 6)),
            (Fraction(1, 6), Fraction(1, 6)),
        )
        other_full = consume_certified_reduced_sizing_v2(
            CertifiedReducedSizingRequestV2(
                context_id="adr0327-cross-game-full-toy",
                betting=_two_live_toy_state(),
                response_model=ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY,
                legal_raise_scope=LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE,
                legal_raise_to_totals=tuple(
                    KernelRaiseToTotal(value) for value in (2, 3, 4)
                ),
                joint_probabilities=other_probabilities,
                showdown_signs=_SIGNS,
            )
        )
        self.assertIsInstance(other_full, CertifiedReducedSizingAcceptedV2)
        assert isinstance(other_full, CertifiedReducedSizingAcceptedV2)
        with self.assertRaisesRegex(ValueError, "different games"):
            build_teacher_subset_observation(
                task=self.subset_task,
                full=other_full,
                accepted=self.subset_toy,
                payoff_span_chips=18,
            )

    def test_consumer_and_numerical_failures_are_typed_and_failure_complete(self) -> None:
        rejected = consume_certified_reduced_sizing_v2(
            self.subset_task.request,
            linprog_function=_forbidden_call,
        )
        self.assertIsInstance(rejected, CertifiedReducedSizingRejectedV2)
        assert isinstance(rejected, CertifiedReducedSizingRejectedV2)
        consumer_failure = ExhaustiveTeacherFailure(
            kind=ExhaustiveTeacherFailureKind.CONSUMER_REJECTION,
            stage=ExhaustiveTeacherFailureStage.SUBSET_ARM,
            task=self.subset_task,
            completed_full=self.full_toy,
            completed_width_results=(),
            incomplete_subset_observations=(),
            rejected=rejected,
        )
        self.assertEqual(
            1 + rejected.public_highs_ds_invocation_count,
            consumer_failure.public_highs_ds_invocation_count,
        )
        numerical_failure = ExhaustiveTeacherFailure(
            kind=ExhaustiveTeacherFailureKind.NUMERICAL_REJECTION,
            stage=ExhaustiveTeacherFailureStage.SUBSET_REGRET,
            task=self.subset_task,
            completed_full=self.full_toy,
            completed_width_results=(),
            incomplete_subset_observations=(),
            accepted_at_failure=self.subset_toy,
            exception_chain=(TeacherRunnerException("builtins", "ValueError", "reverse"),),
        )
        self.assertEqual(2, numerical_failure.public_highs_ds_invocation_count)
        with self.assertRaises(ValueError):
            replace(numerical_failure, exception_chain=())

    def test_preflight_and_unexpected_execution_fail_without_hidden_retry(self) -> None:
        with (
            patch.object(
                teacher,
                "verify_adr0327_teacher_source_and_dependencies",
                side_effect=RuntimeError("synthetic teacher drift"),
            ),
            patch.object(
                teacher,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_call,
            ),
        ):
            rejected = run_adr0323_exhaustive_development_teacher()
        self.assertIsInstance(rejected, ExhaustiveTeacherRunnerRejected)
        assert isinstance(rejected, ExhaustiveTeacherRunnerRejected)
        self.assertIs(ExhaustiveTeacherRunnerStage.SOURCE_PREFLIGHT, rejected.stage)
        self.assertEqual(0, rejected.known_public_highs_ds_invocation_count)
        self.assertTrue(rejected.invocation_count_complete)

        with (
            patch.object(
                teacher,
                "verify_adr0327_teacher_source_and_dependencies",
                return_value="1" * 64,
            ),
            patch.object(
                teacher,
                "verify_adr0327_exhaustive_teacher_schedule",
                return_value=None,
            ),
            patch.object(
                teacher,
                "consume_certified_reduced_sizing_v2",
                return_value=object(),
            ),
        ):
            unexpected = run_adr0323_exhaustive_development_teacher()
        self.assertIsInstance(unexpected, ExhaustiveTeacherRunnerRejected)
        assert isinstance(unexpected, ExhaustiveTeacherRunnerRejected)
        self.assertIs(ExhaustiveTeacherRunnerStage.EXECUTION, unexpected.stage)
        self.assertFalse(unexpected.invocation_count_complete)
        self.assertEqual(0, unexpected.known_public_highs_ds_invocation_count)
        self.assertEqual(self.schedule.tasks[0].digest, unexpected.current_task.digest)

    def test_no_clobber_artifact_retention_is_canonical_and_verified(self) -> None:
        result = ExhaustiveTeacherRunnerRejected(
            stage=ExhaustiveTeacherRunnerStage.SOURCE_PREFLIGHT,
            reason="synthetic source-only artifact",
            pool_sha256=None,
            qualification_result_sha256=None,
            panel_sha256=None,
            schedule_sha256=None,
            teacher_source_sha256=None,
            completed_contexts=(),
            current_task=None,
            known_public_highs_ds_invocation_count=0,
            invocation_count_complete=True,
            exception_chain=(TeacherRunnerException("builtins", "RuntimeError", "drift"),),
        )
        canonical = canonical_exhaustive_teacher_result_bytes(result)
        self.assertTrue(canonical.endswith(b"\n"))
        self.assertFalse(canonical.endswith(b"\n\n"))
        self.assertEqual("runner_rejected", json.loads(canonical)["result_type"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "teacher.json"
            digest, byte_count = retain_exhaustive_teacher_result(
                result,
                output_path=output,
            )
            self.assertEqual(sha256(canonical).hexdigest(), digest)
            self.assertEqual(len(canonical), byte_count)
            self.assertEqual(canonical, output.read_bytes())
            self.assertFalse(output.with_suffix(".json.partial").exists())
            with self.assertRaises(FileExistsError):
                retain_exhaustive_teacher_result(result, output_path=output)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "owned-teacher.json"
            with patch.object(
                teacher,
                "run_adr0323_exhaustive_development_teacher",
                return_value=result,
            ) as owned_run:
                retained = run_and_retain_adr0323_exhaustive_development_teacher(
                    output_path=output,
                )
            self.assertIs(result, retained)
            owned_run.assert_called_once_with()
            self.assertEqual(canonical, output.read_bytes())
            self.assertFalse(output.with_suffix(".json.partial").exists())
            with (
                patch.object(
                    teacher,
                    "run_adr0323_exhaustive_development_teacher",
                    side_effect=_forbidden_call,
                ) as forbidden_run,
                self.assertRaises(FileExistsError),
            ):
                run_and_retain_adr0323_exhaustive_development_teacher(
                    output_path=output,
                )
            forbidden_run.assert_not_called()

    def test_schedule_and_task_corruption_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            replace(
                self.schedule,
                tasks=(self.schedule.tasks[1], self.schedule.tasks[0], *self.schedule.tasks[2:]),
            )
        with self.assertRaises(ValueError):
            replace(self.schedule.tasks[0], request_sha256="0" * 64)
        with self.assertRaises((TypeError, ValueError)):
            ExhaustiveTeacherSchedule(
                pool_sha256=self.schedule.pool_sha256,
                qualification_result_sha256=self.schedule.qualification_result_sha256,
                panel_sha256=self.schedule.panel_sha256,
                tasks=self.schedule.tasks[:-1],
                subset_counts_by_raise_width=self.schedule.subset_counts_by_raise_width,
            )


if __name__ == "__main__":
    unittest.main()
