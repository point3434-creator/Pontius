from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.multiway_river_context import (
    generate_multiway_river_contexts,
    group_split,
    make_multiway_range_targets,
    multiway_context_features,
    serialize_multiway_context,
)


ROOT = Path(__file__).parents[1]
CONFIG = json.loads(
    (
        ROOT
        / "experiments"
        / "configs"
        / "multiway-river-search-acceptance-development-v1.json"
    ).read_text(encoding="utf-8")
)


def generated_contexts(groups: int = 8):
    return generate_multiway_river_contexts(
        groups=groups,
        seed=CONFIG["seed"],
        hands_per_player=CONFIG["hands_per_player"],
        families=tuple(CONFIG["families"]),
        splits=tuple(CONFIG["included_splits"]),
        pot_options=tuple(CONFIG["pot_options"]),
        bet_to_pot_options=tuple(CONFIG["bet_to_pot_options"]),
        effective_stack_to_pot=CONFIG["effective_stack_to_pot"],
        weight_options=tuple(CONFIG["range_weight_options"]),
    )


class MultiwayRiverContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contexts = generated_contexts()

    def test_frozen_generation_materializes_only_six_development_groups(self) -> None:
        groups = {context.group_id for context in self.contexts}
        self.assertEqual(
            groups,
            {
                "river3-g000000",
                "river3-g000002",
                "river3-g000003",
                "river3-g000004",
                "river3-g000005",
                "river3-g000007",
            },
        )
        self.assertEqual(len(self.contexts), 24)
        self.assertTrue(all(context.split == "development" for context in self.contexts))
        self.assertEqual(
            {index: group_split(CONFIG["seed"], index) for index in range(8)},
            {
                0: "development",
                1: "validation",
                2: "development",
                3: "development",
                4: "development",
                5: "development",
                6: "test",
                7: "development",
            },
        )

    def test_generation_is_deterministic_and_all_private_hands_are_supported(self) -> None:
        repeated = generated_contexts()
        self.assertEqual(
            [context.game.provenance_digest for context in repeated],
            [context.game.provenance_digest for context in self.contexts],
        )
        for context in self.contexts:
            game = context.game
            self.assertEqual(game.num_players, 3)
            self.assertLessEqual(len(game.deals), 27)
            self.assertGreater(len(game.deals), 0)
            for player in range(3):
                marginal = game.marginal_distribution(player)
                self.assertEqual(len(marginal), 3)
                for hand in marginal:
                    self.assertTrue(
                        any(deal.hand(player) == hand for deal, _ in game.deals)
                    )

    def test_context_features_are_range_only_and_finite(self) -> None:
        forbidden = {
            "nash_conv",
            "deviation_gain",
            "coalition_gain",
            "accept",
            "solver",
            "checkpoint",
            "family",
            "split",
        }
        for context in self.contexts:
            features = multiway_context_features(context)
            self.assertFalse(any(token in key for key in features for token in forbidden))
            self.assertGreater(features["joint_deals"], 0)
            self.assertGreater(features["compatibility_density"], 0.0)
            self.assertLessEqual(features["compatibility_density"], 1.0)

    def test_four_targets_preserve_support_and_structure_but_change_range(self) -> None:
        for context in self.contexts[:4]:
            targets = make_multiway_range_targets(context, CONFIG["target_specs"])
            self.assertEqual(len(targets), 4)
            self.assertEqual(len({target.name for target in targets}), 4)
            for target in targets:
                self.assertEqual(
                    target.game.structural_digest,
                    context.game.structural_digest,
                )
                self.assertNotEqual(
                    target.game.provenance_digest,
                    context.game.provenance_digest,
                )
                self.assertEqual(
                    set(target.game.joint_distribution()),
                    set(context.game.joint_distribution()),
                )
                self.assertGreater(target.boundary_features["root_total_variation"], 0.0)
                self.assertNotIn("nash_conv", target.boundary_features)
                self.assertNotIn("coalition_gain", target.boundary_features)

    def test_seat_targets_use_declared_seat_and_alignment_uses_no_selected_hand(self) -> None:
        targets = make_multiway_range_targets(self.contexts[0], CONFIG["target_specs"])
        for seat, target in enumerate(targets[:3]):
            self.assertEqual(target.boundary_features["selected_seat"], seat)
            self.assertNotEqual(target.boundary_features["selected_hand"], "none")
        alignment = targets[3]
        self.assertEqual(alignment.boundary_features["selected_seat"], -1)
        self.assertEqual(alignment.boundary_features["selected_hand"], "none")

    def test_serialization_carries_provenance_and_exact_joint_range(self) -> None:
        serialized = serialize_multiway_context(self.contexts[0])
        self.assertEqual(serialized["split"], "development")
        self.assertEqual(serialized["provenance_digest"], self.contexts[0].game.provenance_digest)
        self.assertEqual(len(serialized["joint_range"]), len(self.contexts[0].game.deals))

    def test_invalid_family_split_and_stack_geometry_are_rejected(self) -> None:
        common = {
            "groups": 1,
            "seed": 1,
            "hands_per_player": 3,
            "families": ("balanced",),
            "splits": ("development",),
            "pot_options": (12.0,),
            "bet_to_pot_options": (0.5,),
            "effective_stack_to_pot": 2.0,
            "weight_options": (1.0,),
        }
        for field, value, message in (
            ("families", ("unknown",), "unsupported multiway families"),
            ("splits", ("sealed",), "unsupported context splits"),
            ("effective_stack_to_pot", 0.1, "fit the effective stack"),
        ):
            candidate = dict(common)
            candidate[field] = value
            with self.assertRaisesRegex(ValueError, message):
                generate_multiway_river_contexts(**candidate)


if __name__ == "__main__":
    unittest.main()
