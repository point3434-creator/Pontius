"""Slice-B replay tests: fixtures, independent oracle, terminal accounting."""

from __future__ import annotations

import sys
import tempfile
from dataclasses import replace
import unittest
from hashlib import sha256
from pathlib import Path

from pontius.immutable_blueprint import ImmutableBlueprintActionSource
import pontius.legal_decision_spine_v2 as spine_module
import pontius.v0a.runtime as runtime_module
from dataclasses import replace as dc_replace
from pontius.action_clock import ActionClockLedger
import ast
import pontius.v0a.replay as replay_module
from pontius.v0a.clock import ClockReversedError, MonotonicWitness
from pontius.v0a.model import (
    ActionMailbox,
    FailureCode,
    HandAction,
    OpponentActionEvent,
)
from pontius.v0a.replay import ScriptedAction
from pontius.v0a.runtime import HandRuntime
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
        oracle = chip_depth_settlement(
            total_contributions=(10, 6, 4, 20, 20, 20),
            folded=(False,) * 6,
            starting_stacks=(10, 6, 4, 20, 20, 20),
            strengths=(7, 8, 9, 6, 5, 4),
            button=0,
        )
        self.assertEqual(
            tuple(amount for amount, _ in oracle.pots), FIXTURE_B.expected_pots
        )
        self.assertEqual(oracle.payouts, FIXTURE_B.expected_payouts)
        shifted = chip_depth_settlement(
            total_contributions=(10, 6, 4, 20, 20, 20),
            folded=(False,) * 6,
            starting_stacks=(10, 6, 4, 20, 20, 20),
            strengths=(9, 8, 7, 6, 5, 4),
            button=0,
        )
        self.assertNotEqual(shifted.payouts, FIXTURE_B.expected_payouts)

    def test_a_disagreeing_oracle_rejects_the_hand(self) -> None:
        """The comparison is real: a wrong judge must fail the hand closed."""

        def wrong_oracle(**kwargs):
            oracle = chip_depth_settlement(**kwargs)
            payouts = oracle.payouts
            return replace(oracle, payouts=(payouts[1], payouts[0], *payouts[2:]))

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

        oracle = chip_depth_settlement(
            total_contributions=(5, 5, 10, 10, 0, 0),
            folded=(True, False, False, False, False, False),
            starting_stacks=(20,) * 6,
            strengths=(99, 3, 7, 5, None, None),
            button=0,
        )
        self.assertEqual(tuple(amount for amount, _ in oracle.pots), (20, 10))
        # Seat 0 has the best strength but folded: it collects nothing, and its
        # five chips stay in the pot for the live seats.
        self.assertEqual(oracle.payouts[0], 0)
        self.assertEqual(sum(oracle.payouts), 30)
        self.assertEqual(oracle.payouts[2], 30)
        for _, eligible in oracle.pots:
            self.assertNotIn(0, eligible)

    def test_the_comparison_covers_final_stacks_and_pot_eligibility(self) -> None:
        """Oracles that differ only in a previously ignored field must reject."""

        def wrong_stacks(**kwargs):
            oracle = chip_depth_settlement(**kwargs)
            return replace(oracle, final_stacks=(0,) * 6)

        def wrong_seats(**kwargs):
            oracle = chip_depth_settlement(**kwargs)
            return replace(
                oracle, pots=tuple((amount, (0,)) for amount, _ in oracle.pots)
            )

        for label, judge in (("final_stacks", wrong_stacks), ("pot seats", wrong_seats)):
            with self.subTest(label):
                host = ReplayHost(
                    FIXTURE_B,
                    run_id=f"{PROTOCOL_ID}-correctness-{label.replace(' ', '-')}",
                    blueprint=blueprint(),
                    clock=SteadyClock(),
                    settlement_oracle=judge,
                )
                outcome = host.run()
                self.assertIs(
                    outcome.receipt.failure_reason, FailureCode.SETTLEMENT_MISMATCH
                )
                self.assertFalse(outcome.receipt.passed)

    def test_odd_chips_follow_clockwise_order_from_the_button(self) -> None:
        oracle = chip_depth_settlement(
            total_contributions=(3, 3, 3, 0, 0, 0),
            folded=(False, False, False, True, True, True),
            starting_stacks=(10,) * 6,
            strengths=(7, 7, 1, None, None, None),
            button=0,
        )
        self.assertEqual(tuple(amount for amount, _ in oracle.pots), (9,))
        self.assertEqual(sum(oracle.payouts), 9)
        self.assertEqual(oracle.payouts[1], 5)
        self.assertEqual(oracle.payouts[0], 4)


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

    def test_a_write_failure_after_delivery_is_the_first_cause(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "trace.jsonl"
            target.write_bytes(b"occupied\n")
            host, outcome = run_fixture(FIXTURE_A, destination=target, run_root=root)
            # R4-01: the first observed typed host cause is primary
            # regardless of category; a write failure is not exempt.
            self.assertIs(
                outcome.receipt.failure_reason, FailureCode.TRACE_WRITE_FAILED
            )
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
            self.assertEqual(outcome.receipt.secondary_failures, ())


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


class R2_03HostClosureTests(unittest.TestCase):
    """Host clock failures stay typed: no escape, no manufactured success."""

    def faulting_clock(self, fail_read: int):
        class FaultingClock:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self) -> int:
                self.reads += 1
                if self.reads == fail_read:
                    raise ValueError("host clock died")
                value = self.now
                self.now += 1_000
                return value

        return FaultingClock()

    def test_a_failure_at_the_first_observation_does_not_escape(self) -> None:
        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-firstread",
            blueprint=blueprint(),
            clock=self.faulting_clock(1),
        )
        outcome = host.run()
        self.assertFalse(outcome.receipt.passed)
        self.assertFalse(outcome.receipt.accounting_complete)
        self.assertIsNotNone(outcome.receipt.failure_reason)

    def total_observations(self) -> int:
        """Count a clean run's observations so fault points land inside it."""

        class Counting:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self) -> int:
                self.reads += 1
                value = self.now
                self.now += 1_000
                return value

        clock = Counting()
        ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-count",
            blueprint=blueprint(),
            clock=clock,
        ).run()
        return clock.reads

    def test_a_failure_partway_through_the_hand_does_not_escape(self) -> None:
        total = self.total_observations()
        self.assertGreater(total, 20)
        quarter = max(1, total // 4)
        for fail_read in (quarter, total // 2, total - quarter, total - 1, total):
            with self.subTest(fail_read=fail_read):
                host = ReplayHost(
                    FIXTURE_A,
                    run_id=f"{PROTOCOL_ID}-correctness-mid{fail_read}",
                    blueprint=blueprint(),
                    clock=self.faulting_clock(fail_read),
                )
                outcome = host.run()
                self.assertFalse(
                    outcome.receipt.passed,
                    "a hand whose clock died must never report success",
                )

    def test_incomplete_accounting_cannot_report_success(self) -> None:
        host, outcome = run_fixture(FIXTURE_A)
        self.assertTrue(outcome.receipt.passed)
        self.assertTrue(outcome.receipt.accounting_complete)
        self.assertTrue(host.runtime.accounting().complete)
        # The receipt's own claim must agree with the runtime's final state.
        self.assertEqual(
            outcome.receipt.accounting_complete, host.runtime.accounting().complete
        )


class R2_08HostCountingTests(unittest.TestCase):
    """A late but accepted delivery is still a delivery in the terminal row."""

    def test_a_late_delivery_is_counted_end_to_end(self) -> None:
        clock = SteadyClock()
        real = ActionMailbox()

        class LateMailbox:
            def deliver(self, envelope):
                receipt = real.deliver(envelope)
                clock.now += 16 * NANOS
                return receipt

        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-late",
            blueprint=blueprint(),
            clock=clock,
            mailbox=LateMailbox(),
        )
        outcome = host.run()
        self.assertIs(
            outcome.receipt.failure_reason, FailureCode.ACTION_DEADLINE_EXCEEDED
        )
        self.assertFalse(outcome.receipt.passed)
        self.assertEqual(len(real.accepted), 1, "the mailbox really accepted once")
        parsed = parse_trace(outcome.trace)
        self.assertEqual(
            parsed.terminal["decision_count"],
            1,
            "a delivered late action is a delivery, not a nondelivery",
        )
        self.assertEqual(host.runtime.accepted_delivery_count, 1)


class R3_02TypedClosureCauseTests(unittest.TestCase):
    """A hand that dies on its clock must say so, with ordered typed causes."""

    def faulting_clock(self, fail_read: int, kind: str = "invalid"):
        class FaultingClock:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self):
                self.reads += 1
                if self.reads == fail_read:
                    if kind == "reversed":
                        self.now -= 5_000
                        return self.now
                    if kind == "source":
                        raise OSError("clock source died")
                    return True  # an invalid non-integer sample
                value = self.now
                self.now += 1_000
                return value

        return FaultingClock()

    def observation_count(self) -> int:
        class Counting:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self) -> int:
                self.reads += 1
                value = self.now
                self.now += 1_000
                return value

        clock = Counting()
        ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-obs",
            blueprint=blueprint(),
            clock=clock,
        ).run()
        return clock.reads

    def test_every_observation_that_dies_reports_a_typed_cause(self) -> None:
        """The sweep, not the five known positions: any fault must be named."""

        total = self.observation_count()
        self.assertGreater(total, 100)
        silent = []
        for kind in ("invalid", "reversed", "source"):
            for read in range(1, total + 1):
                host = ReplayHost(
                    FIXTURE_A,
                    run_id=f"{PROTOCOL_ID}-correctness-s{kind}{read}",
                    blueprint=blueprint(),
                    clock=self.faulting_clock(read, kind),
                )
                outcome = host.run()
                receipt = outcome.receipt
                if receipt.passed:
                    continue
                named = receipt.failure_reason is not None or receipt.secondary_failures
                if not named:
                    silent.append((kind, read))
        self.assertEqual(
            silent, [], f"{len(silent)} fault positions produced an unexplained failure"
        )

    def test_each_closure_seam_reports_invalid_and_reversed(self) -> None:
        total = self.observation_count()
        seams = range(total - 4, total + 1)  # bookkeeping, publication, finalization
        for kind, expected in (("invalid", FailureCode.CLOCK_INVALID),
                               ("reversed", FailureCode.CLOCK_REVERSED)):
            for read in seams:
                with self.subTest(kind=kind, read=read):
                    host = ReplayHost(
                        FIXTURE_A,
                        run_id=f"{PROTOCOL_ID}-correctness-seam{kind}{read}",
                        blueprint=blueprint(),
                        clock=self.faulting_clock(read, kind),
                    )
                    receipt = host.run().receipt
                    self.assertFalse(receipt.passed)
                    reported = (receipt.failure_reason, *receipt.secondary_failures)
                    self.assertIn(expected, reported)

    def test_a_clock_fault_before_a_mismatch_keeps_the_clock_as_primary(self) -> None:
        total = self.observation_count()

        def wrong_oracle(**kwargs):
            # A perturbation that always differs, unlike swapping two seats
            # whose fixture-A payouts are both zero.
            oracle = chip_depth_settlement(**kwargs)
            return replace(
                oracle, final_stacks=tuple(v + 1 for v in oracle.final_stacks)
            )

        # Fault at the bookkeeping entry, which precedes the comparison.
        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-clockfirst",
            blueprint=blueprint(),
            clock=self.faulting_clock(total - 4),
            settlement_oracle=wrong_oracle,
        )
        receipt = host.run().receipt
        self.assertIs(receipt.failure_reason, FailureCode.CLOCK_INVALID)
        self.assertIn(FailureCode.SETTLEMENT_MISMATCH, receipt.secondary_failures)

    def test_a_mismatch_before_a_clock_fault_keeps_the_mismatch_as_primary(self) -> None:
        total = self.observation_count()

        def wrong_oracle(**kwargs):
            oracle = chip_depth_settlement(**kwargs)
            return replace(
                oracle, final_stacks=tuple(v + 1 for v in oracle.final_stacks)
            )

        # Fault at the final observation, well after the comparison.
        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-mismatchfirst",
            blueprint=blueprint(),
            clock=self.faulting_clock(total),
            settlement_oracle=wrong_oracle,
        )
        receipt = host.run().receipt
        self.assertIs(receipt.failure_reason, FailureCode.SETTLEMENT_MISMATCH)
        self.assertTrue(receipt.secondary_failures)

    def test_a_dead_clock_is_never_sampled_again(self) -> None:
        total = self.observation_count()
        clock = self.faulting_clock(total - 4)
        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-nosample",
            blueprint=blueprint(),
            clock=clock,
        )
        host.run()
        after_death = clock.reads - (total - 4)
        self.assertLessEqual(
            after_death, 1, "the witness was resampled after it had already failed"
        )

    def test_accepted_actions_survive_a_closure_fault(self) -> None:
        total = self.observation_count()
        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-retain",
            blueprint=blueprint(),
            clock=self.faulting_clock(total - 4),
        )
        outcome = host.run()
        self.assertEqual(
            len(host.mailbox.accepted), FIXTURE_A.expected_controlled_actions
        )
        self.assertEqual(
            len(outcome.decisions), FIXTURE_A.expected_controlled_actions
        )
        self.assertFalse(outcome.receipt.passed)


class R2_03CompoundScheduleTests(unittest.TestCase):
    """Two faults from different channels, ordered by occurrence."""

    def reject_seat_fixture(self):
        """A real fixture whose first scripted opponent is the controlled seat."""

        return dc_replace(
            FIXTURE_A,
            name="reject-seat",
            script=(ScriptedAction("preflop", 3, "call"),) + FIXTURE_A.script[1:],
        )

    def faulting(self, at: int, kind: str = "invalid"):
        class Faulting:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self):
                self.reads += 1
                if self.reads == at:
                    if kind == "reversed":
                        self.now -= 5_000
                        return self.now
                    if kind == "source":
                        raise OSError("clock source died")
                    return True
                value = self.now
                self.now += 1_000
                return value

        return Faulting()

    def observations(self, fixture) -> int:
        class Counting:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self) -> int:
                self.reads += 1
                value = self.now
                self.now += 1_000
                return value

        clock = Counting()
        ReplayHost(
            fixture,
            run_id=f"{PROTOCOL_ID}-correctness-cnt",
            blueprint=blueprint(),
            clock=clock,
        ).run()
        return clock.reads

    def test_a_rejected_input_keeps_its_cause_ahead_of_cleanup(self) -> None:
        """A1-A3: wherever both causes occur, event_order precedes the cleanup.

        The compound case is not assumed to exist at a chosen index: the sweep
        collects every position where both an input rejection and a cleanup
        clock fault genuinely occur, asserts that set is non-empty so the test
        cannot pass vacuously, and asserts the ordering across all of them.
        """

        fixture = self.reject_seat_fixture()
        total = self.observations(fixture)
        compound = []
        for kind in ("invalid", "reversed", "source"):
            for offset in range(1, total + 1):
                host = ReplayHost(
                    fixture,
                    run_id=f"{PROTOCOL_ID}-correctness-a{kind}{offset}",
                    blueprint=blueprint(),
                    clock=self.faulting(offset, kind),
                )
                receipt = host.run().receipt
                codes = (receipt.failure_reason, *receipt.secondary_failures)
                clock_codes = [
                    c for c in codes
                    if c in (FailureCode.CLOCK_INVALID, FailureCode.CLOCK_REVERSED)
                ]
                if FailureCode.EVENT_ORDER in codes and clock_codes:
                    compound.append((kind, offset, codes))
        self.assertTrue(
            compound,
            "no schedule produced both an input rejection and a cleanup fault; "
            "the compound case would be untested",
        )
        for kind, offset, codes in compound:
            self.assertIs(
                codes[0],
                FailureCode.EVENT_ORDER,
                f"cleanup cause ordered ahead of its input failure ({kind} @{offset})",
            )

    def test_the_input_failure_is_never_ordered_after_its_own_cleanup(self) -> None:
        """The R4-02 inversion: cleanup must not become primary."""

        fixture = self.reject_seat_fixture()
        total = self.observations(fixture)
        for offset in range(1, total + 1):
            for kind in ("invalid", "reversed"):
                host = ReplayHost(
                    fixture,
                    run_id=f"{PROTOCOL_ID}-correctness-inv{kind}{offset}",
                    blueprint=blueprint(),
                    clock=self.faulting(offset, kind),
                )
                receipt = host.run().receipt
                codes = (receipt.failure_reason, *receipt.secondary_failures)
                if FailureCode.EVENT_ORDER in codes:
                    clock_codes = [
                        c for c in codes
                        if c in (FailureCode.CLOCK_INVALID, FailureCode.CLOCK_REVERSED)
                    ]
                    if clock_codes:
                        self.assertIs(
                            receipt.failure_reason,
                            FailureCode.EVENT_ORDER,
                            f"cleanup ordered ahead of its cause at {kind} {offset}",
                        )

    def test_a_host_side_exception_is_contained_not_escaped(self) -> None:
        """G1: any host-side exception yields a receipt instead of propagating.

        Several unrelated exception classes, because pinning the one class the
        test happens to raise would let a narrowed catch pass.
        """

        for error in (
            ZeroDivisionError("oracle blew up"),
            ValueError("oracle disagreed"),
            KeyError("oracle lost a seat"),
            AssertionError("oracle broke conservation"),
            OSError("oracle could not read"),
        ):
            with self.subTest(type(error).__name__):
                def exploding(_error=error, **kwargs):
                    raise _error

                host = ReplayHost(
                    FIXTURE_A,
                    run_id=f"{PROTOCOL_ID}-correctness-g1{type(error).__name__}",
                    blueprint=blueprint(),
                    clock=SteadyClock(),
                    settlement_oracle=exploding,
                )
                outcome = host.run()  # must not raise
                self.assertFalse(outcome.receipt.passed)
                self.assertIsNotNone(outcome.receipt.failure_reason)

    def test_a_pre_boundary_rejection_journals_its_cause(self) -> None:
        """A reject that never opened a boundary still names why it failed."""

        runtime = HandRuntime(
            blueprint=blueprint(), mailbox=ActionMailbox(), clock=SteadyClock()
        )
        stray = OpponentActionEvent(
            hand_id="no-such-hand",
            event_index=1,
            street="preflop",
            seat=4,
            action=HandAction(kind="fold", raise_to=None),
        )
        outcome = runtime.dispatch(stray)
        self.assertEqual(outcome.status, "failed")
        self.assertEqual(runtime.closure_failures, (FailureCode.EVENT_ORDER,))

    def test_the_journal_never_deduplicates_repeated_codes(self) -> None:
        runtime = HandRuntime(
            blueprint=blueprint(), mailbox=ActionMailbox(), clock=SteadyClock()
        )
        runtime.record(FailureCode.CLOCK_INVALID)
        runtime.record(FailureCode.CLOCK_INVALID)
        self.assertEqual(
            runtime.closure_failures,
            (FailureCode.CLOCK_INVALID, FailureCode.CLOCK_INVALID),
        )
        with self.assertRaises(TypeError):
            runtime.record("clock_invalid")


class R2_03ConservationTests(unittest.TestCase):
    """Contract property: reported causes equal the faults that genuinely occurred.

    This is stated over an independent observer of the sealed ledger, not over
    the runtime's own bookkeeping, so it survives any reimplementation of the
    cause flow and would catch a closure seam nobody has enumerated.
    """

    def genuine_raises_and_report(self, fixture, at: int, kind: str):
        observed: list[str] = []

        class Recording(ActionClockLedger):
            """The real sealed ledger; every raise it makes is witnessed."""

            # Only the leaf that actually calls the witness is recorded:
            # _observe delegates to _read_clock, so wrapping both would count
            # one genuine fault twice.
            def _read_clock(self):
                alive = not self._clock_ns.failed
                try:
                    return ActionClockLedger._read_clock(self)
                except BaseException as error:
                    if alive:
                        observed.append(
                            "clock_reversed"
                            if isinstance(error, ClockReversedError)
                            else "clock_invalid"
                        )
                    raise

        class Faulting:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self):
                self.reads += 1
                if self.reads == at:
                    if kind == "reversed":
                        self.now -= 5_000
                        return self.now
                    return True
                value = self.now
                self.now += 1_000
                return value

        original_runtime = runtime_module.ActionClockLedger
        original_spine = spine_module.ActionClockLedger
        runtime_module.ActionClockLedger = Recording
        spine_module.ActionClockLedger = Recording
        try:
            host = ReplayHost(
                fixture,
                run_id=f"{PROTOCOL_ID}-correctness-cons{kind}{at}",
                blueprint=blueprint(),
                clock=Faulting(),
            )
            receipt = host.run().receipt
        finally:
            runtime_module.ActionClockLedger = original_runtime
            spine_module.ActionClockLedger = original_spine
        reported = [
            c.value
            for c in (receipt.failure_reason, *receipt.secondary_failures)
            if c in (FailureCode.CLOCK_INVALID, FailureCode.CLOCK_REVERSED)
        ]
        return observed, reported

    def fixtures(self):
        """Both a clean hand and one whose input is rejected mid-hand.

        The rejection fixture is what reaches the abort-cleanup seam; a sweep
        over the clean fixture alone cannot see it, which is how that seam
        stayed unenumerated for two rounds.
        """

        rejecting = dc_replace(
            FIXTURE_A,
            name="reject-seat",
            script=(ScriptedAction("preflop", 3, "call"),) + FIXTURE_A.script[1:],
        )
        return (FIXTURE_A, rejecting)

    def observation_total(self, fixture) -> int:
        class Counting:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0

            def __call__(self) -> int:
                self.reads += 1
                value = self.now
                self.now += 1_000
                return value

        clock = Counting()
        ReplayHost(
            fixture,
            run_id=f"{PROTOCOL_ID}-correctness-ct",
            blueprint=blueprint(),
            clock=clock,
        ).run()
        return clock.reads

    def test_reported_clock_causes_equal_the_genuine_raises(self) -> None:
        """Every genuine ledger fault reaches the receipt; none is invented.

        Stated over an independent observer of the sealed ledger rather than
        over the runtime's bookkeeping, so it survives a reimplementation and
        fails for a closure seam nobody has enumerated. The sweep covers every
        observation of every fixture, because a partial sweep is how the last
        two attempts missed their seam.
        """

        mismatched = []
        checked = 0
        for fixture in self.fixtures():
            total = self.observation_total(fixture)
            for kind in ("invalid", "reversed"):
                for at in range(1, total + 1):
                    genuine, reported = self.genuine_raises_and_report(
                        fixture, at, kind
                    )
                    checked += 1
                    # Conservation is over the ordered sequence, not presence:
                    # a dead-clock echo adds a duplicate that a presence check
                    # cannot see, and a dropped seam removes one.
                    if genuine != reported:
                        mismatched.append((fixture.name, kind, at, genuine, reported))
        self.assertGreater(checked, 200, "the sweep must be broad to mean anything")
        self.assertEqual(
            mismatched,
            [],
            "reported clock causes differ from the faults that genuinely occurred",
        )


class R2_03BodyOwnershipTests(unittest.TestCase):
    """A body owns its cause; cleanup can only follow it.

    The matrix the r005 reviewers specified: returned mismatch versus raised
    error, ledger-origin versus direct-witness-origin faults, and entry, body,
    exit and finalization positions.
    """

    def armed_clock(self):
        class Armed:
            def __init__(self) -> None:
                self.now = 1_000
                self.reads = 0
                self._fail_at = None
                self._kind = "invalid"

            def fail_at(self, read: int, kind: str = "invalid") -> None:
                self._fail_at = read
                self._kind = kind

            def poison(self) -> None:
                self.fail_at(self.reads + 1, "invalid")

            def __call__(self):
                self.reads += 1
                if self._fail_at == self.reads:
                    self._fail_at = None
                    if self._kind == "reversed":
                        self.now -= 5_000
                        return self.now
                    return True
                value = self.now
                self.now += 1_000
                return value

        return Armed()

    def test_a_raised_body_error_precedes_its_cleanup_fault(self) -> None:
        """R5-01: body cause first, exit-seam cleanup cause second."""

        for kind in ("invalid", "reversed"):
            with self.subTest(kind=kind):
                clock = self.armed_clock()

                def exploding(_clock=clock, _kind=kind, **kwargs):
                    # the very next observation is the interval's own exit
                    _clock.fail_at(_clock.reads + 1, _kind)
                    raise ValueError("oracle blew up during the body")

                host = ReplayHost(
                    FIXTURE_A,
                    run_id=f"{PROTOCOL_ID}-correctness-body{kind}",
                    blueprint=blueprint(),
                    clock=clock,
                    settlement_oracle=exploding,
                )
                receipt = host.run().receipt
                self.assertFalse(receipt.passed)
                self.assertIs(
                    receipt.failure_reason,
                    FailureCode.SETTLEMENT_MISMATCH,
                    "the body's own cause must not be overtaken by its cleanup",
                )
                expected = (
                    FailureCode.CLOCK_REVERSED
                    if kind == "reversed"
                    else FailureCode.CLOCK_INVALID
                )
                self.assertIn(expected, receipt.secondary_failures)

    def test_a_clock_fault_raised_by_the_body_is_not_lost(self) -> None:
        """R5-02: a body-origin clock fault is owned, not assumed recorded."""

        for kind in ("invalid", "reversed"):
            with self.subTest(kind=kind):
                source = self.armed_clock()
                witness = MonotonicWitness(source)

                def sampling(_source=source, _witness=witness, _kind=kind, **kwargs):
                    # a real witness read that genuinely fails inside the body
                    _source.fail_at(_source.reads + 1, _kind)
                    return _witness()

                host = ReplayHost(
                    FIXTURE_A,
                    run_id=f"{PROTOCOL_ID}-correctness-wit{kind}",
                    blueprint=blueprint(),
                    clock=witness,
                    settlement_oracle=sampling,
                )
                receipt = host.run().receipt
                self.assertFalse(receipt.passed)
                reported = (receipt.failure_reason, *receipt.secondary_failures)
                expected = (
                    FailureCode.CLOCK_REVERSED
                    if kind == "reversed"
                    else FailureCode.CLOCK_INVALID
                )
                self.assertIsNotNone(
                    receipt.failure_reason,
                    "a genuine body-origin clock fault reached no receipt",
                )
                self.assertIn(expected, reported)

    def test_a_returned_mismatch_still_precedes_a_later_cleanup_fault(self) -> None:
        """The returned-error half of the matrix, against the raised half."""

        clock = self.armed_clock()

        def wrong_and_arm(_clock=clock, **kwargs):
            oracle = chip_depth_settlement(**kwargs)
            _clock.fail_at(_clock.reads + 1, "invalid")
            return replace(oracle, final_stacks=tuple(v + 1 for v in oracle.final_stacks))

        host = ReplayHost(
            FIXTURE_A,
            run_id=f"{PROTOCOL_ID}-correctness-retmm",
            blueprint=blueprint(),
            clock=clock,
            settlement_oracle=wrong_and_arm,
        )
        receipt = host.run().receipt
        self.assertFalse(receipt.passed)
        self.assertIs(receipt.failure_reason, FailureCode.SETTLEMENT_MISMATCH)
        self.assertIn(FailureCode.CLOCK_INVALID, receipt.secondary_failures)

    def test_no_host_operation_uses_an_unowned_interval(self) -> None:
        """Structural: the ordering rule cannot be bypassed by forgetting it.

        The unowned measured intervals are private to the runtime; any host
        operation must go through the owner that journals a body cause before
        cleanup. A future operation added without the owner fails here without
        anyone knowing it exists.
        """

        source = Path(replay_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                "_bookkeeping",
                "_publication_interval",
            ):
                offenders.append(f"{node.attr} at line {node.lineno}")
        self.assertEqual(
            offenders,
            [],
            "a host operation reached an unowned measured interval",
        )
        runtime_source = Path(runtime_module.__file__).read_text(encoding="utf-8")
        self.assertIn("def owned_bookkeeping", runtime_source)
        self.assertIn("def owned_publication", runtime_source)


class FailureAdapterRegressionTests(unittest.TestCase):
    """Real source/host boundaries; expected causes come from scheduled faults."""

    class Source(SteadyClock):
        def __init__(self):
            super().__init__()
            self.reads = 0
            self.fail_at = None
            self.kind = "invalid"
            self.observed = []

        def __call__(self):
            self.reads += 1
            if self.reads == self.fail_at:
                code = (FailureCode.CLOCK_REVERSED if self.kind == "reversed"
                        else FailureCode.CLOCK_INVALID)
                self.observed.append(code)
                if self.kind == "exception":
                    raise OSError("source fault")
                if self.kind == "reversed":
                    return self.now - 5_000
                return True
            return super().__call__()

    def host(self, fixture, source, oracle=chip_depth_settlement):
        return ReplayHost(
            fixture, run_id=f"{PROTOCOL_ID}-correctness-adapter-{fixture.name}",
            blueprint=blueprint(), clock=source, settlement_oracle=oracle,
        )

    def completed(self, host, **kwargs):
        try:
            return host.run(**kwargs)
        except BaseException as error:
            escaped_type = type(error).__name__
        # Assert outside the handler: unittest must not render the hostile
        # exception through the assertion's implicit exception context.
        self.fail("host escaped instead of returning a receipt: " + escaped_type)

    def causes(self, outcome):
        receipt = outcome.receipt
        return (() if receipt.failure_reason is None else (receipt.failure_reason,)) + (
            receipt.secondary_failures
        )

    def entry_read(self, fixture):
        source = self.Source()
        entry = []
        def oracle(**kwargs):
            entry.append(source.reads)
            return chip_depth_settlement(**kwargs)
        outcome = self.completed(self.host(fixture, source, oracle))
        self.assertTrue(outcome.receipt.passed)
        self.assertEqual(len(entry), 1)
        return entry[0]

    def test_one_source_fault_is_not_counted_again_when_the_body_reads_the_dead_witness(self):
        from pontius.v0a.clock import ClockInvalidError
        for fixture in FIXTURES:
            entry = self.entry_read(fixture)
            for kind in ("invalid", "exception", "reversed"):
                for mode in ("echo", "independent_clock", "independent_error"):
                    with self.subTest(fixture=fixture.name, kind=kind, mode=mode):
                        source = self.Source()
                        source.fail_at, source.kind = entry, kind
                        witness = MonotonicWitness(source)
                        def oracle(**kwargs):
                            if mode == "independent_clock":
                                raise ClockInvalidError("a different body occurrence")
                            if mode == "independent_error":
                                raise ValueError("a different body occurrence")
                            witness()
                            return chip_depth_settlement(**kwargs)
                        host = self.host(fixture, witness, oracle)
                        outcome = self.completed(host)
                        wanted = tuple(source.observed)
                        if mode != "echo":
                            wanted += ((FailureCode.CLOCK_INVALID,) if mode == "independent_clock"
                                       else (FailureCode.SETTLEMENT_MISMATCH,))
                        self.assertEqual(self.causes(outcome), wanted)
                        self.assertEqual(source.reads, entry, "a dead source must not be retried")
                        self.assertEqual(host.runtime.accepted_delivery_count,
                                         4 if fixture is FIXTURE_A else 2)
                        self.assertFalse(outcome.receipt.passed)

    def test_caught_source_fault_survives_a_return_or_a_different_body_failure(self):
        from pontius.v0a.clock import ClockInvalidError
        for fixture in FIXTURES:
            for mode in ("return", "raise", "mismatch"):
                with self.subTest(fixture=fixture.name, mode=mode):
                    source = self.Source()
                    witness = MonotonicWitness(source)
                    def oracle(**kwargs):
                        source.fail_at = source.reads + 1
                        try:
                            witness()
                        except ClockInvalidError:
                            pass
                        if mode == "raise":
                            raise ValueError("body failure after caught source fault")
                        result = chip_depth_settlement(**kwargs)
                        return (replace(result, final_stacks=tuple(x + 1 for x in result.final_stacks))
                                if mode == "mismatch" else result)
                    host = self.host(fixture, witness, oracle)
                    outcome = self.completed(host)
                    wanted = tuple(source.observed)
                    if mode != "return":
                        wanted += (FailureCode.SETTLEMENT_MISMATCH,)
                    self.assertEqual(self.causes(outcome), wanted)
                    self.assertFalse(outcome.receipt.passed)
                    self.assertFalse(outcome.receipt.accounting_complete)

    def errors(self, inspected):
        class BadMessage:
            def __str__(self):
                inspected.append("str")
                raise RuntimeError("message rendering is not safe")

        class MetadataError(Exception):
            @property
            def __class__(self):
                inspected.append("__class__")
                raise RuntimeError("metadata inspection is not safe")

        class SpoofedError(Exception):
            @property
            def __class__(self):
                inspected.append("__class__")
                return ClockReversedError

        class TracebackError(Exception):
            def __setattr__(self, name, value):
                if name == "__traceback__":
                    inspected.append("__traceback__")
                    raise RuntimeError("traceback mutation is not safe")
                super().__setattr__(name, value)

        return (ValueError("ordinary"), ValueError(BadMessage()), MetadataError(),
                SpoofedError(), TracebackError(), StopIteration("body stopped"))

    def test_error_handling_does_not_execute_caller_presentation_or_metadata(self):
        for fixture in FIXTURES:
            for boundary in ("settlement", "publication"):
                for cleanup in (False, True):
                    inspected = []
                    for error in self.errors(inspected):
                        with self.subTest(fixture=fixture.name, boundary=boundary,
                                          cleanup=cleanup, error=type(error).__name__):
                            source = self.Source()
                            def fail():
                                if cleanup:
                                    source.fail_at = source.reads + 1
                                raise error
                            def oracle(**kwargs):
                                fail()
                            class Destination:
                                def __fspath__(self):
                                    fail()
                            host = self.host(
                                fixture, source, oracle if boundary == "settlement"
                                else chip_depth_settlement,
                            )
                            with tempfile.TemporaryDirectory() as directory:
                                kwargs = ({"destination": Destination(), "run_root": Path(directory)}
                                          if boundary == "publication" else {})
                                outcome = self.completed(host, **kwargs)
                            first = (FailureCode.SETTLEMENT_MISMATCH if boundary == "settlement"
                                     else FailureCode.TRACE_WRITE_FAILED)
                            self.assertEqual(self.causes(outcome), (first, *source.observed))
                            self.assertEqual(inspected, [])
                            self.assertEqual(len(outcome.decisions), 4 if fixture is FIXTURE_A else 2)
                            self.assertEqual(len(host.mailbox.accepted), len(outcome.decisions))
                            self.assertFalse(outcome.receipt.passed)

    def test_raw_source_exception_metadata_never_reaches_host_adapters(self):
        from pontius.v0a.clock import ClockInvalidError
        touched = []
        class SourceError(ClockInvalidError):
            @property
            def __class__(self):
                touched.append("__class__")
                raise RuntimeError("do not inspect source metadata")
            def __str__(self):
                touched.append("str")
                raise RuntimeError("do not render the source exception")
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture.name):
                reads = []
                def source():
                    reads.append(1)
                    raise SourceError()
                outcome = self.completed(self.host(fixture, source))
                self.assertEqual(self.causes(outcome), (FailureCode.CLOCK_INVALID,))
                self.assertEqual(reads, [1])
                self.assertEqual(touched, [])
                self.assertFalse(outcome.receipt.passed)



class AcceptingReplayTests(unittest.TestCase):
    """An accepting verifier judges supplied traces, not a rerun of their fixture."""

    def checker(self):
        verify = getattr(replay_module, "verify_successful_trace", None)
        self.assertTrue(callable(verify), "a public accepting trace checker is required")
        return verify

    def verify(self, content, fixture=FIXTURE_A, **changes):
        args = dict(fixture=fixture, blueprint=blueprint(), source_commit="0" * 40,
                    source_manifest_sha256="0" * 64, expected_mode="correctness",
                    expected_clock_kind="deterministic_test")
        args.update(changes)
        return self.checker()(content, **args)

    @staticmethod
    def changed(content, change):
        import json
        rows = [json.loads(row) for row in content.splitlines()]
        change(rows)
        keys = ("hand_id", "event_index", "action_index", "street_action_index", "seat",
                "street", "state_before_sha256", "state_after_sha256", "visible_cards_sha256",
                "blueprint_sha256", "selected_action", "selection_reason", "spine_reason",
                "preparation_use")
        dumps = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
        for index, row in enumerate(rows):
            row["record_index"] = index
        payload = dict(events=[row["event"] for row in rows if row["record_type"] == "event"],
                       decisions=[{key: row[key] for key in keys} for row in rows
                                  if row["record_type"] == "decision"],
                       settlement=rows[-1]["settlement"])
        rows[-1]["semantic_sha256"] = sha256(dumps(payload).encode()).hexdigest()
        rows[-1]["trace_prefix_sha256"] = sha256(
            "".join(dumps(row) + "\n" for row in rows[:-1]).encode()).hexdigest()
        return "".join(dumps(row) + "\n" for row in rows).encode()

    def test_accepts_both_real_controls_without_running_the_host_again(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture.name):
                _, outcome = run_fixture(fixture)
                target_codes = {ReplayHost.run.__code__, HandRuntime.dispatch.__code__,
                                runtime_module.select_blueprint_action.__code__,
                                runtime_module._select_admitted_blueprint_action.__code__}
                seen = []
                def observe(frame, event, argument):
                    if event == "call" and frame.f_code in target_codes:
                        seen.append(frame.f_code.co_name)
                previous = sys.getprofile()
                sys.setprofile(observe)
                try:
                    accepted = self.verify(outcome.trace, fixture)
                finally:
                    sys.setprofile(previous)
                self.assertEqual(seen, [])
                self.assertEqual(accepted.semantic_sha256, outcome.semantic_digest)
                self.assertEqual(accepted.payouts, fixture.expected_payouts)

    def test_accepts_a_nonpassive_table_hit_and_fold_terminal(self):
        from pontius.holdem_cards import OneSeatCardState
        from pontius.immutable_blueprint import BlueprintDecisionKey, BlueprintActionEntry
        from pontius.no_limit_betting import NoLimitBettingState
        fixture = replace(FIXTURE_A, name="control-table-hit",
                          script=tuple(replace(step, kind="call")
                              if step.street == "preflop" and step.seat == 2 else step
                              for step in FIXTURE_A.script),
                          expected_payouts=(0, 0, 0, 36, 0, 0), expected_pots=(36,))
        state = NoLimitBettingState.new_hand(button=fixture.button,
                    starting_stacks=fixture.starting_stacks, small_blind=1, big_blind=2)
        cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=fixture.deal().hand(3))
        key = BlueprintDecisionKey.from_state(cards=cards, betting=state,
                                             decision=state.legal_decision())
        policy = ImmutableBlueprintActionSource(source_id="trace-nonpassive-control",
                    entries=(BlueprintActionEntry(key, HandAction("raise", 6).to_betting_action()),))
        host = ReplayHost(fixture, run_id=PROTOCOL_ID + "-correctness-table-hit",
                          blueprint=policy, clock=SteadyClock())
        outcome = host.run()
        self.assertTrue(outcome.receipt.passed, outcome.failures)
        self.assertEqual(self.verify(outcome.trace, fixture, blueprint=policy).payouts,
                         fixture.expected_payouts)
        fold = replace(FIXTURE_A, name="control-fold-terminal",
                       script=tuple(ScriptedAction("preflop", seat, "fold")
                                    for seat in (4, 5, 0, 1, 2)),
                       expected_payouts=(0, 0, 0, 5, 0, 0), expected_pots=(5,),
                       expected_controlled_actions=1)
        host = ReplayHost(fold, run_id=PROTOCOL_ID + "-correctness-fold-terminal",
                          blueprint=policy, clock=SteadyClock())
        outcome = host.run()
        self.assertTrue(outcome.receipt.passed, outcome.failures)
        self.assertEqual(self.verify(outcome.trace, fold, blueprint=policy).payouts,
                         fold.expected_payouts)

    def test_emission_reserve_is_not_a_false_work_failure(self):
        clock = SteadyClock()
        real = ActionMailbox()
        class DelayedMailbox:
            def deliver(self, envelope):
                receipt = real.deliver(envelope)
                clock.now += 14_500_000_000
                return receipt
        host = ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-emission-reserve",
                          blueprint=blueprint(), clock=clock, mailbox=DelayedMailbox())
        outcome = host.run()
        self.assertTrue(outcome.receipt.passed, outcome.failures)
        for record in outcome.decisions:
            self.assertGreater(record.timing.elapsed_ns, 14_000_000_000)
            self.assertLessEqual(record.timing.elapsed_ns, 15_000_000_000)
            self.assertFalse(record.timing.work_cutoff_crossed)
        self.assertEqual(self.verify(outcome.trace).payouts, FIXTURE_A.expected_payouts)

    def test_all_expected_bindings_and_decision_schedule_fields_are_checked(self):
        from pontius.v0a.trace import TraceInvalidError
        _, outcome = run_fixture(FIXTURE_A)
        changes = (
            ("manifest", lambda rows: rows[0].update(source_manifest_sha256="2" * 64)),
            ("mode", lambda rows: rows[0].update(mode="rehearsal")),
            ("clock-kind", lambda rows: rows[0].update(clock_kind="monotonic_ns")),
            ("decision-policy", lambda rows: rows[2].update(blueprint_sha256="2" * 64)),
            ("decision-trigger", lambda rows: rows[2].update(event_index=1)),
            ("street-count", lambda rows: rows[2].update(street_action_index=2)),
            ("decision-actor", lambda rows: rows[2].update(seat=4)),
            ("decision-street", lambda rows: rows[2].update(street="flop")),
            ("state-before", lambda rows: rows[2].update(state_before_sha256="2" * 64)),
            ("spine-reason", lambda rows: rows[2].update(spine_reason="candidate")),
            ("opponent-actor", lambda rows: rows[3]["event"].update(seat=0)),
            ("opponent-action", lambda rows: rows[3]["event"].update(
                action={"kind": "fold", "raise_to": None})),
            ("initial-cards", lambda rows: rows[1]["event"].update(private_cards=[0, 1])),
            ("reveal-cards", lambda rows: next(row["event"] for row in rows
                if row["record_type"] == "event" and row["event"]["kind"] == "street_revealed").update(cards=[0, 1, 2])),
            ("showdown-rank", lambda rows: rows[-2]["event"]["strengths"].__setitem__(0, [0, 1])),
            ("showdown-mask", lambda rows: rows[-2]["event"]["strengths"].__setitem__(0, None)),
        )
        for label, change in changes:
            with self.subTest(label=label):
                with self.assertRaises(TraceInvalidError):
                    self.verify(self.changed(outcome.trace, change))
        for kwargs in (dict(source_commit="2" * 40),
                       dict(source_manifest_sha256="2" * 64),
                       dict(expected_mode="rehearsal"), dict(expected_clock_kind="monotonic_ns")):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(TraceInvalidError):
                    self.verify(outcome.trace, **kwargs)

    def test_expectation_subtypes_cannot_supply_behavior(self):
        from pontius.v0a.trace import TraceInvalidError
        from pontius.v0a.replay import Fixture
        _, outcome = run_fixture(FIXTURE_A)
        touched = []
        class FixtureDelegate(Fixture):
            def deal(self):
                touched.append("fixture")
                return super().deal()
        class PolicyDelegate(ImmutableBlueprintActionSource):
            @property
            def digest(self):
                touched.append("policy")
                return super().digest
        class TextDelegate(str):
            def __eq__(self, other):
                touched.append("text")
                return super().__eq__(other)
        fixture = FixtureDelegate(**{name: getattr(FIXTURE_A, name)
                                     for name in Fixture.__dataclass_fields__})
        for kwargs in (dict(fixture=fixture), dict(blueprint=PolicyDelegate("delegate")),
                       dict(source_commit=TextDelegate("0" * 40))):
            with self.subTest(kwargs=tuple(kwargs)):
                with self.assertRaises(TraceInvalidError):
                    self.verify(outcome.trace, **kwargs)
        self.assertEqual(touched, [])

    def test_rebound_invalid_semantics_are_not_legalized_by_hashes(self):
        from pontius.v0a.trace import TraceInvalidError
        _, outcome = run_fixture(FIXTURE_A)
        changes = (
            ("illegal-check", lambda rows: rows[2].update(
                selected_action={"kind": "check", "raise_to": None})),
            ("illegal-raise", lambda rows: rows[2].update(
                selected_action={"kind": "raise", "raise_to": 1})),
            ("legal-wrong-policy", lambda rows: rows[2].update(
                selected_action={"kind": "raise", "raise_to": 6}, selection_reason="table_hit")),
            ("wrong-state", lambda rows: rows[2].update(state_after_sha256="1" * 64)),
            ("wrong-cards", lambda rows: rows[2].update(visible_cards_sha256="1" * 64)),
            ("false-hit", lambda rows: rows[2].update(selection_reason="table_hit")),
            ("wrong-source", lambda rows: rows[0].update(source_commit="1" * 40)),
            ("wrong-policy", lambda rows: rows[0].update(blueprint_sha256="1" * 64)),
            ("wrong-config", lambda rows: rows[0].update(configuration_sha256="1" * 64)),
            ("payout", lambda rows: rows[-1]["settlement"]["payouts"].reverse()),
            ("final-stacks", lambda rows: rows[-1]["settlement"]["final_stacks"].reverse()),
            ("eligibility", lambda rows: rows[-1]["settlement"]["pots"][0].update(seats=[0])),
            ("missing-decision", lambda rows: (rows.pop(2),
                                               rows[-1].update(decision_count=3))),
            ("reordered-decision", lambda rows: rows.insert(4, rows.pop(2))),
        )
        for label, change in changes:
            with self.subTest(label=label):
                with self.assertRaises(TraceInvalidError):
                    self.verify(self.changed(outcome.trace, change))

    def test_folded_only_depths_do_not_split_an_award(self):
        from pontius.no_limit_betting import NoLimitBettingState
        state = NoLimitBettingState.new_hand(button=0, starting_stacks=(20,) * 6,
                                            small_blind=1, big_blind=2)
        for kind, amount in (("raise", 5), ("call", None), ("call", None),
                             ("fold", None), ("fold", None), ("fold", None)):
            state = state.apply_action(HandAction(kind, amount).to_betting_action())
        state = state.advance_street()
        for kind, amount in (("raise", 10), ("call", None), ("fold", None)):
            state = state.apply_action(HandAction(kind, amount).to_betting_action())
        self.assertEqual(state.total_contributions, (0, 1, 2, 15, 15, 5))
        # Two live tied players claim the same 38 chips; dead contribution
        # depths cannot create extra separately rounded awards (20/18).
        self.assertEqual(tuple((pot.amount, pot.eligible_seats) for pot in state.side_pots()),
                         ((38, (3, 4)),))
        oracle = chip_depth_settlement(total_contributions=state.total_contributions,
                    folded=state.folded, starting_stacks=state.starting_stacks,
                    strengths=(None, None, None, 1, 1, None), button=state.button)
        self.assertEqual(oracle.pots, ((38, (3, 4)),))
        self.assertEqual(oracle.payouts, (0, 0, 0, 19, 19, 0))

    def test_failed_prefix_cannot_obtain_success(self):
        from pontius.v0a.trace import TraceInvalidError
        def failed_clock():
            raise ValueError("ordinary correctness failure")
        host = ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-checker-failure",
                          blueprint=blueprint(), clock=failed_clock)
        outcome = host.run()
        with self.assertRaises(TraceInvalidError):
            self.verify(outcome.trace)


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
