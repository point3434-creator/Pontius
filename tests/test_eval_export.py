"""Teacher/export contracts using a labeled proper subset of validated real rows."""

from hashlib import sha256
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from pontius import eval_bridge as bridge
from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
from pontius.decision_provider.providers import BlueprintProvider
from pontius.immutable_blueprint import BlueprintActionEntry, ImmutableBlueprintActionSource
from pontius.no_limit_betting import CHECK
from pontius.river import make_hole


BOARD = bridge.board_cards(("2c", "7d", "9h", "Js", "Qc"))
BET = str(bridge.DECLARED_BET)
# Previously singleton-validated preflight totals; these are not a full-pool solve.
ROWS = [dict(hand=name, check_total=check, bet_total=bet, denominator=990,
             action=BET if bet > check else str(CHECK), bet=BET)
        for name, check, bet in (("AdAs", 1430, 2860), ("KdKh", 1438, 2876),
                                 ("8dTd", 1914, 3828), ("3c4d", -1962, -3924))]
HANDS = tuple(make_hole(row["hand"][:2], row["hand"][2:]) for row in ROWS)
PERMUTATION = HANDS + tuple(hand for hand in bridge.hero_hands(BOARD) if hand not in HANDS)


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


class TeacherExportTests(unittest.TestCase):
    def test_public_teacher_export_boundary_exists(self):
        for name in ("teacher_bytes", "teacher_actions", "export_teacher", "validate_membership"):
            self.assertTrue(callable(getattr(bridge, name, None)), name)

    def test_ordered_teacher_is_immutable_canonical_and_binds_rows(self):
        rows = [dict(row) for row in ROWS]
        raw = bridge.teacher_bytes(BOARD, PERMUTATION, rows)
        self.assertIs(type(raw), bytes)
        self.assertEqual(raw, canonical(json.loads(raw)))
        rows[0]["check_total"] = 0
        self.assertEqual(bridge.teacher_actions(raw),
                         (BOARD, HANDS, {row["hand"]: bridge.DECLARED_BET
                                        if row["action"] == BET else CHECK for row in ROWS}))
        self.assertNotEqual(raw, bridge.teacher_bytes(BOARD, PERMUTATION, ROWS[:3]))

    def test_serializer_refuses_wrong_coverage_types_totals_and_actions(self):
        invalid = [[], ROWS[::-1], ROWS + ROWS[:1]]
        for field, value in (("hand", "AsAd"), ("check_total", True),
                             ("check_total", 1430.0), ("check_total", 1982),
                             ("bet_total", 2858), ("denominator", 989),
                             ("action", str(CHECK)), ("bet", "raise_to:3"),
                             ("extra", 0), ("wins", 990)):
            invalid.append([dict(ROWS[0], **{field: value}), *ROWS[1:]])
        for rows in invalid:
            with self.subTest(rows=rows), self.assertRaises((TypeError, ValueError)):
                bridge.teacher_bytes(BOARD, PERMUTATION, rows)
        for permutation in (PERMUTATION[:-1], PERMUTATION[:1] * 1081,
                            PERMUTATION[1:] + PERMUTATION[:1]):
            with self.assertRaises(ValueError):
                bridge.teacher_bytes(BOARD, permutation, ROWS)

    def test_parser_refuses_noncanonical_and_changed_domain(self):
        raw = bridge.teacher_bytes(BOARD, PERMUTATION, ROWS)
        for bad in (raw + b"\n", b'{' + b'"board":null,' + raw[1:],
                    raw.replace(b'1430', b'NaN'), raw.decode(), bytearray(raw)):
            with self.subTest(bad_type=type(bad)), self.assertRaises((TypeError, ValueError)):
                bridge.teacher_actions(bad)
        document = json.loads(raw)
        for field, value in (("prefix", []), ("opponent", {}), ("root", {}),
                             ("board", [name.lower() for name in document["board"]]),
                             ("hands", document["hands"][::-1]), ("extra", 1)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                bridge.teacher_actions(canonical(dict(document, **{field: value})))

    def test_actual_royal_zero_production_row_keeps_check_tie(self):
        royal = bridge.board_cards(("Ts", "Js", "Qs", "Ks", "As"))
        hand = make_hole("2c", "3d")
        row = bridge.hand_totals(bridge.replay_root(), royal, hand)
        order = (hand,) + tuple(item for item in bridge.hero_hands(royal) if item != hand)
        raw = bridge.teacher_bytes(royal, order, [row])
        self.assertEqual(bridge.teacher_actions(raw)[2], {"2c3d": CHECK})
        for changed in (dict(row, action=BET), dict(row, ties=989),
                        dict(row, work=dict(row["work"], ranker_calls=True))):
            with self.assertRaises(ValueError):
                bridge.teacher_bytes(royal, order, [changed])

    def test_export_is_deterministic_measures_wire_and_never_solves(self):
        raw = bridge.teacher_bytes(BOARD, PERMUTATION, ROWS)
        # A forbidden recomputation fails immediately; real codec still executes.
        with patch.object(bridge, "hand_totals", side_effect=AssertionError("recomputed teacher")):
            wire, report = bridge.export_teacher(raw)
            self.assertEqual((wire, report), bridge.export_teacher(raw))
        source = decode_blueprint(wire)
        self.assertEqual(source.source_id, "t1:" + sha256(raw).hexdigest())
        self.assertEqual({entry.key.private_hand: entry.action for entry in source.entries},
                         {hand: bridge.DECLARED_BET if index < 3 else CHECK
                          for index, hand in enumerate(HANDS)})
        self.assertEqual(report["wire_bytes"], len(wire))
        self.assertEqual(report["wire_sha256"], sha256(wire).hexdigest())
        self.assertTrue(report["passed"])
        json.dumps(report, allow_nan=False)
        self.assertEqual(bridge.export_teacher(raw, cap=len(wire))[0], wire)
        for cap in (len(wire) - 1, True, 0, 1.5):
            with self.assertRaises((TypeError, ValueError)):
                bridge.export_teacher(raw, cap=cap)

    def test_subset_membership_exhaustively_distinguishes_check_hit_and_default(self):
        raw = bridge.teacher_bytes(BOARD, PERMUTATION, ROWS)
        wire, _ = bridge.export_teacher(raw)
        report = bridge.validate_membership(raw, wire)
        self.assertTrue(report["passed"], report)
        self.assertEqual((report["universe_count"], report["hits"], report["unsupported"]),
                         (1081, 4, 1077))
        rows = {row["hand"]: row for row in report["rows"]}
        self.assertEqual(rows["3c4d"]["provider_reason"], "blueprint_hit")
        self.assertEqual(rows["AdAs"]["provider_action"], BET)
        off_pool = next(row for row in rows.values()
                        if row["hand"] not in {r["hand"] for r in ROWS})
        self.assertEqual((off_pool["provider_reason"], off_pool["classification"]),
                         ("blueprint_default", "unsupported"))
        json.dumps(report, allow_nan=False)
        source = decode_blueprint(wire)
        entry = source.entries[0]
        for entries in (source.entries[1:],
                        (BlueprintActionEntry(entry.key, CHECK), *source.entries[1:])):
            changed = encode_blueprint(ImmutableBlueprintActionSource(source.source_id, entries))
            self.assertFalse(bridge.validate_membership(raw, changed)["passed"])

    def test_membership_detects_relabeling_at_the_real_public_provider_boundary(self):
        raw = bridge.teacher_bytes(BOARD, PERMUTATION, ROWS)
        wire, _ = bridge.export_teacher(raw)
        original = BlueprintProvider.propose

        def relabel(provider, observation):
            # Execute the real provider, then inject only the wrong reason label.
            proposal = original(provider, observation)
            if proposal.action == CHECK:
                reason = ("blueprint_default" if proposal.reason == "blueprint_hit"
                          else "blueprint_hit")
                return replace(proposal, reason=reason)
            return proposal

        with patch.object(BlueprintProvider, "propose", relabel):
            report = bridge.validate_membership(raw, wire)
        self.assertFalse(report["passed"])
        self.assertEqual((report["hits"], report["disagreements"]), (3, 1078))


if __name__ == "__main__":
    unittest.main()
