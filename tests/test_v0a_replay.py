"""Slice-B replay tests: fixtures, independent oracle, terminal accounting."""

from __future__ import annotations

import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from pontius.immutable_blueprint import ImmutableBlueprintActionSource
from pontius.v0a.model import FailureCode
from pontius.v0a.replay import (
    FIXTURE_A,
    FIXTURE_B,
    FIXTURES,
    PROTOCOL_ID,
    ReplayHost,
    chip_depth_settlement,
    permutation_for_label,
    suit_mapping,
)
from pontius.v0a.trace import parse_trace, parsed_semantic_sha256

NANOS = 1_000_000_000


class SteadyClock:
    """Deterministic witness source; advances a fixed step per observation."""

    def __init__(self, start: int = 1_000, step: int = 1_000) -> None:
        self.now = start
        self.step = step

    def __call__(self) -> int:
        value = self.now
        self.now += self.step
        return value


def blueprint() -> ImmutableBlueprintActionSource:
    return ImmutableBlueprintActionSource(source_id="v0a-empty-reference")


def run_fixture(fixture, *, run_id: str | None = None, clock=None, **kwargs):
    host = ReplayHost(
        fixture,
        run_id=run_id or f"{PROTOCOL_ID}-correctness-{fixture.name}",
        blueprint=blueprint(),
        clock=SteadyClock() if clock is None else clock,
    )
    return host, host.run(**kwargs)


class SeedPermutationTests(unittest.TestCase):
    def test_permutations_are_deterministic_and_disclosed(self) -> None:
        self.assertEqual(permutation_for_label(f"{PROTOCOL_ID}/control-A"), "hcsd")
        self.assertEqual(permutation_for_label(f"{PROTOCOL_ID}/control-B"), "hdsc")
        self.assertEqual(FIXTURE_A.permutation, "hcsd")
        self.assertEqual(FIXTURE_B.permutation, "hdsc")

    def test_renaming_preserves_ranks_and_distinctness(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(fixture.name):
                deal = fixture.deal()
                cards = [*deal.board_runout]
                for hand in deal.private_hands:
                    cards.extend(hand)
                self.assertEqual(len(cards), 17)
                self.assertEqual(len(set(cards)), 17)
                original_ranks = sorted(
                    "23456789TJQKA".index(text[0])
                    for text in (*fixture.board_text, *" ".join(fixture.hand_text).split())
                )
                renamed_ranks = sorted(card // 4 for card in cards)
                self.assertEqual(original_ranks, renamed_ranks)

    def test_a_permutation_must_rearrange_the_four_suits(self) -> None:
        for bad in ("cdh", "cdhh", "wxyz"):
            with self.subTest(bad):
                with self.assertRaises(ValueError):
                    suit_mapping(bad)


class FixtureReplayTests(unittest.TestCase):
    def test_fixture_a_reproduces_its_expected_settlement(self) -> None:
        host, outcome = run_fixture(FIXTURE_A)
        self.assertIsNone(outcome.receipt.failure_reason, outcome.failures)
        self.assertTrue(outcome.receipt.passed)
        self.assertEqual(outcome.settlement.payouts, FIXTURE_A.expected_payouts)
        self.assertEqual(
            tuple(pot.amount for pot in outcome.settlement.pots), FIXTURE_A.expected_pots
        )
        self.assertEqual(len(outcome.decisions), FIXTURE_A.expected_controlled_actions)
        self.assertEqual(sum(outcome.settlement.final_stacks), sum(FIXTURE_A.starting_stacks))

    def test_fixture_b_reproduces_its_side_pot_expectations(self) -> None:
        host, outcome = run_fixture(FIXTURE_B)
        self.assertIsNone(outcome.receipt.failure_reason, outcome.failures)
        self.assertTrue(outcome.receipt.passed)
        self.assertEqual(outcome.settlement.payouts, FIXTURE_B.expected_payouts)
        self.assertEqual(
            tuple(pot.amount for pot in outcome.settlement.pots), FIXTURE_B.expected_pots
        )
        self.assertEqual(len(outcome.decisions), FIXTURE_B.expected_controlled_actions)
        self.assertEqual(sum(outcome.settlement.final_stacks), sum(FIXTURE_B.starting_stacks))

    def test_every_controlled_action_is_delivered_once(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(fixture.name):
                host, outcome = run_fixture(fixture)
                self.assertEqual(
                    len(host.mailbox.accepted), fixture.expected_controlled_actions
                )
                indices = sorted(index for _, index in host.mailbox.accepted)
                self.assertEqual(
                    indices, list(range(1, fixture.expected_controlled_actions + 1))
                )

    def test_the_independent_oracle_agrees_with_production_settlement(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(fixture.name):
                host, outcome = run_fixture(fixture)
                self.assertEqual(outcome.oracle_payouts, outcome.settlement.payouts)
                self.assertEqual(outcome.oracle_payouts, fixture.expected_payouts)

    def test_the_oracle_disagrees_when_the_expectation_is_wrong(self) -> None:
        """The oracle is a real judge, not a restatement of production."""

        # Fixture B's real ordering: seat 2 (K-high straight) beats seat 1
        # (Q-high straight) beats seat 0 (aces) beats seat 3 (kings).
        payouts, pots = chip_depth_settlement(
            total_contributions=(10, 6, 4, 20, 20, 20),
            folded=(False,) * 6,
            starting_stacks=(10, 6, 4, 20, 20, 20),
            strengths=(7, 8, 9, 6, 5, 4),
            button=0,
        )
        self.assertEqual(tuple(amount for amount, _ in pots), FIXTURE_B.expected_pots)
        self.assertEqual(payouts, FIXTURE_B.expected_payouts)
        shifted, _ = chip_depth_settlement(
            total_contributions=(10, 6, 4, 20, 20, 20),
            folded=(False,) * 6,
            starting_stacks=(10, 6, 4, 20, 20, 20),
            strengths=(9, 8, 7, 6, 5, 4),
            button=0,
        )
        self.assertNotEqual(shifted, FIXTURE_B.expected_payouts)

    def test_a_disagreeing_oracle_rejects_the_hand(self) -> None:
        """The comparison is real: a wrong judge must fail the hand closed."""

        def wrong_oracle(**kwargs):
            payouts, pots = chip_depth_settlement(**kwargs)
            shifted = (payouts[1], payouts[0], *payouts[2:])
            return shifted, pots

        host = ReplayHost(
            FIXTURE_B,
            run_id=f"{PROTOCOL_ID}-correctness-mismatch",
            blueprint=blueprint(),
            clock=SteadyClock(),
            settlement_oracle=wrong_oracle,
        )
        outcome = host.run()
        self.assertIs(outcome.receipt.failure_reason, FailureCode.SETTLEMENT_MISMATCH)
        self.assertFalse(outcome.receipt.passed)
        parsed = parse_trace(outcome.trace)
        self.assertFalse(parsed.terminal["passed"])
        self.assertIsNone(parsed.terminal["settlement"])
        self.assertEqual(parsed.terminal["failure_reason"], "settlement_mismatch")

    def test_folded_contributors_leave_dead_money_but_win_nothing(self) -> None:
        """A seat that folds after committing chips is a contributor, not a claimant."""

        payouts, pots = chip_depth_settlement(
            total_contributions=(5, 5, 10, 10, 0, 0),
            folded=(True, False, False, False, False, False),
            starting_stacks=(20,) * 6,
            strengths=(99, 3, 7, 5, None, None),
            button=0,
        )
        self.assertEqual(tuple(amount for amount, _ in pots), (20, 10))
        # Seat 0 has the best strength but folded: it collects nothing, and its
        # five chips stay in the pot for the live seats.
        self.assertEqual(payouts[0], 0)
        self.assertEqual(sum(payouts), 30)
        self.assertEqual(payouts[2], 30)
        for _, eligible in pots:
            self.assertNotIn(0, eligible)

    def test_odd_chips_follow_clockwise_order_from_the_button(self) -> None:
        payouts, pots = chip_depth_settlement(
            total_contributions=(3, 3, 3, 0, 0, 0),
            folded=(False, False, False, True, True, True),
            starting_stacks=(10,) * 6,
            strengths=(7, 7, 1, None, None, None),
            button=0,
        )
        self.assertEqual(tuple(amount for amount, _ in pots), (9,))
        self.assertEqual(sum(payouts), 9)
        self.assertEqual(payouts[1], 5)
        self.assertEqual(payouts[0], 4)


class TraceAndAccountingTests(unittest.TestCase):
    def test_the_published_trace_parses_and_rebinds(self) -> None:
        for fixture in FIXTURES:
            with self.subTest(fixture.name):
                host, outcome = run_fixture(fixture)
                parsed = parse_trace(outcome.trace)
                self.assertTrue(parsed.terminal["passed"])
                self.assertTrue(parsed.terminal["complete"])
                self.assertTrue(parsed.terminal["accounting_complete"])
                self.assertEqual(
                    parsed.terminal["semantic_sha256"], parsed_semantic_sha256(parsed)
                )
                self.assertEqual(
                    parsed.terminal["semantic_sha256"], outcome.semantic_digest
                )
                self.assertEqual(
                    len(parsed.decisions), fixture.expected_controlled_actions
                )

    def test_distinct_run_ids_produce_identical_semantic_bytes(self) -> None:
        first = run_fixture(
            FIXTURE_A, run_id=f"{PROTOCOL_ID}-correctness-first"
        )[1]
        second = run_fixture(
            FIXTURE_A, run_id=f"{PROTOCOL_ID}-correctness-second", clock=SteadyClock(9_999, 7)
        )[1]
        self.assertNotEqual(first.trace, second.trace)
        self.assertEqual(first.semantic_digest, second.semantic_digest)
        self.assertEqual(
            parse_trace(first.trace).terminal["semantic_sha256"],
            parse_trace(second.trace).terminal["semantic_sha256"],
        )

    def test_accounting_totals_are_disjoint_and_publication_is_separate(self) -> None:
        host, outcome = run_fixture(FIXTURE_A)
        parsed = parse_trace(outcome.trace)
        preparation = parsed.terminal["preparation_compute_seconds"]
        post_terminal = parsed.terminal["post_terminal_compute_seconds"]
        self.assertIsInstance(preparation, float)
        self.assertIsInstance(post_terminal, float)
        self.assertGreater(preparation, 0.0)
        self.assertGreater(post_terminal, 0.0)
        publication = outcome.receipt.terminal_publication_compute_seconds
        self.assertIsInstance(publication, float)
        # The deterministic witness advances on every observation, so a real
        # measured interval is strictly positive; zero would be a fabrication.
        self.assertGreater(publication, 0.0)
        # Publication is measured after the pre-publication cut and must not
        # move either counter: the totals read after the run still equal the
        # values the terminal row published before it.
        after = host.runtime.accounting()
        self.assertEqual(after.post_terminal_compute_seconds, post_terminal)
        self.assertEqual(after.preparation_compute_seconds, preparation)

    def test_the_receipt_lives_outside_the_trace_it_describes(self) -> None:
        host, outcome = run_fixture(FIXTURE_A)
        receipt = outcome.receipt
        self.assertEqual(receipt.trace_sha256, sha256(outcome.trace).hexdigest())
        self.assertNotIn(b"terminal_publication_compute_seconds", outcome.trace)
        self.assertEqual(receipt.secondary_failures, ())
        self.assertTrue(receipt.accounting_complete)

    def test_trace_files_are_created_new_under_the_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "trace.jsonl"
            host, outcome = run_fixture(
                FIXTURE_A, destination=target, run_root=root
            )
            self.assertTrue(outcome.receipt.passed)
            self.assertEqual(target.read_bytes(), outcome.trace)

    def test_a_write_failure_after_delivery_is_a_recorded_secondary_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "trace.jsonl"
            target.write_bytes(b"occupied\n")
            host, outcome = run_fixture(FIXTURE_A, destination=target, run_root=root)
            self.assertIn(FailureCode.TRACE_WRITE_FAILED, outcome.receipt.secondary_failures)
            self.assertIsNone(outcome.receipt.trace_sha256)
            self.assertFalse(outcome.receipt.passed)
            # The delivered actions stand and their decisions are retained.
            self.assertEqual(
                len(outcome.decisions), FIXTURE_A.expected_controlled_actions
            )
            self.assertEqual(
                len(host.mailbox.accepted), FIXTURE_A.expected_controlled_actions
            )
            self.assertEqual(target.read_bytes(), b"occupied\n")
            # The primary cause is untouched by the later reporting failure.
            self.assertIsNone(outcome.receipt.failure_reason)


class IdentityTests(unittest.TestCase):
    def test_production_identities_are_refused(self) -> None:
        for run_id in (PROTOCOL_ID, f"{PROTOCOL_ID}-", f"{PROTOCOL_ID}-authorized-1", "other"):
            with self.subTest(run_id):
                with self.assertRaises(ValueError):
                    ReplayHost(FIXTURE_A, run_id=run_id, blueprint=blueprint())

    def test_rehearsal_and_correctness_identities_are_disjoint(self) -> None:
        for run_id in (
            f"{PROTOCOL_ID}-correctness-abc",
            f"{PROTOCOL_ID}-rehearsal-abc",
        ):
            with self.subTest(run_id):
                ReplayHost(FIXTURE_A, run_id=run_id, blueprint=blueprint())

    def test_the_configuration_digest_binds_the_schedule_not_the_deal(self) -> None:
        first = FIXTURE_A.configuration_sha256()
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, FIXTURE_B.configuration_sha256())
        host, outcome = run_fixture(FIXTURE_A)
        parsed = parse_trace(outcome.trace)
        self.assertEqual(parsed.header["configuration_sha256"], first)
        # Only the opaque digest reaches the runtime metadata.
        self.assertNotIn(FIXTURE_A.seed_label.encode(), outcome.trace)


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
