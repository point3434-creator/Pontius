from __future__ import annotations

import hashlib
import json
import math
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
            "docs/decisions/ADR-0323-preregister-certified-finite-block-action-width-research.md": (
                "ADR-0323",
                "value-free",
            ),
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

    def test_closed_finite_block_greedy_failure_and_repair_are_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0330", "58-byte `.partial`"),
            "PROJECT.md": ("unretained artifact failure", "write-ahead"),
            "STATUS.md": ("ADR-0330", "permanently closed"),
            "ROADMAP.md": ("self-referential width-gate", "non-replay"),
            "RUNBOOK.md": (
                "a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a",
                "Do not execute this campaign again",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_greedy",
                "exact 58-byte partial witness",
            ),
            "RISK_REGISTER.md": ("R92", "self-free semantic core"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_action_width_recovery_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0331", "402-record synthetic success journal"),
            "PROJECT.md": ("complete original 96-context pool", "torn-tail"),
            "STATUS.md": ("ADR-0331", "append-and-fsync"),
            "ROADMAP.md": ("all-96 semantic non-overlap", "value-free source"),
            "RUNBOOK.md": (
                "a419d1651708dae88c451546dae5639c8d1c2840a4441b93b712802a9b2541ba",
                "exactly 400 observations",
            ),
            "ARCHITECTURE.md": ("previous-envelope hash chain", "402-record"),
            "RISK_REGISTER.md": ("R93", "replay in disguise"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_population_and_durable_journal_are_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0332", "610,098-byte"),
            "PROJECT.md": ("ADR-0332", "all 402 crash prefixes"),
            "STATUS.md": ("ADR-0332", "exclusive `xb` open"),
            "ROADMAP.md": ("ADR-0332", "source-only candidate-blind qualification"),
            "RUNBOOK.md": (
                "b870feb17d6e344b130f7b30d8b776be5b40537e3e71b7a14b9b4d2bcbae3e92",
                "Do not invoke ADR-0322 on the new pool yet",
            ),
            "ARCHITECTURE.md": (
                "durable_evidence_journal",
                "post-`fsync` receipt",
            ),
            "RISK_REGISTER.md": ("R93", "internal creation capability"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_qualification_owner_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0333", "policy and dual hint"),
            "PROJECT.md": ("ADR-0333", "receipt-gated continuation"),
            "STATUS.md": ("ADR-0333", "No replacement sizing value was opened"),
            "ROADMAP.md": ("ADR-0333", "one no-clobber retained"),
            "RUNBOOK.md": (
                "c4979aa8b84ca30c80a3a4a01f4d345bd312dfef044d57243d723c71ac39cf5d",
                "journal, not terminal stdout",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_nonreplay_qualification",
                "raw inequality-multiplier hint",
            ),
            "RISK_REGISTER.md": ("R94", "loses semantic or invocation truth"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_qualification_result_and_panel_are_bounded_and_visible(self) -> None:
        expected = {
            "README.md": ("ADR-0334", "391,986-byte"),
            "PROJECT.md": ("ADR-0334", "98 accepted one-call arms"),
            "STATUS.md": ("ADR-0334", "2,113-task"),
            "ROADMAP.md": ("ADR-0334", "target-only panel"),
            "RUNBOOK.md": (
                "be33cfc4fa5955409ea478552fcdf52de62812ce37fdee94190726537b11f956",
                "Do not invoke it again",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_nonreplay_qualification_result",
                "solver-free",
            ),
            "RISK_REGISTER.md": ("R95", "old ADR-0328 teacher"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_exhaustive_teacher_is_source_sealed_and_value_unopened(self) -> None:
        expected = {
            "README.md": ("ADR-0335", "6,616,076-byte"),
            "PROJECT.md": ("ADR-0335", "2,115-record"),
            "STATUS.md": ("ADR-0335", "2,113-task"),
            "ROADMAP.md": ("ADR-0335", "sole retained"),
            "RUNBOOK.md": (
                "62598e606be983b9fef60a32933bcbbb113ab75aca5aa326bb05d1b2d8b7071f",
                "JSONL journal, not terminal stdout",
            ),
            "ARCHITECTURE.md": ("advances incrementally", "2,115-record"),
            "RISK_REGISTER.md": ("R96", "bookkeeping becomes quadratic"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_exhaustive_teacher_result_is_rebound_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0336", "mean"),
            "PROJECT.md": ("ADR-0336", "376-call"),
            "STATUS.md": ("ADR-0336", "width three"),
            "ROADMAP.md": ("ADR-0336", "positive-lower tail"),
            "RUNBOOK.md": (
                "e4347dbfc6663a636572199f11dcad517fe715d062dcee022566419382f193b0",
                "Never invoke",
            ),
            "ARCHITECTURE.md": ("descriptive median knee", "width four"),
            "RISK_REGISTER.md": ("R97", "descriptive median knee"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_direct_mechanism_is_source_sealed_and_value_unopened(
        self,
    ) -> None:
        expected = {
            "README.md": ("ADR-0337", "6,543"),
            "PROJECT.md": ("ADR-0337", "1,227,894-byte"),
            "STATUS.md": ("ADR-0337", "response-closed direct mechanism"),
            "ROADMAP.md": ("ADR-0337", "376-call"),
            "RUNBOOK.md": (
                "80ba2426399eb3329d33c0d69d58bc71112bdcc5a2608be5a3e8b4b49bfc0c9c",
                "6,543 possible transitions",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_nonreplay_greedy",
                "dynamic-branch rebinder",
            ),
            "RISK_REGISTER.md": ("R98", "wrong branch"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_nonreplay_direct_result_is_rebound_and_development_only(self) -> None:
        expected = {
            "README.md": ("ADR-0338", "97.7775%"),
            "PROJECT.md": ("ADR-0338", "1,437,835-byte"),
            "STATUS.md": ("ADR-0338", "selected development raise width"),
            "ROADMAP.md": ("ADR-0338", "untouched transfer"),
            "RUNBOOK.md": (
                "7317ff19c02efe9fa084802120289286c2a6eb1885b816087ba58b710ca27353",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_nonreplay_greedy_result",
                "no writer",
            ),
            "RISK_REGISTER.md": ("R99", "fixed production ladder"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_untouched_transfer_population_is_source_sealed_and_value_free(
        self,
    ) -> None:
        expected = {
            "README.md": ("ADR-0339", "13,587"),
            "PROJECT.md": ("ADR-0339", "1,244-context"),
            "STATUS.md": ("ADR-0339", "finite absence claim"),
            "ROADMAP.md": ("ADR-0339", "14-of-16"),
            "RUNBOOK.md": (
                "6704084f2bddfac2d58e3066b9844bc0fc633346bf3b00a7034ccc9b154e622f",
                "478 raw candidates",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_transfer_structures",
                "nonzero-base control",
            ),
            "RISK_REGISTER.md": ("R100", "collision-skipping"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_transfer_qualification_owner_is_source_sealed_and_value_unopened(
        self,
    ) -> None:
        expected = {
            "README.md": ("ADR-0340", "111,357-byte"),
            "PROJECT.md": ("ADR-0340", "cross-campaign defect"),
            "STATUS.md": ("ADR-0340", "192 prospective tasks"),
            "ROADMAP.md": ("ADR-0340", "v0a"),
            "RUNBOOK.md": (
                "6233c8161084c0bab07f902c8d6033e8aa555d51ace552017ca97f53fe402bd5",
                "run_and_retain_adr0339_transfer_qualification",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_transfer_qualification",
                "wrong synthetic/real provenance",
            ),
            "RISK_REGISTER.md": ("R101", "empty torn prefix"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_transfer_qualification_result_and_panel_are_bounded_and_visible(
        self,
    ) -> None:
        expected = {
            "README.md": ("ADR-0341", "378,108-byte"),
            "PROJECT.md": ("ADR-0341", "94 one-call arms"),
            "STATUS.md": ("ADR-0341", "94 accepted one-call arms"),
            "ROADMAP.md": ("ADR-0341", "remaining 49 transfer contexts"),
            "RUNBOOK.md": (
                "e6f25068d8362fa2bc9b40fe292506371d6d808b4696bb83c09f75ad3c8d812a",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "fresh_action_width_transfer_qualification_result",
                "payoff-span-normalized",
            ),
            "RISK_REGISTER.md": ("R102", "promoted into width-three confirmation"),
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

    def test_legal_responder_raise_keystone_is_source_sealed_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0344", "short all-in"),
            "PROJECT.md": ("16-by-18", "reporting-only"),
            "STATUS.md": ("ADR-0344", "h4 legal responder-raise"),
            "ROADMAP.md": ("one-hand gate", "full raise from two to four"),
            "RUNBOOK.md": (
                "201b937d351d50e072d4f8f00268b3242855abd8f32c468b3d5870fad1682978",
                "exclusive-create artifact",
            ),
            "ARCHITECTURE.md": (
                "legal_river_continuation",
                "eleven terminal nodes",
            ),
            "RISK_REGISTER.md": ("R105", "prediction ledger"),
            "docs/PREDICTION_LEDGER.md": ("binary Brier", "Status: open"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_responder_raise_keystone_result_is_retained_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0345", "7,400-byte"),
            "PROJECT.md": ("ADR-0345", "16-by-18"),
            "STATUS.md": ("ADR-0345", "h4 legal responder-raise"),
            "ROADMAP.md": ("All 24 gates pass", "not an action-clock"),
            "RUNBOOK.md": (
                "a7cbb0efca87ad3bf9e2a2105d10aa137daf68a763b68518d68e893bfc74be11",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "responder_raise_semantics_keystone_result",
                "authenticates",
            ),
            "RISK_REGISTER.md": ("R106", "0.791-second"),
            "docs/PREDICTION_LEDGER.md": (
                "ADR-0345 satisfies the first semantic conjunct",
                "no Brier score",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_coefficient_differential_is_source_sealed_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0346", "Fraction enumerator"),
            "PROJECT.md": ("Four payoff and two gain rows", "selector"),
            "STATUS.md": ("ADR-0346", "responder-row growth"),
            "ROADMAP.md": ("32 exactly dyadic", "not row capacity"),
            "RUNBOOK.md": (
                "e511be50649a2c1c401948d31c1245f9df890f31aceb4f53a8ef4c63c62803bc",
                "exclusive-create artifact",
            ),
            "ARCHITECTURE.md": (
                "exact_sequence_form_coefficient_oracle",
                "176 terminal paths",
            ),
            "RISK_REGISTER.md": ("R107", "power-of-two denominators"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_coefficient_result_is_retained_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0347", "100,710-byte"),
            "PROJECT.md": ("ADR-0347", "192 exact"),
            "STATUS.md": ("ADR-0347", "responder-row growth"),
            "ROADMAP.md": ("All 34 gates pass", "not row capacity"),
            "RUNBOOK.md": (
                "6dcbf8e44f1c3b2bd54694e0c1f6898082e71373846933bfaa116bc4f2c27255",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_coefficient_result",
                "gain-row algebra",
            ),
            "RISK_REGISTER.md": ("R108", "fully rehashed"),
            "docs/PREDICTION_LEDGER.md": (
                "ADR-0347 extends coefficient identity to h4",
                "no Brier score",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_row_growth_audit_is_source_sealed_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0348", "60-second subject"),
            "PROJECT.md": ("ADR-0348", "read-only observer"),
            "STATUS.md": ("ADR-0348", "selector-window"),
            "ROADMAP.md": ("ADR-0348", "oracle-call algebra"),
            "RUNBOOK.md": (
                "da6c4067cedd71504eb0c5e0c5034ffdf731839d2df71d33f0a07d12bd25cd99",
                "first exclusive-create terminal",
            ),
            "ARCHITECTURE.md": ("one_seat_row_growth_audit", "process-local lock"),
            "RISK_REGISTER.md": ("R109", "shadow solver"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_row_growth_result_is_retained_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0349", "50,963-byte"),
            "PROJECT.md": ("ADR-0349", "zero generated rows"),
            "STATUS.md": ("ADR-0349", "selector-window"),
            "ROADMAP.md": ("All 25 gates pass", "not selector stability"),
            "RUNBOOK.md": (
                "eb35843218741096f214a6c341a0762b8f1cca09a81a1fdce1db21eaa9fc60b8",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_row_growth_result",
                "50,963-byte",
            ),
            "RISK_REGISTER.md": ("R110", "zero-growth"),
            "docs/PREDICTION_LEDGER.md": (
                "ADR-0349 passes the first frozen h4 row-growth",
                "no Brier score",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_selector_normal_fan_is_source_sealed_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0350", "tie_unresolved"),
            "PROJECT.md": ("ADR-0350", "136 production selector calls"),
            "STATUS.md": ("ADR-0350", "selector-stable affine integration"),
            "ROADMAP.md": ("ADR-0350", "normal-fan"),
            "RUNBOOK.md": (
                "08d8d8d9975edd8147065893ef81f0f597fe1a687a5c5a5905fe36e2fec9f866",
                "first exclusive-create terminal",
            ),
            "ARCHITECTURE.md": ("exact_selector_fan", "z >= row"),
            "RISK_REGISTER.md": ("R111", "Total-function identity"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_selector_fan_result_is_retained_but_authority_rejected(self) -> None:
        expected = {
            "README.md": ("ADR-0351", "four such violations"),
            "PROJECT.md": ("ADR-0351", "corrected_certificate_pass: false"),
            "STATUS.md": ("ADR-0351", "tie-aware legal h4 affine-envelope"),
            "ROADMAP.md": ("ADR-0351", "authorizes nothing"),
            "RUNBOOK.md": (
                "7a1d08f1245b93b2a880f92af6c737677b7cd85b5c59a05205a8263adafcbee7",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_selector_fan_result",
                "selector_window_v2",
            ),
            "RISK_REGISTER.md": ("R112", "nonzero-window"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_tie_aware_affine_recovery_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0352", "complete maximum envelope"),
            "PROJECT.md": ("ADR-0352", "both source and current pruned tapes"),
            "STATUS.md": ("ADR-0352", "fresh untouched tie-aware affine"),
            "ROADMAP.md": ("ADR-0352", "development integration"),
            "RUNBOOK.md": (
                "9dae1dbe1c93e1952699f7a2bc11f3837bed2e2cf0296e0bafc5c5b87dceff3f",
                "first exclusive terminal",
            ),
            "ARCHITECTURE.md": (
                "exact_tie_aware_affine_envelope",
                "source and current reachable-pruned tapes",
            ),
            "RISK_REGISTER.md": ("R113", "contaminated same-fixture"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_tie_aware_bound_rejection_is_retained(self) -> None:
        expected = {
            "README.md": ("ADR-0353", "256-tape"),
            "PROJECT.md": ("ADR-0353", "961-byte"),
            "STATUS.md": ("ADR-0353", "factorized exact active-set"),
            "ROADMAP.md": ("ADR-0353", "Never replay"),
            "RUNBOOK.md": (
                "7608abd221114ed6143aa7fbf9af510a09024442f85fd8f4f3f5ed53e036f652",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_tie_aware_affine_result",
                "factorized",
            ),
            "RISK_REGISTER.md": ("R114", "Cartesian materialization"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_exact_directional_face_oracle_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0354", "two independent"),
            "PROJECT.md": ("ADR-0354", "1,073,741,824"),
            "STATUS.md": ("ADR-0354", "directional-face diagnostic"),
            "ROADMAP.md": ("ADR-0354", "billion-tape"),
            "RUNBOOK.md": (
                "cfd37e22b4e3e09321b20f6d6f3bef93f4b8fd35af6ecd13d2166ba3aee7dabf",
                "zero materialized response tapes",
            ),
            "ARCHITECTURE.md": (
                "exact_directional_face_oracle",
                "tie_semantics_conformance",
            ),
            "RISK_REGISTER.md": ("R115", "point instrument"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_directional_face_diagnostic_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0355", "136 scheduled exact point calls"),
            "PROJECT.md": ("ADR-0355", "scratch command"),
            "STATUS.md": ("ADR-0355", "invoke exactly once"),
            "ROADMAP.md": ("ADR-0355", "outcome is gated"),
            "RUNBOOK.md": (
                "5305d2fa43b386d1a7b58bf2dc96943d581013e80ad5f9966438bf11b3289fa7",
                "Never invoke the closed",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_directional_face",
                "136 scheduled point faces",
            ),
            "RISK_REGISTER.md": ("R116", "escape-sequence text"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_directional_face_result_is_retained_and_rebound(self) -> None:
        expected = {
            "README.md": ("ADR-0356", "104,976"),
            "PROJECT.md": ("ADR-0356", "zero materialized response tapes"),
            "STATUS.md": ("ADR-0356", "tie-aware affine integration"),
            "ROADMAP.md": ("ADR-0356", "104,976"),
            "RUNBOOK.md": (
                "5e3473639e67e0a24e21f3c516239c35d4bb7ccb17a6de8d74a5320428af1b49",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_directional_face_result",
                "147,418",
            ),
            "RISK_REGISTER.md": ("R117", "104,976"),
            ".gitattributes": (
                "legal-responder-raise-h4-directional-face-v1.json -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_factorized_tie_aware_affine_integration_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0357", "4,096-member face"),
            "PROJECT.md": ("ADR-0357", "one-sided endpoint slope seams"),
            "STATUS.md": ("ADR-0357", "exclusive legal h4"),
            "ROADMAP.md": ("ADR-0357", "zero fixed-tape scores"),
            "RUNBOOK.md": (
                "8a5b053e1b792ae879f5d10cd8c7614ae69e33fe2033db0d0337388375e83d6a",
                "No legal h4 target invocation is authorized",
            ),
            "ARCHITECTURE.md": (
                "factorized_tie_aware_affine",
                "tie_semantics_conformance_v2",
            ),
            "RISK_REGISTER.md": ("R118", "inward one-sided owner"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_factorized_affine_integration_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0358", "eight live builds"),
            "PROJECT.md": ("ADR-0358", "semantic section identity"),
            "STATUS.md": ("ADR-0358", "invoke exactly once"),
            "ROADMAP.md": ("ADR-0358", "outcome-only"),
            "RUNBOOK.md": (
                "e77f22b739ac714d952f0575735b5705c0b17913cf7930705dfb1588f307263c",
                "Never invoke the closed",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_factorized_affine",
                "eight live adapter builds",
            ),
            "RISK_REGISTER.md": ("R119", "sum of eight individually timed"),
            ".gitattributes": (
                "/experiments/configs/legal-responder-raise-h4-factorized-affine-v1.json -text",
                "/experiments/results/legal-responder-raise-h4-factorized-affine-v1.json -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_legal_h4_factorized_affine_result_is_retained_and_calibrated(self) -> None:
        expected = {
            "README.md": ("ADR-0359", "12 fan rows"),
            "PROJECT.md": ("ADR-0359", "authenticated-only"),
            "STATUS.md": ("ADR-0359", "fresh value-unopened"),
            "ROADMAP.md": ("ADR-0359", "18.152-second"),
            "RUNBOOK.md": (
                "301f7c9c865b8ae2cfcc39e6c6ebca32db68d4fd15e8e6255976ace587c35eea",
                "Never invoke",
            ),
            "ARCHITECTURE.md": (
                "legal_responder_raise_h4_factorized_affine_result",
                "endpoint-only",
            ),
            "RISK_REGISTER.md": ("R120", "ten interval pieces"),
            ".gitattributes": (
                "/experiments/configs/legal-responder-raise-h4-factorized-affine-v1.json -text",
                "/experiments/results/legal-responder-raise-h4-factorized-affine-v1.json -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_fresh_legal_h4_factorized_affine_confirmation_population_is_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0360", "first-in-stream"),
            "PROJECT.md": ("ADR-0360", "normalized semantic non-overlap"),
            "STATUS.md": ("ADR-0360", "exclusive untouched legal h4"),
            "ROADMAP.md": ("ADR-0360", "32-section artifact"),
            "RUNBOOK.md": (
                "902f714a11df4c861312e782b10e08ccdc62c3254b7515bdb1f73caddef32988",
                "No invocation is authorized",
            ),
            "ARCHITECTURE.md": (
                "legal_h4_factorized_affine_confirmation_population",
                "complete section rather than summaries",
            ),
            "RISK_REGISTER.md": ("R121", "reduce all probability pairs"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_full_width_capacity_telemetry_failure_is_retained_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0364", "798-byte"),
            "PROJECT.md": ("ADR-0364", "pre-capacity plumbing rejection"),
            "STATUS.md": ("ADR-0364", "GetProcessMemoryInfo failed"),
            "ROADMAP.md": ("ADR-0364", "separately source-sealed v2"),
            "RUNBOOK.md": (
                "ff1c757fb1c388c239ca3c7fdacad15bffa6ee62e00b882827ffb5626f40a906",
                "Never invoke `pontius.full_width_river_capacity_preflight` again",
            ),
            "ARCHITECTURE.md": ("ADR-0364", "80-byte counters structure"),
            "RISK_REGISTER.md": ("R125", "default integer ABI"),
            ".gitattributes": (
                "/experiments/results/full-width-river-capacity-preflight-v1.json -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_typed_telemetry_capacity_successor_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0365", "512 MiB"),
            "PROJECT.md": ("ADR-0365", "same-PID PowerShell"),
            "STATUS.md": ("ADR-0365", "invoke exactly once"),
            "ROADMAP.md": ("ADR-0365", "80-byte explicitly typed Win64 ABI"),
            "RUNBOOK.md": (
                "23cb6ea4521dc26c5fc1c3962574443b7a1d1b841f9e54c03355f9af9a58ff58",
                "Never invoke v1",
            ),
            "ARCHITECTURE.md": ("ADR-0365", "sampling-skew gate"),
            "RISK_REGISTER.md": ("R126", "same-PID PowerShell"),
            ".gitattributes": (
                "/experiments/configs/full-width-river-capacity-preflight-v2.json -text",
                "/experiments/results/full-width-river-capacity-preflight-v2.json -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_full_width_factor_tt_representation_rejection_is_retained(self) -> None:
        expected = {
            "README.md": ("ADR-0366", "437.434 GB"),
            "PROJECT.md": ("ADR-0366", "five cap/reserve conjuncts"),
            "STATUS.md": (
                "ADR-0366",
                "representation_rejected_before_target_allocation",
            ),
            "ROADMAP.md": ("ADR-0366", "202.627 GB"),
            "RUNBOOK.md": (
                "b486e3ac0269122fc3d578f9fc708ae9bd7472760c7b0603670464df1906b991",
                "Never invoke either capacity owner again",
            ),
            "ARCHITECTURE.md": ("ADR-0366", "733,055,400"),
            "RISK_REGISTER.md": ("R127", "discarded-mass-to-chip-value"),
            ".gitattributes": (
                "/experiments/results/full-width-river-capacity-preflight-v2.json -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_occupied_card_quotient_keystone_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0367", "query/right half"),
            "PROJECT.md": ("ADR-0367", "8,145,060"),
            "STATUS.md": ("ADR-0367", "occupied-card quotient"),
            "ROADMAP.md": ("ADR-0367", "topology-stable refresh"),
            "RUNBOOK.md": ("ADR-0367", "no literal full-width target"),
            "ARCHITECTURE.md": ("ADR-0367", "exact transpose"),
            "RISK_REGISTER.md": ("R128", "erases an open seat"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_exact_occupied_card_quotient_keystone_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0368", "labeled-record transpose"),
            "PROJECT.md": ("ADR-0368", "630 labeled records"),
            "STATUS.md": ("ADR-0368", "exact bounded algebra keystone"),
            "ROADMAP.md": ("ADR-0368", "pre-allocation quotient model"),
            "RUNBOOK.md": ("ADR-0368", "tests.test_occupied_card_quotient"),
            "ARCHITECTURE.md": ("ADR-0368", "seven masks"),
            "RISK_REGISTER.md": ("R129", "scalable builder"),
            "src/pontius/occupied_card_quotient.py": (
                "every source seat is closed",
                "apply_adjoint_exact",
            ),
            "tests/test_occupied_card_quotient.py": (
                "test_source_seat_permutation_and_one_seat_refresh_are_canonical",
                "test_factor_tt_open_mode_and_dense_oracles_match_the_quotient",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr_path = (
            _ROOT
            / "docs/decisions/ADR-0368-seal-the-exact-occupied-card-quotient-keystone.md"
        )
        adr = adr_path.read_text(encoding="utf-8")
        for relative in (
            "src/pontius/occupied_card_quotient.py",
            "tests/test_occupied_card_quotient.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)

    def test_full_width_quotient_preallocation_model_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0369", "2,971-column envelope"),
            "PROJECT.md": ("ADR-0369", "full arithmetic rebuild"),
            "STATUS.md": ("ADR-0369", "source-only arithmetic boundary"),
            "ROADMAP.md": ("ADR-0369", "source/query chunks"),
            "RUNBOOK.md": ("ADR-0369", "14-second action budget"),
            "ARCHITECTURE.md": ("ADR-0369", "forbidden dense one-hot export"),
            "RISK_REGISTER.md": ("R131", "invalid open-source split"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_full_width_quotient_preallocation_model_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0370", "81,711,241,920"),
            "PROJECT.md": ("ADR-0370", "492.449 MB"),
            "STATUS.md": ("ADR-0370", "numeric-array and logical-work result"),
            "ROADMAP.md": ("ADR-0370", "GPU numerical/throughput keystone"),
            "RUNBOOK.md": ("ADR-0370", "8,126,480,964-byte"),
            "ARCHITECTURE.md": ("ADR-0370", "129,017,750,400"),
            "RISK_REGISTER.md": ("R132", "advertised peak FLOPS"),
            "src/pontius/full_width_occupied_card_quotient_capacity.py": (
                "device_adjoint_phase_numeric_bytes",
                "source_seat_refresh_work",
            ),
            "tests/test_full_width_occupied_card_quotient_capacity.py": (
                "test_fixture_rank_trace_and_automaton_bytes_are_independently_derived",
                "test_chunk_changes_only_scratch_not_semantics_or_persistent_storage",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr_path = (
            _ROOT
            / "docs/decisions/ADR-0370-seal-the-full-width-occupied-card-quotient-preallocation-model.md"
        )
        adr = adr_path.read_text(encoding="utf-8")
        for relative in (
            "src/pontius/full_width_occupied_card_quotient_capacity.py",
            "tests/test_full_width_occupied_card_quotient_capacity.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)

    def test_bootstrap_safe_staged_scaling_v2_owner_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0376", "tracked"),
            "PROJECT.md": ("ADR-0376", "before/after-stage wall seams"),
            "ROADMAP.md": ("ADR-0376", "one clean exclusive invocation"),
            "RUNBOOK.md": ("ADR-0376", "Never invoke v1 again"),
            "ARCHITECTURE.md": ("ADR-0376", "envelope campaign"),
            "RISK_REGISTER.md": ("R138", "post-outcome solver-free rebinding"),
            "artifacts/README.md": ("ADR-0375", "v2 result identity"),
            "src/pontius/gpu_quotient_staged_scaling_v2_runner.py": (
                "validate_public_bootstrap(config)",
                "artifact_marker_tracked",
            ),
            "src/pontius/gpu_quotient_staged_scaling_v2_result.py": (
                "envelope/header campaign seam",
                "campaign_wall_crossed_after_stage",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr_path = (
            _ROOT
            / "docs/decisions/ADR-0376-source-seal-the-bootstrap-safe-staged-scaling-v2-owner.md"
        )
        adr = adr_path.read_text(encoding="utf-8")
        for relative in (
            "experiments/configs/gpu-quotient-staged-scaling-v2.json",
            "src/pontius/gpu_quotient_staged_scaling_v2_runner.py",
            "src/pontius/gpu_quotient_staged_scaling_v2_result.py",
            "tests/test_gpu_quotient_staged_scaling_v2.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)
        # The tracked marker is append-only across later artifact owners. Its
        # historical ADR binds the bytes present at ADR-0376, not the digest of
        # today's additive marker.
        self.assertIn(
            "0f13d3c3acfd929be0c41c0ebf4998cbe64f9af99fe366744ab576cd256a7c33",
            adr,
        )

    def test_passing_staged_gpu_quotient_result_is_retained(self) -> None:
        expected = {
            "README.md": ("ADR-0377", "49,557.238 ms"),
            "PROJECT.md": ("ADR-0377", "10.046424 GB"),
            "ROADMAP.md": ("ADR-0377", "streamed-validation"),
            "RUNBOOK.md": (
                "dd5b6d04cd45db0c3a95acdd1bcd05355c72be0852701df347696442261a2b72",
                "Never invoke either staged owner again",
            ),
            "ARCHITECTURE.md": ("ADR-0377", "10,046,423,704 bytes"),
            "RISK_REGISTER.md": ("R139", "per-iteration"),
            "docs/PREDICTION_LEDGER.md": ("0.0225", "ADR-0364"),
            ".gitattributes": (
                "/artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl -text",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr_path = (
            _ROOT
            / "docs/decisions/ADR-0377-retain-the-passing-staged-gpu-quotient-scaling-result.md"
        )
        adr = adr_path.read_text(encoding="utf-8")
        for relative in (
            "experiments/configs/gpu-quotient-staged-scaling-v2.json",
            "src/pontius/gpu_quotient_staged_scaling_v2_runner.py",
            "src/pontius/gpu_quotient_staged_scaling_v2_result.py",
            "tests/test_gpu_quotient_staged_scaling_v2.py",
            "tests/test_gpu_quotient_staged_scaling_v2_result.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)

        artifact = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl"
        self.assertEqual(artifact.stat().st_size, 65_114)
        self.assertEqual(
            hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "dd5b6d04cd45db0c3a95acdd1bcd05355c72be0852701df347696442261a2b72",
        )

    def test_literal_45_quotient_liveness_boundary_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0378", "64-MiB staging window"),
            "PROJECT.md": ("ADR-0378", "full dot-product temporary"),
            "STATUS.md": ("ADR-0378", "source-only literal-target liveness"),
            "ROADMAP.md": ("ADR-0378", "device reference duplication"),
            "RUNBOOK.md": ("ADR-0378", "67,108,864-byte"),
            "ARCHITECTURE.md": ("ADR-0378", "lifetime graph"),
            "RISK_REGISTER.md": ("R140", "literal byte comparison"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def test_literal_45_quotient_liveness_model_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0379", "244,970,204 bytes"),
            "PROJECT.md": ("ADR-0379", "11,755,029,796 bytes"),
            "STATUS.md": ("ADR-0379", "244,970,204-byte"),
            "ROADMAP.md": ("ADR-0379", "allocator/runtime storage"),
            "RUNBOOK.md": (
                "d1a4f3d759fc3d5a2c37277be5957ca7d4ea53621e6ca4178f06d8851ebef367",
                "Do not call 45 cards",
            ),
            "ARCHITECTURE.md": ("ADR-0379", "21,264,700,268 bytes"),
            "RISK_REGISTER.md": (
                "R141",
                "one-chunk control",
                "R142",
                "fresh `-B` subprocess",
            ),
            "src/pontius/literal_45_quotient_liveness.py": (
                "host_large_reference_buffer",
                "device_dot_partial_scratch",
                "live_admission_pass=None",
            ),
            "tests/test_literal_45_quotient_liveness.py": (
                "test_old_schedule_reconstructs_every_retained_stage_and_exposes_hidden_product",
                "test_forward_release_precedes_unique_adjoint_and_host_buffer_bridges_dot",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr_path = (
            _ROOT
            / "docs/decisions/ADR-0379-seal-the-literal-45-quotient-liveness-model.md"
        )
        adr = adr_path.read_text(encoding="utf-8")
        for relative in (
            "src/pontius/literal_45_quotient_liveness.py",
            "tests/test_literal_45_quotient_liveness.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)

    def test_bounded_quotient_validation_seam_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0380", "two-chunk"),
            "PROJECT.md": ("ADR-0380", "before CuPy"),
            "STATUS.md": ("ADR-0380", "complete ordered populations 10 and 22"),
            "ROADMAP.md": ("ADR-0380", "one overwritten unary"),
            "RUNBOOK.md": ("ADR-0380", "Reject 16, 28, 34"),
            "ARCHITECTURE.md": ("ADR-0380", "physical free memory"),
            "RISK_REGISTER.md": ("R143", "76,403,712-byte"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0380-preregister-the-bounded-quotient-validation-seam.md"
        )
        for phrase in (
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "Any allocation helper called with another width, including 45",
            "math.fsum",
        ):
            self.assertIn(phrase, adr)

    def test_bounded_cuda_consumer_numerical_rejection_is_retained(self) -> None:
        expected = {
            "README.md": ("ADR-0390", "absolute `0x1p-20` residual"),
            "PROJECT.md": ("ADR-0390", "distinct `2e-10` absolute conjunct"),
            "STATUS.md": (
                "ADR-0390",
                "accepted bounded-device source-seal rejection",
            ),
            "ROADMAP.md": ("ADR-0390", "same-memory paired high/low"),
            "RUNBOOK.md": ("ADR-0390", "0x1.9a7e7b97a67d1p+32"),
            "ARCHITECTURE.md": ("ADR-0390", "global online pair tree"),
            "RISK_REGISTER.md": ("R154", "one-ULP residual"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0390-retain-the-bounded-cuda-consumer-numerical-rejection.md"
        )
        source_paths = (
            "src/pontius/legal_river_quotient_cuda_consumer.py",
            "tests/test_legal_river_quotient_cuda_consumer.py",
        )
        for relative in source_paths:
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)
        for phrase in (
            "0x1.0000000000000p-20",
            "1.3847561401831852e-16",
            "actual execution, numeric-allocation, and scientific counters at zero",
            "reserved result absent",
            "tolerance is not amended after outcome",
            "same-memory compensated-tile",
            "No earlier one-shot owner is imported",
        ):
            self.assertIn(phrase, adr)

    def test_paired_high_low_cuda_tile_repair_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0391", "`[0,64)`, `[64,128)`, and `[128,176)`"),
            "PROJECT.md": ("ADR-0391", "9,910,940,380-byte device peak"),
            "STATUS.md": (
                "ADR-0391",
                "accepted prospective bounded-arithmetic boundary",
            ),
            "ROADMAP.md": ("ADR-0391", "64/64/48"),
            "RUNBOOK.md": ("ADR-0391", "reach pair 94/95"),
            "ARCHITECTURE.md": ("ADR-0391", "interleaved `(high, low)`"),
            "RISK_REGISTER.md": ("R155", "drops the low lane"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        config_path = (
            _ROOT
            / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json"
        )
        payload = config_path.read_bytes().replace(b"\r\n", b"\n")
        config_hash = hashlib.sha256(payload).hexdigest()
        adr = _contract_text(
            "docs/decisions/ADR-0391-preregister-the-paired-high-low-cuda-tile-repair.md"
        )
        self.assertIn(config_hash, adr)
        config = json.loads(config_path.read_text(encoding="utf-8"))

        sealed_dependencies = {
            "adr0390": (
                "docs/decisions/"
                "ADR-0390-retain-the-bounded-cuda-consumer-numerical-rejection.md"
            ),
            "parent_consumer_config": (
                "experiments/configs/legal-river-quotient-cuda-consumer-v1.json"
            ),
            "parent_consumer_source": "src/pontius/legal_river_quotient_cuda_consumer.py",
            "parent_consumer_controls": "tests/test_legal_river_quotient_cuda_consumer.py",
            "consumer_capacity_source": "src/pontius/legal_river_quotient_consumer_capacity.py",
            "legal_river_bridge_config": "experiments/configs/legal-river-quotient-bridge-v1.json",
            "legal_river_bridge_source": "src/pontius/legal_river_quotient_bridge.py",
            "gitattributes": ".gitattributes",
            "artifact_marker": "artifacts/README.md",
        }
        for key, relative in sealed_dependencies.items():
            dependency = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(
                hashlib.sha256(dependency).hexdigest(),
                config["expected_sources"][key],
                relative,
            )

        tiles = config["logical_tile_contract"]
        self.assertEqual([0, 175], tiles["global_state_feature_range"])
        self.assertEqual([[0, 64], [64, 128], [128, 176]], tiles["ordered_global_logical_ranges"])
        self.assertEqual([64, 64, 48], tiles["ordered_logical_widths"])
        self.assertEqual([128, 128, 96], tiles["ordered_physical_active_widths"])
        self.assertEqual([94, 95], tiles["reach_physical_columns_in_owner_tile"])
        self.assertEqual(128, tiles["physical_stride_width"])

        parent_config = json.loads(
            (_ROOT / sealed_dependencies["parent_consumer_config"]).read_text(
                encoding="utf-8"
            )
        )
        work = config["typed_work_contract"]
        source_pairings_per_tile = (
            parent_config["geometry"]["source_occupancies"]
            * parent_config["geometry"]["source_pairings_per_occupancy"]
        )
        self.assertEqual(source_pairings_per_tile, work["actual_source_pairing_visits_per_tile"])
        self.assertEqual(
            source_pairings_per_tile * work["tile_count"],
            work["actual_source_pairing_visits_per_complete_partition"],
        )
        self.assertEqual(
            2 * work["logical_feature_visits_per_complete_partition"],
            work["physical_high_low_component_visits_per_complete_partition"],
        )

        limits = config["numerical_limits"]
        self.assertEqual(2e-10, limits["bounded_transpose_dot_absolute"])
        self.assertEqual(2e-11, limits["bounded_scale_normalized_relative"])
        self.assertTrue(limits["require_absolute_and_relative_as_distinct_conjuncts"])
        self.assertEqual(
            9910940380,
            config["allocation_contract"][
                "successor_predicted_named_device_peak_bytes"
            ],
        )
        allocation = config["allocation_contract"]
        self.assertEqual(
            allocation["parent_named_device_peak_bytes"]
            - allocation["parent_result_accumulator_bytes"]
            + allocation["successor_result_accumulator_bytes"],
            allocation["successor_predicted_named_device_peak_bytes"],
        )
        self.assertEqual(
            config["global_reduction_contract"]["result_float64_slots"] * 8,
            allocation["successor_result_accumulator_bytes"],
        )
        self.assertEqual(
            180000,
            config["bounded_device_controls"]["multichunk_population_25"][
                "population_wall_limit_ms"
            ],
        )

        scope = config["scope"]
        self.assertTrue((_ROOT / scope["successor_source_relative_path"]).is_file())
        self.assertTrue((_ROOT / scope["successor_controls_relative_path"]).is_file())
        self.assertFalse((_ROOT / scope["successor_runner_relative_path"]).exists())
        self.assertFalse(
            (_ROOT / config["parent_identity"]["reserved_actual_result_relative_path"]).exists()
        )
        self.assertFalse(config["claims"]["compensated_tile_source_exists"])
        self.assertIsNone(config["claims"]["bounded_device_conformance_result"])
        self.assertFalse(config["claims"]["actual_owner_exists"])

    def test_paired_tile_preregistration_correction_is_prospective(self) -> None:
        expected = {
            "README.md": ("ADR-0392", "two-residual paired-division"),
            "PROJECT.md": ("ADR-0392", "query weights require"),
            "STATUS.md": (
                "ADR-0392",
                "accepted prospective preregistration-completeness correction",
            ),
            "ROADMAP.md": ("ADR-0392", "composite v1+v2 authority"),
            "RUNBOOK.md": ("ADR-0392", "`q1/r1/q2/r2/q3`"),
            "ARCHITECTURE.md": ("ADR-0392", "two residual corrections"),
            "RISK_REGISTER.md": ("R156", "unspecified reciprocal"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        v1_path = (
            _ROOT
            / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json"
        )
        v2_path = (
            _ROOT
            / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json"
        )
        v2 = json.loads(v2_path.read_text(encoding="utf-8"))
        v2_hash = hashlib.sha256(
            v2_path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        adr = _contract_text(
            "docs/decisions/ADR-0392-correct-the-paired-tile-preregistration-before-source.md"
        )
        self.assertIn(v2_hash, adr)
        self.assertEqual(
            hashlib.sha256(v1_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            v2["parent_identity"]["v1_config_canonical_lf_sha256"],
        )

        corrected = v2["corrected_arithmetic_contract"]
        self.assertIn(
            "pair_divide_positive_small_integer",
            corrected["required_primitives_replacement"],
        )
        divide = corrected["pair_divide_positive_small_integer_contract"]
        self.assertEqual([1, 2, 3, 4, 5, 6], divide["allowed_divisors"])
        self.assertEqual("q1=high/divisor", divide["step_1"])
        self.assertEqual(
            [0, 1, 2],
            corrected["source_weight_contract_replacement"]["seat_order"],
        )
        self.assertEqual(
            [3, 4, 5], corrected["query_weight_contract"]["seat_order"]
        )
        self.assertTrue(
            corrected["normalization_contract_replacement"][
                "no_device_pair_divide_pair_primitive_authorized"
            ]
        )

        identity = v2["parent_identity"]
        self.assertTrue((_ROOT / identity["successor_source_relative_path"]).is_file())
        self.assertTrue((_ROOT / identity["successor_controls_relative_path"]).is_file())
        self.assertFalse((_ROOT / identity["successor_runner_relative_path"]).exists())
        self.assertFalse((_ROOT / identity["reserved_actual_result_relative_path"]).exists())
        self.assertFalse(v2["claims"]["successor_source_exists"])
        self.assertIsNone(v2["claims"]["primitive_control_result"])
        self.assertIsNone(v2["claims"]["bounded_device_conformance_result"])

    def test_paired_tile_wall_rejection_is_retained(self) -> None:
        expected = {
            "README.md": ("ADR-0393", "nonterminal"),
            "PROJECT.md": ("ADR-0393", "180,000-ms wall"),
            "STATUS.md": (
                "ADR-0393",
                "accepted bounded-device source-seal rejection",
            ),
            "ROADMAP.md": ("ADR-0393", "work-decomposed successor"),
            "RUNBOOK.md": (
                "ADR-0393",
                "wall_kill_before_complete_25_terminal",
            ),
            "ARCHITECTURE.md": ("ADR-0393", "498.7 million"),
            "RISK_REGISTER.md": ("R157", "combinatorial validation work"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0393-retain-the-paired-tile-wall-rejection.md"
        )
        for relative in (
            "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
            "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)
        for phrase in (
            "wall_kill_before_complete_25_terminal",
            "No 25-card numerator, reach, transpose",
            "498713600",
            "1994854400",
            "1.454028420503369e-25",
            "No systems result in this decision is a decision-quality prior",
            "reserved actual result remains absent",
        ):
            self.assertIn(phrase, adr)

    def test_work_decomposed_paired_capacity_preflight_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0405", "15 corrected controls"),
            "PROJECT.md": ("ADR-0405", "Real CUDA diagnostic calls remain"),
            "STATUS.md": (
                "ADR-0405",
                "accepted source seal",
            ),
            "ROADMAP.md": ("ADR-0405", "sole clean"),
            "RUNBOOK.md": (
                "ADR-0405",
                "3e8067a445952e20a3258ffae9c08c6fa228f971be5b28b462de08fa52862a1c",
            ),
            "ARCHITECTURE.md": ("ADR-0405", "ACK-gated"),
            "RISK_REGISTER.md": ("R167", "nominal cubin-first"),
            "artifacts/work_preflight/README.md": (
                "ADR-0394",
                "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        config_path = (
            _ROOT
            / "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json"
        )
        payload = config_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c",
        )
        config = json.loads(payload)
        source_paths = {
            "adr0393": _ROOT
            / "docs/decisions/ADR-0393-retain-the-paired-tile-wall-rejection.md",
            "paired_base_config": _ROOT
            / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json",
            "paired_correction_config": _ROOT
            / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json",
            "paired_source": _ROOT
            / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
            "paired_controls": _ROOT
            / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
            "gitattributes": _ROOT / ".gitattributes",
            "artifact_marker": _ROOT / "artifacts/README.md",
            "work_preflight_gitattributes": _ROOT
            / "artifacts/work_preflight/.gitattributes",
            "work_preflight_artifact_marker": _ROOT
            / "artifacts/work_preflight/README.md",
        }
        self.assertEqual(set(source_paths), set(config["expected_sources"]))
        for label, path in source_paths.items():
            source = path.read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(
                hashlib.sha256(source).hexdigest(),
                config["expected_sources"][label],
            )

        geometry = config["population_geometry"]
        for available_cards, label in (
            (10, "10"),
            (22, "22"),
            (25, "25_projection_only"),
        ):
            row = geometry[label]
            self.assertEqual(row["source_occupancies"], math.comb(available_cards, 6))
            self.assertEqual(row["query_occupancies"], math.comb(available_cards, 4))
            self.assertEqual(
                row["labeled_query_records"], 6 * math.comb(available_cards, 4)
            )
            self.assertEqual(
                row["source_recurrence_rows"],
                sum(math.comb(available_cards, level) for level in range(7)),
            )
            self.assertEqual(
                row["adjoint_recurrence_rows"],
                sum(math.comb(available_cards, level) for level in range(5)),
            )
            self.assertEqual(
                row["compatible_sources_per_query_occupancy"],
                math.comb(available_cards - 4, 6),
            )
            self.assertEqual(
                row["compatible_labeled_query_records_per_source"],
                6 * math.comb(available_cards - 6, 4),
            )

        samples = 16
        repeats = 2
        families = 2
        tiles = 3
        width = 176
        boundaries = 8
        for available_cards, label in (
            (10, "complete_campaign_work_10"),
            (22, "complete_campaign_work_22"),
            (25, "complete_campaign_work_25_projection_only"),
        ):
            source_rows = math.comb(available_cards, 6)
            query_occupancies = math.comb(available_cards, 4)
            query_records = 6 * query_occupancies
            compatible_sources = math.comb(available_cards - 4, 6)
            compatible_queries = 6 * math.comb(available_cards - 6, 4)
            work = config[label]
            self.assertEqual(
                work["source_pairing_visits"],
                source_rows * 90 * tiles * repeats * families,
            )
            self.assertEqual(
                work["forward_recurrence_pair_child_adds"],
                sum(
                    math.comb(available_cards, level)
                    * (available_cards - level)
                    for level in range(6)
                )
                * width
                * repeats
                * families,
            )
            self.assertEqual(
                work["forward_signed_subset_pair_terms"],
                query_records * 16 * width * repeats * families,
            )
            self.assertEqual(
                work["adjoint_signed_subset_pair_terms"],
                source_rows * 57 * width * repeats * families,
            )
            self.assertEqual(
                work["direct_query_source_unranks"],
                samples * source_rows * tiles * repeats * families,
            )
            self.assertEqual(
                work["direct_query_compatible_boundary_pair_adds"],
                samples * compatible_sources * boundaries * repeats * families,
            )
            self.assertEqual(
                work["direct_fold_source_unranks"],
                samples * source_rows * tiles * repeats * families,
            )
            self.assertEqual(
                work["direct_fold_compatible_coefficient_pair_adds"],
                samples * compatible_sources * width * repeats * families,
            )
            self.assertEqual(
                work["direct_adjoint_query_record_visits"],
                samples * query_records * tiles * repeats * families,
            )
            self.assertEqual(
                work["direct_adjoint_compatible_query_weight_builds"],
                samples * compatible_queries * tiles * repeats * families,
            )
            self.assertEqual(
                work["direct_adjoint_compatible_boundary_pair_adds"],
                samples * compatible_queries * boundaries * repeats * families,
            )

        projected = config["complete_campaign_work_25_projection_only"]
        self.assertEqual(projected["rejected_direct_fold_source_unranks"], 1_994_854_400)
        self.assertEqual(projected["direct_fold_source_unranks"], 34_003_200)
        self.assertEqual(
            projected["direct_fold_compatible_coefficient_pair_adds"], 611_229_696
        )
        self.assertEqual(
            projected["source_rank_major_direct_fold_unrank_reduction_ratio"],
            [176, 3],
        )

        phase_order = config["phase_timing_contract"]["phase_order"]
        ratios = config["phase_projection_ratios"]
        self.assertEqual(set(phase_order), set(ratios) - {
            "ratio_format",
            "ratios_are_frozen_not_selected_from_observed_timing",
            "reader_must_rederive_every_ratio_from_geometry_work_chunks_and_live_shapes",
            "reader_rejects_any_ratio_below_any_constituent_ratio",
        })
        for phase in phase_order:
            for endpoint in ("25_over_10", "25_over_22"):
                numerator, denominator = ratios[phase][endpoint]
                self.assertGreaterEqual(numerator, denominator)
                self.assertGreater(denominator, 0)
        self.assertEqual(
            config["projection_contract"]["safety_multiplier_fraction"], [5, 4]
        )
        self.assertEqual(
            config["projection_contract"]["target_population_wall_limit_ns"],
            180_000_000_000,
        )

        scope = config["scope"]
        for field in (
            "successor_source_relative_path",
            "successor_controls_relative_path",
            "successor_runner_relative_path",
            "successor_reader_relative_path",
        ):
            self.assertTrue((_ROOT / scope[field]).is_file(), scope[field])
        result = _ROOT / scope["prospective_result_relative_path"]
        self.assertTrue(result.is_file())
        self.assertEqual(
            hashlib.sha256(result.read_bytes()).hexdigest(),
            "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830",
        )
        self.assertEqual(len(result.read_bytes().splitlines()), 3)
        self.assertFalse(
            (_ROOT / config["parent_identity"]["reserved_actual_result_relative_path"])
            .exists()
        )
        self.assertTrue(
            all(value is None or value is False for value in config["claims"].values())
        )

        adr = _contract_text(
            "docs/decisions/ADR-0394-preregister-the-work-decomposed-paired-capacity-preflight.md"
        )
        for phrase in (
            "1,994,854,400",
            "34,003,200",
            "611,229,696",
            "16 contiguous, nonoverlapping",
            "conservative empirical admission rule, not a theorem",
            "No successor implementation",
            "No work or timing number in this decision is resolver latency",
        ):
            self.assertIn(phrase, adr)

        correction_path = (
            _ROOT
            / "experiments/configs/"
            "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
        )
        correction_payload = correction_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(correction_payload).hexdigest(),
            "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c",
        )
        correction = json.loads(correction_payload)
        self.assertEqual(
            correction["corrected_resource_contract"][
                "stack_plus_local_backing_limit_bytes_per_thread"
            ],
            4096,
        )
        self.assertIsNone(
            correction["corrected_resource_contract"]["exact_spill_load_store_count"]
        )
        self.assertEqual(
            correction["reserve_arithmetic"][
                "maximum_resident_backing_at_4096_bytes_per_thread"
            ],
            536_870_912,
        )

        correction_adr = _contract_text(
            "docs/decisions/ADR-0395-correct-the-work-preflight-resource-instrument-before-result.md"
        )
        for phrase in (
            "unavailable compiler-spill wording",
            "Exact spill-load/store traffic is structurally unavailable",
            "536,870,912",
            "No number here is resolver latency",
        ):
            self.assertIn(phrase, correction_adr)

        seal = _contract_text(
            "docs/decisions/ADR-0396-source-seal-the-work-decomposed-paired-capacity-preflight.md"
        )
        for relative in (
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
            "tests/test_legal_river_quotient_cuda_compensated_work_preflight.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py",
        ):
            current = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(current).hexdigest(), seal)
        for phrase in (
            "18 passed",
            "result paths remain absent",
            "raw `--dump-resource-usage` stdout",
            "no real compilation",
        ):
            self.assertIn(phrase, seal)

    def test_bootstrap_safe_work_preflight_v2_is_preregistered(self) -> None:
        relative = (
            "experiments/configs/"
            "legal-river-quotient-cuda-compensated-work-preflight-owner-v2.json"
        )
        raw = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "e7f2a60035aad77d20461b4e5288bd85375f751b2d9ec410d2f197cfcacaf334",
        )
        config = json.loads(raw)
        self.assertEqual(
            config["schema_version"],
            "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v2",
        )

        parent = config["parent_identity"]
        bound_paths = {
            "adr0394": "adr0394_relative_path",
            "adr0395": "adr0395_relative_path",
            "adr0396": "adr0396_relative_path",
            "adr0397": "adr0397_relative_path",
            "v1_preregistration_config": "v1_preregistration_config_relative_path",
            "resource_correction_config": "resource_correction_config_relative_path",
            "scientific_source": "scientific_source_relative_path",
            "v1_runner": "v1_runner_relative_path",
            "v1_reader": "v1_reader_relative_path",
            "v1_controls": "v1_controls_relative_path",
            "durable_journal": "durable_journal_relative_path",
        }
        for label, path_field in bound_paths.items():
            current = (_ROOT / parent[path_field]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(
                hashlib.sha256(current).hexdigest(),
                parent[f"{label}_canonical_lf_sha256"],
                label,
            )

        retained = config["retained_v1_terminal"]
        v1_result = _ROOT / retained["result_relative_path"]
        self.assertTrue(v1_result.is_file())
        self.assertEqual(len(v1_result.read_bytes()), retained["result_bytes"])
        self.assertEqual(
            hashlib.sha256(v1_result.read_bytes()).hexdigest(), retained["result_sha256"]
        )
        self.assertEqual(len(v1_result.read_bytes().splitlines()), retained["record_count"])
        self.assertEqual(retained["terminal"], "infrastructure_failure")
        self.assertEqual(retained["phase_count"], 0)
        self.assertIsNone(retained["projection"])

        scope = config["successor_scope"]
        for field in (
            "v2_runner_relative_path",
            "v2_reader_relative_path",
            "v2_controls_relative_path",
        ):
            self.assertTrue((_ROOT / scope[field]).is_file(), scope[field])
        v2_result = _ROOT / scope["v2_result_relative_path"]
        self.assertTrue(v2_result.is_file())
        self.assertEqual(len(v2_result.read_bytes()), 8508)
        self.assertEqual(len(v2_result.read_bytes().splitlines()), 4)
        self.assertEqual(
            hashlib.sha256(v2_result.read_bytes()).hexdigest(),
            "9b9a3f606004a281773f6dc83c86fe2f70811ab825fbf1e0b8b47c1c75abdad3",
        )
        self.assertFalse((_ROOT / scope["reserved_actual_result_relative_path"]).exists())

        identity = config["new_identity_contract"]
        self.assertEqual(
            hashlib.sha256(identity["owner_protocol_seed"].encode("ascii")).hexdigest(),
            identity["owner_protocol_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(identity["campaign_seed"].encode("ascii")).hexdigest(),
            identity["campaign_sha256"],
        )
        handshake = config["bootstrap_handshake"]
        self.assertEqual(
            handshake["literal_worker_module"],
            "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner",
        )
        self.assertNotIn("__name__", handshake["literal_worker_module"])
        self.assertEqual(handshake["challenge_bytes"], 32)
        self.assertTrue(
            handshake[
                "handshake_and_campaign_share_one_popen_framing_stdout_stderr_timeout_and_return_function"
            ]
        )
        self.assertTrue(handshake["source_seal_must_spawn_a_real_handshake_child_without_cuda_or_result_creation"])

        science = config["inherited_science"]
        self.assertEqual(science["calibration_populations"], [10, 22])
        self.assertEqual(science["projection_population_integer_only"], 25)
        self.assertEqual(science["phase_count"], 16)
        self.assertEqual(science["safety_multiplier_fraction"], [5, 4])
        self.assertEqual(science["target_projection_wall_limit_ns"], 180_000_000_000)
        self.assertIsNone(science["exact_spill_load_store_count"])
        self.assertTrue(
            all(value is None or value is False for value in config["claims"].values())
        )

        adr = _contract_text(
            "docs/decisions/ADR-0398-preregister-the-bootstrap-safe-work-preflight-v2-owner.md"
        )
        for phrase in (
            "No command may derive it from runtime `__name__`",
            "fresh 32-byte challenge",
            "same `Popen` construction",
            "in-memory validation view",
            "No source-seal test may select campaign child mode",
            '"Preregistered" is not "source-sealed,"',
        ):
            self.assertIn(phrase, adr)

        source_seal = _contract_text(
            "docs/decisions/ADR-0399-source-seal-the-bootstrap-safe-work-preflight-v2-owner.md"
        )
        for relative in (
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_runner.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_result.py",
            "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v2.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py",
            "tests/test_legal_river_quotient_cuda_compensated_work_preflight.py",
        ):
            current = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(current).hexdigest(), source_seal)
        for phrase in (
            "16 passed",
            "Campaign-child calls at this boundary: `0`",
            "stdout EOF does not stop the deadline",
            "v2 result remains absent",
            "not pre-judged to pass",
        ):
            self.assertIn(phrase, source_seal)

        outcome = _contract_text(
            "docs/decisions/ADR-0400-retain-the-work-preflight-v2-evidence-serializer-failure.md"
        )
        for phrase in (
            "event_count=2",
            "handshake=True",
            "phase_count=0",
            "masked and therefore unclassified antecedent",
            "frozen slots dataclass",
            "13 of 16 controls",
            "No laboratory observation survived",
        ):
            self.assertIn(phrase, outcome)

        diagnostic_config_path = (
            _ROOT
            / "experiments/configs/legal-river-exact-cubin-inspector-diagnostic-v1.json"
        )
        diagnostic_raw = diagnostic_config_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(diagnostic_raw).hexdigest(),
            "d52ac02e83f71cb50b6a61e8a9dd18403171e4ddd25227b2036bb61c2085fe8a",
        )
        diagnostic = json.loads(diagnostic_raw)
        self.assertEqual(
            [row["candidate_id"] for row in diagnostic["candidate_commands_in_order"]],
            [
                "cuobjdump_version",
                "cuobjdump_resource_usage",
                "cuobjdump_elf",
                "nvdisasm_version",
                "nvdisasm_default",
            ],
        )
        self.assertTrue(
            diagnostic["lossless_capture_contract"][
                "external_processes_must_run_with_check_false_and_binary_streams"
            ]
        )
        self.assertIsNone(
            diagnostic["candidate_interpretation_contract"]["selected_inspector"]
        )
        self.assertTrue(
            all(value is None or value is False for value in diagnostic["claims"].values())
        )
        diagnostic_scope = diagnostic["successor_scope"]
        for field in (
            "diagnostic_relative_path",
            "owner_relative_path",
            "reader_relative_path",
            "controls_relative_path",
        ):
            self.assertTrue((_ROOT / diagnostic_scope[field]).is_file(), field)
        diagnostic_result = _ROOT / diagnostic_scope["result_relative_path"]
        self.assertTrue(diagnostic_result.is_file())
        diagnostic_result_raw = diagnostic_result.read_bytes()
        self.assertEqual(len(diagnostic_result_raw), 705101)
        self.assertEqual(len(diagnostic_result_raw.splitlines()), 12)
        self.assertEqual(
            hashlib.sha256(diagnostic_result_raw).hexdigest(),
            "9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed",
        )
        self.assertFalse(
            (_ROOT / diagnostic_scope["reserved_actual_result_relative_path"]).exists()
        )

        diagnostic_adr = _contract_text(
            "docs/decisions/ADR-0404-preregister-the-exact-cubin-inspector-diagnostic.md"
        )
        for phrase in (
            "d52ac02e83f71cb50b6a61e8a9dd18403171e4ddd25227b2036bb61c2085fe8a",
            "cubin must become durable before the first external operation",
            "A complete corpus may therefore finish honestly with five nonzero commands",
            "`selected_inspector` is frozen `null`",
            "Real compilation and external candidates remain forbidden",
        ):
            self.assertIn(phrase, diagnostic_adr)

        diagnostic_seal = _contract_text(
            "docs/decisions/ADR-0405-source-seal-the-exact-cubin-inspector-diagnostic.md"
        )
        for relative in (
            "experiments/configs/legal-river-exact-cubin-inspector-diagnostic-v1.json",
            "src/pontius/legal_river_exact_cubin_inspector_diagnostic.py",
            "src/pontius/legal_river_exact_cubin_inspector_diagnostic_runner.py",
            "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py",
            "tests/test_legal_river_exact_cubin_inspector_diagnostic.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
        ):
            current = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(current).hexdigest(), diagnostic_seal)
        for phrase in (
            "15 passed",
            "8 passed",
            "Real CUDA diagnostic-child calls: `0`",
            "Prospective diagnostic result: absent",
            "mapping iteration order",
            "one-second wall",
            "exact prospective-envelope accounting",
            "invoke exactly once",
        ):
            self.assertIn(phrase, diagnostic_seal)

        diagnostic_outcome = _contract_text(
            "docs/decisions/ADR-0406-retain-the-exact-cubin-inspector-diagnostic.md"
        )
        for phrase in (
            "terminal=capture_complete",
            "journal_byte_count=705101",
            "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97",
            "does not contain device code",
            "invalid ELF file",
            "`no_qualified_inspector`",
            "no selected or qualified inspector",
        ):
            self.assertIn(phrase, diagnostic_outcome)

    def test_work_preflight_v3_serializer_recovery_is_preregistered(self) -> None:
        relative = (
            "experiments/configs/"
            "legal-river-quotient-cuda-compensated-work-preflight-owner-v3.json"
        )
        raw = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "2c1a407dbd2a84e3d49d30544f47fef6bb6fffa74274e22d75acbf8ece2f00c1",
        )
        config = json.loads(raw)
        self.assertEqual(
            config["schema_version"],
            "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v3",
        )
        self.assertEqual(
            config["evidence_stage"],
            "preregistered_after_adr0400_before_v3_source_probe_campaign_or_result",
        )

        parent = config["parent_identity"]
        bound_paths = {
            "adr0394": "adr0394_relative_path",
            "adr0395": "adr0395_relative_path",
            "adr0398": "adr0398_relative_path",
            "adr0399": "adr0399_relative_path",
            "adr0400": "adr0400_relative_path",
            "v1_scientific_config": "v1_scientific_config_relative_path",
            "resource_correction_config": "resource_correction_config_relative_path",
            "v2_owner_config": "v2_owner_config_relative_path",
            "scientific_source": "scientific_source_relative_path",
            "v2_runner": "v2_runner_relative_path",
            "v2_reader": "v2_reader_relative_path",
            "v2_controls": "v2_controls_relative_path",
        }
        for label, path_field in bound_paths.items():
            current = (_ROOT / parent[path_field]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(
                hashlib.sha256(current).hexdigest(),
                parent[f"{label}_canonical_lf_sha256"],
                label,
            )

        for version, expected in {
            "v1": (
                "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830",
                5322,
                3,
            ),
            "v2": (
                "9b9a3f606004a281773f6dc83c86fe2f70811ab825fbf1e0b8b47c1c75abdad3",
                8508,
                4,
            ),
        }.items():
            retained = config["retained_artifacts"][version]
            artifact = _ROOT / retained["relative_path"]
            artifact_raw = artifact.read_bytes()
            self.assertEqual(hashlib.sha256(artifact_raw).hexdigest(), expected[0])
            self.assertEqual(len(artifact_raw), expected[1])
            self.assertEqual(len(artifact_raw.splitlines()), expected[2])
            self.assertEqual(retained["phase_count"], 0)
            self.assertIsNone(retained["projection"])

        scope = config["successor_scope"]
        for field in (
            "v3_adapter_relative_path",
            "v3_runner_relative_path",
            "v3_reader_relative_path",
            "v3_controls_relative_path",
        ):
            self.assertTrue((_ROOT / scope[field]).is_file(), scope[field])
        result = _ROOT / scope["v3_result_relative_path"]
        result_raw = result.read_bytes()
        self.assertEqual(len(result_raw), 15783)
        self.assertEqual(len(result_raw.splitlines()), 7)
        self.assertEqual(
            hashlib.sha256(result_raw).hexdigest(),
            "b84d9cd22042427c88f9c42b2da7acd176cdd0d5dec654c7f361bae7fa79cd0d",
        )
        self.assertFalse(
            (_ROOT / scope["reserved_actual_result_relative_path"]).exists(),
            scope["reserved_actual_result_relative_path"],
        )

        identity = config["new_identity_contract"]
        self.assertEqual(
            hashlib.sha256(identity["owner_protocol_seed"].encode("ascii")).hexdigest(),
            "294272bfa2a3402e60698f2835a8716e17ab83c76debf32012d8c324b30f65c9",
        )
        self.assertEqual(
            hashlib.sha256(identity["campaign_seed"].encode("ascii")).hexdigest(),
            "da157b3e01c8f219feb9df032ed942af9cd7e7911b6ad0d76e3a2a8356aefd7e",
        )

        serializer = config["serializer_contract"]
        self.assertEqual(
            serializer["approved_dataclass_fully_qualified_name"],
            "pontius.legal_river_quotient_cuda_consumer.CudaRuntimeIdentity",
        )
        self.assertEqual(
            serializer["approved_dataclass_fields_in_declared_order"],
            [
                "device_name",
                "compute_capability",
                "device_total_bytes",
                "cuda_driver_version",
                "cuda_runtime_version",
                "cupy_version",
            ],
        )
        for field in (
            "approved_dataclass_requires_exact_type_not_subclass",
            "recognize_with_dataclasses_is_dataclass_and_enumerate_dataclasses_fields",
            "generic_vars_or___dict___object_fallback_forbidden",
            "unknown_dataclass_namedtuple_slots_or_object_family_rejected",
            "legacy_plain_success_domain_must_be_byte_identical_on_complete_synthetic_event_corpus",
            "scientific_plain_identity_must_be_checked_before_install_and_restored_in_finally",
        ):
            self.assertTrue(serializer[field], field)

        probe = config["serializer_probe"]
        self.assertEqual(probe["child_mode"], "serializer_probe")
        self.assertEqual(
            probe["forced_exception_message"],
            "forced_serializer_probe_compiler_failure",
        )
        self.assertEqual(
            probe["expected_event_reason"],
            "RuntimeError: forced_serializer_probe_compiler_failure",
        )
        self.assertEqual(probe["expected_terminal"], "compiler_or_primitive_rejection")
        self.assertTrue(probe["must_import_no_cupy_and_execute_no_compiler"])
        self.assertTrue(probe["must_call_the_unchanged_run_calibration_preflight_send_closure"])
        self.assertTrue(probe["source_global_bounded_call_counter_and_all_patched_identities_must_restore"])

        science = config["inherited_science"]
        self.assertEqual(science["calibration_populations"], [10, 22])
        self.assertEqual(science["projection_population_integer_only"], 25)
        self.assertEqual(science["phase_count"], 16)
        self.assertEqual(science["safety_multiplier_fraction"], [5, 4])
        self.assertEqual(science["target_projection_wall_limit_ns"], 180_000_000_000)
        self.assertIsNone(science["exact_spill_load_store_count"])
        self.assertTrue(
            all(value is None or value is False for value in config["claims"].values())
        )

        adr = _contract_text(
            "docs/decisions/ADR-0401-preregister-the-work-preflight-v3-evidence-serializer-recovery.md"
        )
        for phrase in (
            "exact class, not a subclass",
            "generic `vars()`/`__dict__` fallbacks",
            "forced_serializer_probe_compiler_failure",
            "No adapter, probe, child, or campaign exists",
            "Prospective v3 result",
        ):
            self.assertIn(phrase, adr)

        seal = _contract_text(
            "docs/decisions/ADR-0402-source-seal-the-work-preflight-v3-evidence-serializer-recovery.md"
        )
        for relative in (
            "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-owner-v3.json",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_adapter.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_runner.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_result.py",
            "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v3.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_runner.py",
            "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_result.py",
            "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v2.py",
        ):
            current = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(current).hexdigest(), seal, relative)
        for phrase in (
            "16 passed",
            "Campaign-child calls: `0`",
            "named tuple reached",
            "complete synthetic capacity-pass journal",
            "The V3 result remains absent",
            "invoke exactly once",
        ):
            self.assertIn(phrase, seal)

        outcome = _contract_text(
            "docs/decisions/ADR-0403-retain-the-work-preflight-v3-resource-inspector-rejection.md"
        )
        for phrase in (
            "b84d9cd22042427c88f9c42b2da7acd176cdd0d5dec654c7f361bae7fa79cd0d",
            "Result bytes: `15783`",
            "Journal records: `7`",
            "serializer_probe=True",
            "4294967295",
            "phase_count=0",
            "projection=None",
            "why the tool rejected this cubin is not",
            "29613",
            "do not fall back silently to driver-only evidence",
        ):
            self.assertIn(phrase, outcome)

    def test_bounded_quotient_validation_seam_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0381", "204,377,088 bytes"),
            "PROJECT.md": ("ADR-0381", "63-versus-57"),
            "STATUS.md": ("ADR-0381", "one-shot literal-45 CUDA owner"),
            "ROADMAP.md": ("ADR-0381", "complete exact 10-card"),
            "RUNBOOK.md": (
                "cbbd58c56d3fa9031594d6d034acb0a21a6ecc63d597583cf6098f2b0215258d",
                "32 gates per population",
            ),
            "ARCHITECTURE.md": ("ADR-0381", "Seventeen allocator snapshots"),
            "RISK_REGISTER.md": (
                "R144",
                "sizes zero through four",
                "R145",
                "zero-release gate",
            ),
            "tests/test_affine_resident_leaf_adjoint_cfr.py": (
                "tearDownClass",
                "free_all_blocks",
            ),
            "tests/test_canonical_affine_resident_automaton_cache.py": (
                "tearDownClass",
                "free_all_blocks",
            ),
            "src/pontius/gpu_quotient_validation_seam.py": (
                "run_bounded_quotient_validation_seam",
                "_streamed_device_host_dot",
                "sum(comb(SOURCE_CARDS, level) for level in range(QUERY_CARDS + 1))",
            ),
            "tests/test_gpu_quotient_validation_seam.py": (
                "test_literal_bytes_not_digest_decide_later_chunk_mutation",
                "test_every_frozen_gate_passes_in_order",
                "_run_isolated_device_payload",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0381-seal-the-bounded-quotient-validation-seam.md"
        )
        for relative in (
            "src/pontius/gpu_quotient_validation_seam.py",
            "tests/test_gpu_quotient_validation_seam.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)

    def test_literal_45_quotient_owner_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0382", "permanent first outcomes"),
            "PROJECT.md": ("ADR-0382", "125 source chunks"),
            "STATUS.md": ("ADR-0382", "literal-45 config"),
            "ROADMAP.md": ("ADR-0382", "synthetic injected lifecycle"),
            "RUNBOOK.md": (
                "ADR-0382",
                "literal_45_quotient_target_runner",
            ),
            "ARCHITECTURE.md": ("ADR-0382", "8.34-GB source reference"),
            "RISK_REGISTER.md": ("R146", "12-GB workload"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0382-preregister-the-one-shot-literal-45-quotient-owner.md"
        )
        for phrase in (
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "125 chunks",
            "600,000 ms",
        ):
            self.assertIn(phrase, adr)

    def test_literal_45_quotient_source_seal_remains_historical(self) -> None:
        expected = {
            "README.md": ("ADR-0383", "35-allocation"),
            "PROJECT.md": ("ADR-0383", "all target counters zero"),
            "ROADMAP.md": ("ADR-0383", "inert config/mechanism/runner"),
            "RUNBOOK.md": ("ADR-0383", "literal_45_quotient_target_runner"),
            "ARCHITECTURE.md": ("ADR-0383", "Stored pass labels"),
            "RISK_REGISTER.md": ("R147", "one-sided tolerance"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0383-source-seal-the-one-shot-literal-45-quotient-owner.md"
        )
        paths = (
            "experiments/configs/literal-45-quotient-target-v1.json",
            "src/pontius/literal_45_quotient_target.py",
            "src/pontius/literal_45_quotient_target_runner.py",
            "src/pontius/literal_45_quotient_target_result.py",
            "tests/test_literal_45_quotient_target.py",
            "tests/test_literal_45_quotient_target_result.py",
        )
        for relative in paths:
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)
        self.assertTrue(
            (_ROOT / "artifacts/literal_45_quotient_target_v1.jsonl").exists()
        )
        for phrase in (
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "35 ordered named numeric births",
            "never created",
        ):
            self.assertIn(phrase, adr)

    def test_literal_45_quotient_result_is_retained_and_bounded(self) -> None:
        expected = {
            "README.md": ("ADR-0384", "all 27 gates"),
            "PROJECT.md": ("ADR-0384", "11,620,834,304"),
            "STATUS.md": ("ADR-0384", "actual-context quotient bridge"),
            "ROADMAP.md": ("ADR-0384", "actual legal river-context"),
            "RUNBOOK.md": ("ADR-0384", "historical lifecycle tombstone"),
            "ARCHITECTURE.md": ("ADR-0384", "viable full-width river"),
            "RISK_REGISTER.md": ("R148", "per-solve"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        artifact = _ROOT / "artifacts/literal_45_quotient_target_v1.jsonl"
        raw = artifact.read_bytes()
        self.assertEqual(len(raw), 21_663)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "a8c4a91416c35ca94c53349a2bb2c1182d0defea7e8d81dd71ff949d98a11970",
        )
        adr = _contract_text(
            "docs/decisions/ADR-0384-retain-the-passing-literal-45-quotient-target.md"
        )
        assessment = (
            _ROOT / "tests/test_literal_45_quotient_target_assessment.py"
        ).read_bytes().replace(b"\r\n", b"\n")
        for phrase in (
            hashlib.sha256(assessment).hexdigest(),
            "completed_pass",
            "All 27 gates",
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "219,667.20090003219",
            "116,178.429688",
            "no action",
        ):
            self.assertIn(phrase, adr)

    def test_actual_context_quotient_bridge_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0385", "odd-chip and side-pot"),
            "PROJECT.md": ("ADR-0385", "60-chip flat pot"),
            "STATUS.md": ("ADR-0385", "actual-context quotient bridge"),
            "ROADMAP.md": ("ADR-0385", "reduced leaf-adjoint"),
            "RUNBOOK.md": (
                "ADR-0385",
                "af145f4d56cdbdcfb5a0d7ee36613677ad79f57620629266c729997785a1f1f6",
            ),
            "ARCHITECTURE.md": ("ADR-0385", "integer odd-chip settlement"),
            "RISK_REGISTER.md": ("R149", "physical card IDs"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        config = (
            _ROOT / "experiments/configs/legal-river-quotient-bridge-v1.json"
        ).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(config).hexdigest(),
            "af145f4d56cdbdcfb5a0d7ee36613677ad79f57620629266c729997785a1f1f6",
        )
        adr = _contract_text(
            "docs/decisions/ADR-0385-preregister-the-actual-context-quotient-bridge.md"
        )
        for phrase in (
            "dd0f894e572d2217ad27bb6a3fe56e92192860320106cb778c25776745613cd5",
            "lcm(1,2,3,4,5,6) = 60",
            "1,024 Cartesian assignments",
            "contract_heterogeneous_leaf_terms",
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "no action",
        ):
            self.assertIn(phrase, adr)

    def test_actual_context_quotient_bridge_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0386", "15,888,996"),
            "PROJECT.md": ("ADR-0386", "zero chip error"),
            "STATUS.md": ("ADR-0386", "source-sealed actual-context quotient bridge"),
            "ROADMAP.md": ("ADR-0386", "rank 175"),
            "RUNBOOK.md": ("ADR-0386", "full-width quotient value"),
            "ARCHITECTURE.md": ("ADR-0386", "nonadditive"),
            "RISK_REGISTER.md": ("R150", "Python-object"),
            "src/pontius/legal_river_quotient_bridge.py": (
                "compile_warm_inputs",
                "warm bridge automaton identity differs",
            ),
            "tests/test_legal_river_quotient_bridge.py": (
                "test_source_seat_permutation_is_semantic_only_when_data_moves_with_it",
                "test_source_import_and_full_compile_leave_cupy_and_owner_absent",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0386-source-seal-the-actual-context-quotient-bridge.md"
        )
        for relative in (
            "src/pontius/legal_river_quotient_bridge.py",
            "tests/test_legal_river_quotient_bridge.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)
        for phrase in (
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "1.7053025658242404e-13",
            "0.0009707317118028413",
            "no action",
        ):
            self.assertIn(phrase, adr)

    def test_actual_context_quotient_consumer_capacity_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0387", "reach feature 175"),
            "PROJECT.md": ("ADR-0387", "10,922 complete six-label occupancies"),
            "STATUS.md": ("ADR-0387", "consumer-capacity"),
            "ROADMAP.md": ("ADR-0387", "global 128+48 partition"),
            "RUNBOOK.md": (
                "ADR-0387",
                "7cc8fec2b6cb6b7b135f2f7ea5dd74e1a5a3cd4b4a2c48d2b6f8ddde141bb71d",
            ),
            "ARCHITECTURE.md": ("ADR-0387", "forward release before adjoint birth"),
            "RISK_REGISTER.md": ("R151", "slice-local state 0"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        config_path = (
            _ROOT
            / "experiments/configs/legal-river-quotient-consumer-capacity-v1.json"
        )
        config = config_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(config).hexdigest(),
            "7cc8fec2b6cb6b7b135f2f7ea5dd74e1a5a3cd4b4a2c48d2b6f8ddde141bb71d",
        )
        parsed = json.loads(config)
        source_paths = {
            "adr0386": _ROOT
            / "docs/decisions/ADR-0386-source-seal-the-actual-context-quotient-bridge.md",
            "bridge_config": _ROOT
            / "experiments/configs/legal-river-quotient-bridge-v1.json",
            "full_width_quotient_capacity": _ROOT
            / "src/pontius/full_width_occupied_card_quotient_capacity.py",
            "gpu_occupied_card_quotient": _ROOT
            / "src/pontius/gpu_occupied_card_quotient.py",
            "gpu_quotient_staged_scaling": _ROOT
            / "src/pontius/gpu_quotient_staged_scaling.py",
            "legal_river_quotient_bridge": _ROOT
            / "src/pontius/legal_river_quotient_bridge.py",
            "literal_45_quotient_liveness": _ROOT
            / "src/pontius/literal_45_quotient_liveness.py",
            "occupied_card_quotient": _ROOT
            / "src/pontius/occupied_card_quotient.py",
            "structured_showdown_automaton": _ROOT
            / "src/pontius/structured_showdown_automaton.py",
        }
        self.assertEqual(set(parsed["expected_sources"]), set(source_paths))
        for label, path in source_paths.items():
            payload = path.read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(
                hashlib.sha256(payload).hexdigest(),
                parsed["expected_sources"][label],
            )
        self.assertEqual(
            parsed["feature_slices"]["ordered_ranges"], [[0, 128], [128, 176]]
        )
        self.assertEqual(parsed["feature_slices"]["ordered_widths"], [128, 48])
        self.assertEqual(parsed["geometry"]["reach_global_feature_index"], 175)
        self.assertEqual(parsed["geometry"]["total_feature_width"], 176)
        self.assertEqual(
            parsed["streaming"]["adjoint_query_occupancy_chunk"]
            * parsed["streaming"]["query_labels_per_occupancy"],
            parsed["streaming"]["adjoint_query_record_chunk"],
        )
        self.assertNotEqual(
            parsed["streaming"]["forward_query_record_chunk"],
            parsed["streaming"]["adjoint_query_record_chunk"],
        )
        self.assertTrue(
            parsed["lifetime_model"][
                "require_expand_derived_named_arrays_before_phase_sweep"
            ]
        )
        self.assertTrue(
            all(value is None or value is False for value in parsed["claims"].values())
        )
        adr = _contract_text(
            "docs/decisions/ADR-0387-preregister-the-actual-context-quotient-consumer-capacity-seam.md"
        )
        for phrase in (
            "[0, 128)",
            "[128, 176)",
            "10,922 occupancies",
            "per-slice conditional values",
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "no action",
        ):
            self.assertIn(phrase, adr)

    def test_actual_context_quotient_consumer_capacity_is_source_sealed(self) -> None:
        expected = {
            "README.md": ("ADR-0388", "9,910,940,332"),
            "PROJECT.md": ("ADR-0388", "58 named physical rows"),
            "STATUS.md": ("ADR-0388", "source-sealed CuPy-free"),
            "ROADMAP.md": ("ADR-0388", "actual-context CUDA-consumer"),
            "RUNBOOK.md": (
                "ADR-0388",
                "57f8a809041af0f02a371e0f19d3910301d7ba6585eeddc34e969da5bef234f2",
            ),
            "ARCHITECTURE.md": ("ADR-0388", "58 unique physical"),
            "RISK_REGISTER.md": ("R152", "2.089-GB numeric margin"),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        adr = _contract_text(
            "docs/decisions/ADR-0388-source-seal-the-actual-context-quotient-consumer-capacity.md"
        )
        for relative in (
            "src/pontius/legal_river_quotient_consumer_capacity.py",
            "tests/test_legal_river_quotient_consumer_capacity.py",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)
        for phrase in (
            "15,973,968",
            "9,910,940,332",
            "2,089,059,668",
            "58 unique physical rows",
            "2.220446049250313e-16",
            "live admission is `None`",
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "no action",
        ):
            self.assertIn(phrase, adr)

    def test_actual_context_quotient_cuda_consumer_is_preregistered(self) -> None:
        expected = {
            "README.md": ("ADR-0389", "25 named allocation births"),
            "PROJECT.md": ("ADR-0389", "multi-chunk 25-card"),
            "STATUS.md": (
                "ADR-0389",
                "accepted prospective actual-context quotient CUDA-consumer",
            ),
            "ROADMAP.md": ("ADR-0389", "offset-aware 128+48"),
            "RUNBOOK.md": (
                "ADR-0389",
                "7328188d9f731415d4d70d5434b72463b982bc4b3627203347c7157a253486dd",
            ),
            "ARCHITECTURE.md": ("ADR-0389", "fused over the 90"),
            "RISK_REGISTER.md": ("R153", "correct 57"),
            "artifacts/README.md": (
                "ADR-0389",
                "legal_river_quotient_cuda_consumer_v1.jsonl",
            ),
        }
        for relative, phrases in expected.items():
            text = _contract_text(relative)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

        config_path = (
            _ROOT
            / "experiments/configs/legal-river-quotient-cuda-consumer-v1.json"
        )
        payload = config_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            "7328188d9f731415d4d70d5434b72463b982bc4b3627203347c7157a253486dd",
        )
        parsed = json.loads(payload)
        source_paths = {
            "adr0384": _ROOT
            / "docs/decisions/ADR-0384-retain-the-passing-literal-45-quotient-target.md",
            "adr0388": _ROOT
            / "docs/decisions/ADR-0388-source-seal-the-actual-context-quotient-consumer-capacity.md",
            "artifact_marker": _ROOT / "artifacts/README.md",
            "consumer_capacity_config": _ROOT
            / "experiments/configs/legal-river-quotient-consumer-capacity-v1.json",
            "consumer_capacity_source": _ROOT
            / "src/pontius/legal_river_quotient_consumer_capacity.py",
            "durable_evidence_journal": _ROOT
            / "src/pontius/durable_evidence_journal.py",
            "gitattributes": _ROOT / ".gitattributes",
            "gpu_occupied_card_quotient": _ROOT
            / "src/pontius/gpu_occupied_card_quotient.py",
            "gpu_quotient_validation_seam": _ROOT
            / "src/pontius/gpu_quotient_validation_seam.py",
            "legal_river_bridge_config": _ROOT
            / "experiments/configs/legal-river-quotient-bridge-v1.json",
            "legal_river_bridge_source": _ROOT
            / "src/pontius/legal_river_quotient_bridge.py",
            "literal_45_result_reader": _ROOT
            / "src/pontius/literal_45_quotient_target_result.py",
            "occupied_card_quotient": _ROOT
            / "src/pontius/occupied_card_quotient.py",
            "structured_showdown_automaton": _ROOT
            / "src/pontius/structured_showdown_automaton.py",
            "windows_process_memory": _ROOT
            / "src/pontius/windows_process_memory.py",
        }
        self.assertEqual(set(parsed["expected_sources"]), set(source_paths))
        for label, path in source_paths.items():
            source = path.read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(
                hashlib.sha256(source).hexdigest(),
                parsed["expected_sources"][label],
            )

        geometry = parsed["geometry"]
        streaming = parsed["streaming"]
        work = parsed["actual_work"]
        self.assertEqual(geometry["source_occupancies"], math.comb(45, 6))
        self.assertEqual(geometry["query_occupancies"], math.comb(45, 4))
        self.assertEqual(
            geometry["source_recurrence_rows"],
            sum(math.comb(45, level) for level in range(7)),
        )
        self.assertEqual(
            geometry["adjoint_recurrence_rows"],
            sum(math.comb(45, level) for level in range(5)),
        )
        self.assertEqual(streaming["forward_query_chunk_count"], 14)
        self.assertEqual(streaming["forward_final_query_record_chunk"], 42_002)
        self.assertEqual(streaming["adjoint_query_chunk_count"], 14)
        self.assertEqual(streaming["adjoint_final_query_record_chunk"], 42_054)
        self.assertEqual(streaming["adjoint_source_chunk_count"], 249)
        self.assertEqual(
            work["adjoint_terms_per_six_card_source_mask"],
            sum(math.comb(6, level) for level in range(5)),
        )
        self.assertEqual(work["adjoint_source_contract_chunk_invocations"], 996)
        self.assertFalse(any("per_full_feature_pass" in key for key in work))
        self.assertEqual(work["source_pairing_visits_per_slice"], 8_145_060 * 90)
        self.assertEqual(
            work["source_pairing_visits_per_complete_feature_partition"],
            8_145_060 * 90 * 2,
        )
        self.assertEqual(
            work["source_pairing_visits_per_frozen_execution"],
            8_145_060 * 90 * 2 * 2,
        )
        self.assertEqual(
            work["signed_query_vector_terms_per_slice"],
            893_970 * 16,
        )
        self.assertEqual(
            work["signed_query_vector_terms_per_complete_feature_partition"],
            893_970 * 16 * 2,
        )
        self.assertEqual(
            work["signed_query_scalar_additions_per_complete_feature_partition"],
            893_970 * 16 * 176,
        )
        self.assertEqual(
            work["adjoint_signed_source_vector_terms_per_slice"],
            8_145_060 * 57,
        )
        self.assertEqual(
            work[
                "adjoint_signed_source_vector_terms_per_complete_feature_partition"
            ],
            8_145_060 * 57 * 2,
        )
        self.assertEqual(
            work[
                "adjoint_signed_source_scalar_additions_per_complete_feature_partition"
            ],
            8_145_060 * 57 * 176,
        )

        allocations = parsed["actual_allocation_model"]
        phases = parsed["telemetry_contract"]["named_device_bytes_by_phase"]
        self.assertEqual(len(parsed["device_allocation_births"]), 25)
        self.assertEqual(len(set(parsed["device_allocation_births"])), 25)
        self.assertEqual(allocations["complete_named_host_peak_bytes"], 15_980_816)
        self.assertEqual(allocations["named_device_peak_bytes"], 9_910_940_332)
        self.assertEqual(phases["forward_released"], 82_997_932)
        self.assertEqual(phases["adjoint_source_allocated"], 351_819_436)
        self.assertEqual(phases["released"], 0)
        lifecycle = parsed["result_accumulator_lifecycle"]
        self.assertEqual(
            lifecycle["device_float64_slots"],
            [
                "forward_unnormalized_numerator_or_adjoint_transpose_dot",
                "forward_reach_or_adjoint_positive_zero_guard",
            ],
        )
        self.assertEqual(
            lifecycle["host_scalar_result_order"],
            [
                "forward_slice_0_unnormalized_numerator",
                "forward_slice_1_unnormalized_numerator",
                "forward_total_unnormalized_numerator",
                "forward_total_reach",
                "forward_conditional_value_chips",
                "transpose_slice_0_dot",
                "transpose_slice_1_dot",
                "transpose_total_dot",
            ],
        )
        self.assertTrue(
            lifecycle["forbid_double_counting_repeat_or_slice_contributions"]
        )

        samples = parsed["samples"]
        sample_specs = {
            "actual_source_occupancy_ranks": ("actual_source", 8_145_060),
            "actual_query_occupancy_ranks": ("actual_query_occupancy", 148_995),
            "actual_query_record_ranks": ("actual_query_record", 893_970),
            "bounded_25_source_occupancy_ranks": ("bounded25_source", 177_100),
            "bounded_25_query_occupancy_ranks": (
                "bounded25_query_occupancy",
                12_650,
            ),
            "bounded_25_query_record_ranks": ("bounded25_query_record", 75_900),
        }
        for field, (lane, population) in sample_specs.items():
            expected_ranks = samples[field]
            reconstructed = [0, population - 1]
            occupied = set(reconstructed)
            for index in range(len(expected_ranks) - 2):
                label = f"{samples['derivation_seed']}|{lane}|{index}"
                candidate = int.from_bytes(
                    hashlib.sha256(label.encode("ascii")).digest()[:8],
                    "big",
                ) % population
                while candidate in occupied:
                    candidate = (candidate + 1) % population
                reconstructed.append(candidate)
                occupied.add(candidate)
            self.assertEqual(reconstructed, expected_ranks)
            self.assertEqual(samples["lane_labels"][field], lane)

        self.assertTrue(
            all(value is None or value is False for value in parsed["claims"].values())
        )
        attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/artifacts/legal_river_quotient_cuda_consumer_v1.jsonl -text",
            attributes,
        )
        adr = _contract_text(
            "docs/decisions/ADR-0389-preregister-the-actual-context-quotient-cuda-consumer.md"
        )
        for phrase in (
            "25 named numeric allocation births",
            "9,910,940,332",
            "57 terms, never 63",
            "invoke exactly once",
            "exclusive untouched legal h4",
            "selector-window",
            "2,113-task",
            "exhaustive bounded development-teacher",
            "response-closed direct mechanism",
            "caller-owned legal fallback",
            "GetProcessMemoryInfo failed",
            "representation_rejected_before_target_allocation",
            "no action",
        ):
            self.assertIn(phrase, adr)


if __name__ == "__main__":
    unittest.main()
