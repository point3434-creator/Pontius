from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pontius.status_generation import read_decision_headers, render_status

_ROOT = Path(__file__).parents[1]


class StatusGenerationTests(unittest.TestCase):
    def test_status_is_exact_generated_output_from_current_adrs(self) -> None:
        self.assertEqual(
            (_ROOT / "STATUS.md").read_text(encoding="utf-8"),
            render_status(_ROOT),
        )

    def test_decision_numbers_are_unique_and_latest_decision_is_visible(self) -> None:
        rows = read_decision_headers(_ROOT / "docs/decisions")
        self.assertEqual(len({row.number for row in rows}), len(rows))
        rendered = render_status(_ROOT)
        self.assertIn(f"ADR-{rows[-1].number:04d}", rendered)
        self.assertIn(rows[-1].title, rendered)

    def test_runtime_contract_remains_visible_outside_the_recent_ledger(self) -> None:
        rendered = render_status(_ROOT, recent_count=1)
        self.assertIn("## Governing runtime contract", rendered)
        self.assertIn("[ADR-0282]", rendered)
        self.assertIn("fifteen-second street wall", rendered)

    def test_front_door_heads_do_not_depend_on_title_or_status_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decisions = root / "docs" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "ADR-0001-research.md").write_text(
                "# ADR-0001: Preregister process words in a research title\n\n"
                "- Status: accepted preregistration process result\n"
                "- Date: 2026-08-22\n\n"
                "## Decision\n\nResearch head.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0002-revoked.md").write_text(
                "# ADR-0002: Ordinary title\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n\n"
                "## Decision\n\nOld gate.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0003-controller.md").write_text(
                "# ADR-0003: Front-door controller\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-0003\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: ADR-0002\n"
                "- Front-Door-Active-Next: Build the replacement gate\n"
                "- Front-Door-Blockers: replacement is not preregistered\n\n"
                "## Decision\n\nControl the front door.\n",
                encoding="utf-8",
            )

            rendered = render_status(root)
            self.assertIn("Latest accepted research result: [ADR-0001]", rendered)
            self.assertIn("Latest process decision: [ADR-0003]", rendered)
            self.assertIn("revoked by ADR-0003", rendered)
            self.assertIn("## Active next\n\nBuild the replacement gate", rendered)
            self.assertIn(
                "Current blockers: replacement is not preregistered.", rendered
            )
            compact = render_status(root, recent_count=1)
            self.assertIn("## Revoked authorities", compact)
            self.assertIn("[ADR-0002]", compact)
            self.assertIn("revoked by [ADR-0003]", compact)

    def test_incomplete_front_door_snapshot_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decisions = root / "docs" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "ADR-0001-partial.md").write_text(
                "# ADR-0001: Partial controller\n\n"
                "- Status: accepted\n"
                "- Front-Door-Research: ADR-0001\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "incomplete front-door"):
                render_status(root)

    def test_latest_adr_cannot_silently_reuse_an_older_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decisions = root / "docs" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "ADR-0001-controller.md").write_text(
                "# ADR-0001: Controller\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-0001\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: none\n"
                "- Front-Door-Active-Next: Old next\n"
                "- Front-Door-Blockers: none\n\n"
                "## Decision\n\nOld decision.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0002-new-result.md").write_text(
                "# ADR-0002: New result without snapshot\n\n"
                "- Status: accepted\n\n"
                "## Decision\n\nNew decision.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "latest ADR must carry"):
                render_status(root)

    def test_later_snapshot_cannot_forget_a_revocation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decisions = root / "docs" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "ADR-0001-research.md").write_text(
                "# ADR-0001: Research\n\n- Status: accepted\n- Date: 2026-08-22\n\n"
                "## Decision\n\nResearch.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0002-revoked.md").write_text(
                "# ADR-0002: Unsafe authority\n\n- Status: accepted\n- Date: 2026-08-22\n\n"
                "## Decision\n\nUnsafe.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0003-controller.md").write_text(
                "# ADR-0003: Revoke\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-0003\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: ADR-0002\n"
                "- Front-Door-Active-Next: Build a replacement\n"
                "- Front-Door-Blockers: replacement absent\n\n"
                "## Decision\n\nRevoke it.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0004-controller.md").write_text(
                "# ADR-0004: Forget\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-0004\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: none\n"
                "- Front-Door-Active-Next: Reconsider ADR-0002\n"
                "- Front-Door-Blockers: none\n\n"
                "## Decision\n\nForget it.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "cannot forget prior revocations"):
                render_status(root)

    def test_adr_chain_requires_contiguous_matching_filename_and_title_numbers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            decisions = Path(directory)
            (decisions / "ADR-0001-first.md").write_text(
                "# ADR-0001: First\n\n## Decision\n\nFirst.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0003-gap.md").write_text(
                "# ADR-0003: Gap\n\n## Decision\n\nGap.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "contiguous"):
                read_decision_headers(decisions)

        with tempfile.TemporaryDirectory() as directory:
            decisions = Path(directory)
            (decisions / "ADR-0001-wrong.md").write_text(
                "# ADR-0002: Wrong title number\n\n## Decision\n\nWrong.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "filename/title"):
                read_decision_headers(decisions)

    def test_every_historical_front_door_snapshot_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decisions = root / "docs" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "ADR-0001-research.md").write_text(
                "# ADR-0001: Research\n\n- Status: accepted\n- Date: 2026-08-22\n\n"
                "## Decision\n\nResearch.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0002-stale-controller.md").write_text(
                "# ADR-0002: Invalid old controller\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-9999\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: none\n"
                "- Front-Door-Active-Next: Old next\n"
                "- Front-Door-Blockers: none\n\n"
                "## Decision\n\nInvalid.\n",
                encoding="utf-8",
            )
            (decisions / "ADR-0003-current-controller.md").write_text(
                "# ADR-0003: Valid current controller\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-0003\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: none\n"
                "- Front-Door-Active-Next: Current next\n"
                "- Front-Door-Blockers: none\n\n"
                "## Decision\n\nValid.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "future ADR"):
                render_status(root)

    def test_header_metadata_is_scanned_until_the_first_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            decisions = Path(directory)
            filler = "".join(f"header filler {index}\n" for index in range(40))
            (decisions / "ADR-0001-controller.md").write_text(
                "# ADR-0001: Controller\n\n"
                "- Status: accepted\n"
                "- Date: 2026-08-22\n"
                "- Front-Door-Kind: controller-v1\n"
                "- Front-Door-Research: ADR-0001\n"
                "- Front-Door-Process: ADR-0001\n"
                "- Front-Door-Contract: ADR-0001\n"
                "- Front-Door-Revoked: none\n"
                "- Front-Door-Active-Next: Next\n"
                "- Front-Door-Blockers: none\n"
                + filler
                + "- Front-Door-Revoked: ADR-0000\n\n"
                "## Decision\n\nControl.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "repeats metadata"):
                read_decision_headers(decisions)

    def test_recent_count_must_be_a_positive_integer(self) -> None:
        for value in (True, 0, -1, 1.5):
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError,
                "positive integer",
            ):
                render_status(_ROOT, recent_count=value)  # type: ignore[arg-type]

    def test_controller_requires_kind_status_date_and_decision(self) -> None:
        base = (
            "# ADR-0001: Controller\n\n"
            "- Status: accepted\n"
            "- Date: 2026-08-22\n"
            "- Front-Door-Kind: controller-v1\n"
            "- Front-Door-Research: ADR-0001\n"
            "- Front-Door-Process: ADR-0001\n"
            "- Front-Door-Contract: ADR-0001\n"
            "- Front-Door-Revoked: none\n"
            "- Front-Door-Active-Next: Next\n"
            "- Front-Door-Blockers: none\n\n"
            "## Decision\n\nControl.\n"
        )
        cases = (
            (base.replace("- Status: accepted\n", ""), "currently accepted"),
            (base.replace("- Date: 2026-08-22\n", ""), "ISO decision date"),
            (base.replace("Control.\n", ""), "nonempty Decision"),
            (
                base.replace("controller-v1", "untyped-controller"),
                "exactly controller-v1",
            ),
        )
        for content, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                decisions = root / "docs" / "decisions"
                decisions.mkdir(parents=True)
                (decisions / "ADR-0001-controller.md").write_text(
                    content,
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, message):
                    render_status(root)


if __name__ == "__main__":
    unittest.main()
