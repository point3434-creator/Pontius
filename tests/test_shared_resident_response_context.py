from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence
from pontius.factor_tt_contraction import FactorTTBeliefWorkspace
from pontius.h32_policy_delta_verifier_audit import (
    parse_h32_policy_delta_verifier_config,
)
from pontius.h32_warm_search_acceptance_audit import build_target_belief
from pontius.leaf_adjoint_checkpoint_ladder_audit import _build_case
from pontius.leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from pontius.open_mode_factor_tt import OpenModeFactorTTWorkspace
from pontius.river import parse_cards
from pontius.shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
    shared_device_numeric_bytes,
    unique_response_numeric_bytes,
)


_ROOT = Path(__file__).parents[1]


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class SharedResidentResponseContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = json.loads(
            (_ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.parsed = parse_h32_policy_delta_verifier_config(config)
        board = parse_cards(*cls.parsed["board"])
        source_belief, cls.layout, cls.sparse, retained = _build_case(
            parsed=cls.parsed,
            board=board,
            hand_count=3,
            family="balanced",
        )
        source_workspace, _, cls.automata = retained
        cls.workspaces = []
        cls.beliefs = []
        for shift in cls.parsed["target_shifts"]:
            belief, _ = build_target_belief(
                source_belief,
                board=board,
                shift=shift,
                local_blocker_target_seat=cls.parsed["local_blocker_target_seat"],
            )
            base = FactorTTBeliefWorkspace.compile(
                source_workspace.topology.base,
                belief,
                query_chunk_records=cls.parsed["query_chunk_records"],
            )
            cls.beliefs.append(belief)
            cls.workspaces.append(
                OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
            )
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.sparse)
        cls.bundle = SharedResidentAutomatonBundle.compile(
            cls.workspaces[0], cls.automata
        )

    def test_two_belief_contexts_share_automata_and_remain_exact(self) -> None:
        contexts = tuple(
            bind_resident_response_context(
                self.bundle,
                layout=self.layout,
                workspace=workspace,
                sparse=self.sparse,
                source_policy={},
                hands_by_player=belief.hands_by_player,
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
            )
            for workspace, belief in zip(self.workspaces, self.beliefs, strict=True)
        )
        for context, workspace, belief in zip(
            contexts, self.workspaces, self.beliefs, strict=True
        ):
            complete = evaluate_leaf_adjoint_profile(
                self.layout,
                workspace,
                self.sparse,
                {},
                self.automata,
                hands_by_player=belief.hands_by_player,
                maximum_feature_width_per_batch=96,
            )
            for seat, cache in enumerate(context.response_caches):
                self.assertAlmostEqual(
                    cache.source_evaluation.profile_utility,
                    complete.seats[seat].profile_utility,
                    places=12,
                )
                self.assertAlmostEqual(
                    cache.source_evaluation.best_response_value,
                    complete.seats[seat].best_response_value,
                    places=12,
                )
        self.assertGreater(shared_device_numeric_bytes(self.bundle, contexts), 0)
        self.assertGreater(unique_response_numeric_bytes(contexts), 0)
        self.assertIs(
            contexts[0].response_caches[0].workspace.topology,
            contexts[1].response_caches[0].workspace.topology,
        )

    def test_unrelated_topology_is_rejected(self) -> None:
        source_belief, _, _, retained = _build_case(
            parsed=self.parsed,
            board=parse_cards(*self.parsed["board"]),
            hand_count=3,
            family="balanced",
        )
        unrelated, _, _ = retained
        with self.assertRaisesRegex(ValueError, "another topology"):
            self.bundle.validate_workspace(unrelated)


if __name__ == "__main__":
    unittest.main()
