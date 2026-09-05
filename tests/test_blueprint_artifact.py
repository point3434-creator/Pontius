from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from pontius.blueprint_artifact.codec import (
    BlueprintArtifactError,
    decode_blueprint,
    encode_blueprint,
)
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
)
from pontius.no_limit_betting import BettingAction, BettingActionKind, BettingStreet, raise_to
from pontius.v0a.model import ActionMailbox, DeliveryStatus, FailureCode, HandStartedEvent
from pontius.v0a.replay import (
    Fixture, PROTOCOL_ID, ReplayHost, ScriptedAction, verify_successful_trace)
from pontius.v0a.runtime import HandRuntime
FIXTURES = Path(__file__).with_name("fixtures") / "blueprint_artifact"
RAISE = FIXTURES / "raise_control.json"
HISTORY = FIXTURES / "history_control.json"
DELETE = object()
HAND = "pontius-v0a-blueprint-artifact-v1-correctness-hand"
def expected_raise(action: BettingAction | None = None) -> ImmutableBlueprintActionSource:
    key = BlueprintDecisionKey(
        controlled_seat=3, private_hand=(1, 13), board=(), button=0,
        small_blind=1, big_blind=2, street=BettingStreet.PREFLOP,
        starting_stacks=(200,) * 6, stacks=(200, 199, 198, 200, 200, 200),
        total_contributions=(0, 1, 2, 0, 0, 0),
        street_contributions=(0, 1, 2, 0, 0, 0), folded=(False,) * 6,
        pending_seats=(3, 4, 5, 0, 1, 2), last_full_raise_size=2,
        acted_at_bet=(None,) * 6, public_history=(),
    )
    return ImmutableBlueprintActionSource(
        source_id="pontius-v0a-blueprint-artifact-v1-correctness-policy",
        entries=(BlueprintActionEntry(key, action or raise_to(6)),),
    )
def changed(path: tuple[object, ...], value: object = DELETE, fixture: Path = RAISE) -> bytes:
    document = json.loads(fixture.read_text(encoding="utf-8"))
    target = document
    for part in path[:-1]:
        target = target[part]
    if value is DELETE:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return json.dumps(document, ensure_ascii=True).encode("ascii")
def forge(value: object, **changes: object) -> object:
    clone = object.__new__(type(value))
    for name in value.__slots__:
        object.__setattr__(clone, name, changes.get(name, getattr(value, name)))
    return clone
class StepClock:
    def __init__(self) -> None:
        self.now = 1_000
    def __call__(self) -> int:
        self.now += 1_000
        return self.now
class BlueprintArtifactTests(unittest.TestCase):
    def assert_refused(self, raw: object) -> None:
        with self.assertRaises(BlueprintArtifactError):
            decode_blueprint(raw)
    def test_handwritten_fixtures_full_keys_actions_and_canonical_bytes(self) -> None:
        loaded = decode_blueprint(RAISE.read_bytes())
        self.assertEqual(loaded, expected_raise())
        self.assertEqual(encode_blueprint(loaded), RAISE.read_bytes())
        history = decode_blueprint(HISTORY.read_bytes())
        key = history.entries[0].key
        self.assertEqual(history.source_id, "artifact-history-🚀")
        self.assertEqual((key.street, key.board), (BettingStreet.FLOP, (20, 21, 22)))
        self.assertEqual(tuple(atom[2] for atom in key.public_history),
                         ("fold", "check", "call", "raise"))
        self.assertEqual(key.public_history[-1][3:], (6, 6, True, 3, 4))
        document = json.loads(HISTORY.read_text(encoding="utf-8"))
        second = json.loads(json.dumps(document["entries"][0]))
        second["key"]["private_hand"] = [2, 3]
        second["action"] = {"kind": "fold", "raise_to": None}
        document["entries"].append(second)
        forward = decode_blueprint(json.dumps(document).encode())
        document["entries"].reverse()
        reverse = decode_blueprint(json.dumps(document).encode())
        self.assertEqual(encode_blueprint(forward), encode_blueprint(reverse))
        empty = ImmutableBlueprintActionSource("artifact-empty")
        self.assertEqual(decode_blueprint(encode_blueprint(empty)), empty)
    def test_decode_rejects_closed_schema_and_value_corruptions(self) -> None:
        cases = [
            changed(("version",), "v2"), changed(("source_id",), " "),
            changed(("entries",), {}), changed(("extra",), 1), changed(("version",)),
            changed(("entries", 0, "extra"), 1), changed(("entries", 0, "action")),
            changed(("entries", 0, "key", "extra"), 1),
            changed(("entries", 0, "key", "version")),
            changed(("entries", 0, "key", "controlled_seat"), True),
            changed(("entries", 0, "key", "controlled_seat"), 6),
            changed(("entries", 0, "key", "private_hand"), [1]),
            changed(("entries", 0, "key", "private_hand"), [1, 1]),
            changed(("entries", 0, "key", "folded", 0), 0),
            changed(("entries", 0, "key", "stacks"), [0] * 5),
            changed(("entries", 0, "key", "pending_seats"), [3, 3]),
            changed(("entries", 0, "key", "acted_at_bet", 0), False),
            changed(("entries", 0, "key", "street"), "fifth"),
            changed(("entries", 0, "action", "kind"), "bet"),
            changed(("entries", 0, "action", "raise_to"), None),
            changed(("entries", 0, "key", "small_blind"), 2.0),
            changed(("entries", 0, "key", "big_blind"), float("nan")),
            changed(("entries", 0, "key", "board"), [1, 2, 3], HISTORY),
            changed(("entries", 0, "key", "public_history", 0), ["preflop"], HISTORY),
            b"\xff", RAISE.read_bytes() + b"x", b"[" * 1100 + b"]" * 1100,
            b'{"version":1,"version":2}',
            RAISE.read_bytes().replace(b'"controlled_seat":3',
                                       b'"controlled_seat":3,"controlled_seat":3'),
            RAISE.read_bytes().replace(b'"kind":"raise"',
                                       b'"kind":"raise","kind":"raise"'),
        ]
        duplicate = json.loads(RAISE.read_text())
        duplicate["entries"].append(json.loads(json.dumps(duplicate["entries"][0])))
        duplicate["entries"][-1]["key"]["private_hand"].reverse()
        cases.append(json.dumps(duplicate).encode())
        duplicate["entries"][-1]["action"]["kind"] = "bad"
        cases.append(json.dumps(duplicate).encode())
        for index, raw in enumerate(cases):
            with self.subTest(index=index):
                self.assert_refused(raw)
        self.assert_refused(bytearray(RAISE.read_bytes()))
    def test_numeric_unicode_and_removed_byte_ceiling_are_symmetric(self) -> None:
        base = RAISE.read_bytes()
        maximum = b"9" * 640
        admitted = decode_blueprint(base.replace(b'"last_full_raise_size":2',
                                                 b'"last_full_raise_size":' + maximum))
        self.assertEqual(admitted.entries[0].key.last_full_raise_size, 10**640 - 1)
        self.assertEqual(decode_blueprint(encode_blueprint(admitted)).digest, admitted.digest)
        for token in (b"1" + b"0" * 640, b"9" * 641):
            self.assert_refused(base.replace(b'"last_full_raise_size":2',
                                             b'"last_full_raise_size":' + token))
        source = expected_raise()
        key = forge(source.entries[0].key, last_full_raise_size=10**640)
        entry = forge(source.entries[0], key=key)
        with self.assertRaises(BlueprintArtifactError):
            encode_blueprint(forge(source, entries=(entry,)))
        pair = base.replace(b'"source_id":"pontius-v0a-blueprint-artifact-v1-correctness-policy"',
                            b'"source_id":"\\ud83d\\ude80"')
        self.assertEqual(decode_blueprint(pair).source_id, "🚀")
        for escaped in (b"\\ud800", b"\\udfff"):
            self.assert_refused(pair.replace(b"\\ud83d\\ude80", escaped))
        for text in ("\ud800", "\udfff", "\ud800\udfff"):
            with self.assertRaises(BlueprintArtifactError):
                encode_blueprint(ImmutableBlueprintActionSource(text))
        large = ImmutableBlueprintActionSource("x" * (1_048_576 + 1))
        self.assertEqual(decode_blueprint(encode_blueprint(large)), large)
    def test_export_rejects_foreign_and_malformed_exact_graphs_before_hooks(self) -> None:
        marker: list[str] = []
        class Trap(ImmutableBlueprintActionSource):
            def __getattribute__(self, name: str) -> object:
                marker.append(name)
                raise AssertionError("foreign hook invoked")
        entry = (source := expected_raise()).entries[0]
        foreign = lambda value: object.__new__(type("Foreign", (type(value),), {}))
        bad = [object.__new__(Trap), forge(source, entries=[]), forge(source, source_id="\ud800"),
               forge(source, entries=(forge(entry, key=forge(entry.key, folded=(0,) * 6)),)),
               forge(source, entries=(foreign(entry),)),
               forge(source, entries=(forge(entry, key=foreign(entry.key)),)),
               forge(source, entries=(forge(entry, action=foreign(entry.action)),))]
        for value in bad:
            with self.subTest(type=type(value)):
                with self.assertRaises(BlueprintArtifactError):
                    encode_blueprint(value)
        self.assertEqual(marker, [])
    def test_file_bytes_are_portable_without_codec_file_io(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_bytes(RAISE.read_bytes())
            loaded = decode_blueprint(path.read_bytes())
            path.write_bytes(encode_blueprint(loaded))
            self.assertEqual(decode_blueprint(path.read_bytes()), expected_raise())
    def test_loaded_policy_hits_misses_and_illegal_hits_through_runtime(self) -> None:
        def run(raw: bytes):
            mailbox = ActionMailbox()
            runtime = HandRuntime(blueprint=decode_blueprint(raw), mailbox=mailbox,
                                  clock=StepClock())
            outcome = runtime.dispatch(HandStartedEvent(
                hand_id=HAND, event_index=0, button=0, controlled_seat=3,
                starting_stacks=(200,) * 6, small_blind=1, big_blind=2,
                private_cards=(1, 13)))
            return outcome, mailbox
        hit, mailbox = run(RAISE.read_bytes())
        self.assertEqual((hit.decision.selection_reason.value,
                          hit.decision.selected_action.raise_to), ("table_hit", 6))
        self.assertEqual(len(mailbox.accepted), 1)
        miss, mailbox = run(RAISE.read_bytes().replace(b'"private_hand":[1,13]',
                                                       b'"private_hand":[2,14]'))
        self.assertEqual((miss.decision.selection_reason.value,
                          miss.decision.selected_action.kind), ("passive_default", "call"))
        self.assertEqual(len(mailbox.accepted), 1)
        illegal, mailbox = run(RAISE.read_bytes().replace(b'"raise_to":6', b'"raise_to":1000'))
        self.assertIs(illegal.failure.code, FailureCode.INVALID_BLUEPRINT_ENTRY)
        self.assertIs(illegal.failure.delivery_status, DeliveryStatus.NOT_ATTEMPTED)
        self.assertEqual(len(mailbox.accepted), 0)
    def test_loaded_policy_completes_replay_and_independent_reader(self) -> None:
        fixture = Fixture(
            name="artifact-fold-control",
            seed_label="pontius-v0a-blueprint-artifact-v1-correctness-seed",
            hand_id=HAND, button=0, controlled_seat=3, starting_stacks=(200,) * 6,
            small_blind=1, big_blind=2,
            board_text=("7c", "8d", "9h", "Js", "Qc"),
            hand_text=("As Ad", "Kh Kd", "Ts 8s", "2c 5c", "Ah 3h", "4s 6s"),
            script=tuple(ScriptedAction("preflop", seat, "fold")
                         for seat in (4, 5, 0, 1, 2)),
            expected_payouts=(0, 0, 0, 5, 0, 0), expected_pots=(5,),
            expected_controlled_actions=1,
        )
        host = ReplayHost(fixture, run_id=f"{PROTOCOL_ID}-correctness-artifact",
                          blueprint=decode_blueprint(RAISE.read_bytes()), clock=StepClock())
        outcome = host.run()
        self.assertTrue(outcome.receipt.passed)
        self.assertEqual(outcome.oracle_payouts, (0, 0, 0, 5, 0, 0))
        self.assertEqual(outcome.settlement.final_stacks, (200, 199, 198, 203, 200, 200))
        self.assertEqual(len(host.mailbox.accepted), 1)
        verify_successful_trace(
            outcome.trace, fixture=fixture, blueprint=expected_raise(),
            source_commit="0" * 40, source_manifest_sha256="0" * 64,
            expected_mode="correctness", expected_clock_kind="deterministic_test",
        )
if __name__ == "__main__":
    unittest.main()
