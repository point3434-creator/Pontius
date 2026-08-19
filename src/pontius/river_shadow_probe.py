"""Attach a traversal-free shadow-regret probe to an exact river trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from statistics import mean, median
from typing import Any

from .cfr import TabularCFR
from .river_context import generate_river_contexts, serialize_river_context
from .river_opportunity import _regret_features

TOLERANCE = 1e-12


def _run_solver(
    game: Any,
    checkpoint: int,
    *,
    with_shadow: bool,
) -> tuple[TabularCFR, float, float, dict[str, float | int]]:
    solver = TabularCFR(
        game,
        "dcfr",
        shadow_regret_variants=(("cfr_plus",) if with_shadow else ()),
    )
    solve_start = time.perf_counter()
    solver.run(checkpoint)
    solver_milliseconds = (time.perf_counter() - solve_start) * 1_000.0

    feature_start = time.perf_counter()
    features: dict[str, float | int] = _regret_features(
        [
            regret
            for data in solver.information_sets.values()
            for regret in data.regrets.values()
        ],
        game.payoff_span,
    )
    if with_shadow:
        shadow = solver.shadow_regret_summary("cfr_plus")
        features.update(
            {
                "shadow_cfr_plus_positive_regret_mass": shadow[
                    "positive_regret_mass"
                ],
                "shadow_cfr_plus_negative_regret_mass": shadow[
                    "negative_regret_mass"
                ],
                "shadow_cfr_plus_normalized_positive_regret_mass": (
                    float(shadow["positive_regret_mass"]) / game.payoff_span
                ),
                "shadow_cfr_plus_normalized_negative_regret_mass": (
                    float(shadow["negative_regret_mass"]) / game.payoff_span
                ),
                "shadow_cfr_plus_maximum_positive_regret": shadow[
                    "maximum_positive_regret"
                ],
                "shadow_cfr_plus_positive_regret_concentration": shadow[
                    "positive_regret_concentration"
                ],
                "shadow_cfr_plus_materialized_information_sets": shadow[
                    "materialized_information_sets"
                ],
                "shadow_cfr_plus_regret_entries": shadow["regret_entries"],
                "shadow_cfr_plus_instantaneous_regret_updates": shadow[
                    "instantaneous_regret_updates"
                ],
                "shadow_cfr_plus_regret_discount_updates": shadow[
                    "regret_discount_updates"
                ],
            }
        )
    feature_milliseconds = (time.perf_counter() - feature_start) * 1_000.0
    return solver, solver_milliseconds, feature_milliseconds, features


def _maximum_active_difference(first: TabularCFR, second: TabularCFR) -> float:
    if first.iteration != second.iteration:
        raise AssertionError("paired solvers stopped at different iterations")
    if first.information_sets.keys() != second.information_sets.keys():
        raise AssertionError("shadow instrumentation changed materialized information sets")
    maximum = 0.0
    for key, first_data in first.information_sets.items():
        second_data = second.information_sets[key]
        if first_data.actions != second_data.actions:
            raise AssertionError("shadow instrumentation changed legal actions")
        for action in first_data.actions:
            maximum = max(
                maximum,
                abs(first_data.regrets[action] - second_data.regrets[action]),
                abs(
                    first_data.strategy_sum[action]
                    - second_data.strategy_sum[action]
                ),
            )
    return maximum


def run_river_shadow_probe(
    source: dict[str, Any],
    *,
    checkpoint: int = 2,
    source_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Regenerate source contexts and measure a DCFR-fed CFR+ accumulator.

    The paired plain solve proves that instrumentation leaves the active DCFR
    trajectory unchanged. Timing charges both shadow-update overhead and the
    one-pass feature summary. No equilibrium teacher or future label is used.
    """

    if source.get("experiment_type") != "exact_river_early_opportunity_trace":
        raise ValueError("source is not an exact river opportunity trace")
    config = source["config"]
    if config.get("sequential_raise") is not True:
        raise ValueError("shadow screen requires the sequential river tree")
    if "dcfr" not in config["solvers"]:
        raise ValueError("source trace must contain DCFR")
    if checkpoint not in config["checkpoints"] or checkpoint <= 0:
        raise ValueError("probe checkpoint must be a positive source checkpoint")
    if set(config["included_splits"]) != {"development"}:
        raise ValueError("shadow probe is restricted to development contexts")

    contexts = generate_river_contexts(
        groups=int(config["groups"]),
        seed=int(config["seed"]),
        hands_per_player=int(config["hands_per_player"]),
        families=tuple(str(value) for value in config["families"]),
        splits=tuple(str(value) for value in config["included_splits"]),
        sequential_raise=True,
    )
    source_contexts = {
        str(context["context_id"]): context for context in source["contexts"]
    }
    source_records = {
        str(record["context_id"]): record
        for record in source["records"]
        if record["solver"] == "dcfr" and int(record["checkpoint"]) == checkpoint
    }
    expected_ids = {context.context_id for context in contexts}
    if set(source_contexts) != expected_ids or set(source_records) != expected_ids:
        raise ValueError("regenerated and source context identities differ")

    rows = []
    maximum_active_difference = 0.0
    for index, context in enumerate(contexts):
        serialized = serialize_river_context(context)
        source_context = source_contexts[context.context_id]
        for field in (
            "group_id",
            "split",
            "family",
            "seed",
            "structural_digest",
            "provenance_digest",
            "board",
            "pot",
            "stacks",
            "bet_size",
            "raise_to",
            "joint_range",
            "features",
        ):
            if serialized[field] != source_context[field]:
                raise ValueError(
                    f"regenerated context {context.context_id!r} differs at {field!r}"
                )

        if index % 2 == 0:
            plain = _run_solver(context.game, checkpoint, with_shadow=False)
            shadowed = _run_solver(context.game, checkpoint, with_shadow=True)
        else:
            shadowed = _run_solver(context.game, checkpoint, with_shadow=True)
            plain = _run_solver(context.game, checkpoint, with_shadow=False)
        plain_solver, plain_ms, plain_feature_ms, plain_features = plain
        shadow_solver, shadow_ms, feature_ms, shadow_features = shadowed
        active_difference = _maximum_active_difference(plain_solver, shadow_solver)
        maximum_active_difference = max(maximum_active_difference, active_difference)
        if active_difference > TOLERANCE:
            raise AssertionError("shadow accumulator changed the active DCFR solve")

        source_active = float(
            source_records[context.context_id]["online_features"][
                "normalized_positive_regret_mass"
            ]
        )
        regenerated_active = float(plain_features["normalized_positive_regret_mass"])
        if abs(source_active - regenerated_active) > TOLERANCE:
            raise ValueError(
                f"source DCFR feature did not reproduce for {context.context_id!r}"
            )

        conservative_overhead = max(0.0, shadow_ms - plain_ms) + feature_ms
        rows.append(
            {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "split": context.split,
                "family": context.family,
                "provenance_digest": context.game.provenance_digest,
                "checkpoint": checkpoint,
                "online_features": shadow_features,
                "timing": {
                    "plain_dcfr_solver_milliseconds": plain_ms,
                    "plain_active_feature_summary_milliseconds": plain_feature_ms,
                    "shadowed_dcfr_solver_milliseconds": shadow_ms,
                    "charged_feature_summary_milliseconds": feature_ms,
                    "conservative_instrumentation_overhead_milliseconds": (
                        conservative_overhead
                    ),
                },
            }
        )

    plain_times = [
        float(row["timing"]["plain_dcfr_solver_milliseconds"]) for row in rows
    ]
    shadow_times = [
        float(row["timing"]["shadowed_dcfr_solver_milliseconds"]) for row in rows
    ]
    feature_times = [
        float(row["timing"]["charged_feature_summary_milliseconds"]) for row in rows
    ]
    plain_feature_times = [
        float(row["timing"]["plain_active_feature_summary_milliseconds"])
        for row in rows
    ]
    charged_overheads = [
        float(
            row["timing"]["conservative_instrumentation_overhead_milliseconds"]
        )
        for row in rows
    ]
    plain_total = sum(plain_times)
    result = {
        "schema_version": 1,
        "experiment_type": "exact_river_shadow_regret_probe",
        "status": "development_only_causal_feature_measurement",
        "config": {
            "active_solver": "dcfr",
            "shadow_regret_variant": "cfr_plus",
            "checkpoint": checkpoint,
            "paired_order": "alternated by regenerated context index",
            "feature_cost_charged": True,
        },
        "source_provenance": source_provenance,
        "counts": {
            "contexts": len(rows),
            "groups": len({row["group_id"] for row in rows}),
            "active_tree_traversals_per_context": checkpoint * 2,
            "extra_shadow_tree_traversals": 0,
        },
        "correctness": {
            "maximum_active_accumulator_difference": maximum_active_difference,
            "all_source_active_features_reproduced": True,
            "all_context_provenance_reproduced": True,
            "standalone_cfr_plus_equivalence_claimed": False,
        },
        "timing": {
            "plain_solver_total_milliseconds": plain_total,
            "shadowed_solver_total_milliseconds": sum(shadow_times),
            "plain_active_feature_summary_total_milliseconds": sum(
                plain_feature_times
            ),
            "feature_summary_total_milliseconds": sum(feature_times),
            "conservative_instrumentation_overhead_total_milliseconds": sum(
                charged_overheads
            ),
            "shadowed_to_plain_solver_ratio": (
                sum(shadow_times) / plain_total if plain_total > 0.0 else None
            ),
            "conservative_overhead_fraction_of_plain_probe": (
                sum(charged_overheads) / plain_total if plain_total > 0.0 else None
            ),
            "mean_conservative_overhead_milliseconds": mean(charged_overheads),
            "median_conservative_overhead_milliseconds": median(charged_overheads),
        },
        "interpretation_warnings": [
            "The shadow uses DCFR-generated instantaneous regret deltas; it is not a standalone CFR+ solve.",
            "Wall-clock deltas are noisy. Conservative per-context charging floors negative paired deltas at zero.",
            "The probe reads no equilibrium or future label when constructing its online feature.",
        ],
        "records": rows,
    }
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checkpoint", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = args.source.read_bytes()
    source = json.loads(raw)
    result = run_river_shadow_probe(
        source,
        checkpoint=args.checkpoint,
        source_provenance={
            "path": str(args.source.resolve()),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
    )
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "river shadow probe: "
        f"contexts={result['counts']['contexts']}, "
        f"overhead={result['timing']['conservative_overhead_fraction_of_plain_probe']:.3%}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
