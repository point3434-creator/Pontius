"""Pre-rank axis-order correction for the frozen ADR-0076 audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .factorized_belief import FactorizedCardBelief as _FactorizedCardBelief
from .river import HoleCards
from . import real_policy_representation_audit as _base_audit

_ROOT = Path(__file__).parents[2]
_BASE_CONFIG = (
    _ROOT / "experiments" / "configs" / "real-policy-representation-audit-v1.json"
)
_V2_CONFIG = (
    _ROOT / "experiments" / "configs" / "real-policy-representation-audit-v2.json"
)
_SOURCE_ARTIFACT = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_BASE_IMPLEMENTATION = _ROOT / "src" / "pontius" / "real_policy_representation_audit.py"
_IMPLEMENTATION = Path(__file__)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonicalized_factorized_belief(
    *,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    mixture_weights: object,
    unary_weights: tuple[object, ...],
    board: tuple[int, ...],
) -> _FactorizedCardBelief:
    """Sort hands within each seat and carry their unary columns with them."""

    if len(hands_by_player) != len(unary_weights):
        raise ValueError("one unary table is required for every hand axis")
    canonical_axes = tuple(tuple(sorted(hands)) for hands in hands_by_player)
    canonical_unaries = []
    for hands, canonical, supplied in zip(
        hands_by_player, canonical_axes, unary_weights, strict=True
    ):
        hand_to_column = {hand: index for index, hand in enumerate(hands)}
        if len(hand_to_column) != len(hands):
            raise ValueError("factor-belief hand axes must not contain duplicates")
        values = np.asarray(supplied, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != len(hands):
            raise ValueError("factor-belief unary table does not match its hand axis")
        canonical_unaries.append(
            np.ascontiguousarray(
                values[:, [hand_to_column[hand] for hand in canonical]],
                dtype=np.float64,
            )
        )
    return _FactorizedCardBelief(
        hands_by_player=canonical_axes,
        mixture_weights=mixture_weights,
        unary_weights=tuple(canonical_unaries),
        board=board,
    )


def parse_real_policy_representation_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the additive pre-rank correction and immutable base audit."""

    required = {
        "evidence_stage",
        "expected_source_artifact_sha256",
        "expected_base_config_sha256",
        "expected_base_implementation_sha256",
        "expected_correction_implementation_sha256",
        "axis_order_correction",
        "failed_attempt",
        "base_workload_and_gates_unchanged",
        "representation_results_observed_before_correction",
    }
    if set(config) != required:
        raise ValueError("ADR-0077 correction config fields differ from the freeze")
    frozen = {
        "evidence_stage": "preregistered_pre_rank_axis_order_correction",
        "expected_source_artifact_sha256": (
            "cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e"
        ),
        "expected_base_config_sha256": (
            "fa13bc219050ca885b176fe024b2af3ce2940c40806626b7be8dcd1eb991c22f"
        ),
        "expected_base_implementation_sha256": (
            "584548f9de392cd6691db710b2b95b17c574e363369b7c802048bad660ed6351"
        ),
        "axis_order_correction": (
            "stable_lexicographic_hand_order_with_matching_unary_column_permutation"
        ),
        "failed_attempt": "hand_axis_mismatch_before_first_root_composition",
        "base_workload_and_gates_unchanged": True,
        "representation_results_observed_before_correction": False,
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("ADR-0077 correction contract differs from the freeze")
    if config["expected_correction_implementation_sha256"] != _sha256(
        _IMPLEMENTATION
    ):
        raise ValueError("ADR-0077 correction implementation hash mismatch")
    if config["expected_source_artifact_sha256"] != _sha256(_SOURCE_ARTIFACT):
        raise ValueError("canonical source artifact hash mismatch")
    if config["expected_base_config_sha256"] != _sha256(_BASE_CONFIG):
        raise ValueError("immutable ADR-0076 config hash mismatch")
    if config["expected_base_implementation_sha256"] != _sha256(
        _BASE_IMPLEMENTATION
    ):
        raise ValueError("immutable ADR-0076 implementation hash mismatch")
    return dict(config)


def run_real_policy_representation_audit_v2(
    config: dict[str, Any],
) -> dict[str, object]:
    """Run ADR-0076 unchanged after canonicalizing source belief hand order."""

    parsed = parse_real_policy_representation_v2_config(config)
    base_config = json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    previous_constructor = _base_audit.FactorizedCardBelief
    _base_audit.FactorizedCardBelief = _canonicalized_factorized_belief  # type: ignore[assignment]
    try:
        result = _base_audit.run_real_policy_representation_audit(base_config)
    finally:
        _base_audit.FactorizedCardBelief = previous_constructor

    inherited_config = result["config"]
    result.update(
        {
            "schema_version": 2,
            "experiment_type": (
                "real_policy_representation_and_clean_fringe_audit_axis_corrected"
            ),
            "status": "preregistered_pre_rank_axis_order_correction_executed",
            "config": parsed,
            "base_config": inherited_config,
            "config_sha256": _sha256(_V2_CONFIG),
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "base_config_sha256": _sha256(_BASE_CONFIG),
            "base_implementation_sha256": _sha256(_BASE_IMPLEMENTATION),
            "axis_order_correction": {
                "hands": "stable lexicographic order independently within each seat",
                "weights": "matching permutation of every mixture-component unary column",
                "seat_order": "unchanged",
                "source_policy": "unchanged canonical serialized table",
            },
        }
    )
    limitations = list(result["limitations"])
    limitations.append(
        "ADR-0076's first execution stopped at hand-axis provenance before any root rank; ADR-0077 changes only within-seat axis order and matching unary columns."
    )
    result["limitations"] = limitations
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_real_policy_representation_audit_v2(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "real-policy representation v2: "
        f"ranks={result['counts']['rank_rows']}, "
        f"candidates={result['counts']['candidate_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
