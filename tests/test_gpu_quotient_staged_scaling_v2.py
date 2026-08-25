from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from pontius.durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordKind,
)
from pontius.gpu_quotient_staged_scaling import (
    GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
    STAGE_CARDS,
    build_synthetic_stage_payload,
    stage_semantic_identity,
)
from pontius import gpu_quotient_staged_scaling_v2_runner as runner
from pontius.gpu_quotient_staged_scaling_v2_result import (
    rebind_staged_scaling_v2_journal,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/gpu-quotient-staged-scaling-v2.json"
_RESULT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl"
_PARTIAL = Path(f"{_RESULT}.partial")
_V1_RESULT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl"
_V1_PARTIAL = Path(f"{_V1_RESULT}.partial")
_MARKER = _ROOT / "artifacts/README.md"


class GpuQuotientStagedScalingV2Tests(unittest.TestCase):
    def test_source_seal_config_rebinds_without_changing_stage_science(self) -> None:
        payload = json.loads(_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(runner.parse_config(payload), payload)
        self.assertEqual(payload["stage_cards"], list(STAGE_CARDS))
        self.assertNotIn(45, payload["stage_cards"])
        self.assertEqual(
            payload["parent_failure"],
            "journal parent directory does not exist",
        )
        mutation = deepcopy(payload)
        mutation["stage_cards"][-1] = 45
        with self.assertRaisesRegex(ValueError, "stage_cards"):
            runner.parse_config(mutation)

    def test_tracked_parent_and_closed_v1_are_literal_public_preconditions(self) -> None:
        payload = json.loads(_CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(_MARKER.is_file())
        self.assertEqual(
            runner.canonical_lf_sha256(_MARKER),
            payload["expected_artifact_marker_sha256"],
        )
        self.assertFalse(_PARTIAL.exists())
        self.assertFalse(_V1_RESULT.exists())
        self.assertFalse(_V1_PARTIAL.exists())
        if _RESULT.exists():
            result = rebind_staged_scaling_v2_journal(
                _RESULT.read_bytes(),
                expected_config_sha256=sha256(_CONFIG.read_bytes()).hexdigest(),
            )
            self.assertIn(
                result.terminal,
                {
                    "completed_pass",
                    "completed_stage_rejection",
                    "infrastructure_failure",
                },
            )
        else:
            runner.validate_public_bootstrap(payload)

    def test_bootstrap_preflight_fails_closed_without_creating_any_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "artifacts"
            marker = parent / "README.md"
            output = parent / "result.jsonl"
            partial = Path(f"{output}.partial")

            with self.assertRaisesRegex(FileNotFoundError, "parent"):
                runner.validate_output_bootstrap(
                    output_path=output,
                    partial_path=partial,
                    marker_path=marker,
                    expected_marker_sha256="0" * 64,
                )
            self.assertFalse(parent.exists())

            parent.mkdir()
            marker.write_text("tracked marker\n", encoding="ascii", newline="\n")
            marker_sha256 = runner.canonical_lf_sha256(marker)
            runner.validate_output_bootstrap(
                output_path=output,
                partial_path=partial,
                marker_path=marker,
                expected_marker_sha256=marker_sha256,
            )
            self.assertFalse(output.exists())
            self.assertFalse(partial.exists())

            with self.assertRaisesRegex(ValueError, "drifted"):
                runner.validate_output_bootstrap(
                    output_path=output,
                    partial_path=partial,
                    marker_path=marker,
                    expected_marker_sha256="0" * 64,
                )
            output.write_bytes(b"retained")
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                runner.validate_output_bootstrap(
                    output_path=output,
                    partial_path=partial,
                    marker_path=marker,
                    expected_marker_sha256=marker_sha256,
                )

    def test_v2_owner_is_additive_and_preflights_before_stage_execution(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn(
            "from .gpu_quotient_staged_scaling_runner import",
            source,
        )
        self.assertNotIn(".mkdir(", source)
        main = source[source.index("def main()") :]
        self.assertLess(
            main.index("validate_public_bootstrap(config)"),
            main.index("strict_git_metadata()"),
        )
        self.assertLess(
            main.index("strict_git_metadata()"),
            main.index("execute_campaign_to_path("),
        )

    def test_synthetic_complete_journal_rebinds_and_exclusive_replay_fails(self) -> None:
        calls: list[int] = []

        def synthetic(cards: int):
            calls.append(cards)
            return build_synthetic_stage_payload(cards)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="a" * 64,
                source_commit="b" * 40,
                stage_executor=synthetic,
            )
            self.assertEqual(terminal["terminal"], "completed_pass")
            result = rebind_staged_scaling_v2_journal(
                path.read_bytes(),
                expected_config_sha256="a" * 64,
                expected_source_commit="b" * 40,
            )
            self.assertTrue(result.passed)
            self.assertEqual(result.completed_stage_cards, STAGE_CARDS)
            self.assertEqual(calls, list(STAGE_CARDS))
            with self.assertRaises(FileExistsError):
                runner.execute_campaign_to_path(
                    output_path=path,
                    config_sha256="a" * 64,
                    source_commit="b" * 40,
                    stage_executor=synthetic,
                )

    def test_scientific_rejection_and_exception_stop_at_the_first_boundary(self) -> None:
        rejected_calls: list[int] = []

        def rejected(cards: int):
            rejected_calls.append(cards)
            return build_synthetic_stage_payload(cards, passed=cards != 28)

        with tempfile.TemporaryDirectory() as directory:
            rejected_path = Path(directory) / "rejected.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=rejected_path,
                config_sha256="c" * 64,
                source_commit="d" * 40,
                stage_executor=rejected,
            )
            self.assertEqual(terminal["terminal"], "completed_stage_rejection")
            result = rebind_staged_scaling_v2_journal(rejected_path.read_bytes())
            self.assertEqual(result.failed_stage_cards, 28)
            self.assertEqual(rejected_calls, [10, 16, 22, 28])

            failed_calls: list[int] = []

            def failed(cards: int):
                failed_calls.append(cards)
                if cards == 22:
                    raise RuntimeError("injected v2 stage failure")
                return build_synthetic_stage_payload(cards)

            failed_path = Path(directory) / "failed.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=failed_path,
                config_sha256="e" * 64,
                source_commit="f" * 40,
                stage_executor=failed,
            )
            self.assertEqual(terminal["terminal"], "infrastructure_failure")
            result = rebind_staged_scaling_v2_journal(failed_path.read_bytes())
            self.assertEqual(result.completed_stage_cards, (10, 16))
            self.assertEqual(result.failed_stage_cards, 22)
            self.assertEqual(failed_calls, [10, 16, 22])

    def test_before_and_after_stage_campaign_walls_have_distinct_seams(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before_path = root / "before.jsonl"
            before_clock = iter((0.0, 601.0))
            terminal = runner.execute_campaign_to_path(
                output_path=before_path,
                config_sha256="1" * 64,
                source_commit="2" * 40,
                stage_executor=lambda cards: self.fail("stage must not run"),
                monotonic=lambda: next(before_clock),
            )
            self.assertEqual(terminal["reason"], "campaign_wall_crossed_before_stage")
            before = rebind_staged_scaling_v2_journal(before_path.read_bytes())
            self.assertEqual(before.completed_stage_cards, ())
            self.assertEqual(before.failed_stage_cards, 10)

            after_path = root / "after.jsonl"
            after_clock = iter((0.0, 0.0, 601.0))
            terminal = runner.execute_campaign_to_path(
                output_path=after_path,
                config_sha256="3" * 64,
                source_commit="4" * 40,
                stage_executor=build_synthetic_stage_payload,
                monotonic=lambda: next(after_clock),
            )
            self.assertEqual(terminal["reason"], "campaign_wall_crossed_after_stage")
            after = rebind_staged_scaling_v2_journal(after_path.read_bytes())
            self.assertEqual(after.completed_stage_cards, (10,))
            self.assertEqual(after.failed_stage_cards, 10)

    def test_torn_suffix_semantic_mutation_and_campaign_seam_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "complete.jsonl"
            runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="5" * 64,
                source_commit="6" * 40,
                stage_executor=build_synthetic_stage_payload,
            )
            raw = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                rebind_staged_scaling_v2_journal(raw[:-13])

            mutation_path = root / "mutation.jsonl"
            campaign = runner.campaign_identity(
                config_sha256="7" * 64,
                source_commit="8" * 40,
            )
            header = runner._header_payload(
                config_sha256="7" * 64,
                source_commit="8" * 40,
                campaign_sha256=campaign,
            )
            stage = build_synthetic_stage_payload(10)
            stage["work"] = {**stage["work"], "cold_source_pairing_visits": 7}
            terminal = runner._terminal_payload(
                terminal="infrastructure_failure",
                completed_stage_cards=[10],
                failed_stage_cards=16,
                reason="synthetic semantic mutation",
                campaign_wall_ms=1.0,
            )
            with DurableEvidenceJournalWriter.create(
                path=mutation_path,
                protocol_sha256=GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
                campaign_sha256=campaign,
            ) as writer:
                writer.append(
                    kind=JournalRecordKind.HEADER,
                    semantic_identity_sha256=runner._semantic_digest(header),
                    payload=header,
                )
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=stage_semantic_identity(10),
                    payload=stage,
                )
                writer.append(
                    kind=JournalRecordKind.TERMINAL,
                    semantic_identity_sha256=runner._semantic_digest(terminal),
                    payload=terminal,
                )
            with self.assertRaisesRegex(ValueError, "work ledger"):
                rebind_staged_scaling_v2_journal(mutation_path.read_bytes())

            seam_path = root / "campaign-seam.jsonl"
            envelope_campaign = "9" * 64
            clean_terminal = runner._terminal_payload(
                terminal="infrastructure_failure",
                completed_stage_cards=[],
                failed_stage_cards=10,
                reason="synthetic envelope seam",
                campaign_wall_ms=1.0,
            )
            with DurableEvidenceJournalWriter.create(
                path=seam_path,
                protocol_sha256=GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
                campaign_sha256=envelope_campaign,
            ) as writer:
                writer.append(
                    kind=JournalRecordKind.HEADER,
                    semantic_identity_sha256=runner._semantic_digest(header),
                    payload=header,
                )
                writer.append(
                    kind=JournalRecordKind.TERMINAL,
                    semantic_identity_sha256=runner._semantic_digest(clean_terminal),
                    payload=clean_terminal,
                )
            with self.assertRaisesRegex(ValueError, "envelope/header campaign seam"):
                rebind_staged_scaling_v2_journal(seam_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
