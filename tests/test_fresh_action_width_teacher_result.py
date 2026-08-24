from __future__ import annotations

import ast
import copy
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import pontius.certified_reduced_sizing_consumer_v2 as consumer
import pontius.fresh_action_width_teacher as teacher
import pontius.fresh_action_width_teacher_result as retained
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.fresh_action_width_teacher import (
    ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
    build_adr0323_exhaustive_teacher_schedule,
)
from pontius.fresh_action_width_teacher_result import (
    ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES,
    ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_RELATIVE_PATH,
    ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256,
    ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256,
    ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256,
    exhaustive_teacher_result_protocol_sha256,
    verify_adr0323_exhaustive_teacher_result_artifact,
)
from pontius.fresh_action_width_teacher_result_seal import (
    ADR0328_EXHAUSTIVE_TEACHER_RESULT_PROTOCOL_SHA256,
    ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST,
)


def _forbidden_call(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("the retained teacher rebinder reached a solver path")


class FreshActionWidthTeacherResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact_path = (
            Path(retained.__file__).resolve().parents[2]
            / ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_RELATIVE_PATH
        )
        cls.raw = cls.artifact_path.read_bytes()
        cls.decoded = json.loads(cls.raw)
        cls.schedule = build_adr0323_exhaustive_teacher_schedule()
        with (
            patch.object(
                teacher,
                "consume_certified_reduced_sizing_v2",
                side_effect=_forbidden_call,
            ),
            patch.object(
                consumer,
                "solve_certified_reduced_sizing_highs",
                side_effect=_forbidden_call,
            ),
        ):
            cls.result = verify_adr0323_exhaustive_teacher_result_artifact()

    def test_source_protocol_and_artifact_identities_are_exact(self) -> None:
        source_root = Path(retained.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(source_root / name)
            for name in ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST
        }
        self.assertEqual(
            dict(ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST),
            actual,
        )
        self.assertEqual(
            exhaustive_teacher_result_protocol_sha256(),
            ADR0328_EXHAUSTIVE_TEACHER_RESULT_PROTOCOL_SHA256,
        )
        self.assertEqual(len(self.raw), ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES)
        self.assertEqual(
            hashlib.sha256(self.raw).hexdigest(),
            ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(self.raw[:-1]).hexdigest(),
            ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256,
        )
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertFalse(self.raw.endswith(b"\n\n"))
        self.assertEqual(
            json.dumps(
                self.decoded,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
            + b"\n",
            self.raw,
        )

    def test_rebinder_is_solver_free_complete_and_failureless(self) -> None:
        result = self.result
        self.assertEqual(
            result.campaign_result_sha256,
            ADR0323_EXHAUSTIVE_TEACHER_RESULT_SHA256,
        )
        self.assertEqual(len(result.contexts), 16)
        self.assertEqual(result.context_width_count, 80)
        self.assertEqual(
            result.public_highs_ds_invocation_count,
            ADR0323_EXHAUSTIVE_TEACHER_TASK_COUNT,
        )
        self.assertEqual(
            sum(
                len(width.subsets)
                for context in result.contexts
                for width in context.widths
            ),
            2_479,
        )
        self.assertEqual(self.decoded["stop_reason"], "completed")
        self.assertIsNone(self.decoded["failure"])
        source = Path(retained.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertNotIn("consume_certified_reduced_sizing_v2", imported_names)
        self.assertNotIn("solve_certified_reduced_sizing_highs", imported_names)
        self.assertNotIn("run_adr0323_exhaustive_development_teacher", imported_names)

    def test_retained_flatness_map_and_regret_curve_are_exact(self) -> None:
        expected_nondominated = {
            2: {1: 16},
            3: {1: 14, 2: 2},
            4: {1: 1, 4: 2, 6: 5, 7: 1, 8: 6, 11: 1},
            5: {6: 2, 7: 1, 9: 1, 15: 5, 25: 1, 28: 6},
            6: {4: 2, 5: 1, 20: 5, 21: 1, 30: 1, 56: 6},
        }
        expected_max_upper_hex = {
            2: "0x1.867ce7b5a2951p-8",
            3: "0x1.0914b1b474000p-15",
            4: "0x1.4a90d79435e51p-43",
            5: "0x1.4a90d79435e51p-43",
            6: "0x1.4a90d79435e51p-43",
        }
        for width_index, raise_width in enumerate(range(2, 7)):
            widths = [context.widths[width_index] for context in self.result.contexts]
            nondominated = Counter(
                width.nondominated_subset_count for width in widths
            )
            equivalent = Counter(
                len(width.equivalent_subset_indices) for width in widths
            )
            self.assertEqual(dict(sorted(nondominated.items())), expected_nondominated[raise_width])
            self.assertEqual(equivalent, nondominated)
            self.assertNotIn(0, equivalent)
            self.assertEqual(
                max(width.normalized_full_regret_upper for width in widths).hex(),
                expected_max_upper_hex[raise_width],
            )

    def test_semantic_corruptions_fail_independent_rebinding(self) -> None:
        cases: list[tuple[str, tuple[object, ...], object]] = [
            (
                "task request",
                ("contexts", 0, "widths", 0, "subset_observations", 0, "task", "request_sha256"),
                "0" * 64,
            ),
            (
                "boolean task ordinal",
                ("contexts", 0, "widths", 0, "subset_observations", 0, "task", "ordinal"),
                False,
            ),
            (
                "boolean public call count",
                ("contexts", 0, "full", "public_call_count"),
                True,
            ),
            (
                "regret direction",
                (
                    "contexts",
                    0,
                    "widths",
                    0,
                    "subset_observations",
                    0,
                    "regret",
                    "nonnegative_upper_hex",
                ),
                "0x0.0p+0",
            ),
            (
                "teacher survivors",
                ("contexts", 0, "widths", 1, "envelope", "nondominated_subset_indices"),
                [],
            ),
            (
                "boolean unique survivor",
                ("contexts", 0, "widths", 0, "envelope", "unique_best_subset_index"),
                False,
            ),
            (
                "nested width digest",
                ("contexts", 0, "widths", 0, "width_result_sha256"),
                "f" * 64,
            ),
            ("campaign digest", ("digest",), "a" * 64),
        ]
        for label, path, replacement in cases:
            with self.subTest(label=label):
                corrupted = copy.deepcopy(self.decoded)
                owner: object = corrupted
                for key in path[:-1]:
                    owner = owner[key]  # type: ignore[index]
                owner[path[-1]] = replacement  # type: ignore[index]
                with self.assertRaises((TypeError, ValueError)):
                    retained._rebind_completed_payload(
                        corrupted,
                        schedule=self.schedule,
                    )

    def test_byte_boundary_rejects_noncanonical_and_truncated_artifacts(self) -> None:
        variants = (
            b" " + self.raw,
            self.raw[:-1],
            self.raw + b"\n",
        )
        for index, raw in enumerate(variants):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "teacher.json"
                path.write_bytes(raw)
                payload = raw[:-1] if raw.endswith(b"\n") else raw
                with (
                    patch.object(
                        retained,
                        "verify_adr0328_teacher_result_source_and_dependencies",
                        return_value="0" * 64,
                    ),
                    patch.object(
                        retained,
                        "ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_BYTES",
                        len(raw),
                    ),
                    patch.object(
                        retained,
                        "ADR0323_EXHAUSTIVE_TEACHER_ARTIFACT_SHA256",
                        hashlib.sha256(raw).hexdigest(),
                    ),
                    patch.object(
                        retained,
                        "ADR0323_EXHAUSTIVE_TEACHER_PAYLOAD_SHA256",
                        hashlib.sha256(payload).hexdigest(),
                    ),
                ):
                    with self.assertRaises(ValueError):
                        verify_adr0323_exhaustive_teacher_result_artifact(path)


if __name__ == "__main__":
    unittest.main()
