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
            "STATUS.md": ("ADR-0312", "Seal the native-simplex audit compiler and corpora"),
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
            "STATUS.md": ("ADR-0313", "Seal the native-simplex audit runner before results"),
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
            "STATUS.md": ("ADR-0314", "Retain the native-simplex audit and reject the frozen gate"),
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

    def test_artifact_only_gate_correction_and_solver_trust_model_are_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0315", "authoritative retained-evidence read"),
            "PROJECT.md": ("ADR-0315", "temporally separated exact-digest reanalysis"),
            "STATUS.md": ("ADR-0315", "Source-seal the artifact-only native-simplex"),
            "ROADMAP.md": (
                "persistent warm HiGHS",
                "product-of-simplexes proposer",
            ),
            "RUNBOOK.md": (
                "reanalyze_sealed_adr0314_artifact",
                "0755546e6260708ffb4165ec50ebf4ff88c473354faeb7303e8b84e568fca1be",
            ),
            "ARCHITECTURE.md": (
                "native_simplex_audit_reanalysis",
                "optional complete failing-set identity",
            ),
            "RISK_REGISTER.md": (
                "R76",
                "post-outcome artifact reanalysis",
                "R77",
                "untrusted proposer",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_corrected_audit_pass_and_bounded_replacement_eligibility_are_visible(
        self,
    ) -> None:
        expected = {
            "README.md": ("ADR-0316", "prospective replacement-adapter"),
            "PROJECT.md": ("ADR-0316", "passes with zero failures"),
            "STATUS.md": (
                "ADR-0316",
                "Accept the corrected audit and bound replacement eligibility",
            ),
            "ROADMAP.md": (
                "eligible only to enter a later",
                "persistent warm HiGHS",
            ),
            "RUNBOOK.md": (
                "f44d518bba0953c064cd04c3015c37ec8abf27a91a96afa9902caf16c8ffe038",
                "nonexclusive 21-row",
            ),
            "ARCHITECTURE.md": (
                "ADR-0316",
                "corrected gate has zero failures",
            ),
            "RISK_REGISTER.md": (
                "R78",
                "stale basis/model",
                "authorize no consumer on audit evidence alone",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_solver_classes_and_materiality_boundary_are_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0317", "5%"),
            "PROJECT.md": ("compact reduced-sizing LP", "0.063%-0.151%"),
            "STATUS.md": (
                "ADR-0317",
                "Separate solver classes and prioritize the certified sizing adapter",
            ),
            "ROADMAP.md": ("perfect-solver materiality trigger", "rejected native simplex"),
            "RUNBOOK.md": ("177-base schedule", "behavioral master already uses HiGHS"),
            "ARCHITECTURE.md": ("ADR-0317", "Historical behavioral-master v1"),
            "RISK_REGISTER.md": ("R79", "Evidence from one LP class"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_certified_sizing_adapter_source_boundary_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0318", "untrusted proposer"),
            "PROJECT.md": ("177-canonical-base", "11 controls"),
            "STATUS.md": ("ADR-0318", "HiGHS 1.12.0"),
            "ROADMAP.md": ("ADR-0318", "exact behavioral/outward-bound"),
            "RUNBOOK.md": (
                "4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f",
                "128 fresh sizing bases",
            ),
            "ARCHITECTURE.md": (
                "certified_reduced_sizing_highs",
                "no legacy sizing consumer imports",
            ),
            "RISK_REGISTER.md": ("R80", "policy repair hides a semantic failure"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_canonical_sizing_validation_source_boundary_is_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0319", "one public HiGHS-DS proposal"),
            "PROJECT.md": ("one-public-call counter", "129 sizing bases"),
            "STATUS.md": ("ADR-0319", "one public HiGHS-DS call"),
            "ROADMAP.md": ("ADR-0319", "exact ordered 177-base schedule"),
            "RUNBOOK.md": (
                "5116c1d4b2632da76cf83e6d7d015b190e061330094d27b3c9719631a89252e1",
                "48 canonical exact-micro paths",
            ),
            "ARCHITECTURE.md": (
                "certified_sizing_validation_runner",
                "129 sizing passes",
            ),
            "RISK_REGISTER.md": ("R81", "loses backend accountability"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_canonical_certified_sizing_pass_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0320", "177 observations pass"),
            "PROJECT.md": ("129/129 sizing", "8.50e-11"),
            "STATUS.md": ("All 177 ordered observations pass", "consumer eligible"),
            "ROADMAP.md": ("ADR-0320", "own-column and opponent-row"),
            "RUNBOOK.md": (
                "5a2a75a9cf0ddaf60795597aa6ff3f788d4bfc7ccf5519813f37856dad02f9f5",
                "Do not rerun the campaign",
            ),
            "ARCHITECTURE.md": ("sole canonical campaign", "No module fills"),
            "RISK_REGISTER.md": ("R82", "stale response rows"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_certified_v2_consumer_preregistration_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0321", "fold/call-only"),
            "PROJECT.md": ("research-only boundary", "distinct reduced bet increments"),
            "STATUS.md": ("ADR-0321", "caller-owned legal fallback"),
            "ROADMAP.md": ("ADR-0321", "not a six-player action chooser"),
            "RUNBOOK.md": ("two-live-seat river", "one counted public HiGHS-DS call"),
            "ARCHITECTURE.md": ("typed no-action rejection", "Actual responder raises"),
            "RISK_REGISTER.md": ("R83", "raise-to street total"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_certified_v2_consumer_source_boundary_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0322", "Eleven unsealed controls"),
            "PROJECT.md": ("ADR-0322", "every rejection retains its cause chain"),
            "STATUS.md": ("ADR-0322", "no action"),
            "ROADMAP.md": ("ADR-0322", "best-subset teachers"),
            "RUNBOOK.md": (
                "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a",
                "full-versus-restricted scope",
            ),
            "ARCHITECTURE.md": ("recompile and rebind", "eleven tests are unsealed"),
            "RISK_REGISTER.md": ("R84", "complete exception chain"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_finite_block_action_width_preregistration_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0323", "not action-abstraction v5"),
            "PROJECT.md": ("exhaustive best-subset teachers", "opponent-row identity"),
            "STATUS.md": ("ADR-0323", "value-free"),
            "ROADMAP.md": ("raise widths two through six", "Development selects"),
            "RUNBOOK.md": ("Check does not count as a raise", "L_full-U_subset"),
            "ARCHITECTURE.md": ("not an ordinary standalone LP column", "finite difference"),
            "RISK_REGISTER.md": ("R85", "stale-row reduced cost"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_fresh_action_width_structure_seal_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0324", "12,556"),
            "PROJECT.md": ("7/9/11 raises", "candidate-blind qualifier"),
            "STATUS.md": ("ADR-0324", "value-unopened"),
            "ROADMAP.md": ("96-context fresh", "full-versus-width-two"),
            "RUNBOOK.md": (
                "429f72fff02de515536db36a4754708e71cf93653ad6574026c1fe3c4de82acf",
                "not solver calls or latency",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_structures",
                "12,556 future subsets",
            ),
            "RISK_REGISTER.md": ("R86", "sign diversity as sizing power"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_action_width_qualification_source_seal_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0325", "192-task"),
            "PROJECT.md": ("L_full-U_subset", "call-accounting status"),
            "STATUS.md": ("ADR-0325", "exactly once"),
            "ROADMAP.md": ("target-only panel", "one authorized invocation"),
            "RUNBOOK.md": (
                "95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7",
                "at most once",
            ),
            "ARCHITECTURE.md": ("fresh_action_width_qualification", "float hex endpoints"),
            "RISK_REGISTER.md": ("R87", "Full lower is compared with subset lower"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_action_width_qualification_result_and_panel_are_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0326", "2,495-task"),
            "PROJECT.md": ("16-context development panel", "solver call"),
            "STATUS.md": ("ADR-0326", "exhaustive bounded development-teacher"),
            "ROADMAP.md": ("51 contexts", "set-valued dominance/equivalence"),
            "RUNBOOK.md": (
                "d8bcf79a08eed1af6fece257b4917424e71123574c4a99b858c7a7e93cf2a7f5",
                "never rerun a one-shot campaign",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_qualification_result",
                "95,083-byte",
            ),
            "RISK_REGISTER.md": ("R88", "terminal renderer"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_exhaustive_teacher_source_seal_is_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0327", "reporting-only equivalence set"),
            "PROJECT.md": ("2,479 anchored", "cardinality is the flatness"),
            "STATUS.md": ("ADR-0327", "exhaustive bounded development-teacher"),
            "ROADMAP.md": ("potentially empty reporting equivalence", "plateau cardinality"),
            "RUNBOOK.md": (
                "14250c3dbe504318640fc0ca35098c5c014e03eca23d3ea8fee4ec470705b8fd",
                "staging marker is created and fsynced",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_teacher",
                "no secondary runtime rule can edit",
            ),
            "RISK_REGISTER.md": ("R89", "permit an empty equivalence set"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_exhaustive_teacher_result_is_rebound_and_not_overpromoted(self) -> None:
        expected = {
            "README.md": ("ADR-0328", "not a selected action width"),
            "PROJECT.md": ("4,975,258-byte", "49 of 64 context-widths"),
            "STATUS.md": ("ADR-0328", "direct closed finite-block greedy"),
            "ROADMAP.md": ("all 2,495 calls complete", "full-regret-only"),
            "RUNBOOK.md": (
                "6da6f43a02c6a0f97237bcdc9c66f845bac5735c290236d0ffdab481b7f82765",
                "solver-free owner",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_teacher_result",
                "49 plateaus",
            ),
            "RISK_REGISTER.md": ("R90", "campaign wall"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_closed_finite_block_greedy_owner_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0329", "exactly 400 calls"),
            "PROJECT.md": ("7,848 possible", "all five frozen conjuncts"),
            "STATUS.md": ("ADR-0329", "exactly once"),
            "ROADMAP.md": ("complete adaptive graph", "no-retry development"),
            "RUNBOOK.md": (
                "a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a",
                "own block, complete semantic fold/call response",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_greedy",
                "eight-row own block",
            ),
            "RISK_REGISTER.md": ("R91", "7,848-edge graph"),
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
