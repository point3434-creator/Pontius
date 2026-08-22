from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import unittest

import numpy as np

from pontius.factorized_belief import FactorizedCardBelief
from pontius import h32_action_conditioned_posterior_manifest as manifest
from pontius.river import _format_hole


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-action-conditioned-posterior-manifest-v1.json"


def _toy_source() -> FactorizedCardBelief:
    hands = tuple(
        ((4 * seat, 4 * seat + 1), (4 * seat + 2, 4 * seat + 3))
        for seat in range(6)
    )
    return FactorizedCardBelief(
        hands_by_player=hands,
        mixture_weights=[1.0],
        unary_weights=tuple(np.ones((1, 2), dtype=np.float64) for _ in range(6)),
    )


def _node_policy(
    source: FactorizedCardBelief,
    *,
    actor: int,
    history: str,
    action: str,
    probabilities: tuple[float, float],
) -> dict[str, dict[str, float]]:
    other = "bet" if action == "check" else "check"
    return {
        f"toy|p{actor}|hand={_format_hole(hand)}|history={history}": {
            action: probability,
            other: 1.0 - probability,
        }
        for hand, probability in zip(
            source.hands_by_player[actor], probabilities, strict=True
        )
    }


class H32ActionConditionedPosteriorManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_latin_panel_is_balanced_before_labels(self) -> None:
        parsed = manifest.parse_h32_action_conditioned_posterior_manifest_config(
            self.config
        )
        self.assertEqual(len(parsed["target_plan"]), 12)
        self.assertEqual(
            set(Counter(row["source"] for row in parsed["target_plan"]).values()),
            {2},
        )
        self.assertEqual(
            Counter(row["observed_bettor"] for row in parsed["target_plan"]),
            Counter({seat: 2 for seat in range(6)}),
        )
        self.assertEqual(
            sum(
                len(manifest.observed_bet_sequence(row["observed_bettor"]))
                for row in parsed["target_plan"]
            ),
            42,
        )

    def test_posterior_multiplies_every_prefix_action(self) -> None:
        source = _toy_source()
        policy = {}
        policy.update(
            _node_policy(
                source,
                actor=0,
                history="root",
                action="check",
                probabilities=(0.8, 0.2),
            )
        )
        policy.update(
            _node_policy(
                source,
                actor=1,
                history="p0:check",
                action="check",
                probabilities=(0.6, 0.4),
            )
        )
        policy.update(
            _node_policy(
                source,
                actor=2,
                history="p0:check/p1:check",
                action="bet",
                probabilities=(0.1, 0.9),
            )
        )
        posterior, descriptor = manifest.build_action_conditioned_posterior(
            source,
            policy,
            bettor=2,
        )
        self.assertEqual(descriptor["observation_count"], 3)
        np.testing.assert_allclose(posterior.unary_weights[0][0], [1.0, 0.25])
        np.testing.assert_allclose(posterior.unary_weights[1][0], [1.0, 2.0 / 3.0])
        np.testing.assert_allclose(posterior.unary_weights[2][0], [1.0 / 9.0, 1.0])
        np.testing.assert_allclose(posterior.unary_weights[3][0], [1.0, 1.0])

    def test_missing_prefix_action_and_mutations_fail(self) -> None:
        source = _toy_source()
        with self.assertRaisesRegex(ValueError, "absent from the blueprint"):
            manifest.build_action_conditioned_posterior(source, {}, bettor=0)

        changed = json.loads(json.dumps(self.config))
        changed["target_plan"][0]["observed_bettor"] = 5
        with self.assertRaisesRegex(ValueError, "workload differs"):
            manifest.parse_h32_action_conditioned_posterior_manifest_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_source_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            manifest.parse_h32_action_conditioned_posterior_manifest_config(changed)


if __name__ == "__main__":
    unittest.main()
