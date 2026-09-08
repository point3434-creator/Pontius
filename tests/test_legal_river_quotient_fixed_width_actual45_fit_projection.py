"""Projection arithmetic and interpretation checks, independent of the retired run owner."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pontius import legal_river_quotient_fixed_width_actual45_fit_projection as source
from pontius import legal_river_quotient_fixed_width_actual45_fit_projection_result as reader


ROOT = Path(__file__).parents[1]
SOURCE = Path(source.__file__)


def _phase_partition(names: tuple[str, ...], elapsed: int, *, start: int = 0) -> dict[str, object]:
    rows = []
    cursor = start
    for name in names:
        end = cursor + elapsed
        rows.append(
            {
                "name": name,
                "start_ns": cursor,
                "end_ns": end,
                "elapsed_ns": elapsed,
            }
        )
        cursor = end
    return {"rows": rows, "total_ns": elapsed * len(names)}


def synthetic_events(
    elapsed_by_arm: dict[str, int] | None = None,
    *,
    validation_elapsed_by_arm: dict[str, int] | None = None,
) -> list[dict[str, object]]:
    elapsed_by_arm = elapsed_by_arm or {arm: 0 for arm in source.ARMS}
    validation_elapsed_by_arm = validation_elapsed_by_arm or {}
    events: list[dict[str, object]] = []
    for arm in source.ARMS:
        names = source.PHASES[arm]
        for population in source.POPULATIONS:
            schedules = [
                ("warmup", "ascending_colex", 0),
                *(
                    ("timed", direction, repeat)
                    for direction in ("ascending_colex", "descending_colex")
                    for repeat in range(3)
                ),
            ]
            for kind, direction, repeat in schedules:
                base_elapsed = elapsed_by_arm.get(arm, 0)
                partition = _phase_partition(names, base_elapsed)
                if arm in validation_elapsed_by_arm:
                    rows = partition["rows"]
                    assert isinstance(rows, list)
                    cursor = 0
                    for row in rows:
                        assert isinstance(row, dict)
                        value = (
                            validation_elapsed_by_arm[arm]
                            if row["name"] == source.VALIDATION_PHASE
                            else base_elapsed
                        )
                        row["start_ns"] = cursor
                        cursor += value
                        row["end_ns"] = cursor
                        row["elapsed_ns"] = value
                    partition["total_ns"] = cursor
                events.append(
                    {
                        "arm": arm,
                        "population": population,
                        "exact_verified": True,
                        "schedule_kind": kind,
                        "traversal_order": direction,
                        "repeat_index": repeat,
                        "phase_partition": partition,
                    }
                )
    return events


def source_snapshot(
    elapsed_by_arm: dict[str, int] | None = None,
    *,
    validation_elapsed_by_arm: dict[str, int] | None = None,
) -> source.CalibrationSnapshot:
    return source.calibration_snapshot_from_events(
        synthetic_events(
            elapsed_by_arm,
            validation_elapsed_by_arm=validation_elapsed_by_arm,
        ),
        source.MEMORY,
    )


def reader_snapshot(snapshot: source.CalibrationSnapshot) -> reader.IndependentSnapshot:
    return reader.IndependentSnapshot(
        snapshot.phase_maxima_ns,
        snapshot.phase_observations_ns,
        snapshot.memory,
    )


def synthetic_document(snapshot: source.CalibrationSnapshot) -> dict[str, object]:
    return {
        "schema_version": "legal-river-quotient-fixed-width-actual45-fit-projection-result-v1",
        "source_commit": "a" * 40,
        "config_sha256": source.CONFIG_SHA256,
        "correction_config_sha256": source.CORRECTION_CONFIG_SHA256,
        "dependency_hashes": {
            relative: "b" * 64 for relative in reader.DEPENDENCY_RELATIVE_PATHS
        },
        "input": {
            "relative_path": source.INPUT_RELATIVE_PATH,
            "bytes": source.INPUT_BYTES,
            "raw_sha256": source.INPUT_SHA256,
            "consumed": True,
        },
        "projection": source.project_snapshot(snapshot),
        "claims": source.result_claims(),
    }


class Literal45FitProjectionTests(unittest.TestCase):
    def test_projection_counts_and_runtime_phase_classes(self) -> None:
        self.assertEqual(len(source.RUNTIME_PHASES[source.POSITIONAL]), 11)
        self.assertEqual(len(source.RUNTIME_PHASES[source.BATCHED_RRNS]), 19)
        counts = source.projection_constituents(45, 176, 3)
        self.assertEqual(counts["adjoint_global_subset_entries"], 81_711_241_920)
        self.assertEqual(counts["adjoint_stream_chunks"], 5_967)

    def test_import_does_not_load_cuda(self) -> None:
        source_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        top_imports = {
            alias.name.split(".")[0]
            for node in ast.walk(source_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("cupy", top_imports)
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "import sys; "
                        "import pontius.legal_river_quotient_fixed_width_actual45_fit_projection; "
                        "import pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result; "
                        "print(int('cupy' in sys.modules))"
                    ),
                ],
                cwd=directory,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.stdout.strip(), "0")

    def test_six_timed_rows_maxima_counterfactuals_and_independent_reader_agree(self) -> None:
        events = synthetic_events({source.POSITIONAL: 2, source.BATCHED_RRNS: 3})
        snapshot = source.calibration_snapshot_from_events(events, source.MEMORY)
        independent = reader.independent_snapshot_from_events(events, reader.MEMORY)
        projected = source.project_snapshot(snapshot)
        self.assertEqual(projected, reader.independent_projection(independent))
        for arm in source.ARMS:
            phases = projected["arms"][arm]["phase_projections"]
            self.assertEqual(len(phases), len(source.PHASES[arm]))
            for phase in phases:
                for population in source.POPULATIONS:
                    self.assertEqual(
                        len(phase["endpoints"][population]["timed_observations_ns"]),
                        6,
                    )
            self.assertEqual(
                set(projected["arms"][arm]["reporting_only_endpoint_counterfactuals"]),
                set(source.POPULATIONS),
            )
        document = synthetic_document(snapshot)
        rebound = reader.validate_projection_document(
            document,
            reader_snapshot(snapshot),
            validate_dependencies=False,
        )
        self.assertEqual(rebound.eligible_arms, source.ARMS)
        self.assertIsNone(rebound.candidate_selected)

    def test_runtime_boundary_and_validation_exclusion_are_exact(self) -> None:
        self.assertTrue(source.component_projection_passes(13_999_999_999))
        self.assertTrue(source.component_projection_passes(14_000_000_000))
        self.assertFalse(source.component_projection_passes(14_000_000_001))
        snapshot = source_snapshot(
            {arm: 0 for arm in source.ARMS},
            validation_elapsed_by_arm={arm: 10**18 for arm in source.ARMS},
        )
        projection = source.project_snapshot(snapshot)
        for arm in source.ARMS:
            row = projection["arms"][arm]
            self.assertTrue(row["component_wall_passed"])
            self.assertLessEqual(row["runtime_component_projection_ns"], 14_000_000_000)
            self.assertGreater(row["laboratory_validation_projection_ns"], 14_000_000_000)

    def test_zero_one_two_and_tie_survivor_outcomes(self) -> None:
        both = source.project_snapshot(source_snapshot())
        self.assertEqual(both["projection_eligible_arms"], list(source.ARMS))
        self.assertEqual(
            both["terminal"], "projection_admits_two_arms_for_separate_live_screen"
        )
        self.assertIsNone(both["candidate_selected"])
        positional_only = source.project_snapshot(
            source_snapshot({source.POSITIONAL: 0, source.BATCHED_RRNS: 20_000_000_000})
        )
        self.assertEqual(positional_only["projection_eligible_arms"], [source.POSITIONAL])
        self.assertEqual(
            positional_only["terminal"],
            "projection_admits_one_arm_for_separate_live_screen",
        )
        neither = source.project_snapshot(
            source_snapshot({arm: 20_000_000_000 for arm in source.ARMS})
        )
        self.assertEqual(neither["projection_eligible_arms"], [])
        self.assertEqual(neither["terminal"], "projection_rejected_before_target_allocation")

    def test_schedule_phase_and_endpoint_mutations_reject(self) -> None:
        mutation = synthetic_events()
        mutation[0]["repeat_index"] = 1
        with self.assertRaises(ValueError):
            source.calibration_snapshot_from_events(mutation, source.MEMORY)

        mutation = synthetic_events()
        partition = mutation[1]["phase_partition"]
        assert isinstance(partition, dict)
        rows = partition["rows"]
        assert isinstance(rows, list)
        rows.pop()
        with self.assertRaises(ValueError):
            source.calibration_snapshot_from_events(mutation, source.MEMORY)

        mutation = synthetic_events()
        partition = mutation[1]["phase_partition"]
        assert isinstance(partition, dict)
        rows = partition["rows"]
        assert isinstance(rows, list)
        rows[-1] = deepcopy(rows[-2])
        with self.assertRaises(ValueError):
            source.calibration_snapshot_from_events(mutation, source.MEMORY)

        mutation = synthetic_events()
        partition = mutation[1]["phase_partition"]
        assert isinstance(partition, dict)
        rows = partition["rows"]
        assert isinstance(rows, list)
        rows[1]["start_ns"] += 1
        with self.assertRaises(ValueError):
            source.calibration_snapshot_from_events(mutation, source.MEMORY)

        snapshot = source_snapshot()
        document = synthetic_document(snapshot)
        bad = deepcopy(document)
        bad["projection"]["arms"][source.POSITIONAL]["phase_projections"][0]["endpoints"].pop("signed_12")
        with self.assertRaises(ValueError):
            reader.validate_projection_document(
                bad, reader_snapshot(snapshot), validate_dependencies=False
            )

    def test_result_claim_ratio_arm_and_selection_mutations_reject(self) -> None:
        snapshot = source_snapshot()
        baseline = synthetic_document(snapshot)
        mutations = []
        bad = deepcopy(baseline)
        bad["claims"]["candidate_selected"] = source.POSITIONAL
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["claims"]["literal_45_numeric_value"] = 0
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["claims"]["action_clock_result"] = True
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["projection"]["candidate_selected"] = source.POSITIONAL
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["projection"]["arms"]["resident_nine_RRNS"] = {}
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["projection"]["arms"][source.POSITIONAL]["symbolic_memory"]["live_allocation"] = True
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["projection"]["cross_arm_ranking"] = [source.POSITIONAL, source.BATCHED_RRNS]
        mutations.append(bad)
        bad = deepcopy(baseline)
        bad["projection"]["arms"][source.POSITIONAL]["phase_projections"][0]["endpoints"]["complete_10"]["phase_ratio"] = [1, 1]
        mutations.append(bad)
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(ValueError):
                reader.validate_projection_document(
                    mutation,
                    reader_snapshot(snapshot),
                    validate_dependencies=False,
                )

    def test_noncanonical_and_duplicate_json_reject(self) -> None:
        snapshot = source_snapshot()
        document = synthetic_document(snapshot)
        canonical = source.canonical_json_bytes(document)
        parsed = json.loads(canonical)
        self.assertEqual(parsed, document)
        duplicate = b'{"a":1,"a":2}\n'
        with self.assertRaises(ValueError):
            json.loads(duplicate, object_pairs_hook=reader._unique_object)


if __name__ == "__main__":
    unittest.main()
