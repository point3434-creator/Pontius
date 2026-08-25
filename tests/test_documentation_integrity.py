from __future__ import annotations

import hashlib
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
            "STATUS.md": ("ADR-0376", "bootstrap-safe"),
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
            "artifacts/README.md",
        ):
            payload = (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            self.assertIn(hashlib.sha256(payload).hexdigest(), adr)

    def test_passing_staged_gpu_quotient_result_is_retained(self) -> None:
        expected = {
            "README.md": ("ADR-0377", "49,557.238 ms"),
            "PROJECT.md": ("ADR-0377", "10.046424 GB"),
            "STATUS.md": ("ADR-0377", "126 frozen gates"),
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


if __name__ == "__main__":
    unittest.main()
