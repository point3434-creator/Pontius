from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

_ROOT = Path(__file__).parents[1]
_MAINTAINED = (
    _ROOT / "README.md",
    _ROOT / "PROJECT.md",
    _ROOT / "STATUS.md",
    _ROOT / "ROADMAP.md",
    _ROOT / "RUNBOOK.md",
    _ROOT / "ARCHITECTURE.md",
    _ROOT / "RISK_REGISTER.md",
    _ROOT / "experiments/RESULTS.md",
    _ROOT / "docs/reviews/C1-exact-game-laboratory.md",
)
_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def _contract_text(relative: str) -> str:
    """Read prose contracts without making line wrapping semantically relevant."""

    return " ".join((_ROOT / relative).read_text(encoding="utf-8").split())


class DocumentationIntegrityTests(unittest.TestCase):
    def test_maintained_local_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for source in _MAINTAINED:
            self.assertTrue(source.is_file(), source)
            for raw_target in _LINK.findall(source.read_text(encoding="utf-8")):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith(("mailto:", "#")):
                    continue
                destination = (source.parent / unquote(target)).resolve()
                if not destination.exists():
                    failures.append(f"{source.relative_to(_ROOT)} -> {raw_target}")
        self.assertEqual([], failures)

    def test_current_contract_is_visible_in_every_front_door(self) -> None:
        expected = {
            "README.md": ("six-player river control", "15-second"),
            "PROJECT.md": ("15,000 ms", "immutable blueprint"),
            "ROADMAP.md": ("ADR-0184", "direction/opportunity"),
            "RUNBOOK.md": ("PONTIUS_CUDA_DLL_DIRECTORY", "pontius.runner_harness"),
            "ARCHITECTURE.md": (
                "Current h32 execution spine",
                "deadline-admitted exact winner certificate",
            ),
            "RISK_REGISTER.md": ("R36", "Coincidental equality"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_active_campaign_deadline_is_visible_in_maintained_contracts(self) -> None:
        expected = {
            "PROJECT.md": ("shared monotonic deadline", "15-second action-response wall"),
            "ROADMAP.md": ("ADR-0279", "12.966 seconds"),
            "RUNBOOK.md": (
                "campaign_deadline",
                "MonotonicCampaignDeadline",
                "CampaignDeadlineStop",
            ),
            "ARCHITECTURE.md": (
                "campaign_deadline",
                "MonotonicCampaignDeadline",
                "campaign overrun",
            ),
            "RISK_REGISTER.md": ("R41", "R42"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_fifteen_second_wall_is_the_authoritative_action_contract(self) -> None:
        project = _contract_text("PROJECT.md")
        roadmap = _contract_text("ROADMAP.md")
        architecture = _contract_text("ARCHITECTURE.md")
        self.assertIn("15,000 ms wall-clock response deadline", project)
        self.assertIn("A later controlled action receives a new response wall", project)
        self.assertNotIn("Initial online budgets", project)
        self.assertIn(
            "Older cumulative-street and 5-250 ms targets are historical only",
            roadmap,
        )
        self.assertIn("does not pause through emission", architecture)
        runbook = _contract_text("RUNBOOK.md")
        risks = _contract_text("RISK_REGISTER.md")
        for relative, text in (("RUNBOOK.md", runbook), ("RISK_REGISTER.md", risks)):
            self.assertIn("action-response", text, relative)
            self.assertNotIn("per-decision live ledger", text, relative)

    def test_review_successors_and_claim_boundaries_remain_visible(self) -> None:
        expected = {
            "PROJECT.md": ("completion-seal phases", "probability feasibility"),
            "ROADMAP.md": ("ADR-0285", "No h32"),
            "RUNBOOK.md": ("runner_harness_v2", "StreetDeadlineLedger"),
            "ARCHITECTURE.md": ("separately persisted seal", "dense coefficient oracle"),
            "RISK_REGISTER.md": ("R49", "R50", "R51"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_decision_spine_and_charged_idle_boundary_are_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0288", "ADR-0286", "1,225/1,081/1,035/990"),
            "PROJECT.md": ("Opponent think and transport idle", "legal decision spine"),
            "ROADMAP.md": (
                "45,456 semantic states",
                "complete reference hand replay",
                "ADR-0288",
            ),
            "RUNBOOK.md": (
                "pontius.no_limit_betting",
                "charge_compute()",
                "immutable-blueprint fallback",
                "replay_reference_hand",
            ),
            "ARCHITECTURE.md": (
                "Exact legal decision spine",
                "folded-only threshold",
                "Opponent or transport idle is paused",
                "complete explicit-deal reference hand loop",
            ),
            "RISK_REGISTER.md": ("R52", "R53", "R54", "R55", "R56", "R57"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")


if __name__ == "__main__":
    unittest.main()
