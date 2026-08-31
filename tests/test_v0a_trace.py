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
        response_compute_seconds=(elapsed // 2) / 1_000_000_000,
        response_uninstrumented_seconds=(elapsed - elapsed // 2) / 1_000_000_000,
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
        failure_reason=(timing.interruption_reason
                        if timing is not None and timing.status is TimingStatus.INTERRUPTED else None),
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
                strengths=(None, (5, 1), (4, 9), None, None, None),
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
        if rebind and index != len(rows) - 1:
            return TraceSchemaRegressionTests.encode(rows)
        return b"".join((canonical_json(row) + "\n").encode("utf-8") for row in rows)

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
        with self.assertRaises(TraceInvalidError):
            parse_trace(semantic)

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
        trace.add_failure(FailureRecord(hand_id=HAND, event_index=0, action_index=1,
            code=FailureCode.CLOCK_INVALID, delivery_status=DeliveryStatus.ACCEPTED,
            delivered_action=HandAction("call", None), timing=interrupted_timing()))
        content = trace.close(
            hand_id=HAND, complete=False, passed=False,
            failure_reason=FailureCode.CLOCK_INVALID, event_count=1, decision_count=1,
            interrupted_response_count=1, accounting_complete=False, settlement=None,
            semantic_digest=semantic_sha256(events=(started(),),
                decisions=(decision(timing=interrupted_timing()),), settlement=None),
            preparation_compute_seconds=None,
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
            semantic_digest=semantic_sha256(events=(started(),), decisions=(), settlement=None),
            preparation_compute_seconds=None,
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



class TraceSchemaRegressionTests(unittest.TestCase):
    """Real trace field controls; hashes are rebound independently of production."""

    def real_trace(self):
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost
        ticks = iter(range(1000, 10000000, 1000))
        return ReplayHost(
            FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-schema",
            blueprint=ImmutableBlueprintActionSource("schema-policy"),
            clock=lambda: next(ticks),
        ).run().trace

    @staticmethod
    def encode(rows, *, rebind=True):
        projection_keys = (
            "hand_id", "event_index", "action_index", "street_action_index", "seat", "street",
            "state_before_sha256", "state_after_sha256", "visible_cards_sha256",
            "blueprint_sha256", "selected_action", "selection_reason", "spine_reason",
            "preparation_use",
        )
        dumps = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
        if rebind:
            payload = {
                "events": [row["event"] for row in rows if row["record_type"] == "event"],
                "decisions": [{key: row[key] for key in projection_keys}
                              for row in rows if row["record_type"] == "decision"],
                "settlement": rows[-1]["settlement"],
            }
            rows[-1]["semantic_sha256"] = sha256(dumps(payload).encode("utf-8")).hexdigest()
            prefix = "".join(dumps(row) + "\n" for row in rows[:-1]).encode("utf-8")
            rows[-1]["trace_prefix_sha256"] = sha256(prefix).hexdigest()
        return "".join(dumps(row) + "\n" for row in rows).encode("utf-8")

    def failed_trace(self, *, interrupted=False):
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.model import ActionMailbox
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost
        state = dict(now=1000, interrupt=False)
        real = ActionMailbox()
        def clock():
            if state["interrupt"]:
                state["interrupt"] = False
                return True
            state["now"] += 1000
            return state["now"]
        class Mailbox:
            def deliver(self, envelope):
                receipt = real.deliver(envelope)
                if interrupted:
                    state["interrupt"] = True
                else:
                    state["now"] += 16_000_000_000
                return receipt
        return ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-schema-failure",
                    blueprint=ImmutableBlueprintActionSource("schema-policy"),
                    clock=clock, mailbox=Mailbox()).run().trace

    def test_failure_fields_and_accepted_delivery_pairs_are_exact(self):
        content = self.failed_trace()
        parsed = parse_trace(content)
        self.assertEqual(parsed.terminal["decision_count"], 1)
        self.assertEqual(parsed.events, ())  # failed triggering event is absent
        mutations = (
            ("hand-id", lambda rows: rows[1].update(hand_id=[])),
            ("event-index", lambda rows: rows[1].update(event_index=False)),
            ("action-index", lambda rows: rows[1].update(action_index=False)),
            ("code", lambda rows: rows[1].update(code="clock_invalid")),
            ("completed-clock-code", lambda rows: (rows[1].update(code="clock_invalid"),
                rows[2].update(failure_reason="clock_invalid"))),
            ("delivery-action", lambda rows: rows[1].update(delivered_action=None)),
            ("delivery-kind", lambda rows: rows[1]["delivered_action"].update(kind="fold")),
            ("unknown-delivery", lambda rows: rows[1].update(delivery_status="unknown",
                                                            delivered_action=None)),
            ("timing", lambda rows: rows[1].update(timing=None)),
            ("no-failure-pair", lambda rows: rows.pop(1)),
            ("duplicate-failure-pair", lambda rows: rows.insert(1, dict(rows[1]))),
            ("false-count", lambda rows: rows[-1].update(decision_count=0)),
        )
        for label, change in mutations:
            rows = [json.loads(row) for row in content.splitlines()]
            change(rows)
            for index, row in enumerate(rows):
                row["record_index"] = index
            with self.subTest(label=label):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.encode(rows))
        for path in ((1,), (1, "timing"), (1, "delivered_action")):
            for mutation in ("missing", "unknown"):
                rows = [json.loads(row) for row in content.splitlines()]
                target = rows
                for part in path:
                    target = target[part]
                if mutation == "missing":
                    target.pop(next(iter(target)))
                else:
                    target["not_in_schema"] = 0
                with self.subTest(path=path, mutation=mutation):
                    with self.assertRaises(TraceInvalidError):
                        parse_trace(self.encode(rows))
        interrupted = parse_trace(self.failed_trace(interrupted=True))
        self.assertEqual(interrupted.terminal["decision_count"], 1)
        self.assertEqual(interrupted.terminal["interrupted_response_count"], 1)
        self.assertEqual(interrupted.decisions[0]["timing"]["status"], "interrupted")

    def test_exact_fields_and_nested_event_variants_are_checked(self):
        original = self.real_trace()
        cases = (
            ("record-bool", lambda rows: rows[0].update(record_index=False)),
            ("source-list", lambda rows: rows[0].update(source_commit=[])),
            ("event-extra", lambda rows: rows[1]["event"].update(timestamp=123)),
            ("event-missing", lambda rows: rows[1]["event"].pop("button")),
            ("event-index-bool", lambda rows: rows[1]["event"].update(event_index=False)),
            ("decision-seat", lambda rows: rows[2].update(seat=6)),
            ("decision-reason", lambda rows: rows[2].update(spine_reason="invented")),
            ("decision-hand-id", lambda rows: rows[2].update(hand_id=[])),
            ("decision-null-timing", lambda rows: rows[2].update(timing=None)),
            ("decision-nan", lambda rows: rows[2]["timing"].update(
                response_compute_seconds=float("nan"))),
            ("terminal-inf", lambda rows: rows[-1].update(
                post_terminal_compute_seconds=float("inf"))),
            ("terminal-count", lambda rows: rows[-1].update(decision_count=0)),
        )
        for label, change in cases:
            with self.subTest(label=label):
                rows = [json.loads(row) for row in original.splitlines()]
                change(rows)
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.encode(rows))

    def test_every_nested_variant_rejects_missing_unknown_and_wrong_leaf_values(self):
        source = [json.loads(row) for row in self.real_trace().splitlines()]
        paths = [(0,), (2,), (-1,), (2, "selected_action"), (2, "timing"),
                 (2, "preparation_use"), (-1, "settlement"),
                 (-1, "settlement", "pots", 0)]
        for index, row in enumerate(source):
            if row["record_type"] == "event":
                paths.append((index, "event"))
                if row["event"]["kind"] == "opponent_action":
                    paths.append((index, "event", "action"))
        for path in paths:
            for mutation in ("missing", "unknown"):
                rows = [json.loads(row) for row in self.real_trace().splitlines()]
                target = rows
                for part in path:
                    target = target[part]
                if mutation == "missing":
                    # Keep projection fields available to the independent
                    # rebinder; missing inner fields have their own cases.
                    key = next(iter(target))
                    if path in ((2,), (-1,)):
                        key = "timing" if path == (2,) else "complete"
                    target.pop(key)
                else:
                    target["not_in_schema"] = 0
                with self.subTest(path=path, mutation=mutation):
                    with self.assertRaises(TraceInvalidError):
                        parse_trace(self.encode(rows))
        mutations = (
            ("card-bool", lambda rows: rows[1]["event"].update(private_cards=[False, 13])),
            ("card-range", lambda rows: rows[1]["event"].update(private_cards=[0, 52])),
            ("stack-bool", lambda rows: rows[1]["event"]["starting_stacks"].__setitem__(0, True)),
            ("pot-seat-bool", lambda rows: rows[-1]["settlement"]["pots"][0].update(seats=[True])),
            ("pot-seat-range", lambda rows: rows[-1]["settlement"]["pots"][0].update(seats=[6])),
            ("pot-seat-object", lambda rows: rows[-1]["settlement"]["pots"][0].update(seats=[{}])),
            ("rank-bool", lambda rows: rows[-2]["event"]["strengths"].__setitem__(0, True)),
            ("rank-mixed", lambda rows: rows[-2]["event"]["strengths"].__setitem__(0, 1)),
            ("rank-empty", lambda rows: rows[-2]["event"]["strengths"].__setitem__(0, [])),
            ("reveal-width", lambda rows: next(row["event"] for row in rows
                if row["record_type"] == "event" and row["event"]["kind"] == "street_revealed").update(cards=[1])),
        )
        for label, change in mutations:
            rows = [json.loads(row) for row in self.real_trace().splitlines()]
            change(rows)
            with self.subTest(label=label):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.encode(rows))

    def test_float_overflow_and_noncanonical_number_spellings_are_rejected(self):
        content = self.real_trace()
        for token in (b"1e999", b"NaN", b"Infinity", b"-Infinity", b"0e0"):
            rows = [json.loads(row) for row in content.splitlines()]
            rows[-1]["preparation_compute_seconds"] = 0.0
            broken = self.encode(rows).replace(b'"preparation_compute_seconds":0.0',
                                               b'"preparation_compute_seconds":' + token)
            with self.subTest(token=token):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(broken)

    def test_structural_integer_strengths_keep_the_models_unbounded_ordering_domain(self):
        for strengths in ((None, -2, -1, None, None, None),
                          (None, (-2, 4), (-1, 3), None, None, None)):
            event = ShowdownResultEvent(hand_id=HAND, event_index=1, strengths=strengths)
            parsed = parse_trace(complete_trace(events=(started(), event)))
            self.assertEqual(parsed.events[-1]["strengths"], strengths)

    def test_deep_malformed_input_has_a_typed_refusal(self):
        content = self.real_trace()
        nested = b"[" * 700 + b"0" + b"]" * 700
        broken = content.replace(b'{"blueprint_sha256":', b'{"extra":' + nested
                                 + b',"blueprint_sha256":', 1)
        with self.assertRaises(TraceInvalidError):
            parse_trace(broken)

    def test_semantic_mismatch_and_noncanonical_json_are_refused(self):
        content = self.real_trace()
        rows = [json.loads(row) for row in content.splitlines()]
        rows[-1]["semantic_sha256"] = "f" * 64
        with self.assertRaises(TraceInvalidError):
            parse_trace(self.encode(rows, rebind=False))
        with self.assertRaises(TraceInvalidError):
            parse_trace(b"\n".join(json.dumps(row).encode() for row in
                                  [json.loads(raw) for raw in content.splitlines()]) + b"\n")

    def test_successive_response_intervals_cannot_reverse_the_clock(self):
        rows = [json.loads(row) for row in self.real_trace().splitlines()]
        decisions = [row for row in rows if row["record_type"] == "decision"]
        first, second = decisions[0]["timing"], decisions[1]["timing"]
        start = first["wall_start_ns"] + 1
        second.update(wall_start_ns=start,
                      last_valid_observation_ns=start + second["elapsed_ns"],
                      emission_observed_ns=start + second["elapsed_ns"])
        with self.assertRaises(TraceInvalidError):
            parse_trace(self.encode(rows))

    def test_completed_timing_cannot_hide_deadline_or_impossible_accounting(self):
        original = self.real_trace()
        for elapsed, compute, flag in ((16_000_000_000, 16.0, False), (10_000, 2.0, False)):
            rows = [json.loads(row) for row in original.splitlines()]
            timing = rows[2]["timing"]
            timing.update(elapsed_ns=elapsed, emission_observed_ns=timing["wall_start_ns"] + elapsed,
                          last_valid_observation_ns=timing["wall_start_ns"] + elapsed,
                          response_compute_seconds=compute, response_uninstrumented_seconds=0.0,
                          deadline_crossed=flag)
            with self.subTest(elapsed=elapsed):
                with self.assertRaises(TraceInvalidError):
                    parse_trace(self.encode(rows))


class ObservedTerminalClock:
    """Fault the real witness source at observed reads, without replacing its owner."""

    def __init__(self, *, fail_at=None, fault="invalid"):
        self.now = 10_000
        self.calls = 0
        self.fail_at = fail_at
        self.fault = fault
        self.armed = False

    def __call__(self):
        self.calls += 1
        if self.armed or self.calls == self.fail_at:
            if self.fault == "reversed":
                return self.now - 1 if self.calls > 1 else -1
            if self.fault == "exception":
                raise RuntimeError("clock source failed")
            return True
        self.now += 1_000
        return self.now


class TerminalAdmissionTests(unittest.TestCase):
    """All-outcome implications through real hosts; neither digest uses the reader."""

    encode = staticmethod(TraceSchemaRegressionTests.encode)

    @staticmethod
    def host_case(kind="success", *, source=None, fixture=None):
        from dataclasses import replace
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.model import ActionMailbox
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost, ScriptedAction

        source = ObservedTerminalClock() if source is None else source
        real = ActionMailbox()
        fixture = FIXTURE_A if fixture is None else fixture
        if kind == "event_order":
            fixture = replace(fixture, script=(ScriptedAction("preflop", 3, "call"),)
                              + fixture.script[1:])
        class Mailbox:
            def deliver(self, envelope):
                if kind == "rejected":
                    # Exact ingress refusal inside the real mailbox; no action accepted.
                    return real.deliver(None)
                receipt = real.deliver(envelope)
                if kind == "interrupted":
                    source.armed = True
                elif kind == "unknown":
                    raise RuntimeError("accepted by real mailbox, acknowledgement lost")
                elif kind == "late":
                    source.now += 16_000_000_000
                return receipt

        class InvalidInputHost(ReplayHost):
            def _events(self):
                # Feed malformed external input through the real runtime dispatch path.
                yield {"kind": "hand_started"}

        def broken_oracle(**kwargs):
            raise ValueError("settlement body failure")

        options = {"settlement_oracle": broken_oracle} if kind == "settlement" else {}
        host_type = InvalidInputHost if kind == "invalid_event" else ReplayHost
        host = host_type(fixture, run_id=PROTOCOL_ID + "-correctness-terminal-" + kind,
                         blueprint=ImmutableBlueprintActionSource("terminal-policy"),
                         clock=source, mailbox=Mailbox(), **options)
        # Fail at the real dispatch boundary. Host header work now has its own
        # required entry, so source read one no longer means runtime no-start.
        from pontius.v0a.runtime import HandRuntime
        previous = sys.getprofile()
        def observe(frame, event, arg):
            if event == "call" and frame.f_code is HandRuntime.dispatch.__code__:
                source.armed = True
        try:
            if kind == "no_start":
                sys.setprofile(observe)
            outcome = host.run()
        finally:
            if kind == "no_start":
                sys.setprofile(previous)
        return outcome, real, source

    def test_real_outcome_controls_preserve_delivery_timing_and_terminal_fields(self):
        cases = (
            ("success", None, None, None, 4),
            ("late", "action_deadline_exceeded", "accepted", "completed", 1),
            ("interrupted", "clock_invalid", "accepted", "interrupted", 1),
            ("unknown", "delivery_ambiguous", "unknown", "interrupted", 1),
            ("rejected", "delivery_rejected", "rejected", "interrupted", 0),
            ("no_start", "clock_invalid", "not_attempted", None, 0),
            ("event_order", "event_order", "not_attempted", None, 1),
            ("invalid_event", "invalid_event", "not_attempted", None, 0),
            ("settlement", "settlement_mismatch", None, None, 4),
        )
        for kind, reason, delivery, timing, accepted in cases:
            with self.subTest(kind=kind):
                outcome, mailbox, _ = self.host_case(kind)
                parsed = parse_trace(outcome.trace)
                self.assertEqual(parsed.terminal["failure_reason"], reason)
                self.assertEqual(len(mailbox.accepted), accepted)
                self.assertEqual(parsed.terminal["passed"], kind == "success")
                if delivery is None:
                    self.assertEqual(parsed.failures, ())
                else:
                    failure = parsed.failures[0]
                    self.assertEqual(failure["delivery_status"], delivery)
                    self.assertEqual(None if failure["timing"] is None else
                                     failure["timing"]["status"], timing)
                if kind == "unknown":
                    self.assertEqual(parsed.decisions, ())
                    self.assertIsNone(parsed.failures[0]["delivered_action"])
                if kind != "success":
                    self.assertIsNone(parsed.terminal["settlement"])

    def test_all_flag_combinations_for_real_outcome_variants(self):
        from itertools import product

        # Tuples are (complete, passed, accounting_complete). For a noninterrupted
        # failure these fields cannot reconstruct missing lifecycle chronology.
        failed_allowed = {(False, False, False), (False, False, True),
                          (True, False, False), (True, False, True)}
        cases = (
            ("success", {(True, True, True)}),
            ("late", failed_allowed), ("event_order", failed_allowed),
            ("invalid_event", failed_allowed), ("no_start", failed_allowed),
            ("settlement", failed_allowed),
            ("interrupted", {(False, False, False)}),
            ("unknown", {(False, False, False)}),
            ("rejected", {(False, False, False)}),
        )
        for kind, allowed in cases:
            content = self.host_case(kind)[0].trace
            parse_trace(content)
            for flags in product((False, True), repeat=3):
                rows = [json.loads(raw) for raw in content.splitlines()]
                rows[-1].update(zip(("complete", "passed", "accounting_complete"), flags))
                # Finite totals make this a flag implication check, independent of
                # the separate category-availability controls below.
                rows[-1].update(preparation_compute_seconds=0.0,
                                post_terminal_compute_seconds=0.0)
                with self.subTest(kind=kind, flags=flags):
                    if flags in allowed:
                        self.assertEqual(parse_trace(self.encode(rows)).terminal["passed"],
                                         flags[1])
                    else:
                        with self.assertRaises(TraceInvalidError):
                            parse_trace(self.encode(rows))

    def test_failed_settlement_and_erased_or_replaced_primary_are_refused(self):
        settlement_value = json.loads(self.host_case()[0].trace.splitlines()[-1])["settlement"]
        for kind in ("late", "interrupted", "unknown", "rejected", "no_start",
                     "event_order", "invalid_event", "settlement"):
            content = self.host_case(kind)[0].trace
            for mutation in ("settlement", "erased", "replaced"):
                rows = [json.loads(raw) for raw in content.splitlines()]
                if mutation == "settlement":
                    rows[-1]["settlement"] = settlement_value
                else:
                    rows[-1]["failure_reason"] = (None if mutation == "erased"
                                                   else "source_binding_mismatch")
                with self.subTest(kind=kind, mutation=mutation):
                    if kind == "settlement" and mutation == "replaced":
                        # A terminal-only cause has no row that establishes another cause.
                        parse_trace(self.encode(rows))
                    else:
                        with self.assertRaises(TraceInvalidError):
                            parse_trace(self.encode(rows))

    def test_accounting_complete_requires_both_category_totals_on_failed_hands(self):
        for kind in ("late", "event_order", "invalid_event", "settlement", "no_start"):
            content = self.host_case(kind)[0].trace
            for prep, post in ((None, None), (None, 0.0), (0.0, None), (0.0, 0.0)):
                rows = [json.loads(raw) for raw in content.splitlines()]
                rows[-1].update(accounting_complete=True, preparation_compute_seconds=prep,
                                post_terminal_compute_seconds=post)
                with self.subTest(kind=kind, prep=prep, post=post):
                    if prep is not None and post is not None:
                        parse_trace(self.encode(rows))
                    else:
                        with self.assertRaises(TraceInvalidError):
                            parse_trace(self.encode(rows))
                # Aggregate incompleteness does not erase a completed category.
                rows[-1]["accounting_complete"] = False
                parsed = parse_trace(self.encode(rows))
                self.assertEqual(parsed.terminal["preparation_compute_seconds"], prep)
                self.assertEqual(parsed.terminal["post_terminal_compute_seconds"], post)

    def test_unknown_delivery_forces_flags_even_without_a_started_timing_record(self):
        content = self.host_case("no_start")[0].trace
        for complete, accounting in ((False, False), (True, False), (False, True), (True, True)):
            rows = [json.loads(raw) for raw in content.splitlines()]
            rows[1].update(code="delivery_ambiguous", delivery_status="unknown")
            rows[-1].update(failure_reason="delivery_ambiguous", complete=complete,
                            accounting_complete=accounting, preparation_compute_seconds=0.0,
                            post_terminal_compute_seconds=0.0)
            with self.subTest(complete=complete, accounting=accounting):
                if complete or accounting:
                    with self.assertRaises(TraceInvalidError):
                        parse_trace(self.encode(rows))
                else:
                    parsed = parse_trace(self.encode(rows))
                    self.assertEqual(parsed.terminal["interrupted_response_count"], 0)

    def test_source_cause_survives_later_real_adapter_outcomes(self):
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.clock import ClockInvalidError, ClockReversedError, MonotonicWitness
        from pontius.v0a.model import ActionMailbox
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost

        for fault in ("invalid", "reversed"):
            for finish in ("acknowledge", "raise", "reject"):
                source = ObservedTerminalClock(fault=fault)
                witness = MonotonicWitness(source)
                real = ActionMailbox()

                class Mailbox:
                    def deliver(self, envelope):
                        receipt = real.deliver(envelope) if finish != "reject" else None
                        source.armed = True
                        try:
                            witness()
                        except (ClockInvalidError, ClockReversedError):
                            pass
                        if finish == "raise":
                            raise RuntimeError("adapter body after source failure")
                        if finish == "reject":
                            return real.deliver(None)
                        return receipt

                host = ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-source-"
                                  + fault + "-" + finish,
                                  blueprint=ImmutableBlueprintActionSource("terminal-policy"),
                                  clock=witness, mailbox=Mailbox())
                outcome = host.run()
                with self.subTest(fault=fault, finish=finish):
                    parsed = parse_trace(outcome.trace)
                    self.assertEqual(parsed.terminal["failure_reason"], "clock_" + fault)
                    self.assertEqual(len(real.accepted), 0 if finish == "reject" else 1)
                    expected = {"acknowledge": ("clock_invalid", "accepted"),
                                "raise": ("delivery_ambiguous", "unknown"),
                                "reject": ("delivery_rejected", "rejected")}[finish]
                    self.assertEqual((parsed.failures[0]["code"],
                                      parsed.failures[0]["delivery_status"]), expected)
                    rows = [json.loads(raw) for raw in outcome.trace.splitlines()]
                    rows[-1]["failure_reason"] = "invalid_event"
                    with self.assertRaises(TraceInvalidError):
                        parse_trace(self.encode(rows))

    def test_prefailed_witness_and_opposing_host_only_source_body_causes(self):
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.clock import ClockInvalidError, ClockReversedError, MonotonicWitness
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost

        for fault in ("invalid", "reversed"):
            source = ObservedTerminalClock(fault=fault)
            witness = MonotonicWitness(source)
            witness()
            source.armed = True
            with self.assertRaises((ClockInvalidError, ClockReversedError)):
                witness()
            outcome = ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-prefailed-"
                                 + fault,
                                 blueprint=ImmutableBlueprintActionSource("terminal-policy"),
                                 clock=witness).run()
            parsed = parse_trace(outcome.trace)
            self.assertEqual(parsed.terminal["failure_reason"], "clock_" + fault)
            # Required host entry now refuses before acquiring input.
            self.assertEqual(parsed.failures, ())
            self.assertEqual(parsed.decisions, ())

            from pontius.v0a.runtime import HandRuntime
            source = ObservedTerminalClock(fault=fault)
            witness = MonotonicWitness(source)
            observed = []
            def prefailed_at_dispatch(frame, event, arg):
                if event == "call" and frame.f_code is HandRuntime.dispatch.__code__:
                    observed.append(1)
                    source.armed = True
                    with self.assertRaises((ClockInvalidError, ClockReversedError)):
                        witness()
            previous = sys.getprofile()
            try:
                sys.setprofile(prefailed_at_dispatch)
                outcome = ReplayHost(
                    FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-prefailed-dispatch-" + fault,
                    blueprint=ImmutableBlueprintActionSource("terminal-policy"),
                    clock=witness,
                ).run()
            finally:
                sys.setprofile(previous)
            parsed = parse_trace(outcome.trace)
            self.assertEqual(observed, [1])
            self.assertEqual(parsed.terminal["failure_reason"], "clock_" + fault)
            self.assertEqual(parsed.failures[0]["code"], "clock_invalid")
            self.assertIsNone(parsed.failures[0]["timing"])
            self.assertEqual(parsed.decisions, ())

        for source_first in (False, True):
            source = ObservedTerminalClock(fault="reversed")
            witness = MonotonicWitness(source)

            def oracle(**kwargs):
                source.armed = True
                if source_first:
                    with self.assertRaises(ClockReversedError):
                        witness()
                raise ValueError("independent settlement body failure")

            outcome = ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-body-"
                                 + str(source_first),
                                 blueprint=ImmutableBlueprintActionSource("terminal-policy"),
                                 clock=witness, settlement_oracle=oracle).run()
            parsed = parse_trace(outcome.trace)
            self.assertEqual(parsed.failures, ())
            self.assertEqual(parsed.terminal["failure_reason"],
                             "clock_reversed" if source_first else "settlement_mismatch")
            self.assertEqual(tuple(str(code) for code in outcome.receipt.secondary_failures),
                             ("settlement_mismatch" if source_first else "clock_reversed",))
            self.assertIsNone(parsed.terminal["settlement"])
            self.assertFalse(parsed.terminal["accounting_complete"])
            # Failed closing work stays unavailable; category completion is separate.
            self.assertIsNone(parsed.terminal["post_terminal_compute_seconds"])

    def test_every_observed_normal_and_rejected_input_clock_read_preserves_prefixes(self):
        counts = {}
        cleanup_primaries = 0
        for kind in ("success", "event_order"):
            _, _, baseline = self.host_case(kind)
            self.assertGreater(baseline.calls, 0)
            counts[kind] = baseline.calls
            for fault in ("invalid", "reversed", "exception"):
                for position in range(1, baseline.calls + 1):
                    source = ObservedTerminalClock(fail_at=position, fault=fault)
                    outcome, _, _ = self.host_case(kind, source=source)
                    with self.subTest(kind=kind, fault=fault, position=position):
                        self.assertEqual(source.calls, position)
                        self.assertFalse(outcome.receipt.passed)
                        parsed = parse_trace(outcome.trace)
                        if (parsed.failures and parsed.failures[0]["code"] == "event_order"
                                and outcome.receipt.secondary_failures):
                            cleanup_primaries += 1
                            self.assertEqual(parsed.terminal["failure_reason"], "event_order")
                            rows = [json.loads(raw) for raw in outcome.trace.splitlines()]
                            rows[-1]["failure_reason"] = "clock_invalid"
                            with self.assertRaises(TraceInvalidError):
                                parse_trace(self.encode(rows))
        self.assertGreater(cleanup_primaries, 0)
        print("terminal clock sweep", json.dumps({"observed_reads": counts,
              "fault_kinds": ["invalid", "reversed", "exception"],
              "preserved_input_primary_controls": cleanup_primaries}, sort_keys=True))

    def test_first_write_failure_keeps_accepted_prefix_inspectable(self):
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "already-present.jsonl"
            destination.write_bytes(b"preserve existing destination")
            host = ReplayHost(FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-write-failure",
                              blueprint=ImmutableBlueprintActionSource("terminal-policy"),
                              clock=ObservedTerminalClock())
            outcome = host.run(destination=destination, run_root=root)
            self.assertEqual(outcome.receipt.failure_reason, FailureCode.TRACE_WRITE_FAILED)
            self.assertFalse(outcome.receipt.passed)
            parsed = parse_trace(outcome.trace)
            self.assertEqual(parsed.failures, ())
            self.assertFalse(parsed.terminal["passed"])
            self.assertEqual(parsed.terminal["failure_reason"], "trace_write_failed")
            self.assertEqual(len(parsed.decisions), 1)
            self.assertIsNone(parsed.terminal["settlement"])
            self.assertEqual(destination.read_bytes(), b"preserve existing destination")

    def test_final_publication_clock_failure_does_not_rewrite_terminal_cut(self):
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.replay import FIXTURE_A, PROTOCOL_ID, ReplayHost
        from pontius.v0a.trace import TraceBuilder

        source = ObservedTerminalClock()
        observed = []
        def observe(frame, event, arg):
            if event == "return" and frame.f_code is TraceBuilder.close.__code__:
                observed.append(1)
                source.armed = True
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            outcome = ReplayHost(
                FIXTURE_A, run_id=PROTOCOL_ID + "-correctness-publication-close",
                blueprint=ImmutableBlueprintActionSource("terminal-policy"), clock=source,
            ).run()
        finally:
            sys.setprofile(previous)
        self.assertEqual(observed, [1])
        self.assertFalse(outcome.receipt.passed)
        self.assertEqual(outcome.receipt.failure_reason, FailureCode.CLOCK_INVALID)
        self.assertFalse(outcome.receipt.accounting_complete)
        parsed = parse_trace(outcome.trace)
        self.assertTrue(parsed.terminal["passed"])
        self.assertIsNone(parsed.terminal["failure_reason"])


class EventConstructorAdmissionTests(unittest.TestCase):
    """Wire-representable value domains, with legal replay intentionally separate."""

    encode = staticmethod(TraceSchemaRegressionTests.encode)

    @staticmethod
    def rows():
        return [json.loads(raw) for raw in TraceSchemaRegressionTests().real_trace().splitlines()]

    def assert_bad_event(self, kind, **updates):
        rows = self.rows()
        event = next(row["event"] for row in rows if row["record_type"] == "event"
                     and row["event"]["kind"] == kind)
        event.update(updates)
        with self.assertRaises(TraceInvalidError):
            parse_trace(self.encode(rows))

    def test_every_event_common_constructor_field_rejects_invalid_wire_values(self):
        for kind in ("hand_started", "opponent_action", "street_revealed", "showdown_result"):
            for key, values in (
                ("schema_version", (None, True, 1, [], {}, "foreign")),
                ("hand_id", (None, True, 1, [], {}, "", "non-ascii-\u00e9")),
                ("event_index", (None, True, -1, 0.5, [], {}, "0")),
            ):
                for value in values:
                    with self.subTest(kind=kind, key=key, value=value):
                        self.assert_bad_event(kind, **{key: value})

    def test_private_pair_order_and_all_starting_value_domains(self):
        cases = {
            "private_cards": ([45, 32], [32, 32], [False, 32], [-1, 32], [32, 52],
                              [32], [0, 1, 2], None, {}),
            "button": (True, -1, 6, "0", None),
            "controlled_seat": (False, -1, 6, "3", None),
            "starting_stacks": (None, {}, [200] * 5, [200] * 7, [True] * 6,
                                [0] * 6, [-1] * 6, [1] * 6, [200.0] * 6),
            "small_blind": (None, False, 0, -1, 2, 3, 1.0),
            "big_blind": (None, True, 0, -1, 1, 2.0),
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assert_bad_event("hand_started", **{field: value})
        rows = self.rows()
        rows[1]["event"].update(private_cards=[0, 51], starting_stacks=[2] * 6)
        parsed = parse_trace(self.encode(rows))
        self.assertEqual(parsed.events[0]["private_cards"], (0, 51))
        self.assertEqual(parsed.events[0]["starting_stacks"], (2,) * 6)

    def test_opponent_action_constructor_and_nested_action_domains(self):
        for key, values in (("street", (None, True, "bad", [], {})),
                            ("seat", (None, False, -1, 6, 1.0))):
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assert_bad_event("opponent_action", **{key: value})
        actions = [None, [], {}, {"kind": "fold"},
                   {"kind": "call", "raise_to": None, "extra": 0}]
        actions.extend({"kind": kind, "raise_to": None} for kind in (None, True, [], "bad"))
        actions.extend({"kind": "raise", "raise_to": value}
                       for value in (None, False, 0, -1, 1.0, [], "2"))
        actions.extend({"kind": kind, "raise_to": value}
                       for kind in ("fold", "check", "call") for value in (0, False, 1))
        for action in actions:
            with self.subTest(action=action):
                self.assert_bad_event("opponent_action", action=action)
        for kind, amount in (("fold", None), ("check", None), ("call", None), ("raise", 1)):
            rows = self.rows()
            next(row["event"] for row in rows if row["record_type"] == "event"
                 and row["event"]["kind"] == "opponent_action")["action"] = {
                     "kind": kind, "raise_to": amount}
            parse_trace(self.encode(rows))

    def test_reveal_domains_preserve_unsorted_board_order(self):
        for street in (None, True, "preflop", "bad", [], {}):
            with self.subTest(street=street):
                self.assert_bad_event("street_revealed", street=street)
        for street, good in (("flop", [51, 2, 0]), ("turn", [51]), ("river", [0])):
            bad = (None, {}, [], [True] * len(good), [-1] * len(good),
                   [52] * len(good), [1.0] * len(good), good + [3])
            if street == "flop":
                bad += ([0, 0, 1], [0])
            for cards in bad:
                with self.subTest(street=street, cards=cards):
                    self.assert_bad_event("street_revealed", street=street, cards=cards)
            rows = self.rows()
            event = next(row["event"] for row in rows if row["record_type"] == "event"
                         and row["event"]["kind"] == "street_revealed")
            event.update(street=street, cards=good)
            parsed = parse_trace(self.encode(rows))
            reveal = next(event for event in parsed.events if event["kind"] == "street_revealed")
            self.assertEqual(reveal["cards"], tuple(good))

    def test_showdown_constructor_domains_and_structural_comparability(self):
        values = (None, {}, [], [None] * 5, [None] * 7, [True] * 6,
                  [1.0] * 6, ["rank"] * 6, [[]] * 6, [[True]] * 6,
                  [[1.0]] * 6, [[{}]] * 6, [1, [1], None, None, None, None])
        for strengths in values:
            with self.subTest(strengths=strengths):
                self.assert_bad_event("showdown_result", strengths=strengths)
        for strengths in ([None] * 6, [-2, -1, 0, None, None, None],
                          [[-2], [-1, 3], [0], None, None, None]):
            rows = self.rows()
            rows[-2]["event"]["strengths"] = strengths
            parse_trace(self.encode(rows))



class StableTraceWriterTests(unittest.TestCase):
    def test_checked_parent_cannot_be_replaced_before_creation(self):
        import os
        import subprocess
        import pontius.v0a.trace as trace_module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent, outside = root / "parent", root / "outside"
            parent.mkdir()
            outside.mkdir()
            moved = root / "moved"
            target = parent / "trace.jsonl"
            attempts = []
            def observe(frame, event, arg):
                legacy = (event == "c_call" and arg is os.open
                          and frame.f_code is write_trace.__code__)
                native = (event == "call" and frame.f_code.co_name == "_open_native"
                          and frame.f_globals.get("__name__") == trace_module.__name__
                          and frame.f_locals.get("directory") is False)
                if attempts or not (legacy or native):
                    return
                attempts.append("attempted")
                try:
                    parent.rename(moved)
                except PermissionError:
                    attempts.append("denied")
                    return
                command = str(Path(os.environ["SYSTEMROOT"]) / "System32" / "cmd.exe")
                result = subprocess.run([command, "/c", "mklink", "/J", str(parent), str(outside)],
                                        capture_output=True, check=True)
                attempts.append("replaced")
            previous = sys.getprofile()
            sys.setprofile(observe)
            try:
                try:
                    digest = write_trace(b"one row\n", target, run_root=parent)
                except (TraceWriteError, OSError):
                    digest = None
            finally:
                sys.setprofile(previous)
                if attempts == ["attempted", "replaced"]:
                    # Remove only our junction, never recursively follow it.
                    os.rmdir(parent)
            self.assertTrue(attempts)
            self.assertFalse((outside / "trace.jsonl").exists())
            if digest is not None:
                self.assertEqual(digest, sha256(b"one row\n").hexdigest())
                self.assertEqual(target.read_bytes(), b"one row\n")



    def test_stream_pins_parent_and_file_until_successful_close(self):
        import pontius.v0a.trace as trace_module
        writer_type = getattr(trace_module, "TraceWriter", None)
        self.assertIsNotNone(writer_type, "publication needs an owned incremental stream")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "parent"
            parent.mkdir()
            target = parent / "trace.jsonl"
            writer = writer_type(target, run_root=root)
            try:
                writer.append(b"header\n")
                self.assertEqual(target.read_bytes(), b"header\n")
                with self.assertRaises(PermissionError):
                    parent.rename(root / "moved")
                with self.assertRaises(PermissionError):
                    target.rename(parent / "other.jsonl")
                with self.assertRaises(PermissionError):
                    with target.open("ab") as foreign:
                        foreign.write(b"foreign")
                writer.append(b"terminal\n")
                self.assertEqual(writer.finish(), sha256(b"header\nterminal\n").hexdigest())
                with self.assertRaises(TraceWriteError):
                    writer.append(b"late")
                with self.assertRaises(TraceWriteError):
                    writer.finish()
            finally:
                writer.close()
            parent.rename(root / "moved")
            self.assertEqual((root / "moved" / "trace.jsonl").read_bytes(),
                             b"header\nterminal\n")

    def test_junction_root_is_refused_without_outside_publication(self):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            outer = Path(temporary)
            outside = outer / "outside"
            outside.mkdir()
            alias = outer / "alias"
            command = str(Path(os.environ["SYSTEMROOT"]) / "System32" / "cmd.exe")
            subprocess.run([command, "/c", "mklink", "/J", str(alias), str(outside)],
                           capture_output=True, check=True)
            try:
                for root, target in ((alias, Path("trace.jsonl")),
                                     (outer, alias / "trace.jsonl")):
                    with self.subTest(root=root):
                        with self.assertRaises(TraceWriteError):
                            write_trace(b"forbidden\n", target, run_root=root)
                        self.assertEqual(list(outside.iterdir()), [])
            finally:
                os.rmdir(alias)  # Remove only this test's junction, never its target.

    def test_failed_acquisition_releases_all_handles_and_latches_no_retry(self):
        import ctypes
        from ctypes import wintypes
        import pontius.v0a.trace as trace_module
        writer_type = getattr(trace_module, "TraceWriter", None)
        self.assertIsNotNone(writer_type, "failure needs a retained native owner")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        process = kernel.GetCurrentProcess
        process.argtypes, process.restype = (), wintypes.HANDLE
        count = kernel.GetProcessHandleCount
        count.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        count.restype = wintypes.BOOL
        def handles():
            value = wintypes.DWORD()
            self.assertTrue(count(process(), ctypes.byref(value)))
            return value.value
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "existing.jsonl"
            existing.write_bytes(b"sentinel")
            write_trace(b"warm", root / "warm.jsonl", run_root=root)
            before = handles()
            for index in range(24):
                target = existing if index % 2 == 0 else root / "absent" / "trace.jsonl"
                writer = writer_type(target, run_root=root)
                try:
                    with self.assertRaises(TraceWriteError):
                        writer.append(b"first")
                    with self.assertRaises(TraceWriteError):
                        writer.append(b"retry")
                    with self.assertRaises(TraceWriteError):
                        writer.finish()
                finally:
                    writer.close()
                    writer.close()
            self.assertEqual(handles(), before, "failed native opens leaked handles")
            self.assertEqual(existing.read_bytes(), b"sentinel")
            existing.rename(root / "released.jsonl")


def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
