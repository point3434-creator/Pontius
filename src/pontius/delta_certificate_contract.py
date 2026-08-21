"""Fail-closed semantics for local policy-delta certificate experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from .evaluation import Policy
from .game import Action


@dataclass(frozen=True, slots=True)
class EnvelopeProbeClassification:
    cap_passes: bool
    objective_passes: bool
    classification: str
    cap_excesses: tuple[float, ...]
    normalized_objective_reduction: float


@dataclass(frozen=True, slots=True)
class DeltaCertificateScope:
    episode_blueprint_policy_sha256: str
    public_root_sha256: str
    payoff_model_sha256: str
    belief_sha256: str
    deployed_prefix_sha256: str
    candidate_policy_sha256: str
    verifier_implementation_sha256: str
    source_provenance_sha256: str
    blueprint_deviation_gains: tuple[float, ...]
    cap_vector: tuple[float, ...]
    raw_guard: float
    payoff_span: float
    payoff_span_source: str
    certificate_epoch: int
    expires_after_public_transition: bool = True
    selected_candidate_becomes_anchor: bool = False
    cumulative_episode_safety_claim: bool = False


@dataclass(frozen=True, slots=True)
class AtomicPolicyDelta:
    information_key: str
    changed_entries: int
    maximum_absolute_probability_delta: float


def classify_envelope_probe(
    blueprint_deviation_gains: Sequence[float],
    candidate_deviation_gains: Sequence[float],
    *,
    blueprint_nash_conv: float,
    candidate_nash_conv: float,
    raw_guard: float,
    payoff_span: float,
) -> EnvelopeProbeClassification:
    """Classify cap and scalar-objective conditions independently."""

    baseline = tuple(float(value) for value in blueprint_deviation_gains)
    candidate = tuple(float(value) for value in candidate_deviation_gains)
    values = (*baseline, *candidate, blueprint_nash_conv, candidate_nash_conv,
              raw_guard, payoff_span)
    if not baseline or len(baseline) != len(candidate):
        raise ValueError("probe requires equal nonempty deviation-gain vectors")
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("probe values must be finite")
    if any(value < 0.0 for value in (*baseline, *candidate)):
        raise ValueError("deviation gains must be nonnegative")
    if raw_guard < 0.0 or payoff_span <= 0.0:
        raise ValueError("guard must be nonnegative and payoff span positive")
    excesses = tuple(
        new - old - raw_guard
        for old, new in zip(baseline, candidate, strict=True)
    )
    cap_passes = max(excesses) <= 0.0
    objective_passes = candidate_nash_conv < blueprint_nash_conv - raw_guard
    classification = {
        (True, True): "admissible_improvement",
        (False, True): "cap_only_rejection",
        (True, False): "objective_only_rejection",
        (False, False): "cap_and_objective_rejection",
    }[(cap_passes, objective_passes)]
    return EnvelopeProbeClassification(
        cap_passes=cap_passes,
        objective_passes=objective_passes,
        classification=classification,
        cap_excesses=excesses,
        normalized_objective_reduction=(
            float(blueprint_nash_conv) - float(candidate_nash_conv)
        ) / float(payoff_span),
    )


def geometric_halving_scales(*, numerical_floor: float = 1e-10) -> tuple[float, ...]:
    """Return the shared line-search grid down to the inherited Float64 floor."""

    if not math.isfinite(numerical_floor) or not 0.0 < numerical_floor <= 1.0:
        raise ValueError("numerical floor must be finite and in (0, 1]")
    scales = []
    value = 1.0
    while value >= numerical_floor:
        scales.append(value)
        value *= 0.5
    return tuple(scales)


def atomic_policy_manifest(
    blueprint: Mapping[str, Mapping[Action, float]],
    candidate: Mapping[str, Mapping[Action, float]],
    *,
    tolerance: float = 0.0,
) -> tuple[AtomicPolicyDelta, ...]:
    """Describe the exact information-set acceptance units in a policy delta."""

    if not math.isfinite(tolerance) or tolerance < 0.0 or tolerance > 1e-10:
        raise ValueError("policy-delta tolerance exceeds the inherited numerical floor")
    _validate_matching_policies(blueprint, candidate)
    atoms = []
    for key in sorted(blueprint):
        differences = tuple(
            abs(float(candidate[key][action]) - float(blueprint[key][action]))
            for action in blueprint[key]
        )
        changed = sum(value > tolerance for value in differences)
        if changed:
            atoms.append(
                AtomicPolicyDelta(
                    information_key=key,
                    changed_entries=changed,
                    maximum_absolute_probability_delta=max(differences),
                )
            )
    return tuple(atoms)


def interpolate_policy_atoms(
    blueprint: Mapping[str, Mapping[Action, float]],
    candidate: Mapping[str, Mapping[Action, float]],
    information_keys: Sequence[str],
    *,
    scale: float,
) -> Policy:
    """Apply selected source-relative atomic directions at one common scale."""

    _validate_matching_policies(blueprint, candidate)
    if not math.isfinite(scale) or not 0.0 <= scale <= 1.0:
        raise ValueError("atomic interpolation scale must be in [0, 1]")
    selected = tuple(information_keys)
    if len(selected) != len(set(selected)) or set(selected) - set(blueprint):
        raise ValueError("atomic information-set selection is invalid")
    selected_set = set(selected)
    result: Policy = {}
    for key in sorted(blueprint):
        if key in selected_set:
            result[key] = {
                action: (
                    (1.0 - scale) * float(blueprint[key][action])
                    + scale * float(candidate[key][action])
                )
                for action in blueprint[key]
            }
        else:
            result[key] = {
                action: float(probability)
                for action, probability in blueprint[key].items()
            }
    return result


def interaction_residual(
    blueprint_values: Sequence[float],
    first_values: Sequence[float],
    second_values: Sequence[float],
    union_values: Sequence[float],
) -> tuple[float, ...]:
    """Return exact inclusion-exclusion residuals for a recertified union."""

    rows = tuple(tuple(float(value) for value in row) for row in (
        blueprint_values, first_values, second_values, union_values,
    ))
    if not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("interaction vectors must have equal nonzero length")
    if any(not math.isfinite(value) for row in rows for value in row):
        raise ValueError("interaction vectors must be finite")
    base, first, second, union = rows
    return tuple(
        joined - left - right + origin
        for origin, left, right, joined in zip(base, first, second, union, strict=True)
    )


def validate_certificate_scope(
    scope: DeltaCertificateScope,
    expected: DeltaCertificateScope,
) -> None:
    """Reject stale, reanchored, span-mutated, or otherwise mismatched scope."""

    if scope != expected:
        differing = tuple(
            key for key, value in asdict(scope).items()
            if value != asdict(expected)[key]
        )
        raise ValueError(f"delta certificate scope mismatch: {differing!r}")
    if scope.payoff_span_source != "layout.game.payoff_span":
        raise ValueError("payoff span is not bound to the constructed game")
    if len(scope.blueprint_deviation_gains) != len(scope.cap_vector):
        raise ValueError("certificate cap vector has the wrong width")
    expected_caps = tuple(value + scope.raw_guard for value in scope.blueprint_deviation_gains)
    if scope.cap_vector != expected_caps:
        raise ValueError("certificate caps do not derive from the immutable blueprint")
    if not scope.expires_after_public_transition:
        raise ValueError("delta certificate must expire after a public transition")
    if scope.selected_candidate_becomes_anchor or scope.cumulative_episode_safety_claim:
        raise ValueError("delta certificate cannot reanchor or claim composition")


def certificate_scope_digest(scope: DeltaCertificateScope) -> str:
    """Return the canonical identity of every certificate-bound field."""

    payload = asdict(scope)
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def deadline_fallback_required(
    *, elapsed_ms: float, decision_budget_ms: float = 15000.0,
    emission_reserve_ms: float,
) -> bool:
    """Fail closed when a new certificate cannot be emitted inside the deadline."""

    values = (elapsed_ms, decision_budget_ms, emission_reserve_ms)
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("deadline values must be finite and nonnegative")
    if emission_reserve_ms >= decision_budget_ms:
        raise ValueError("emission reserve must leave a positive decision window")
    return elapsed_ms + emission_reserve_ms >= decision_budget_ms


def _validate_matching_policies(
    blueprint: Mapping[str, Mapping[Action, float]],
    candidate: Mapping[str, Mapping[Action, float]],
) -> None:
    if set(blueprint) != set(candidate) or not blueprint:
        raise ValueError("policies must have the same nonempty information schema")
    for key in blueprint:
        if set(blueprint[key]) != set(candidate[key]) or not blueprint[key]:
            raise ValueError("policies must have matching nonempty action schemas")
        for row in (blueprint[key], candidate[key]):
            values = tuple(float(value) for value in row.values())
            if any(not math.isfinite(value) or value < 0.0 for value in values):
                raise ValueError("policy probabilities must be finite and nonnegative")
            if abs(math.fsum(values) - 1.0) > 1e-12:
                raise ValueError("policy probabilities must sum to one")
