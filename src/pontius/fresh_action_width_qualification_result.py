"""Rebind the committed ADR-0323 qualification result without solving again.

The value-owning runner was invoked once.  This module treats its committed
canonical artifact as evidence, independently reconstructs every value-free
request identity and conservative endpoint calculation, and exposes only the
qualified development panel plus immutable diagnostics.  It has no solver or
action-emission path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from .certified_reduced_sizing_consumer_v2 import (
    ADR0321_CONSUMER_PROTOCOL_SHA256,
    _bind_request,
    canonical_lf_source_sha256,
)
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    ADR0323_OPPORTUNITY_FLOOR,
    ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
    ActionWidthQualificationClassification,
    CertifiedChipValueInterval,
    QualifiedActionWidthDevelopmentPanel,
    _canonical_sha256,
    certified_full_minus_subset_regret,
    classify_action_width_opportunity,
    qualification_requests_for_context,
    verify_adr0324_structure_source_and_pool,
)
from .fresh_action_width_qualification_seal import (
    ADR0323_QUALIFICATION_SCHEDULE_SHA256,
    ADR0323_QUALIFICATION_SOURCE_MANIFEST,
)


ADR0323_QUALIFICATION_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-development-qualification-v1.json"
)
ADR0323_QUALIFICATION_ARTIFACT_BYTES = 95_083
ADR0323_QUALIFICATION_ARTIFACT_SHA256 = (
    "dc46a433dec0973ef5e4603df255a8ce1ec94751dc5ada9c9f0122de0550cd60"
)
ADR0323_QUALIFICATION_PAYLOAD_SHA256 = (
    "e1fbda599e9a665549e58c49564786cac0fb2bde62f8657328dacf2791490404"
)
ADR0323_QUALIFICATION_RESULT_SHA256 = (
    "d8bcf79a08eed1af6fece257b4917424e71123574c4a99b858c7a7e93cf2a7f5"
)
ADR0323_QUALIFIED_PANEL_SHA256 = (
    "7757bfb37bc28f4a23707f9b4dfae9401ffb0afa016e87890d18a18117c66792"
)
ADR0323_QUALIFIED_POOL_INDICES = (
    0,
    6,
    11,
    14,
    19,
    20,
    23,
    25,
    27,
    28,
    29,
    32,
    42,
    45,
    49,
    50,
)
ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS = (
    "2295eed510ec65330be1a24bed9793815f89fdc4d51d5fd5bbfc4a87e1358f2d",
    "6bf64f6279863129582d9bb30a8c3a35a0486e32f3489bc19d7178645d44438e",
    "9e5bf22b3ac720343d4b1d9f0fee32ace7daaa52709a54b7ff9f77023c12986b",
    "219485a14c683c117ad730ee6ab8012e1469635c10a7ea69069282711238a279",
    "90169c1299ef8341d2ef410bfa0c7e0091e46b54986175e48a30ac554072eded",
    "6c3dbdc6af712481cc410d741a6ef56ff65294de383eab6b92961a362aa8553b",
    "c869307d6c27813e152cda2f83305088cefbe316b379e8cf3117d7a157bbc324",
    "f8eb3f5c91f02acd603555a7284a53a469d5dd5967c04d5454beb542e4ae0627",
    "eaf791bd1f30f5ba2e123b2d3156db598ede8d93f1d45423c4628307e5bf50d1",
    "17d2b3f3e5f35284abfb6925a2320843ae2ba911c06edcde8fefe8005fa82b3e",
    "89b97312cf27bb51eedda5e39f4a988a008cbe7e37b700a34a5e4f23b6fac702",
    "bb777f04e813f46d54ad46559d5254e13459a659fa8343020040fee5689bfb8a",
    "cf9c2923225f4bda87a53b90a5f40e081ea1c6b2bb3160aafcd02ca4ca0a77ac",
    "da2df45ca9bfcd2425d601aad3da8c89e94edb650d9bc0aad2671596291b19dc",
    "eabbfc86e7d8366c0a7154e151598b16ab6b37b1f12578c9c5d68631caef5a93",
    "f8d82c440396455495fb0fec77e098519c5adaa46e57a6e3c87e47d436c283f7",
)

_EXPECTED_TOP_LEVEL_KEYS = {
    "digest",
    "elapsed_seconds",
    "observations",
    "panel",
    "pool_sha256",
    "public_call_count",
    "qualification_source_sha256",
    "qualified_indices",
    "result_type",
    "schedule_sha256",
    "stop_reason",
}
_EXPECTED_OBSERVATION_KEYS = {
    "classification",
    "context_index",
    "context_semantic_digest",
    "full",
    "regret",
    "width_two",
}
_EXPECTED_ARM_KEYS = {
    "consumer_protocol_sha256",
    "consumer_source_sha256",
    "gap_hex",
    "legal_raise_set_sha256",
    "linear_program_sha256",
    "lower_hex",
    "public_calls",
    "public_state_sha256",
    "raise_to_totals",
    "request_sha256",
    "signed_gap_hex",
    "upper_hex",
}
_EXPECTED_REGRET_KEYS = {
    "nonnegative_lower_hex",
    "nonnegative_upper_hex",
    "signed_lower_hex",
    "signed_upper_hex",
}


@dataclass(frozen=True, slots=True)
class RetainedActionWidthQualificationObservation:
    context_index: int
    context_semantic_digest: str
    classification: ActionWidthQualificationClassification
    full_lower_chips: float
    full_upper_chips: float
    width_two_lower_chips: float
    width_two_upper_chips: float
    regret_lower_chips: float
    regret_upper_chips: float


@dataclass(frozen=True, slots=True)
class RetainedActionWidthQualificationResult:
    artifact_sha256: str
    payload_sha256: str
    qualification_result_sha256: str
    panel: QualifiedActionWidthDevelopmentPanel
    observations: tuple[RetainedActionWidthQualificationObservation, ...]
    public_highs_ds_invocation_count: int
    observed_elapsed_seconds: float


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[2] / ADR0323_QUALIFICATION_ARTIFACT_RELATIVE_PATH


def _require_exact_keys(value: object, expected: set[str], *, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} fields differ from the committed schema")
    return value


def _require_float_hex(value: object, *, label: str) -> float:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a float hex string")
    try:
        decoded = float.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{label} is not a float hex string") from error
    if not isfinite(decoded) or decoded.hex() != value:
        raise ValueError(f"{label} is not a canonical finite float hex string")
    return decoded


def _accepted_digest_payload(
    arm: dict[str, object],
    *,
    bet_increments: tuple[int, ...],
) -> dict[str, object]:
    return {
        "bet_increments": bet_increments,
        "certified_gap_hex": arm["gap_hex"],
        "certified_upper_hex": arm["upper_hex"],
        "consumer_protocol_sha256": arm["consumer_protocol_sha256"],
        "consumer_source_sha256": arm["consumer_source_sha256"],
        "feasible_lower_hex": arm["lower_hex"],
        "legal_raise_set_sha256": arm["legal_raise_set_sha256"],
        "linear_program_sha256": arm["linear_program_sha256"],
        "public_call_count": arm["public_calls"],
        "public_state_sha256": arm["public_state_sha256"],
        "raise_to_totals": tuple(arm["raise_to_totals"]),
        "request_sha256": arm["request_sha256"],
        "signed_gap_hex": arm["signed_gap_hex"],
    }


def qualification_result_protocol_sha256() -> str:
    return _canonical_sha256(
        {
            "artifact_bytes": ADR0323_QUALIFICATION_ARTIFACT_BYTES,
            "artifact_sha256": ADR0323_QUALIFICATION_ARTIFACT_SHA256,
            "context_semantic_digests": ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
            "opened_context_count": 51,
            "panel_sha256": ADR0323_QUALIFIED_PANEL_SHA256,
            "payload_sha256": ADR0323_QUALIFICATION_PAYLOAD_SHA256,
            "pool_indices": ADR0323_QUALIFIED_POOL_INDICES,
            "public_call_count": 102,
            "qualification_result_sha256": ADR0323_QUALIFICATION_RESULT_SHA256,
            "version": "adr0326-action-width-qualification-artifact-protocol-v1",
        }
    )


def verify_adr0326_qualification_result_source_and_dependencies() -> str:
    from .fresh_action_width_qualification_result_seal import (
        ADR0326_QUALIFICATION_RESULT_PROTOCOL_SHA256,
        ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST,
    )

    source_root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(source_root / name)
        for name in ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0326 qualification-result source closure drifted")
    if qualification_result_protocol_sha256() != (
        ADR0326_QUALIFICATION_RESULT_PROTOCOL_SHA256
    ):
        raise RuntimeError("ADR-0326 qualification-result protocol drifted")
    return actual["fresh_action_width_qualification_result.py"]


def verify_adr0323_qualification_result_artifact(
    path: Path | None = None,
) -> RetainedActionWidthQualificationResult:
    """Verify and rebind every retained result field without invoking a solver."""

    verify_adr0326_qualification_result_source_and_dependencies()
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0323_QUALIFICATION_ARTIFACT_BYTES:
        raise ValueError("ADR-0323 qualification artifact byte count drifted")
    if hashlib.sha256(raw).hexdigest() != ADR0323_QUALIFICATION_ARTIFACT_SHA256:
        raise ValueError("ADR-0323 qualification artifact SHA-256 drifted")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValueError("ADR-0323 qualification artifact must have one final LF")
    payload = raw[:-1]
    if hashlib.sha256(payload).hexdigest() != ADR0323_QUALIFICATION_PAYLOAD_SHA256:
        raise ValueError("ADR-0323 qualification payload SHA-256 drifted")
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ADR-0323 qualification artifact is not canonical JSON") from error
    if json.dumps(
        decoded,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii") != payload:
        raise ValueError("ADR-0323 qualification artifact is not canonical ASCII JSON")
    root = _require_exact_keys(decoded, _EXPECTED_TOP_LEVEL_KEYS, label="result")

    pool = verify_adr0324_structure_source_and_pool()
    if root["result_type"] != "ActionWidthQualificationCampaignResult":
        raise ValueError("ADR-0323 qualification result type drifted")
    if root["pool_sha256"] != pool.digest:
        raise ValueError("ADR-0323 qualification result belongs to another pool")
    if root["schedule_sha256"] != ADR0323_QUALIFICATION_SCHEDULE_SHA256:
        raise ValueError("ADR-0323 qualification schedule identity drifted")
    qualification_source = ADR0323_QUALIFICATION_SOURCE_MANIFEST[
        "fresh_action_width_qualification.py"
    ]
    if root["qualification_source_sha256"] != qualification_source:
        raise ValueError("ADR-0323 qualification source identity drifted")
    if root["stop_reason"] != "target_reached":
        raise ValueError("ADR-0323 qualification did not retain the target stop")
    elapsed = root["elapsed_seconds"]
    if not isinstance(elapsed, float) or not isfinite(elapsed) or elapsed <= 0.0:
        raise ValueError("ADR-0323 observed elapsed time is invalid")

    raw_observations = root["observations"]
    if not isinstance(raw_observations, list) or len(raw_observations) != 51:
        raise ValueError("ADR-0323 qualification must retain its 51-context prefix")
    retained: list[RetainedActionWidthQualificationObservation] = []
    digest_observations: list[dict[str, object]] = []
    qualified_indices: list[int] = []
    public_calls = 0
    for index, raw_observation in enumerate(raw_observations):
        observation = _require_exact_keys(
            raw_observation,
            _EXPECTED_OBSERVATION_KEYS,
            label=f"observation {index}",
        )
        context = pool.contexts[index]
        if (
            observation["context_index"] != index
            or observation["context_semantic_digest"] != context.semantic_digest
        ):
            raise ValueError(f"observation {index} differs from its sealed context")
        full_task, width_two_task = qualification_requests_for_context(
            context=context,
            context_index=index,
        )
        digest_arms: dict[str, dict[str, object]] = {}
        intervals: dict[str, CertifiedChipValueInterval] = {}
        for arm_name, task in (
            ("full", full_task),
            ("width_two", width_two_task),
        ):
            arm = _require_exact_keys(
                observation[arm_name],
                _EXPECTED_ARM_KEYS,
                label=f"observation {index} {arm_name}",
            )
            bound = _bind_request(task.request)
            expected_identity = {
                "consumer_protocol_sha256": ADR0321_CONSUMER_PROTOCOL_SHA256,
                "consumer_source_sha256": ADR0323_QUALIFICATION_SOURCE_MANIFEST[
                    "certified_reduced_sizing_consumer_v2.py"
                ],
                "legal_raise_set_sha256": bound.legal_raise_set_sha256,
                "linear_program_sha256": bound.linear_program_sha256,
                "public_calls": 1,
                "public_state_sha256": bound.public_state_sha256,
                "raise_to_totals": [value.chips for value in bound.legal_raise_to_totals],
                "request_sha256": bound.request_sha256,
            }
            if any(arm[key] != value for key, value in expected_identity.items()):
                raise ValueError(
                    f"observation {index} {arm_name} identity or call count drifted"
                )
            lower = _require_float_hex(
                arm["lower_hex"],
                label=f"observation {index} {arm_name} lower",
            )
            upper = _require_float_hex(
                arm["upper_hex"],
                label=f"observation {index} {arm_name} upper",
            )
            signed_gap = _require_float_hex(
                arm["signed_gap_hex"],
                label=f"observation {index} {arm_name} signed gap",
            )
            gap = _require_float_hex(
                arm["gap_hex"],
                label=f"observation {index} {arm_name} gap",
            )
            if lower > upper or signed_gap != upper - lower or gap != max(0.0, signed_gap):
                raise ValueError(f"observation {index} {arm_name} endpoint gap drifted")
            intervals[arm_name] = CertifiedChipValueInterval(lower, upper)
            digest_arms[arm_name] = _accepted_digest_payload(
                arm,
                bet_increments=tuple(
                    value.chips for value in bound.reduced_bet_increments
                ),
            )
            public_calls += 1

        regret = certified_full_minus_subset_regret(
            full=intervals["full"],
            subset=intervals["width_two"],
            reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
        )
        raw_regret = _require_exact_keys(
            observation["regret"],
            _EXPECTED_REGRET_KEYS,
            label=f"observation {index} regret",
        )
        expected_regret_hex = {
            "nonnegative_lower_hex": regret.nonnegative_lower_chips.hex(),
            "nonnegative_upper_hex": regret.nonnegative_upper_chips.hex(),
            "signed_lower_hex": regret.signed_lower_chips.hex(),
            "signed_upper_hex": regret.signed_upper_chips.hex(),
        }
        if raw_regret != expected_regret_hex:
            raise ValueError(f"observation {index} regret endpoint direction drifted")
        classification = classify_action_width_opportunity(
            regret=regret,
            payoff_span_chips=context.payoff_span_chips,
            opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
            ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
        )
        if observation["classification"] != classification.value:
            raise ValueError(f"observation {index} classification drifted")
        if classification is ActionWidthQualificationClassification.QUALIFYING:
            qualified_indices.append(index)
        retained.append(
            RetainedActionWidthQualificationObservation(
                context_index=index,
                context_semantic_digest=context.semantic_digest,
                classification=classification,
                full_lower_chips=intervals["full"].lower_chips,
                full_upper_chips=intervals["full"].upper_chips,
                width_two_lower_chips=intervals["width_two"].lower_chips,
                width_two_upper_chips=intervals["width_two"].upper_chips,
                regret_lower_chips=regret.nonnegative_lower_chips,
                regret_upper_chips=regret.nonnegative_upper_chips,
            )
        )
        digest_observations.append(
            {
                "classification": classification.value,
                "context_index": index,
                "context_semantic_digest": context.semantic_digest,
                "full": digest_arms["full"],
                "regret": expected_regret_hex,
                "width_two": digest_arms["width_two"],
            }
        )

    if tuple(qualified_indices) != ADR0323_QUALIFIED_POOL_INDICES:
        raise ValueError("ADR-0323 qualified indices drifted")
    if tuple(root["qualified_indices"]) != ADR0323_QUALIFIED_POOL_INDICES:
        raise ValueError("ADR-0323 retained qualified indices drifted")
    if root["public_call_count"] != public_calls or public_calls != 102:
        raise ValueError("ADR-0323 public HiGHS-DS call count drifted")

    rebuilt_result_digest = _canonical_sha256(
        {
            "consumer_failure": None,
            "observations": tuple(digest_observations),
            "pool_sha256": pool.digest,
            "qualified_indices": ADR0323_QUALIFIED_POOL_INDICES,
            "qualification_source_sha256": qualification_source,
            "schedule_sha256": ADR0323_QUALIFICATION_SCHEDULE_SHA256,
            "stop_reason": "target_reached",
            "version": "adr0323-action-width-qualification-result-v1",
        }
    )
    if (
        rebuilt_result_digest != ADR0323_QUALIFICATION_RESULT_SHA256
        or root["digest"] != rebuilt_result_digest
    ):
        raise ValueError("ADR-0323 qualification result digest drifted")

    panel = QualifiedActionWidthDevelopmentPanel(
        pool_sha256=pool.digest,
        qualification_result_sha256=rebuilt_result_digest,
        pool_indices=ADR0323_QUALIFIED_POOL_INDICES,
        context_semantic_digests=ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
    )
    expected_panel_payload = {
        "context_semantic_digests": list(ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS),
        "digest": ADR0323_QUALIFIED_PANEL_SHA256,
        "pool_indices": list(ADR0323_QUALIFIED_POOL_INDICES),
        "qualification_result_sha256": rebuilt_result_digest,
    }
    if root["panel"] != expected_panel_payload or panel.digest != ADR0323_QUALIFIED_PANEL_SHA256:
        raise ValueError("ADR-0323 qualified panel identity drifted")
    if tuple(pool.contexts[index].semantic_digest for index in panel.pool_indices) != (
        ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS
    ):
        raise ValueError("ADR-0323 qualified panel no longer rebinds to its pool")

    return RetainedActionWidthQualificationResult(
        artifact_sha256=ADR0323_QUALIFICATION_ARTIFACT_SHA256,
        payload_sha256=ADR0323_QUALIFICATION_PAYLOAD_SHA256,
        qualification_result_sha256=rebuilt_result_digest,
        panel=panel,
        observations=tuple(retained),
        public_highs_ds_invocation_count=public_calls,
        observed_elapsed_seconds=elapsed,
    )


__all__ = [
    "ADR0323_QUALIFICATION_ARTIFACT_BYTES",
    "ADR0323_QUALIFICATION_ARTIFACT_RELATIVE_PATH",
    "ADR0323_QUALIFICATION_ARTIFACT_SHA256",
    "ADR0323_QUALIFICATION_PAYLOAD_SHA256",
    "ADR0323_QUALIFICATION_RESULT_SHA256",
    "ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS",
    "ADR0323_QUALIFIED_PANEL_SHA256",
    "ADR0323_QUALIFIED_POOL_INDICES",
    "RetainedActionWidthQualificationObservation",
    "RetainedActionWidthQualificationResult",
    "qualification_result_protocol_sha256",
    "verify_adr0323_qualification_result_artifact",
    "verify_adr0326_qualification_result_source_and_dependencies",
]
