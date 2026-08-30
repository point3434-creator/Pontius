"""Slice-B trace contract tests: canonical bytes, strict parsing, semantics."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from pontius.v0a.model import (
    DecisionRecord,
    DeliveryStatus,
    FailureCode,
    FailureRecord,
    HandAction,
    HandStartedEvent,
    OpponentActionEvent,
    PotRecord,
    PreparationUseRecord,
    SelectionReason,
    SettlementRecord,
    ShowdownResultEvent,
    StreetRevealedEvent,
    TimingRecord,
    TimingStatus,
)
from pontius.v0a.trace import (
    TRACE_SCHEMA_VERSION,
    TraceBuilder,
    TraceInvalidError,
    TraceWriteError,
    canonical_json,
    parse_trace,
    parsed_semantic_sha256,
    semantic_sha256,
    write_trace,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
HAND = "hand-A"


def completed_timing(start: int = 1_000, elapsed: int = 5_000) -> TimingRecord:
    return TimingRecord(
        status=TimingStatus.COMPLETED,
        interruption_reason=None,
        wall_start_ns=start,
        last_valid_observation_ns=start + elapsed,
        emission_observed_ns=start + elapsed,
        elapsed_ns=elapsed,
        response_compute_seconds=0.25,
        response_uninstrumented_seconds=0.5,
        work_cutoff_crossed=False,
        deadline_crossed=False,
    )


def interrupted_timing(code: FailureCode = FailureCode.CLOCK_INVALID) -> TimingRecord:
    return TimingRecord(
        status=TimingStatus.INTERRUPTED,
        interruption_reason=code,
        wall_start_ns=1_000,
        last_valid_observation_ns=1_200,
        emission_observed_ns=None,
        elapsed_ns=None,
        response_compute_seconds=None,
        response_uninstrumented_seconds=None,
        work_cutoff_crossed=None,
        deadline_crossed=None,
    )


def decision(action_index: int = 1, timing: TimingRecord | None = None) -> DecisionRecord:
    return DecisionRecord(
        hand_id=HAND,
        event_index=0,
        action_index=action_index,
        street_action_index=action_index,
        seat=3,
        street="preflop",
        state_before_sha256=DIGEST_A,
        state_after_sha256=DIGEST_B,
        visible_cards_sha256=DIGEST_C,
        blueprint_sha256=DIGEST_D,
        selected_action=HandAction(kind="call", raise_to=None),
        selection_reason=SelectionReason.PASSIVE_DEFAULT,
        spine_reason="no_candidate",
        timing=completed_timing() if timing is None else timing,
        preparation_use=PreparationUseRecord(),
        failure_reason=None,
    )


def started() -> HandStartedEvent:
    return HandStartedEvent(
        hand_id=HAND,
        event_index=0,
        button=0,
        controlled_seat=3,
        starting_stacks=(200,) * 6,
        small_blind=1,
        big_blind=2,
        private_cards=(0, 13),
    )


def settlement() -> SettlementRecord:
    return SettlementRecord(
        payouts=(12, 0, 0, 0, 0, 0),
        final_stacks=(210, 198, 198, 198, 198, 198),
        pots=(PotRecord(amount=12, seats=(0, 1, 2, 3, 4, 5)),),
    )


def builder(run_id: str = "run-1", mode: str = "correctness") -> TraceBuilder:
    return TraceBuilder(
        run_id=run_id,
        mode=mode,
        source_commit="0" * 40,
        source_manifest_sha256=DIGEST_A,
        configuration_sha256=DIGEST_B,
        blueprint_sha256=DIGEST_D,
        clock_kind="deterministic_test",
    )


def complete_trace(run_id: str = "run-1", *, events=None, decisions=None) -> bytes:
    events = (started(),) if events is None else events
    decisions = (decision(),) if decisions is None else decisions
    trace = builder(run_id)
    for event in events:
        trace.add_event(event)
    for record in decisions:
        trace.add_decision(record)
    return trace.close(
        hand_id=HAND,
        complete=True,
        passed=True,
        failure_reason=None,
        event_count=len(events),
        decision_count=len(decisions),
        interrupted_response_count=0,
        accounting_complete=True,
        settlement=settlement(),
        semantic_digest=semantic_sha256(
            events=tuple(events), decisions=tuple(decisions), settlement=settlement()
        ),
        preparation_compute_seconds=0.125,
        post_terminal_compute_seconds=0.0625,
    )


class CanonicalFormTests(unittest.TestCase):
    def test_rows_are_lf_terminated_sorted_and_compact(self) -> None:
        content = complete_trace()
        self.assertTrue(content.endswith(b"\n"))
        self.assertNotIn(b"\r", content)
        self.assertFalse(content.startswith(b"\xef\xbb\xbf"))
        for raw in content.split(b"\n")[:-1]:
            text = raw.decode("utf-8")
            self.assertNotIn(", ", text)
            self.assertNotIn(": ", text)
            keys = list(json.loads(text))
            self.assertEqual(keys, sorted(keys))

    def test_canonical_json_refuses_non_finite_numbers(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                canonical_json({"value": value})

    def test_authorized_mode_is_refused(self) -> None:
        with self.assertRaises(TraceInvalidError):
            builder(mode="authorized")
        with self.assertRaises(TraceInvalidError):
            builder(mode="production")

    def test_record_indices_are_contiguous_from_the_header(self) -> None:
        content = complete_trace()
        rows = [json.loads(raw) for raw in content.split(b"\n")[:-1]]
        self.assertEqual([row["record_index"] for row in rows], list(range(len(rows))))
        self.assertEqual(rows[0]["record_type"], "header")
        self.assertEqual(rows[-1]["record_type"], "terminal")
        for row in rows:
            self.assertEqual(row["schema_version"], TRACE_SCHEMA_VERSION)


class RoundTripTests(unittest.TestCase):
    def test_complete_trace_parses_and_rebinds_its_digests(self) -> None:
        content = complete_trace()
        parsed = parse_trace(content)
        self.assertEqual(parsed.run_id, "run-1")
        self.assertEqual(len(parsed.events), 1)
        self.assertEqual(len(parsed.decisions), 1)
        self.assertTrue(parsed.terminal["complete"])
        self.assertEqual(
            parsed.terminal["semantic_sha256"], parsed_semantic_sha256(parsed)
        )

    def test_decoded_arrays_are_immutable_tuples(self) -> None:
        parsed = parse_trace(complete_trace())
        self.assertIsInstance(parsed.events[0]["starting_stacks"], tuple)
        self.assertIsInstance(parsed.terminal["settlement"]["payouts"], tuple)
        self.assertIsInstance(parsed.terminal["settlement"]["pots"][0]["seats"], tuple)

    def test_distinct_run_ids_share_identical_semantic_bytes(self) -> None:
        first = parse_trace(complete_trace("run-1"))
        second = parse_trace(complete_trace("run-2"))
        self.assertNotEqual(first.run_id, second.run_id)
        self.assertNotEqual(complete_trace("run-1"), complete_trace("run-2"))
        self.assertEqual(
            first.terminal["semantic_sha256"], second.terminal["semantic_sha256"]
        )
        self.assertEqual(parsed_semantic_sha256(first), parsed_semantic_sha256(second))

    def test_timing_never_enters_the_semantic_projection(self) -> None:
        fast = decision(timing=completed_timing(start=1_000, elapsed=5_000))
        slow = decision(timing=completed_timing(start=9_999, elapsed=13_000_000_000))
        self.assertEqual(
            semantic_sha256(events=(started(),), decisions=(fast,), settlement=settlement()),
            semantic_sha256(events=(started(),), decisions=(slow,), settlement=settlement()),
        )

    def test_semantic_digest_changes_with_a_different_action(self) -> None:
        other = DecisionRecord(
            **{
                **{
                    field: getattr(decision(), field)
                    for field in DecisionRecord.__dataclass_fields__
                },
                "selected_action": HandAction(kind="raise", raise_to=6),
                "selection_reason": SelectionReason.TABLE_HIT,
            }
        )
        self.assertNotEqual(
            semantic_sha256(
                events=(started(),), decisions=(decision(),), settlement=settlement()
            ),
            semantic_sha256(events=(started(),), decisions=(other,), settlement=settlement()),
        )

    def test_all_event_kinds_round_trip(self) -> None:
        events = (
            started(),
            OpponentActionEvent(
                hand_id=HAND,
                event_index=1,
                street="preflop",
                seat=4,
                action=HandAction(kind="raise", raise_to=6),
            ),
            StreetRevealedEvent(
                hand_id=HAND, event_index=2, street="flop", cards=(20, 21, 22)
            ),
            ShowdownResultEvent(
                hand_id=HAND,
                event_index=3,
                strengths=(None, (5, 1), 9, None, None, None),
            ),
        )
        parsed = parse_trace(complete_trace(events=events))
        self.assertEqual(len(parsed.events), 4)
        self.assertEqual(parsed.events[1]["action"]["raise_to"], 6)
        self.assertEqual(parsed.events[3]["strengths"][1], (5, 1))
        self.assertEqual(
            parsed.terminal["semantic_sha256"], parsed_semantic_sha256(parsed)
        )


class StrictRejectionTests(unittest.TestCase):
    def mutate(self, content: bytes, index: int, change, *, rebind: bool = True) -> bytes:
        """Mutate one row; by default rebind the terminal's prefix digest.

        Without rebinding, every change to a non-terminal row is caught by the
        prefix digest before the rule under test runs — so each rule would be
        tested only by accident. Rebinding isolates the rule; the prefix digest
        has its own dedicated test below.
        """

        rows = [json.loads(raw) for raw in content.split(b"\n")[:-1]]
        change(rows[index])
        encoded = [(canonical_json(row) + "\n").encode("utf-8") for row in rows]
        if rebind and index != len(rows) - 1:
            rows[-1]["trace_prefix_sha256"] = sha256(b"".join(encoded[:-1])).hexdigest()
            encoded[-1] = (canonical_json(rows[-1]) + "\n").encode("utf-8")
        return b"".join(encoded)

    def test_the_mutation_helper_produces_an_otherwise_valid_trace(self) -> None:
        """The helper itself must not smuggle in a second violation."""

        parse_trace(self.mutate(complete_trace(), 2, lambda row: row.update(seat=4)))

    def test_rejects_a_duplicate_json_key(self) -> None:
        content = complete_trace()
        rows = content.split(b"\n")[:-1]
        # Duplicate inside the terminal row, which no prefix digest covers, so
        # only the duplicate-key rule can reject this trace.
        opening = b'{"accounting_complete":true,'
        doubled = rows[-1].replace(opening, opening + b'"accounting_complete":true,', 1)
        self.assertNotEqual(doubled, rows[-1])
        broken = b"\n".join([*rows[:-1], doubled]) + b"\n"
        with self.assertRaises(TraceInvalidError):
            parse_trace(broken)

    def test_rejects_unknown_and_missing_keys(self) -> None:
        with self.assertRaises(TraceInvalidError):
            parse_trace(self.mutate(complete_trace(), 0, lambda row: row.update(extra=1)))
        with self.assertRaises(TraceInvalidError):
            parse_trace(self.mutate(complete_trace(), 0, lambda row: row.pop("clock_kind")))

    def test_rejects_wrong_exact_types(self) -> None:
        cases = [
            (2, lambda row: row.update(action_index=True)),
            (2, lambda row: row.update(action_index="1")),
            (3, lambda row: row.update(complete="true")),
            (3, lambda row: row.update(event_count=1.0)),
        ]
        for index, change in cases:
            with self.subTest(index=index):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.mutate(complete_trace(), index, change))

    def test_rejects_bad_digests_and_enums(self) -> None:
        cases = [
            (2, lambda row: row.update(state_before_sha256="XYZ")),
            (2, lambda row: row.update(state_before_sha256="A" * 64)),
            (2, lambda row: row.update(selection_reason="guessed")),
            (0, lambda row: row.update(clock_kind="wall_clock")),
            (0, lambda row: row.update(mode="authorized")),
        ]
        for index, change in cases:
            with self.subTest(index=index):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.mutate(complete_trace(), index, change))

    def test_rejects_discontinuous_or_foreign_rows(self) -> None:
        cases = [
            (2, lambda row: row.update(record_index=99)),
            (2, lambda row: row.update(run_id="other-run")),
            (2, lambda row: row.update(schema_version="pontius-v0a-trace-v2")),
            (2, lambda row: row.update(hand_id="hand-Z")),
        ]
        for index, change in cases:
            with self.subTest(index=index):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.mutate(complete_trace(), index, change))

    def test_rejects_truncated_missing_and_duplicated_terminals(self) -> None:
        content = complete_trace()
        rows = content.split(b"\n")[:-1]
        with self.assertRaises(TraceInvalidError):
            parse_trace(b"\n".join(rows[:-1]) + b"\n")
        with self.assertRaises(TraceInvalidError):
            parse_trace(b"\n".join([*rows, rows[-1]]) + b"\n")
        with self.assertRaises(TraceInvalidError):
            parse_trace(content[:-1])
        with self.assertRaises(TraceInvalidError):
            parse_trace(content.replace(b"\n", b"\r\n"))

    def test_rejects_a_tampered_prefix_or_semantic_digest(self) -> None:
        content = complete_trace()
        # No rebinding here: this is the prefix digest's own test.
        tampered = self.mutate(content, 2, lambda row: row.update(seat=4), rebind=False)
        with self.assertRaises(TraceInvalidError):
            parse_trace(tampered)
        semantic = self.mutate(content, 3, lambda row: row.update(semantic_sha256=DIGEST_C))
        parsed = parse_trace(semantic)
        self.assertNotEqual(parsed.terminal["semantic_sha256"], parsed_semantic_sha256(parsed))

    def test_rejects_a_counted_terminal_that_disagrees(self) -> None:
        with self.assertRaises(TraceInvalidError):
            parse_trace(self.mutate(complete_trace(), 3, lambda row: row.update(event_count=9)))

    def test_rejects_success_without_complete_accounting(self) -> None:
        with self.assertRaises(TraceInvalidError):
            parse_trace(
                self.mutate(complete_trace(), 3, lambda row: row.update(accounting_complete=False))
            )

    def test_rejects_interrupted_timing_that_claims_a_false_flag(self) -> None:
        trace = builder()
        trace.add_event(started())
        trace.add_decision(decision(timing=interrupted_timing()))
        content = trace.close(
            hand_id=HAND, complete=False, passed=False,
            failure_reason=FailureCode.CLOCK_INVALID, event_count=1, decision_count=1,
            interrupted_response_count=1, accounting_complete=False, settlement=None,
            semantic_digest=DIGEST_A, preparation_compute_seconds=None,
            post_terminal_compute_seconds=None,
        )
        parse_trace(content)
        rows = [json.loads(raw) for raw in content.split(b"\n")[:-1]]
        rows[2]["timing"]["deadline_crossed"] = False
        broken = b"".join((canonical_json(row) + "\n").encode("utf-8") for row in rows)
        with self.assertRaises(TraceInvalidError):
            parse_trace(broken)

    def test_rejects_a_delivered_action_without_acceptance(self) -> None:
        trace = builder()
        trace.add_event(started())
        record = FailureRecord(
            hand_id=HAND,
            event_index=0,
            action_index=1,
            code=FailureCode.DELIVERY_REJECTED,
            delivery_status=DeliveryStatus.REJECTED,
            delivered_action=None,
            timing=interrupted_timing(FailureCode.DELIVERY_REJECTED),
        )
        trace.add_failure(record)
        content = trace.close(
            hand_id=HAND, complete=False, passed=False,
            failure_reason=FailureCode.DELIVERY_REJECTED, event_count=1, decision_count=0,
            interrupted_response_count=1, accounting_complete=False, settlement=None,
            semantic_digest=DIGEST_A, preparation_compute_seconds=None,
            post_terminal_compute_seconds=None,
        )
        parse_trace(content)
        rows = [json.loads(raw) for raw in content.split(b"\n")[:-1]]
        rows[2]["delivered_action"] = {"kind": "call", "raise_to": None}
        broken = b"".join((canonical_json(row) + "\n").encode("utf-8") for row in rows)
        with self.assertRaises(TraceInvalidError):
            parse_trace(broken)


class TraceWriteTests(unittest.TestCase):
    def test_create_new_write_then_refuse_overwrite(self) -> None:
        content = complete_trace()
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            target = root / "run" / "trace.jsonl"
            target.parent.mkdir()
            digest = write_trace(content, target, run_root=root)
            self.assertEqual(digest, sha256(content).hexdigest())
            self.assertEqual(target.read_bytes(), content)
            with self.assertRaises(TraceWriteError):
                write_trace(content, target, run_root=root)

    def test_refuses_paths_outside_the_run_root(self) -> None:
        content = complete_trace()
        with tempfile.TemporaryDirectory() as enclosing:
            # The escape target lives inside the enclosing temp directory but
            # outside the run root, so a successful escape is observable here
            # and never leaks into a shared temp directory.
            outer = Path(enclosing)
            root = outer / "root"
            root.mkdir()
            escaped = outer / "escape.jsonl"
            for destination in (Path("..") / "escape.jsonl", escaped):
                with self.subTest(destination=str(destination)):
                    with self.assertRaises(TraceWriteError):
                        write_trace(content, destination, run_root=root)
                    self.assertFalse(escaped.exists(), "the escape wrote outside the run root")
            self.assertEqual(list(root.iterdir()), [])

    def test_refuses_an_absent_destination_directory(self) -> None:
        content = complete_trace()
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            with self.assertRaises(TraceWriteError):
                write_trace(content, root / "missing" / "trace.jsonl", run_root=root)


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
