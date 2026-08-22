"""Read-only timing analysis of the rejected ADR-0277 invocation.

This module never evaluates a policy or reconstructs a redacted master point.
It verifies the sealed ADR-0278 artifact and reprices only timing terms that
were already opened by that invocation.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).parents[2]
_SEALED_RESULT = _ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.json"
_EXPECTED_RESULT_SHA256 = "d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7"
_EXPECTED_CHECKPOINT_SHA256 = "a94e66fda42258cc4494cd3d026de7b9c97b8757da40f4e560e5ab5e232360e0"
_EXPECTED_CONFIG_SHA256 = "4ee7f77a84d7638f304dbd7a8c51aea6eb5b6c0e7e9f9adbd0bc6eb4985b760a"
_EXPECTED_IMPLEMENTATION_SHA256 = "db4cd478aaa95cee48fc50e6b75dbc36b1ed3bffe3d630f773c31f08904d2a1b"
_EXPECTED_INVENTORY_SHA256 = "52a847ab3fb3d2e3066ba7dd0808674e66a0bff805df7c9ee1db7820cc5aadf6"

_STREET_BUDGET_MS = 15_000.0
_SECOND_MASTER_FLOOR_MS = 500.0
_PROOF_RESERVE_MS = 1_250.0
_RETREAT_ENVELOPE_RESERVE_MS = 50.0
_EMISSION_RESERVE_MS = 1_000.0


@dataclass(frozen=True, slots=True)
class _ArmTiming:
    target_id: str
    acting_player: int
    arm_name: str
    warm_step_ms: float
    initial_row_ms: float
    source_oracle_ms: float
    fixed_response_row_ms: float
    first_master_ms: float
    frozen_proxy_ms: float


def _finite_nonnegative(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"sealed timing {label} is not numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"sealed timing {label} is invalid")
    return result


def _arm_timing(
    target: Mapping[str, Any],
    arm_name: str,
) -> _ArmTiming:
    target_id = target.get("target_id")
    acting_player = target.get("acting_player")
    if not isinstance(target_id, str) or not target_id:
        raise ValueError("sealed timing target identifier is invalid")
    if (
        isinstance(acting_player, bool)
        or not isinstance(acting_player, int)
        or acting_player not in range(6)
    ):
        raise ValueError("sealed timing acting player is invalid")
    arms = target.get("arms")
    if not isinstance(arms, Mapping) or set(arms) != {"one_size", "two_size"}:
        raise ValueError("sealed timing target arms differ")
    arm = arms[arm_name]
    if not isinstance(arm, Mapping) or arm.get("arm") != arm_name:
        raise ValueError("sealed timing arm label differs")
    pass_rows = arm.get("initial_pass_rows")
    if not isinstance(pass_rows, list) or len(pass_rows) != 11:
        raise ValueError("sealed timing initial pass inventory differs")
    fixed_rows = [
        row for row in pass_rows if isinstance(row, Mapping) and row.get("kind") == "fixed_response"
    ]
    profile_rows = [
        row for row in pass_rows if isinstance(row, Mapping) and row.get("kind") == "profile"
    ]
    if len(fixed_rows) != 5 or len(profile_rows) != 6:
        raise ValueError("sealed timing pass roles differ")
    fixed_response_ms = math.fsum(
        _finite_nonnegative(row.get("wall_ms"), label="fixed response pass") for row in fixed_rows
    )
    master = arm.get("master")
    capacity = arm.get("capacity")
    warm = arm.get("warm_step")
    if not all(isinstance(value, Mapping) for value in (master, capacity, warm)):
        raise ValueError("sealed timing arm telemetry is incomplete")
    return _ArmTiming(
        target_id=target_id,
        acting_player=acting_player,
        arm_name=arm_name,
        warm_step_ms=_finite_nonnegative(warm.get("wall_ms"), label="warm step"),
        initial_row_ms=_finite_nonnegative(
            arm.get("initial_row_ms"),
            label="initial rows",
        ),
        source_oracle_ms=_finite_nonnegative(
            arm.get("source_oracle_timing_ms"),
            label="source oracle",
        ),
        fixed_response_row_ms=fixed_response_ms,
        first_master_ms=_finite_nonnegative(
            master.get("solve_ms"),
            label="first master",
        ),
        frozen_proxy_ms=_finite_nonnegative(
            capacity.get("complete_one_round_proxy_ms"),
            label="frozen proxy",
        ),
    )


def _proxy(
    row: _ArmTiming,
    *,
    charge_warm: bool,
    charge_initial_rows: bool,
) -> float:
    warm_ms = row.warm_step_ms if charge_warm else 0.0
    endpoint_ms = (
        max(row.source_oracle_ms, row.warm_step_ms) if charge_warm else row.source_oracle_ms
    )
    return math.fsum(
        (
            warm_ms,
            row.initial_row_ms if charge_initial_rows else 0.0,
            row.first_master_ms,
            2.0 * endpoint_ms,
            row.fixed_response_row_ms,
            max(row.first_master_ms, _SECOND_MASTER_FLOOR_MS),
            _PROOF_RESERVE_MS,
            _RETREAT_ENVELOPE_RESERVE_MS,
            _EMISSION_RESERVE_MS,
        )
    )


def _no_warm_proxy(
    row: _ArmTiming,
    *,
    initial_row_ms: float,
    source_oracle_ms: float,
    fixed_response_row_ms: float,
) -> float:
    for label, value in (
        ("initial overlay", initial_row_ms),
        ("source overlay", source_oracle_ms),
        ("fixed-response overlay", fixed_response_row_ms),
    ):
        _finite_nonnegative(value, label=label)
    return math.fsum(
        (
            initial_row_ms,
            row.first_master_ms,
            2.0 * source_oracle_ms,
            fixed_response_row_ms,
            max(row.first_master_ms, _SECOND_MASTER_FLOOR_MS),
            _PROOF_RESERVE_MS,
            _RETREAT_ENVELOPE_RESERVE_MS,
            _EMISSION_RESERVE_MS,
        )
    )


def _summary(rows: Sequence[tuple[int, float]]) -> dict[str, Any]:
    if len(rows) != 36:
        raise ValueError("counterfactual timing summary requires 36 targets")
    values = [value for _, value in rows]
    by_position = {
        acting_player: [value for seat, value in rows if seat == acting_player]
        for acting_player in range(6)
    }
    if any(len(values_at_position) != 6 for values_at_position in by_position.values()):
        raise ValueError("counterfactual timing position crossing differs")
    return {
        "minimum_ms": min(values),
        "median_ms": statistics.median(values),
        "maximum_ms": max(values),
        "fit_count": sum(value <= _STREET_BUDGET_MS for value in values),
        "complete_positions": [
            acting_player
            for acting_player, position_values in by_position.items()
            if all(value <= _STREET_BUDGET_MS for value in position_values)
        ],
        "maximum_by_position_ms": {
            str(acting_player): max(position_values)
            for acting_player, position_values in by_position.items()
        },
    }


def _distribution(values: Sequence[float]) -> dict[str, float]:
    if len(values) != 36 or any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("sealed component distribution is invalid")
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def _validate_evidence_boundary(result: Mapping[str, Any]) -> None:
    if result.get("passed") is not False:
        raise ValueError("sealed capacity invocation is not the rejected result")
    if result.get("decision") != "reject_pre_bet_action_width_capacity_execution":
        raise ValueError("sealed capacity decision differs")
    if result.get("checkpoint_sha256") != _EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("sealed capacity checkpoint digest differs")
    if result.get("config_sha256") != _EXPECTED_CONFIG_SHA256:
        raise ValueError("sealed capacity config digest differs")
    if result.get("implementation_sha256") != _EXPECTED_IMPLEMENTATION_SHA256:
        raise ValueError("sealed capacity implementation digest differs")
    if result.get("inventory_sha256") != _EXPECTED_INVENTORY_SHA256:
        raise ValueError("sealed capacity inventory digest differs")
    if result.get("actual_emitted_policy") != "immutable_one_size_blueprint_only":
        raise ValueError("sealed capacity external policy differs")
    if result.get("strategy_population_claim") is not None:
        raise ValueError("sealed capacity artifact opened a population claim")
    methodology = result.get("methodology")
    gates = result.get("gates")
    if not isinstance(methodology, Mapping) or not isinstance(gates, Mapping):
        raise ValueError("sealed capacity evidence boundary is incomplete")
    expected_zero = {
        "master_candidate_endpoint_evaluations": 0,
        "retreat_or_certificate_evaluations": 0,
        "strategy_quality_rows_serialized": 0,
        "candidate_policies_emitted": 0,
    }
    if any(methodology.get(key) != value for key, value in expected_zero.items()):
        raise ValueError("sealed capacity artifact opened a forbidden label")
    failed_leaf_gates = [key for key, value in gates.items() if key != "passed" and value is False]
    if failed_leaf_gates != ["resource_caps"]:
        raise ValueError("sealed capacity failed-leaf inventory differs")


def analyze_h32_pre_bet_work_reduction(
    result_path: Path = _SEALED_RESULT,
) -> dict[str, Any]:
    """Verify and reprice the sealed timing matrix without opening new labels."""

    raw = result_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != _EXPECTED_RESULT_SHA256:
        raise ValueError("sealed action-width capacity result digest differs")
    decoded = json.loads(raw)
    if not isinstance(decoded, Mapping):
        raise ValueError("sealed action-width capacity result is not an object")
    _validate_evidence_boundary(decoded)
    runtime_rows = decoded.get("runtime_rows")
    if not isinstance(runtime_rows, list) or len(runtime_rows) != 36:
        raise ValueError("sealed action-width runtime matrix differs")

    timings = {
        arm_name: tuple(_arm_timing(target, arm_name) for target in runtime_rows)
        for arm_name in ("one_size", "two_size")
    }
    maximum_formula_error = max(
        abs(_proxy(row, charge_warm=True, charge_initial_rows=True) - row.frozen_proxy_ms)
        for arm_rows in timings.values()
        for row in arm_rows
    )
    if maximum_formula_error > 1e-9:
        raise ValueError("sealed capacity timing formula does not reconstruct")

    arm_reports = {}
    for arm_name, arm_rows in timings.items():
        frozen = [(row.acting_player, row.frozen_proxy_ms) for row in arm_rows]
        warm_removed = [
            (
                row.acting_player,
                _proxy(row, charge_warm=False, charge_initial_rows=True),
            )
            for row in arm_rows
        ]
        exact_initial_cache = [
            (
                row.acting_player,
                _proxy(row, charge_warm=True, charge_initial_rows=False),
            )
            for row in arm_rows
        ]
        combined = [
            (
                row.acting_player,
                _proxy(row, charge_warm=False, charge_initial_rows=False),
            )
            for row in arm_rows
        ]
        arm_reports[arm_name] = {
            "components_ms": {
                "warm_step": _distribution([row.warm_step_ms for row in arm_rows]),
                "initial_eleven_rows": _distribution([row.initial_row_ms for row in arm_rows]),
                "source_all_seat_oracle": _distribution([row.source_oracle_ms for row in arm_rows]),
                "five_fixed_response_rows": _distribution(
                    [row.fixed_response_row_ms for row in arm_rows]
                ),
                "first_master": _distribution([row.first_master_ms for row in arm_rows]),
                "warm_removal_proxy_savings": _distribution(
                    [
                        frozen_row[1] - removed_row[1]
                        for frozen_row, removed_row in zip(
                            frozen,
                            warm_removed,
                            strict=True,
                        )
                    ]
                ),
            },
            "scenarios": {
                "frozen": _summary(frozen),
                "remove_nonfeeding_warm_step": _summary(warm_removed),
                "zero_cost_exact_initial_row_cache_hit": _summary(exact_initial_cache),
                "remove_warm_plus_zero_cost_exact_initial_row_cache_hit": _summary(combined),
            },
        }

    paired = []
    for one, two in zip(timings["one_size"], timings["two_size"], strict=True):
        if one.target_id != two.target_id or one.acting_player != two.acting_player:
            raise ValueError("sealed one-size/two-size target pairing differs")
        paired.append((one, two))
    paired_diagnostics = {}
    for label, getter in (
        ("initial_eleven_rows", lambda row: row.initial_row_ms),
        ("five_fixed_response_rows", lambda row: row.fixed_response_row_ms),
        ("source_all_seat_oracle", lambda row: row.source_oracle_ms),
    ):
        deltas = [getter(two) - getter(one) for one, two in paired]
        ratios = [getter(two) / getter(one) for one, two in paired]
        paired_diagnostics[label] = {
            "two_minus_one_ms": _distribution(deltas),
            "two_over_one": _distribution(ratios),
            "all_two_size_slower": all(delta > 0.0 for delta in deltas),
        }

    optimistic_initial_overlay = []
    optimistic_initial_and_cut_overlay = []
    optimistic_all_contraction_overlay = []
    for one, two in paired:
        initial_delta = max(0.0, two.initial_row_ms - one.initial_row_ms)
        fixed_delta = max(
            0.0,
            two.fixed_response_row_ms - one.fixed_response_row_ms,
        )
        source_delta = max(0.0, two.source_oracle_ms - one.source_oracle_ms)
        optimistic_initial_overlay.append(
            (
                two.acting_player,
                _no_warm_proxy(
                    two,
                    initial_row_ms=initial_delta,
                    source_oracle_ms=two.source_oracle_ms,
                    fixed_response_row_ms=two.fixed_response_row_ms,
                ),
            )
        )
        optimistic_initial_and_cut_overlay.append(
            (
                two.acting_player,
                _no_warm_proxy(
                    two,
                    initial_row_ms=initial_delta,
                    source_oracle_ms=two.source_oracle_ms,
                    fixed_response_row_ms=fixed_delta,
                ),
            )
        )
        optimistic_all_contraction_overlay.append(
            (
                two.acting_player,
                _no_warm_proxy(
                    two,
                    initial_row_ms=initial_delta,
                    source_oracle_ms=source_delta,
                    fixed_response_row_ms=fixed_delta,
                ),
            )
        )
    arm_reports["two_size"]["unmeasured_overlay_arithmetic"] = {
        "assumption": (
            "One-size work is available at zero live cost and each added-column "
            "cost equals the observed paired full-layout timing difference."
        ),
        "initial_rows_only_after_warm_removal": _summary(optimistic_initial_overlay),
        "initial_and_future_cut_rows_after_warm_removal": _summary(
            optimistic_initial_and_cut_overlay
        ),
        "all_contractions_after_warm_removal": _summary(optimistic_all_contraction_overlay),
        "evidence_status": (
            "optimistic counterfactual only; paired differences do not isolate an "
            "incremental overlay primitive"
        ),
    }

    return {
        "schema_version": 1,
        "source_result_sha256": digest,
        "evidence_boundary": {
            "rejected_invocation_only": True,
            "failed_leaf_gate": "resource_caps/campaign_duration",
            "master_candidate_endpoint_evaluations": 0,
            "retreat_or_certificate_evaluations": 0,
            "strategy_quality_rows_serialized": 0,
            "candidate_policies_emitted": 0,
            "actual_emitted_policy": "immutable_one_size_blueprint_only",
        },
        "street_budget_ms": _STREET_BUDGET_MS,
        "maximum_frozen_formula_error_ms": maximum_formula_error,
        "arms": arm_reports,
        "paired_diagnostics": paired_diagnostics,
        "hypothesis_limits": {
            "warm_step": (
                "Static runner dataflow proves solver state is telemetry-only after "
                "the measured step; the repricing still requires a successor schedule."
            ),
            "exact_initial_row_cache": (
                "The zero-cost hit is conditional arithmetic, not a measured cache. "
                "A lawful entry must bind full policy, belief, continuation topology, "
                "action schema, acting/payoff roles, fixed-response tapes, and primitive "
                "identity, then charge lookup and validation on-clock."
            ),
            "incremental_bet6_overlay": (
                "Paired deltas are confounded full-layout measurements. The optimistic "
                "arithmetic is reported as a falsifier, but no added-column primitive "
                "or overlay timing was measured, so no savings are claimed."
            ),
            "anytime_separation": (
                "The sealed invocation evaluated zero candidate endpoints or cuts, so "
                "its matrix cannot quantify an anytime separation schedule."
            ),
        },
    }
