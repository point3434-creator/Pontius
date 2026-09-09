from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from pontius.blueprint_artifact.codec import (
    BlueprintArtifactError, decode_blueprint, encode_blueprint)
from pontius.immutable_blueprint import (
    BlueprintActionEntry, BlueprintDecisionKey, ImmutableBlueprintActionSource)
from pontius.no_limit_betting import BettingAction, BettingActionKind, BettingStreet, raise_to
from pontius.v0a.model import ActionMailbox, DeliveryStatus, FailureCode, HandStartedEvent
from pontius.v0a.replay import (
    Fixture, PROTOCOL_ID, ReplayHost, ScriptedAction, verify_successful_trace)
from pontius.v0a.runtime import HandRuntime
FIXTURES = Path(__file__).with_name("fixtures") / "blueprint_artifact"
RAISE, HISTORY = (FIXTURES / "raise_control.json", FIXTURES / "history_control.json")
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
        "pontius-v0a-blueprint-artifact-v1-correctness-policy",
        (BlueprintActionEntry(key, action or raise_to(6)),))
def expected_history() -> ImmutableBlueprintActionSource:
    key = BlueprintDecisionKey(
        controlled_seat=0, private_hand=(0, 1), board=(20, 21, 22), button=0,
        small_blind=1, big_blind=2, street=BettingStreet.FLOP,
        starting_stacks=(200,) * 6, stacks=(200,) * 6,
        total_contributions=(0,) * 6, street_contributions=(0,) * 6,
        folded=(False,) * 6, pending_seats=(0, 1), last_full_raise_size=2,
        acted_at_bet=(None,) * 6, public_history=(
            ("preflop", 0, "fold", None, 0, False, None, 0),
            ("preflop", 1, "check", None, 0, False, None, 0),
            ("preflop", 2, "call", None, 2, False, None, 0),
            ("preflop", 3, "raise", 6, 6, True, 3, 4)),
    )
    return ImmutableBlueprintActionSource(
        "artifact-history-🚀",
        (BlueprintActionEntry(key, BettingAction(BettingActionKind.CHECK)),))
def changed(path: tuple[object, ...], value: object = ..., fixture: Path = RAISE) -> bytes:
    document = json.loads(fixture.read_text(encoding="utf-8"))
    target = document
    for part in path[:-1]:
        target = target[part]
    if value is ...:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return json.dumps(document, ensure_ascii=True).encode("ascii")
def forge(value: object, **changes: object) -> object:
    clone = object.__new__(type(value))
    for name in value.__slots__:
        object.__setattr__(clone, name, changes.get(name, getattr(value, name)))
    return clone
def numeric_source(family: str, value: int) -> ImmutableBlueprintActionSource:
    source = expected_history() if family == "history" else expected_raise()
    entry, key, action = source.entries[0], source.entries[0].key, source.entries[0].action
    if family == "vector":
        key = forge(key, stacks=(value,) + key.stacks[1:])
    elif family == "history":
        rows = key.public_history
        changed_row = rows[2][:4] + (value,) + rows[2][5:]
        key = forge(key, public_history=rows[:2] + (changed_row,) + rows[3:])
    elif family == "action":
        action = forge(action, raise_to=value)
    else:
        key = forge(key, last_full_raise_size=value)
    return forge(source, entries=(forge(entry, key=key, action=action),))
class StepClock:
    now = 1_000
    def __call__(self) -> int:
        self.now += 1_000
        return self.now
class BlueprintArtifactTests(unittest.TestCase):
    def test_weighted_artifact_round_trip_and_identity(self):
        from pontius.immutable_blueprint import WeightedBlueprintAction
        from pontius.no_limit_betting import CALL, FOLD
        action = WeightedBlueprintAction(((CALL, 2), (FOLD, 1)))
        source = expected_raise(action)
        raw = encode_blueprint(source)
        self.assertEqual(json.loads(raw)['version'], 'pontius-v0a-blueprint-artifact-v2')
        self.assertEqual(decode_blueprint(raw), source)
        self.assertEqual(encode_blueprint(decode_blueprint(raw)), raw)
        self.assertEqual(source.digest, expected_raise(
            WeightedBlueprintAction(((FOLD, 1), (CALL, 2)))).digest)
        self.assertNotEqual(source.digest, expected_raise(
            WeightedBlueprintAction(((CALL, 1), (FOLD, 2)))).digest)
        self.assertEqual(encode_blueprint(expected_raise()), RAISE.read_bytes())

    def test_weighted_artifact_rejects_malformed_weights_and_mixed_v1(self):
        from pontius.immutable_blueprint import WeightedBlueprintAction
        from pontius.no_limit_betting import CALL, FOLD
        raw = encode_blueprint(expected_raise(WeightedBlueprintAction(((CALL, 2), (FOLD, 1)))))
        for weight in (0, -1, True, 0.5, '2', 2**63):
            document = json.loads(raw)
            document['entries'][0]['action']['choices'][0]['weight'] = weight
            self.assert_refused(json.dumps(document).encode())
        document = json.loads(raw)
        document['version'] = 'pontius-v0a-blueprint-artifact-v1'
        self.assert_refused(json.dumps(document).encode())
        for choices in ((), ((CALL, 0),), ((CALL, 1), (CALL, 2)),
                        ((CALL, 2**62), (FOLD, 2**62))):
            with self.assertRaises((ValueError, TypeError)):
                WeightedBlueprintAction(choices)

    def assert_refused(self, raw: object) -> None:
        self.assertRaises(BlueprintArtifactError, decode_blueprint, raw)
    def test_handwritten_fixtures_full_keys_actions_and_canonical_bytes(self) -> None:
        loaded = decode_blueprint(RAISE.read_bytes())
        self.assertEqual(loaded, expected_raise())
        self.assertEqual(encode_blueprint(loaded), RAISE.read_bytes())
        self.assertEqual(decode_blueprint(HISTORY.read_bytes()), expected_history())
        for label, amount, expected in (
            ("fold", None, BettingAction(BettingActionKind.FOLD)),
            ("check", None, BettingAction(BettingActionKind.CHECK)),
            ("call", None, BettingAction(BettingActionKind.CALL)),
            ("raise", 7, BettingAction(BettingActionKind.RAISE, 7)),
        ):
            raw = changed(("entries", 0, "action"), {"kind": label, "raise_to": amount})
            self.assertEqual(decode_blueprint(raw).entries[0].action, expected)
        source = expected_raise()
        second = forge(source.entries[0], key=forge(source.entries[0].key, private_hand=(2, 3)),
                       action=BettingAction(BettingActionKind.FOLD))
        forward = forge(source, entries=(source.entries[0], second))
        reverse = forge(source, entries=forward.entries[::-1])
        self.assertEqual(encode_blueprint(forward), encode_blueprint(reverse))
        empty = ImmutableBlueprintActionSource("artifact-empty")
        self.assertEqual(decode_blueprint(encode_blueprint(empty)), empty)
    def test_decode_rejects_closed_schema_and_value_corruptions(self) -> None:
        entry, key, action = ("entries", 0), ("entries", 0, "key"), ("entries", 0, "action")
        cases = [
            changed(("version",), "v2"), changed(("source_id",), " "),
            changed(("entries",), {}), changed(("extra",), 1), changed(("version",)),
            changed((*entry, "extra"), 1), changed((*entry, "action")),
            changed((*key, "extra"), 1), changed((*key, "version")),
            changed((*key, "controlled_seat"), True), changed((*key, "controlled_seat"), 6),
            changed((*key, "private_hand"), [1]), changed((*key, "private_hand"), [1, 1]),
            changed((*key, "folded", 0), 0), changed((*key, "stacks"), [0] * 5),
            changed((*key, "pending_seats"), [3, 3]), changed((*key, "acted_at_bet", 0), False),
            changed((*key, "street"), "fifth"), changed((*action, "kind")),
            changed((*action, "extra"), 1), changed((*action, "kind"), "bet"),
            changed((*action, "raise_to"), None), changed((*key, "small_blind"), 2.0),
            changed((*key, "big_blind"), float("nan")),
            changed((*key, "board"), [1, 2, 3], HISTORY),
            changed((*key, "public_history", 0), ["preflop"], HISTORY),
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
        for raw in cases:
            self.assert_refused(raw)
        self.assert_refused(bytearray(RAISE.read_bytes()))
    def test_numeric_unicode_and_removed_byte_ceiling_are_symmetric(self) -> None:
        maximum = b"9" * 640
        cases = (
            ("scalar", RAISE, b'"last_full_raise_size":2', b'"last_full_raise_size":', b""),
            ("vector", RAISE, b'"stacks":[200,199', b'"stacks":[', b",199"),
            ("history", HISTORY, b'["preflop", 2, "call", null, 2, false',
             b'["preflop", 2, "call", null, ', b", false"),
            ("action", RAISE, b'"action":{"kind":"raise","raise_to":6}',
             b'"action":{"kind":"raise","raise_to":', b"}"),
        )
        for family, fixture, old, before, after in cases:
            mutate = lambda token: fixture.read_bytes().replace(old, before + token + after)
            exact = numeric_source(family, 10**640 - 1)
            self.assertEqual(decode_blueprint(mutate(maximum)), exact)
            self.assertEqual(decode_blueprint(encode_blueprint(exact)), exact)
            self.assertEqual(decode_blueprint(encode_blueprint(exact)).digest, exact.digest)
            self.assertRaises(BlueprintArtifactError, encode_blueprint,
                              numeric_source(family, 10**640))
            for token in (b"1" + b"0" * 640, b"9" * 641):
                self.assert_refused(mutate(token))
        base = RAISE.read_bytes()
        pair = base.replace(b'"source_id":"pontius-v0a-blueprint-artifact-v1-correctness-policy"',
                            b'"source_id":"\\ud83d\\ude80"')
        self.assertEqual(decode_blueprint(pair).source_id, "🚀")
        for escaped in (b"\\ud800", b"\\udfff"):
            self.assert_refused(pair.replace(b"\\ud83d\\ude80", escaped))
        for text in ("\ud800", "\udfff", "\ud800\udfff"):
            self.assertRaises(BlueprintArtifactError, encode_blueprint,
                              ImmutableBlueprintActionSource(text))
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
               object.__new__(ImmutableBlueprintActionSource),
               forge(source, entries=(entry, object.__new__(BlueprintActionEntry))),
               forge(source, entries=(forge(entry, key=object.__new__(BlueprintDecisionKey)),)),
               forge(source, entries=(forge(entry, action=object.__new__(BettingAction)),)),
               forge(source, entries=(forge(entry, key=forge(entry.key, folded=(0,) * 6)),)),
               forge(source, entries=(foreign(entry),)),
               forge(source, entries=(forge(entry, key=foreign(entry.key)),)),
               forge(source, entries=(forge(entry, action=foreign(entry.action)),))]
        for value in bad:
            self.assertRaises(BlueprintArtifactError, encode_blueprint, value)
        self.assertEqual(marker, [])
    def test_file_bytes_are_portable_without_codec_file_io(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_bytes(RAISE.read_bytes())
            path.write_bytes(encode_blueprint(decode_blueprint(path.read_bytes())))
            self.assertEqual(decode_blueprint(path.read_bytes()), expected_raise())
    def test_loaded_policy_hits_misses_and_illegal_hits_through_runtime(self) -> None:
        def run(raw: bytes):
            mailbox = ActionMailbox()
            outcome = HandRuntime(blueprint=decode_blueprint(raw), mailbox=mailbox,
                                  clock=StepClock()).dispatch(HandStartedEvent(
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
            expected_payouts=(0, 0, 0, 5, 0, 0), expected_pots=(5,), expected_controlled_actions=1)
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
