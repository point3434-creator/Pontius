from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_atomic_response_preflight import (
    _expected_stop,
    parse_h32_atomic_response_preflight_config,
    select_one_atom_per_acting_seat,
)
from pontius.h32_policy_delta_verifier_audit import (
    parse_h32_policy_delta_verifier_config,
)
from pontius.leaf_adjoint_checkpoint_ladder_audit import _build_case
from pontius.public_policy_tt import information_schema_for_axes
from pontius.river import parse_cards


_ROOT = Path(__file__).parents[1]


class H32AtomicResponsePreflightTests(unittest.TestCase):
    def test_frozen_config_and_mutation_rejection(self) -> None:
        config = json.loads(
            (_ROOT / "experiments/configs/h32-atomic-response-preflight-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(parse_h32_atomic_response_preflight_config(config), config)
        mutated = dict(config)
        mutated["bundle_candidate_id"] = "search_current2"
        with self.assertRaisesRegex(ValueError, "differs from ADR-0159"):
            parse_h32_atomic_response_preflight_config(mutated)

    def test_expected_stop_distinguishes_cap_objective_and_complete(self) -> None:
        blueprint = (1.0,) * 6
        order = tuple(range(6))
        cap = _expected_stop((1.2, 0, 0, 0, 0, 0), blueprint, 6.0, 0.1, order)
        self.assertEqual(cap["stop_reason"], "blueprint_cap")
        self.assertEqual(cap["stop_seat"], 0)
        objective = _expected_stop(
            (1.05,) * 6, blueprint, 6.0, 0.1, order
        )
        self.assertEqual(objective["stop_reason"], "objective_lower_bound")
        self.assertEqual(objective["stop_seat"], 5)
        complete = _expected_stop((0.9,) * 6, blueprint, 6.0, 0.1, order)
        self.assertTrue(complete["complete"])

    def test_atomic_rule_is_one_lexicographic_key_per_acting_seat(self) -> None:
        try:
            import scipy  # noqa: F401
        except ImportError as error:
            raise unittest.SkipTest("optional SciPy screen") from error
        parent = json.loads(
            (_ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json").read_text(
                encoding="utf-8"
            )
        )
        parsed = parse_h32_policy_delta_verifier_config(parent)
        belief, layout, _, _ = _build_case(
            parsed=parsed,
            board=parse_cards(*parsed["board"]),
            hand_count=3,
            family="balanced",
        )
        schema = information_schema_for_axes(layout, belief.hands_by_player)
        blueprint = {
            key: {action: 1.0 / len(actions) for action in actions}
            for key, actions in schema.items()
        }
        bundle = {
            key: {
                action: float(index == 0)
                for index, action in enumerate(actions)
            }
            for key, actions in schema.items()
        }
        selected = select_one_atom_per_acting_seat(
            layout, belief.hands_by_player, blueprint, bundle
        )
        self.assertEqual([row["acting_seat"] for row in selected], list(range(6)))
        self.assertEqual(len({row["information_key"] for row in selected}), 6)


if __name__ == "__main__":
    unittest.main()
