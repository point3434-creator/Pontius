"""Build a label-free manifest of exact blueprint action posteriors."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .open_mode_audit import _canonical_belief
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import _format_hole, parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-action-conditioned-posterior-manifest-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_SOURCE_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_RESULT = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_DECISION = (
    _ROOT / "docs/decisions/ADR-0145-six-fresh-panel-source-blueprints-are-frozen.md"
)
_LEDGER_RESULT = _ROOT / "experiments/results/h32-resident-record-to-hand-fold-v1.json"
_PROFILE_DECISION = (
    _ROOT / "docs/decisions/ADR-0218-resident-sparse-profile-identifies-compute-pressure.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_action_conditioned_posterior_manifest.py"

_PATHS = {
    "expected_source_config_sha256": _SOURCE_CONFIG,
    "expected_source_result_sha256": _SOURCE_RESULT,
    "expected_source_decision_sha256": _SOURCE_DECISION,
    "expected_ledger_result_sha256": _LEDGER_RESULT,
    "expected_profile_decision_sha256": _PROFILE_DECISION,
    "expected_belief_implementation_sha256": _ROOT / "src/pontius/factorized_belief.py",
    "expected_source_builder_sha256": _ROOT / "src/pontius/open_mode_audit.py",
    "expected_policy_implementation_sha256": _ROOT / "src/pontius/real_policy.py",
    "expected_manifest_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_SOURCE_SPECS = (
    ("panel_1/balanced", ("5c", "8c", "8d", "Jc", "As"), "balanced"),
    (
        "panel_1/blocker_heavy",
        ("5c", "8c", "8d", "Jc", "As"),
        "blocker_heavy",
    ),
    (
        "panel_2/blocker_heavy",
        ("2c", "3s", "5d", "Js", "Qc"),
        "blocker_heavy",
    ),
    ("panel_2/balanced", ("2c", "3s", "5d", "Js", "Qc"), "balanced"),
    ("panel_3/balanced", ("4h", "7h", "9s", "Jd", "Kc"), "balanced"),
    (
        "panel_3/blocker_heavy",
        ("4h", "7h", "9s", "Jd", "Kc"),
        "blocker_heavy",
    ),
)

_TARGET_PLAN = tuple(
    {
        "target_id": f"{source}/checks_then_bet_seat{bettor}",
        "source": source,
        "observed_bettor": bettor,
        "round": round_name,
    }
    for round_name, offset in (("latin_a", 0), ("latin_b", 3))
    for source_index, (source, _board, _family) in enumerate(_SOURCE_SPECS)
    for bettor in ((source_index + offset) % 6,)
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required posterior-manifest input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed_bet_sequence(bettor: int) -> tuple[dict[str, Any], ...]:
    """Return all checks and the final bet required by one observed prefix."""

    if isinstance(bettor, bool) or bettor not in range(6):
        raise ValueError("observed bettor must be a seat from zero through five")
    observations = []
    history: list[tuple[int, str]] = []
    for seat in range(bettor + 1):
        action = "bet" if seat == bettor else "check"
        public_history = (
            "root"
            if not history
            else "/".join(f"p{actor}:{prior}" for actor, prior in history)
        )
        observations.append(
            {
                "actor": seat,
                "public_history": public_history,
                "action": action,
            }
        )
        history.append((seat, action))
    return tuple(observations)


def _policy_node_index(
    policy: Mapping[str, Mapping[str, float]],
) -> dict[tuple[int, str, str], Mapping[str, float]]:
    index: dict[tuple[int, str, str], Mapping[str, float]] = {}
    for key, distribution in policy.items():
        parts = key.split("|")
        players = [part for part in parts if part.startswith("p") and part[1:].isdigit()]
        hands = [part.removeprefix("hand=") for part in parts if part.startswith("hand=")]
        histories = [
            part.removeprefix("history=")
            for part in parts
            if part.startswith("history=")
        ]
        if len(players) != 1 or len(hands) != 1 or len(histories) != 1:
            raise ValueError("blueprint information key has ambiguous public coordinates")
        coordinate = (int(players[0][1:]), hands[0], histories[0])
        if coordinate in index:
            raise ValueError("blueprint contains duplicate public coordinates")
        index[coordinate] = distribution
    return index


def action_likelihood(
    index: Mapping[tuple[int, str, str], Mapping[str, float]],
    belief: Any,
    observation: Mapping[str, Any],
) -> np.ndarray:
    """Read one exact public-action likelihood in canonical hand-axis order."""

    actor = int(observation["actor"])
    history = str(observation["public_history"])
    action = str(observation["action"])
    values = []
    for hand in belief.hands_by_player[actor]:
        coordinate = (actor, _format_hole(hand), history)
        if coordinate not in index:
            raise ValueError("observed public action is absent from the blueprint")
        distribution = index[coordinate]
        if action not in distribution:
            raise ValueError("observed action is illegal at its blueprint node")
        values.append(float(distribution[action]))
    likelihood = np.ascontiguousarray(values, dtype=np.float64)
    if (
        not np.all(np.isfinite(likelihood))
        or np.any(likelihood < 0.0)
        or np.any(likelihood > 1.0)
        or float(np.max(likelihood)) <= 0.0
    ):
        raise ValueError("observed action likelihood is not a finite nonzero probability")
    return likelihood


def build_action_conditioned_posterior(
    source: Any,
    policy: Mapping[str, Mapping[str, float]],
    *,
    bettor: int,
) -> tuple[Any, dict[str, Any]]:
    """Apply every observed prefix action as an exact unary Bayes likelihood."""

    index = _policy_node_index(policy)
    posterior = source
    rows = []
    for observation in observed_bet_sequence(bettor):
        likelihood = action_likelihood(index, source, observation)
        posterior = posterior.with_likelihood(int(observation["actor"]), likelihood)
        rows.append(
            {
                **observation,
                "likelihood_minimum": float(np.min(likelihood)),
                "likelihood_maximum": float(np.max(likelihood)),
                "likelihood_mean": float(np.mean(likelihood)),
                "positive_hand_count": int(np.count_nonzero(likelihood > 0.0)),
                "zero_hand_count": int(np.count_nonzero(likelihood == 0.0)),
            }
        )
    return posterior, {
        "construction": "sequential_blueprint_action_likelihoods_for_every_prefix_action",
        "observed_bettor": bettor,
        "public_sequence": [dict(row) for row in observed_bet_sequence(bettor)],
        "observation_rows": rows,
        "observation_count": len(rows),
        "hand_axes_identity": posterior.hands_by_player == source.hands_by_player,
    }


def _digest_absent_at_commit(digest: str, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "grep", "-F", "-n", digest, commit, "--", "."],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 1:
        return True
    if completed.returncode == 0:
        return False
    raise RuntimeError(f"posterior freshness scan failed: {completed.stderr.strip()}")


def parse_h32_action_conditioned_posterior_manifest_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the complete label-free posterior panel."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "freshness_base_commit",
        "seed",
        "source_specs",
        "target_plan",
        "posterior_construction",
        "panel_design",
        "players",
        "hands_per_player",
        "axis_seed",
        "mixture_components",
        "split_index",
        "label_policy",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("posterior-manifest fields differ from ADR-0219")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0218_before_any_action_conditioned_warm_"
            "step_certificate_or_strategy_label"
        ),
        "freshness_base_commit": "6d966cb",
        "seed": 20260821,
        "source_specs": [
            {"source": source, "board": list(board), "range_family": family}
            for source, board, family in _SOURCE_SPECS
        ],
        "target_plan": [dict(row) for row in _TARGET_PLAN],
        "posterior_construction": (
            "multiply_the_source_blueprint_probability_of_every_observed_check_"
            "and_final_bet_on_the_actors_unary_range_in_public_order"
        ),
        "panel_design": (
            "two_label_independent_latin_rounds_each_source_twice_each_bettor_"
            "twice_all_three_boards_and_both_range_families"
        ),
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "label_policy": (
            "zero_new_warm_steps_certificates_quality_evaluations_or_strategy_"
            "labels_manifest_only"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("posterior-manifest workload differs from ADR-0219")
    gates = {
        "expected_sources": 6,
        "expected_targets": 12,
        "expected_targets_per_source": 2,
        "expected_targets_per_bettor": 2,
        "expected_observation_rows": 42,
        "maximum_marginal_split_relative_error": 1e-12,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_ledger_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_blueprint_identity": True,
        "require_target_digest_unique": True,
        "require_target_digest_fresh": True,
        "require_target_differs_from_source": True,
        "require_nonzero_acting_marginal_shift": True,
        "require_hand_axes_identity": True,
        "require_finite": True,
        "require_new_strategy_labels_zero": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("posterior-manifest gates differ from ADR-0219")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"posterior-manifest source mismatch: {field}")
    return {**config, "target_plan": tuple(dict(row) for row in config["target_plan"])}


def _source_belief(parsed: Mapping[str, Any], spec: Mapping[str, Any]) -> Any:
    return _canonical_belief(
        board=parse_cards(*spec["board"]),
        hand_count=int(parsed["hands_per_player"]),
        family=str(spec["range_family"]),
        components=int(parsed["mixture_components"]),
        seed=int(parsed["axis_seed"]),
    )


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, Sequence):
        return all(_finite_tree(item) for item in value)
    return True


def run_h32_action_conditioned_posterior_manifest(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Freeze target identities without opening the scientific label campaign."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_action_conditioned_posterior_manifest_config(config)
    source_parent = json.loads(_SOURCE_RESULT.read_text(encoding="utf-8"))
    ledger_parent = json.loads(_LEDGER_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("posterior manifest requires a clean Git state")

    source_specs = {row["source"]: row for row in parsed["source_specs"]}
    parent_rows = {row["source"]: row for row in source_parent["source_rows"]}
    source_cache: dict[str, tuple[Any, Any, Any]] = {}
    target_rows = []
    for target_spec in parsed["target_plan"]:
        source_key = str(target_spec["source"])
        if source_key not in source_cache:
            spec = source_specs[source_key]
            source = _source_belief(parsed, spec)
            parent = parent_rows[source_key]
            state = parent["final_checkpoint"]
            blueprint = _average_policy_from_state(state)
            source_marginals = source.meet_in_middle_contract(
                tuple(range(parsed["split_index"]))
            )
            source_cache[source_key] = (source, blueprint, source_marginals)
        source, blueprint, source_marginals = source_cache[source_key]
        bettor = int(target_spec["observed_bettor"])
        posterior, descriptor = build_action_conditioned_posterior(
            source,
            blueprint,
            bettor=bettor,
        )
        target_marginals = posterior.meet_in_middle_contract(
            tuple(range(parsed["split_index"]))
        )
        marginal_tvs = [
            0.5 * float(np.sum(np.abs(before - after)))
            for before, after in zip(
                source_marginals.marginals,
                target_marginals.marginals,
                strict=True,
            )
        ]
        descriptor = {
            **descriptor,
            "target_id": target_spec["target_id"],
            "source": source_key,
            "round": target_spec["round"],
            "source_belief_sha256": _belief_digest(source),
            "target_belief_sha256": _belief_digest(posterior),
            "marginal_total_variation_by_seat": marginal_tvs,
            "maximum_marginal_total_variation": max(marginal_tvs),
            "acting_seat_marginal_total_variation": marginal_tvs[bettor],
            "source_partition": source_marginals.partition,
            "target_partition": target_marginals.partition,
            "source_split_relative_error": source_marginals.split_partition_relative_error,
            "target_split_relative_error": target_marginals.split_partition_relative_error,
        }
        descriptor_digest = _json_digest(descriptor)
        target_rows.append(
            {
                **descriptor,
                "target_descriptor_sha256": descriptor_digest,
                "fresh_at_base_commit": _digest_absent_at_commit(
                    descriptor["target_belief_sha256"],
                    parsed["freshness_base_commit"],
                )
                and _digest_absent_at_commit(
                    descriptor_digest,
                    parsed["freshness_base_commit"],
                ),
            }
        )

    source_checkpoint_identity = all(
        _belief_digest(source_cache[source][0]) == parent_rows[source]["source_belief_sha256"]
        for source in source_cache
    )
    blueprint_identity = all(
        policy_digest(source_cache[source][1])
        == parent_rows[source]["final_checkpoint"]["average_policy_sha256"]
        for source in source_cache
    )
    source_counts = Counter(row["source"] for row in target_rows)
    bettor_counts = Counter(int(row["observed_bettor"]) for row in target_rows)
    digests = [row["target_belief_sha256"] for row in target_rows]
    total_seconds = time.perf_counter() - started
    gate_config = parsed["gates"]
    gates = {
        "clean_git": (not git["dirty"]) == gate_config["require_clean_git_state"],
        "source_parent_passed": bool(source_parent["passed"])
        == gate_config["require_source_parent_passed"],
        "ledger_parent_passed": bool(ledger_parent["passed"])
        == gate_config["require_ledger_parent_passed"],
        "source_count": len(source_cache) == gate_config["expected_sources"],
        "target_count": len(target_rows) == gate_config["expected_targets"],
        "source_balance": set(source_counts.values())
        == {gate_config["expected_targets_per_source"]},
        "bettor_balance": set(bettor_counts.values())
        == {gate_config["expected_targets_per_bettor"]},
        "observation_count": sum(row["observation_count"] for row in target_rows)
        == gate_config["expected_observation_rows"],
        "source_checkpoint_identity": source_checkpoint_identity
        == gate_config["require_source_checkpoint_identity"],
        "blueprint_identity": blueprint_identity
        == gate_config["require_blueprint_identity"],
        "target_digest_unique": (len(set(digests)) == len(digests))
        == gate_config["require_target_digest_unique"],
        "target_digest_fresh": all(row["fresh_at_base_commit"] for row in target_rows)
        == gate_config["require_target_digest_fresh"],
        "target_differs_from_source": all(
            row["target_belief_sha256"] != row["source_belief_sha256"]
            for row in target_rows
        )
        == gate_config["require_target_differs_from_source"],
        "nonzero_acting_marginal_shift": all(
            row["acting_seat_marginal_total_variation"] > 0.0 for row in target_rows
        )
        == gate_config["require_nonzero_acting_marginal_shift"],
        "hand_axes_identity": all(row["hand_axes_identity"] for row in target_rows)
        == gate_config["require_hand_axes_identity"],
        "marginal_split_identity": max(
            max(row["source_split_relative_error"], row["target_split_relative_error"])
            for row in target_rows
        )
        <= gate_config["maximum_marginal_split_relative_error"],
        "total_seconds": total_seconds <= gate_config["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate_config["require_finite"],
        "new_strategy_labels_zero": True
        == gate_config["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": True
        == gate_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1,
        "status": "h32_action_conditioned_posterior_manifest_executed",
        "environment": {**environment_metadata(), "git": git},
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "new_warm_steps": 0,
            "new_certificates": 0,
            "new_quality_evaluations": 0,
            "new_strategy_labels": 0,
            "source_blueprints_reconstructed": len(source_cache),
            "posterior_targets_constructed": len(target_rows),
        },
        "target_rows": target_rows,
        "aggregate": {
            "source_counts": dict(sorted(source_counts.items())),
            "bettor_counts": {str(key): value for key, value in sorted(bettor_counts.items())},
            "observation_rows": sum(row["observation_count"] for row in target_rows),
            "minimum_acting_seat_marginal_tv": min(
                row["acting_seat_marginal_total_variation"] for row in target_rows
            ),
            "maximum_acting_seat_marginal_tv": max(
                row["acting_seat_marginal_total_variation"] for row in target_rows
            ),
            "minimum_maximum_seat_marginal_tv": min(
                row["maximum_marginal_total_variation"] for row in target_rows
            ),
            "maximum_maximum_seat_marginal_tv": max(
                row["maximum_marginal_total_variation"] for row in target_rows
            ),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "authorize_action_conditioned_widened_corpus_preregistration"
            if gates["passed"]
            else "reject_action_conditioned_posterior_manifest"
        ),
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "The posterior uses the frozen blueprint as the action-likelihood model.",
            "The panel conditions ranges but does not yet compile a continuation-root subgame.",
            "Marginal TV is a belief-shift descriptor, not a strategy opportunity label.",
            "No strategy-quality, transfer, deployment, or population claim is made.",
        ],
    }
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_action_conditioned_posterior_manifest(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
