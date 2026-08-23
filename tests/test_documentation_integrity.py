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

    def test_action_clock_and_preparation_successor_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0308", "LegalDecisionSpineV2"),
            "PROJECT.md": ("ActionClockLedger", "PreparationBank"),
            "ROADMAP.md": ("ADR-0308", "quality evidence remain absent"),
            "RUNBOOK.md": (
                "pontius.legal_decision_spine_v2",
                "claim_preparation",
            ),
            "ARCHITECTURE.md": ("implemented and accepted", "live host"),
            "RISK_REGISTER.md": ("R67", "R68", "marginal decision quality"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_capacity_filling_structural_freeze_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0309", "48/96/96"),
            "PROJECT.md": ("qualified-A", "748-context"),
            "ROADMAP.md": ("239/570/451", "candidate-blind qualification"),
            "RUNBOOK.md": (
                "fresh_capacity_filling_structures",
                "qualified-A",
            ),
            "ARCHITECTURE.md": (
                "fresh_capacity_filling_structures",
                "finite-inventory disjoint",
            ),
            "RISK_REGISTER.md": ("R66", "R69", "value-free fresh stream"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_capacity_filling_qualification_rejection_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0310", "context 21"),
            "PROJECT.md": ("ADR-0310", "A is provisional"),
            "STATUS.md": ("ADR-0310", "native-simplex robustness"),
            "ROADMAP.md": ("qualified B", "numerical kill criterion"),
            "RUNBOOK.md": (
                "fresh_capacity_filling_qualification",
                "03c5dc4f00c0429d3c615352a1d52f9c64dec0d3b4c4cf72f6d7cc171e3a26fe",
            ),
            "ARCHITECTURE.md": (
                "fresh_capacity_filling_qualification",
                "digest-bound numerical failure",
            ),
            "RISK_REGISTER.md": ("R70", "post-outcome solver substitution"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_native_simplex_audit_preregistration_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0311", "metamorphic representations"),
            "PROJECT.md": ("48 exact micro LPs", "HiGHS-IPM"),
            "STATUS.md": ("ADR-0311", "Preregister the native-simplex robustness audit"),
            "ROADMAP.md": ("five exact metamorphic representations", "ADR-0311"),
            "RUNBOOK.md": ("177-base/885-instance", "Do not edit"),
            "ARCHITECTURE.md": (
                "48 exact bounded micro LP inputs",
                "original-coordinate feasible sizing reconstruction",
            ),
            "RISK_REGISTER.md": ("R71", "overfit to one known failure"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_native_simplex_audit_value_free_seal_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0312", "885 exact representations"),
            "PROJECT.md": ("finite 988-context inventory", "runner and result-schema"),
            "STATUS.md": ("ADR-0312", "2,655-invocation schedule"),
            "ROADMAP.md": ("ADR-0312", "No optimum or backend result"),
            "RUNBOOK.md": (
                "4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3",
                "2,655-call schedule",
            ),
            "ARCHITECTURE.md": ("All 885 materialized representations", "No runner"),
            "RISK_REGISTER.md": ("R72", "duplicate numerical LP"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_native_simplex_audit_runner_seal_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0313", "2,655-call schedule"),
            "PROJECT.md": (
                "cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16",
                "one-shot complete audit invocation",
            ),
            "STATUS.md": ("ADR-0313", "2,655 scheduled observations"),
            "ROADMAP.md": ("embedded HiGHS 1.12.0", "Only unsealed toys"),
            "RUNBOOK.md": (
                "execute_sealed_adr0311_audit",
                "full variant-major 2,655-observation campaign",
            ),
            "ARCHITECTURE.md": (
                "native_simplex_audit_runner",
                "immutable failure-complete observations",
            ),
            "RISK_REGISTER.md": ("R73", "wrong-sign hints"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_native_simplex_audit_frozen_gate_rejection_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0314", "36 failures"),
            "PROJECT.md": ("all 2,655 arms", "complete above-allowance row set"),
            "STATUS.md": ("ADR-0314", "artifact-bound semantic-gate correction"),
            "ROADMAP.md": ("known-native-regression-mismatch", "1,770 HiGHS arms"),
            "RUNBOOK.md": (
                "1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a",
                "complete failing-row tuple",
            ),
            "ARCHITECTURE.md": (
                "849 verified returns and 36 exceptions",
                "literal gate rejects",
            ),
            "RISK_REGISTER.md": (
                "R74",
                "unique maximum-residual row",
                "R75",
                "core.autocrlf=true",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

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
