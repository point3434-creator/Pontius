"""Solver-free owner and corrected assessment for ADR-0351.

The ADR-0350 runner is permanently closed.  This module reads only its exact
retained JSON artifact, verifies the source-sealed closure, rebinds the exact
fan partitions, tapes, affine rows, schedule, envelope algebra, controls, and
timing, then applies the post-invocation semantic correction: any source
selector tie makes the certificate window zero before slope is considered.

It imports no runner, game, evaluator, optimizer, selector, action, or write
path.  The finite fan map is retained; the recorded integration authorization
is rejected because four reachable source-tie sections received nonzero v1
certificate windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from math import gcd, isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


ADR0351_INVOCATION_SOURCE_COMMIT = (
    "fbbf49b261703add2cf4103409e957a89a15cc3b"
)
ADR0351_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/legal-responder-raise-h4-selector-window-v1.json"
)
ADR0351_ARTIFACT_BYTES = 1_493_122
ADR0351_ARTIFACT_SHA256 = (
    "7a1d08f1245b93b2a880f92af6c737677b7cd85b5c59a05205a8263adafcbee7"
)
ADR0351_CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-responder-raise-h4-selector-window-v1.json"
)
ADR0351_CONFIG_SHA256 = (
    "08d8d8d9975edd8147065893ef81f0f597fe1a687a5c5a5905fe36e2fec9f866"
)
ADR0351_ROOT_PUBLIC_STATE_SHA256 = (
    "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
)
ADR0351_PUBLIC_SCHEMA_SHA256 = (
    "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
)
ADR0351_GAME_STRUCTURAL_SHA256 = (
    "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
)
ADR0351_GAME_PROVENANCE_SHA256 = (
    "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
)
ADR0351_SOURCE_POLICY_SHA256 = (
    "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a"
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "docs/decisions/ADR-0349-retain-and-seal-the-legal-h4-row-growth-result.md"
        ),
        "expected_parent_artifact_sha256": (
            "experiments/results/legal-responder-raise-h4-row-growth-v1.json"
        ),
        "expected_parent_result_owner_sha256": (
            "src/pontius/legal_responder_raise_h4_row_growth_result.py"
        ),
        "expected_legal_kernel_sha256": "src/pontius/no_limit_betting.py",
        "expected_legal_game_sha256": "src/pontius/legal_river_continuation.py",
        "expected_fixture_sha256": "src/pontius/legal_h4_selector_fixture.py",
        "expected_direction_compiler_sha256": (
            "src/pontius/legal_h4_selector_directions.py"
        ),
        "expected_cfr_sha256": "src/pontius/cfr.py",
        "expected_generation_primitive_sha256": (
            "src/pontius/one_seat_convex_generation.py"
        ),
        "expected_evaluation_sha256": "src/pontius/evaluation.py",
        "expected_exact_selector_oracle_sha256": (
            "src/pontius/exact_selector_window_oracle.py"
        ),
        "expected_exact_fan_sha256": "src/pontius/exact_selector_fan.py",
        "expected_selector_window_sha256": "src/pontius/selector_window.py",
        "expected_fan_controls_sha256": "src/pontius/selector_fan_controls.py",
        "expected_exact_control_test_sha256": "tests/test_exact_selector_fan.py",
        "expected_implementation_sha256": (
            "src/pontius/legal_responder_raise_h4_selector_window.py"
        ),
        "expected_control_test_sha256": (
            "tests/test_legal_responder_raise_h4_selector_window.py"
        ),
    }
)
_EXPECTED_SOURCE_HASHES = MappingProxyType(
    {
        "expected_parent_decision_sha256": (
            "61d393fdd4d5d9a9a99d34be62276b6ca967aefc77a17d8807a7606ce8b02620"
        ),
        "expected_parent_artifact_sha256": (
            "eb35843218741096f214a6c341a0762b8f1cca09a81a1fdce1db21eaa9fc60b8"
        ),
        "expected_parent_result_owner_sha256": (
            "b300b5b5a022a698c7bce2c77a99212da272ecaa50e1964eac76a21c392add53"
        ),
        "expected_legal_kernel_sha256": (
            "9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396"
        ),
        "expected_legal_game_sha256": (
            "4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250"
        ),
        "expected_fixture_sha256": (
            "978777a66aa22fe6b460695b9c418194b0b780e76953998e33226c2f4245da95"
        ),
        "expected_direction_compiler_sha256": (
            "0542639a491417be78415ee3019e864d256ff460adae5ae1ddc75f9e4dceaf88"
        ),
        "expected_cfr_sha256": (
            "d0e3c8fbc983a9863ec3feaa47cf1b932942623dd9f03eaed88d6e356e34051e"
        ),
        "expected_generation_primitive_sha256": (
            "a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231"
        ),
        "expected_evaluation_sha256": (
            "c362fb1e294bb8bac722adf479df4d2f27ddcf8c26390c037ec88f858702cda8"
        ),
        "expected_exact_selector_oracle_sha256": (
            "5156d8155e017c44587f900a126ddcb67f13b701e643550ad668cee06d5e2e3f"
        ),
        "expected_exact_fan_sha256": (
            "03ddc731c1d866b728d24b999be92df89d203a14e4872da5c88a9298fa20deee"
        ),
        "expected_selector_window_sha256": (
            "81189f1e4d3639e44f87fe6234ec8ec3872451de53356ee137cb84bdb860aa4b"
        ),
        "expected_fan_controls_sha256": (
            "f8d24a6323eec4aeba0a7b72d0f47142dc61a62628a9aac4f6a6786cf253e975"
        ),
        "expected_exact_control_test_sha256": (
            "df3ddf35675ada59a85edade058ec7c0e71f2e6a28b902170782b3b5272f744c"
        ),
        "expected_implementation_sha256": (
            "9a252e13bc51b3f713a05c9b4444ad40c544797b5119c1d97d7bb85dd693f070"
        ),
        "expected_control_test_sha256": (
            "3ce5a2a92b339048ef187a6ec695ee9547b2837627262f09b7ebfe16fa55ae46"
        ),
    }
)
_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "aggregate",
        "config_sha256",
        "decision",
        "direction_descriptors",
        "directions",
        "engineered_controls",
        "environment",
        "fan_semantics",
        "game_provenance_sha256",
        "game_structural_sha256",
        "gates",
        "implementation_sha256",
        "limitations",
        "methodology",
        "passed",
        "public_schema_sha256",
        "quality_rows_serialized",
        "root_public_state_sha256",
        "schedule",
        "schema_version",
        "source_policy_sha256",
        "status",
        "strategy_labels_generated",
        "strategy_quality_claim",
        "total_seconds",
    }
)
_EXPECTED_GATE_KEYS = frozenset(
    {
        "affine_row_activation",
        "clean_git_state",
        "conservative_total_tape_window",
        "direction_identities",
        "direction_inventory",
        "engineered_crossing_identity",
        "engineered_tie_nonempty",
        "exact_tape_optimality",
        "exact_three_state_partition",
        "finite",
        "fixed_tape_value_identity",
        "fixture_identity",
        "float_exact_response_values",
        "legacy_breakpoint_identity",
        "parent_pass",
        "passed",
        "reachable_identity_is_reporting_only",
        "scientific_payload_bytes",
        "selector_call_sites",
        "subject_selector_wall",
        "total_and_reachable_identity_columns",
        "total_time",
        "unique_selector_agreement",
        "upper_envelope_direction",
        "zero_allowance_breakpoint_values",
    }
)
_STATES = frozenset({"fixed", "tie_unresolved", "switched"})
_SOURCE_TAPE_SHA256S = (
    "83b57620097d496624aabfa49fdba1ab64ccb5cd519a9daf20130ade55f7e908",
    "778a91ab318ea0c94d1baa8dcfe9481ed6155604cc964a6b014720b0b20877f8",
)
_DIRECTION_DESCRIPTORS = (
    {
        "label": "regret_vertex::p0:raise-to-2/p1:raise-to-4",
        "direction_class": "one_step_dcfr_regret_vertex",
        "changed_public_histories": ["p0:raise-to-2/p1:raise-to-4"],
        "endpoint_policy_sha256": (
            "bd9533ae86809b0cbcaeb643c3b1503794f6e7812c0b48950849bb976a7e4f9d"
        ),
    },
    {
        "label": "regret_vertex::p0:raise-to-3/p1:raise-to-4",
        "direction_class": "one_step_dcfr_regret_vertex",
        "changed_public_histories": ["p0:raise-to-3/p1:raise-to-4"],
        "endpoint_policy_sha256": (
            "e849f04dbc967c6422a719cf430d4e5a646ba59a6bb00a0c9b9e17ff27892209"
        ),
    },
    {
        "label": "regret_vertex::root",
        "direction_class": "one_step_dcfr_regret_vertex",
        "changed_public_histories": ["root"],
        "endpoint_policy_sha256": (
            "3372dd9b65180afdbb2c3260d43f559366c77017bfd9c498371406aa7d001e2e"
        ),
    },
    {
        "label": "lp_proposed::adr0349_restricted_master",
        "direction_class": "retained_restricted_master_proposal",
        "changed_public_histories": ["root"],
        "endpoint_policy_sha256": (
            "0f9be1f884cb09eb8318a88a1548afb402ec256e8fa52f19118c64569fe7658b"
        ),
    },
)
_EXPECTED_SOURCE_UPPERS = (
    (Fraction(1), Fraction(15, 19)),
    (Fraction(1), Fraction(139, 163)),
    (Fraction(1), Fraction(1)),
    (Fraction(1), Fraction(1)),
)
_EXPECTED_CELL_SHA256S = (
    (
        (_SOURCE_TAPE_SHA256S[0],),
        (
            _SOURCE_TAPE_SHA256S[1],
            "d7876ab38f7e6127132bce3bbd6638ec04112a47ee6a474206be1b349a6081bc",
        ),
    ),
    (
        (_SOURCE_TAPE_SHA256S[0],),
        (
            _SOURCE_TAPE_SHA256S[1],
            "229985e35c07d2c85bcf4d393ce4f919f1584a34c4a15dcd32d9277748d4f45e",
        ),
    ),
    (
        (_SOURCE_TAPE_SHA256S[0],),
        (
            _SOURCE_TAPE_SHA256S[1],
            "d13e5ec55d6f5ae56da97bf99aca7629f8cb1471887c90d76914dd752a6b9064",
        ),
    ),
    (
        (_SOURCE_TAPE_SHA256S[0],),
        (
            _SOURCE_TAPE_SHA256S[1],
            "cbbf05b85462131028b75649e583df5a48f3ad680ed8109b852b161b211a7cd0",
        ),
    ),
)
_EXPECTED_MEASURES = (
    ((Fraction(0), Fraction(1), Fraction(0)), (Fraction(15, 19), Fraction(0), Fraction(4, 19))),
    ((Fraction(0), Fraction(1), Fraction(0)), (Fraction(139, 163), Fraction(0), Fraction(24, 163))),
    ((Fraction(0), Fraction(1), Fraction(0)), (Fraction(1), Fraction(0), Fraction(0))),
    ((Fraction(0), Fraction(1), Fraction(0)), (Fraction(1), Fraction(0), Fraction(0))),
)

_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0351_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0351_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0351_ARTIFACT_SHA256,
    "cell_sha256s": [[list(player) for player in direction] for direction in _EXPECTED_CELL_SHA256S],
    "config_sha256": ADR0351_CONFIG_SHA256,
    "corrected_certificate_pass": False,
    "direction_descriptors": list(_DIRECTION_DESCRIPTORS),
    "game_provenance_sha256": ADR0351_GAME_PROVENANCE_SHA256,
    "game_structural_sha256": ADR0351_GAME_STRUCTURAL_SHA256,
    "invocation_source_commit": ADR0351_INVOCATION_SOURCE_COMMIT,
    "public_schema_sha256": ADR0351_PUBLIC_SCHEMA_SHA256,
    "recorded_source_tie_window_violations": 4,
    "root_public_state_sha256": ADR0351_ROOT_PUBLIC_STATE_SHA256,
    "source_hashes": dict(_EXPECTED_SOURCE_HASHES),
    "source_policy_sha256": ADR0351_SOURCE_POLICY_SHA256,
    "source_tape_sha256s": list(_SOURCE_TAPE_SHA256S),
    "successor_authorized": False,
    "version": "adr0351-legal-h4-selector-fan-result-protocol-v1",
}
ADR0351_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0351_RESULT_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _RESULT_PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key in ADR-0351 artifact: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(token: str) -> None:
    raise ValueError(f"nonfinite JSON number in ADR-0351 artifact: {token}")


def _decode_strict_object(raw: bytes, *, source: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid ADR-0351 JSON in {source}") from exc
    if not isinstance(decoded, dict):
        raise TypeError(f"ADR-0351 JSON in {source} must be an object")
    return decoded


def _raw_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"ADR-0351 required path is unavailable: {path}")
    return sha256(path.read_bytes()).hexdigest()


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    return sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _require_digest(value: Any, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"ADR-0351 {field} is not a lowercase SHA-256")
    return value


def _fraction(record: Any, *, field: str) -> Fraction:
    if not isinstance(record, dict) or set(record) != {"numerator", "denominator"}:
        raise TypeError(f"ADR-0351 {field} is not an exact fraction")
    numerator = record["numerator"]
    denominator = record["denominator"]
    if (
        isinstance(numerator, bool)
        or isinstance(denominator, bool)
        or not isinstance(numerator, int)
        or not isinstance(denominator, int)
        or denominator <= 0
        or gcd(abs(numerator), denominator) != 1
    ):
        raise ValueError(
            f"ADR-0351 {field} is not reduced with positive denominator"
        )
    return Fraction(numerator, denominator)


def _hex_float(value: Any, *, field: str) -> float:
    if not isinstance(value, str):
        raise TypeError(f"ADR-0351 {field} must be hexadecimal Float64")
    try:
        parsed = float.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"ADR-0351 {field} is not hexadecimal Float64") from exc
    if not isfinite(parsed) or parsed.hex() != value:
        raise ValueError(f"ADR-0351 {field} is not canonical finite Float64")
    return parsed


def _finite_nonnegative(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"ADR-0351 {field} must be numeric")
    result = float(value)
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"ADR-0351 {field} must be finite and nonnegative")
    return result


def _verify_tape(
    tape: Any,
    digest: Any,
    *,
    field: str,
    expected_width: int | None = None,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(tape, list):
        raise TypeError(f"ADR-0351 {field} tape must be a list")
    if expected_width is not None and len(tape) != expected_width:
        raise ValueError(f"ADR-0351 {field} tape width drifted")
    rows = []
    for item in tape:
        if not isinstance(item, dict) or set(item) != {"information_key", "action"}:
            raise ValueError(f"ADR-0351 {field} tape item drifted")
        key = item["information_key"]
        action = item["action"]
        if not isinstance(key, str) or not key or not isinstance(action, str) or not action:
            raise ValueError(f"ADR-0351 {field} tape text drifted")
        rows.append((key, action))
    if rows != sorted(rows) or len({key for key, _ in rows}) != len(rows):
        raise ValueError(f"ADR-0351 {field} tape ordering drifted")
    if not isinstance(digest, str) or _canonical_sha256(tape) != digest:
        raise ValueError(f"ADR-0351 {field} tape digest drifted")
    return tuple(rows)


def _verify_tie_rows(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(f"ADR-0351 {field} tie rows must be a list")
    keys = []
    for row in value:
        if not isinstance(row, dict) or set(row) != {
            "information_key",
            "maximizing_actions",
        }:
            raise ValueError(f"ADR-0351 {field} tie schema drifted")
        key = row["information_key"]
        actions = row["maximizing_actions"]
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(actions, list)
            or len(actions) < 2
            or any(not isinstance(action, str) or not action for action in actions)
            or len(set(actions)) != len(actions)
        ):
            raise ValueError(f"ADR-0351 {field} tie witness drifted")
        keys.append(key)
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ValueError(f"ADR-0351 {field} tie ordering drifted")
    return tuple(keys)


@dataclass(frozen=True, slots=True)
class RetainedLegalH4SelectorFanResult:
    """Immutable corrected interpretation of ADR-0350's finite artifact."""

    record: Mapping[str, Any]
    source_commit: str
    total_seconds: float
    selector_seconds: float
    sections: int
    source_tie_sections: int
    recorded_source_tie_window_violations: int
    corrected_certificate_pass: bool
    successor_authorized: bool

    def __post_init__(self) -> None:
        if not isinstance(self.record, Mapping) or not self.record:
            raise TypeError("retained h4 selector-fan record must be a mapping")
        if self.source_commit != ADR0351_INVOCATION_SOURCE_COMMIT:
            raise ValueError("retained h4 selector-fan source commit drifted")
        if not 0.0 <= self.selector_seconds <= self.total_seconds <= 120.0:
            raise ValueError("retained h4 selector-fan timing is invalid")
        if (
            self.sections,
            self.source_tie_sections,
            self.recorded_source_tie_window_violations,
        ) != (8, 4, 4):
            raise ValueError("retained h4 selector-fan dimensions drifted")
        if self.corrected_certificate_pass or self.successor_authorized:
            raise ValueError("ADR-0351 may not authorize the rejected successor")


def verify_adr0351_result_source_and_dependencies() -> str:
    """Verify this owner and every ADR-0350 source-sealed input."""

    from .legal_responder_raise_h4_selector_fan_result_seal import (
        ADR0351_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0351_RESULT_SOURCE_MANIFEST,
    )

    module_path = Path(__file__).resolve()
    actual_module = _canonical_lf_sha256(module_path)
    if ADR0351_RESULT_SOURCE_MANIFEST != {module_path.name: actual_module}:
        raise RuntimeError("ADR-0351 result-owner source closure drifted")
    if sealed_protocol != ADR0351_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0351 result protocol drifted")
    config_path = _ROOT / ADR0351_CONFIG_RELATIVE_PATH
    if _raw_sha256(config_path) != ADR0351_CONFIG_SHA256:
        raise RuntimeError("ADR-0351 source-sealed config drifted")
    config = _decode_strict_object(config_path.read_bytes(), source=str(config_path))
    for field, relative_path in _SOURCE_PATHS.items():
        expected = _EXPECTED_SOURCE_HASHES[field]
        if config.get(field) != expected:
            raise RuntimeError(f"ADR-0351 config identity drifted: {field}")
        if _raw_sha256(_ROOT / relative_path) != expected:
            raise RuntimeError(f"ADR-0351 source input drifted: {relative_path}")
    return actual_module


def _expected_state(
    ties: tuple[str, ...],
    response_digest: str,
    source_digest: str,
) -> str:
    if ties:
        return "tie_unresolved"
    return "fixed" if response_digest == source_digest else "switched"


def _verify_fan(
    fan: Any,
    *,
    direction_index: int,
    target_player: int,
) -> tuple[
    tuple[tuple[str, str], ...],
    dict[str, tuple[Fraction, Fraction]],
    list[tuple[Fraction, str, str]],
]:
    expected_keys = {
        "cells",
        "legacy_source_breakpoint",
        "measure",
        "points",
        "segments",
        "source_cell_upper",
        "source_tape",
        "source_tape_sha256",
        "tie_points",
    }
    if not isinstance(fan, dict) or set(fan) != expected_keys:
        raise ValueError("ADR-0351 fan schema drifted")
    source_digest = _require_digest(
        fan["source_tape_sha256"], field="fan.source_tape_sha256"
    )
    if source_digest != _SOURCE_TAPE_SHA256S[target_player]:
        raise ValueError("ADR-0351 source response tape identity drifted")
    source_tape = _verify_tape(
        fan["source_tape"],
        source_digest,
        field="fan.source",
        expected_width=12,
    )
    upper = _fraction(fan["source_cell_upper"], field="fan.source_cell_upper")
    legacy = _fraction(
        fan["legacy_source_breakpoint"],
        field="fan.legacy_source_breakpoint",
    )
    if upper != legacy or upper != _EXPECTED_SOURCE_UPPERS[direction_index][target_player]:
        raise ValueError("ADR-0351 exact legacy breakpoint identity drifted")

    cells = fan["cells"]
    expected_digests = _EXPECTED_CELL_SHA256S[direction_index][target_player]
    if not isinstance(cells, list) or len(cells) != len(expected_digests):
        raise ValueError("ADR-0351 fan cell inventory drifted")
    cell_bounds: dict[str, tuple[Fraction, Fraction]] = {}
    boundaries = {Fraction(0), Fraction(1)}
    for index, (cell, expected_digest) in enumerate(zip(cells, expected_digests, strict=True)):
        if not isinstance(cell, dict) or set(cell) != {
            "lower",
            "response_tape",
            "response_tape_sha256",
            "upper",
        }:
            raise ValueError("ADR-0351 fan cell schema drifted")
        digest = _require_digest(
            cell["response_tape_sha256"],
            field=f"fan.cell[{index}].response_tape_sha256",
        )
        if digest != expected_digest or digest in cell_bounds:
            raise ValueError("ADR-0351 fan cell tape inventory drifted")
        _verify_tape(
            cell["response_tape"],
            digest,
            field=f"fan.cell[{index}]",
            expected_width=12,
        )
        lower = _fraction(cell["lower"], field=f"fan.cell[{index}].lower")
        cell_upper = _fraction(cell["upper"], field=f"fan.cell[{index}].upper")
        if not Fraction(0) <= lower <= cell_upper <= 1:
            raise ValueError("ADR-0351 fan cell bounds drifted")
        cell_bounds[digest] = (lower, cell_upper)
        boundaries.update((lower, cell_upper))
    if source_digest not in cell_bounds or cell_bounds[source_digest][1] != upper:
        raise ValueError("ADR-0351 source cell is detached from its breakpoint")

    points = fan["points"]
    ordered_boundaries = sorted(boundaries)
    if not isinstance(points, list) or len(points) != len(ordered_boundaries):
        raise ValueError("ADR-0351 fan point inventory drifted")
    point_states: list[tuple[Fraction, str, str]] = []
    derived_total_tie_points = []
    derived_reachable_tie_points = []
    for index, (point, scale) in enumerate(zip(points, ordered_boundaries, strict=True)):
        if not isinstance(point, dict) or set(point) != {
            "reachable_state",
            "reachable_tape_sha256",
            "reachable_tie_information_sets",
            "response_tape_sha256",
            "scale",
            "total_state",
            "total_tie_information_sets",
        }:
            raise ValueError("ADR-0351 fan point schema drifted")
        if _fraction(point["scale"], field=f"fan.point[{index}].scale") != scale:
            raise ValueError("ADR-0351 fan point scale drifted")
        total_ties = tuple(point["total_tie_information_sets"])
        reachable_ties = tuple(point["reachable_tie_information_sets"])
        if (
            list(total_ties) != sorted(total_ties)
            or len(total_ties) != len(set(total_ties))
            or list(reachable_ties) != sorted(reachable_ties)
            or len(reachable_ties) != len(set(reachable_ties))
            or not set(reachable_ties) <= set(total_ties)
        ):
            raise ValueError("ADR-0351 fan point tie keys drifted")
        response_digest = _require_digest(
            point["response_tape_sha256"],
            field=f"fan.point[{index}].response_tape_sha256",
        )
        _require_digest(
            point["reachable_tape_sha256"],
            field=f"fan.point[{index}].reachable_tape_sha256",
        )
        total_state = point["total_state"]
        reachable_state = point["reachable_state"]
        if (
            response_digest not in cell_bounds
            or not cell_bounds[response_digest][0]
            <= scale
            <= cell_bounds[response_digest][1]
            or
            total_state
            != _expected_state(total_ties, response_digest, source_digest)
            or reachable_state not in _STATES
            or (reachable_state == "tie_unresolved") != bool(reachable_ties)
        ):
            raise ValueError("ADR-0351 fan point classification drifted")
        if total_state == "tie_unresolved":
            derived_total_tie_points.append(scale)
        if reachable_state == "tie_unresolved":
            derived_reachable_tie_points.append(scale)
        point_states.append((scale, total_state, reachable_state))

    segments = fan["segments"]
    if not isinstance(segments, list) or len(segments) != len(points) - 1:
        raise ValueError("ADR-0351 fan segment inventory drifted")
    derived_measures = {
        "total": {state: Fraction(0) for state in _STATES},
        "reachable": {state: Fraction(0) for state in _STATES},
    }
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or set(segment) != {
            "lower",
            "reachable_state",
            "reachable_tape_sha256",
            "reachable_tie_information_sets",
            "response_tape_sha256",
            "total_state",
            "total_tie_information_sets",
            "upper",
            "witness",
        }:
            raise ValueError("ADR-0351 fan segment schema drifted")
        lower = _fraction(segment["lower"], field=f"fan.segment[{index}].lower")
        segment_upper = _fraction(
            segment["upper"], field=f"fan.segment[{index}].upper"
        )
        witness = _fraction(
            segment["witness"], field=f"fan.segment[{index}].witness"
        )
        if (
            lower != ordered_boundaries[index]
            or segment_upper != ordered_boundaries[index + 1]
            or witness != (lower + segment_upper) / 2
        ):
            raise ValueError("ADR-0351 fan segment partition drifted")
        response_digest = _require_digest(
            segment["response_tape_sha256"],
            field=f"fan.segment[{index}].response_tape_sha256",
        )
        _require_digest(
            segment["reachable_tape_sha256"],
            field=f"fan.segment[{index}].reachable_tape_sha256",
        )
        total_ties = tuple(segment["total_tie_information_sets"])
        reachable_ties = tuple(segment["reachable_tie_information_sets"])
        total_state = segment["total_state"]
        reachable_state = segment["reachable_state"]
        if (
            list(total_ties) != sorted(total_ties)
            or list(reachable_ties) != sorted(reachable_ties)
            or not set(reachable_ties) <= set(total_ties)
            or response_digest not in cell_bounds
            or not cell_bounds[response_digest][0] <= witness <= cell_bounds[response_digest][1]
            or total_state
            != _expected_state(total_ties, response_digest, source_digest)
            or reachable_state not in _STATES
            or (reachable_state == "tie_unresolved") != bool(reachable_ties)
        ):
            raise ValueError("ADR-0351 fan segment classification drifted")
        width = segment_upper - lower
        derived_measures["total"][total_state] += width
        derived_measures["reachable"][reachable_state] += width

    measure = fan["measure"]
    if not isinstance(measure, dict) or set(measure) != {"total", "reachable"}:
        raise ValueError("ADR-0351 fan measure schema drifted")
    for view in ("total", "reachable"):
        if not isinstance(measure[view], dict) or set(measure[view]) != _STATES:
            raise ValueError("ADR-0351 fan state measure schema drifted")
        rebound = {
            state: _fraction(measure[view][state], field=f"fan.measure.{view}.{state}")
            for state in _STATES
        }
        if rebound != derived_measures[view] or sum(rebound.values(), Fraction(0)) != 1:
            raise ValueError("ADR-0351 fan measures do not rebind")
    expected_measure = _EXPECTED_MEASURES[direction_index][target_player]
    total_measure_tuple = tuple(
        derived_measures["total"][state]
        for state in ("fixed", "tie_unresolved", "switched")
    )
    if total_measure_tuple != expected_measure:
        raise ValueError("ADR-0351 retained fan geometry drifted")

    tie_points = fan["tie_points"]
    if not isinstance(tie_points, dict) or set(tie_points) != {"total", "reachable"}:
        raise ValueError("ADR-0351 fan tie-point schema drifted")
    for view, derived in (
        ("total", derived_total_tie_points),
        ("reachable", derived_reachable_tie_points),
    ):
        stored = [
            _fraction(value, field=f"fan.tie_points.{view}")
            for value in tie_points[view]
        ]
        if stored != derived:
            raise ValueError("ADR-0351 fan tie points do not rebind")
    return source_tape, cell_bounds, point_states


def _verify_row_library(
    rows: Any,
    *,
    cell_bounds: Mapping[str, tuple[Fraction, Fraction]],
) -> dict[str, tuple[Fraction, Fraction]]:
    if not isinstance(rows, list) or len(rows) != len(cell_bounds):
        raise ValueError("ADR-0351 affine-row inventory drifted")
    result: dict[str, tuple[Fraction, Fraction]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "active_cell_lower",
            "active_cell_upper",
            "deviation_gain_row_intercept",
            "deviation_gain_row_slope",
            "envelope_role",
            "profile_utility_intercept",
            "profile_utility_slope",
            "response_tape",
            "response_tape_sha256",
            "response_value_intercept",
            "response_value_slope",
        }:
            raise ValueError("ADR-0351 affine-row schema drifted")
        digest = row["response_tape_sha256"]
        _verify_tape(
            row["response_tape"],
            digest,
            field=f"row_library[{index}]",
            expected_width=12,
        )
        if digest not in cell_bounds or digest in result:
            raise ValueError("ADR-0351 affine-row tape inventory drifted")
        lower = _fraction(row["active_cell_lower"], field="row.active_cell_lower")
        upper = _fraction(row["active_cell_upper"], field="row.active_cell_upper")
        if (lower, upper) != cell_bounds[digest]:
            raise ValueError("ADR-0351 affine row detached from fan cell")
        response_intercept = _fraction(
            row["response_value_intercept"], field="row.response_intercept"
        )
        response_slope = _fraction(
            row["response_value_slope"], field="row.response_slope"
        )
        profile_intercept = _fraction(
            row["profile_utility_intercept"], field="row.profile_intercept"
        )
        profile_slope = _fraction(
            row["profile_utility_slope"], field="row.profile_slope"
        )
        gain_intercept = _fraction(
            row["deviation_gain_row_intercept"], field="row.gain_intercept"
        )
        gain_slope = _fraction(
            row["deviation_gain_row_slope"], field="row.gain_slope"
        )
        if (
            gain_intercept != response_intercept - profile_intercept
            or gain_slope != response_slope - profile_slope
            or row["envelope_role"]
            != "lower_bound_row_under_maximum_upper_envelope"
        ):
            raise ValueError("ADR-0351 affine gain-row algebra drifted")
        result[digest] = (gain_intercept, gain_slope)
    return result


def _fan_at_scale(
    fan: Mapping[str, Any],
    scale: Fraction,
) -> tuple[str, str, str, str]:
    for point in fan["points"]:
        if _fraction(point["scale"], field="fan.point.scale") == scale:
            return (
                point["total_state"],
                point["reachable_state"],
                point["response_tape_sha256"],
                point["reachable_tape_sha256"],
            )
    for segment in fan["segments"]:
        lower = _fraction(segment["lower"], field="fan.segment.lower")
        upper = _fraction(segment["upper"], field="fan.segment.upper")
        if lower < scale < upper:
            return (
                segment["total_state"],
                segment["reachable_state"],
                segment["response_tape_sha256"],
                segment["reachable_tape_sha256"],
            )
    raise ValueError("ADR-0351 schedule scale lies outside the exact fan")


def _verify_schedule(
    schedule: Any,
    *,
    fan: Mapping[str, Any],
    source_tape: tuple[tuple[str, str], ...],
    row_library: Mapping[str, tuple[Fraction, Fraction]],
) -> tuple[float, int, int, int]:
    if not isinstance(schedule, list) or len(schedule) != 17:
        raise ValueError("ADR-0351 production schedule width drifted")
    selector_seconds = 0.0
    source_tie = 0
    tie_window_violation = 0
    phantom_identity = 0
    source_digest = _canonical_sha256(
        [
            {"information_key": key, "action": action}
            for key, action in source_tape
        ]
    )
    profile_intercepts = set()
    profile_slopes = set()
    for row in fan.get("_row_records", []):
        profile_intercepts.add(_fraction(row["profile_utility_intercept"], field="profile"))
        profile_slopes.add(_fraction(row["profile_utility_slope"], field="profile"))
    if len(profile_intercepts) != 1 or len(profile_slopes) != 1:
        raise ValueError("ADR-0351 profile affine rows disagree")
    profile_intercept = next(iter(profile_intercepts))
    profile_slope = next(iter(profile_slopes))

    expected_schedule_keys = {
        "active_row_identity",
        "exact_response_tape",
        "exact_response_tape_sha256",
        "exact_response_value",
        "exact_ties",
        "fixed_tape_value_identity",
        "float_exact_response_value_error",
        "identity_columns",
        "production_response_tape",
        "production_response_tape_sha256",
        "production_response_value_hex",
        "production_selector_seconds",
        "production_tape_exactly_optimal",
        "reachable_response_tape",
        "reachable_response_tape_sha256",
        "reachable_state",
        "scale",
        "total_state",
        "unique_exact_selector_agreement",
        "upper_envelope_identity",
    }
    for index, row in enumerate(schedule):
        if not isinstance(row, dict) or set(row) != expected_schedule_keys:
            raise ValueError("ADR-0351 production schedule schema drifted")
        scale = _fraction(row["scale"], field=f"schedule[{index}].scale")
        if scale != Fraction(index, 16):
            raise ValueError("ADR-0351 production schedule scale drifted")
        exact_tape = _verify_tape(
            row["exact_response_tape"],
            row["exact_response_tape_sha256"],
            field=f"schedule[{index}].exact",
            expected_width=12,
        )
        production_tape = _verify_tape(
            row["production_response_tape"],
            row["production_response_tape_sha256"],
            field=f"schedule[{index}].production",
            expected_width=12,
        )
        reachable_tape = _verify_tape(
            row["reachable_response_tape"],
            row["reachable_response_tape_sha256"],
            field=f"schedule[{index}].reachable",
        )
        tie_keys = _verify_tie_rows(row["exact_ties"], field=f"schedule[{index}]")
        (
            total_state,
            reachable_state,
            fan_response_digest,
            fan_reachable_digest,
        ) = _fan_at_scale(fan, scale)
        reachable_tie_keys = tuple(key for key in tie_keys if key in dict(reachable_tape))
        if (
            row["total_state"] != total_state
            or row["reachable_state"] != reachable_state
            or row["exact_response_tape_sha256"] != fan_response_digest
            or row["reachable_response_tape_sha256"] != fan_reachable_digest
            or total_state != _expected_state(tie_keys, row["exact_response_tape_sha256"], source_digest)
            or (reachable_state == "tie_unresolved") != bool(reachable_tie_keys)
        ):
            raise ValueError("ADR-0351 scheduled fan classification drifted")
        if index == 0 and tie_keys:
            source_tie = 1

        exact_value = _fraction(
            row["exact_response_value"], field=f"schedule[{index}].exact_value"
        )
        production_value = _hex_float(
            row["production_response_value_hex"],
            field=f"schedule[{index}].production_value",
        )
        if (
            _finite_nonnegative(
                row["float_exact_response_value_error"],
                field=f"schedule[{index}].value_error",
            )
            != 0.0
            or float(exact_value) != production_value
            or row["production_tape_exactly_optimal"] is not True
            or row["fixed_tape_value_identity"] is not True
            or row["active_row_identity"] is not True
            or row["upper_envelope_identity"] is not True
        ):
            raise ValueError("ADR-0351 scheduled value or certificate bit drifted")
        if tie_keys:
            if row["unique_exact_selector_agreement"] is not True:
                raise ValueError("ADR-0351 tied selector agreement bit drifted")
        elif production_tape != exact_tape or row["unique_exact_selector_agreement"] is not True:
            raise ValueError("ADR-0351 unique selector agreement drifted")

        profile_value = profile_intercept + scale * profile_slope
        exact_gain = exact_value - profile_value
        row_values = {
            digest: intercept + scale * slope
            for digest, (intercept, slope) in row_library.items()
        }
        exact_digest = row["exact_response_tape_sha256"]
        if (
            exact_digest not in row_values
            or row_values[exact_digest] != exact_gain
            or max(row_values.values()) != exact_gain
            or any(value > exact_gain for value in row_values.values())
        ):
            raise ValueError("ADR-0351 maximum affine envelope drifted")

        identity = row["identity_columns"]
        if not isinstance(identity, dict) or set(identity) != {
            "common_reachable_action_changes",
            "current_reachable_entries",
            "current_unreachable_entry_changes",
            "reachable_identity",
            "reachable_support_added",
            "reachable_support_removed",
            "source_reachable_entries",
            "total_entry_changes",
            "total_identity",
        }:
            raise ValueError("ADR-0351 tape identity columns drifted")
        source = dict(source_tape)
        current = dict(exact_tape)
        current_live = dict(reachable_tape)
        changed = {key for key in source if source[key] != current[key]}
        if (
            identity["total_identity"] != (source_tape == exact_tape)
            or identity["total_entry_changes"] != len(changed)
            or identity["current_reachable_entries"] != len(current_live)
            or identity["current_unreachable_entry_changes"]
            != len(changed - set(current_live))
            or not isinstance(identity["reachable_identity"], bool)
            or any(
                isinstance(identity[field], bool)
                or not isinstance(identity[field], int)
                or identity[field] < 0
                for field in (
                    "common_reachable_action_changes",
                    "reachable_support_added",
                    "reachable_support_removed",
                    "source_reachable_entries",
                )
            )
        ):
            raise ValueError("ADR-0351 tape identity arithmetic drifted")
        if not identity["total_identity"] and identity["reachable_identity"]:
            phantom_identity += 1
        selector_seconds += _finite_nonnegative(
            row["production_selector_seconds"],
            field=f"schedule[{index}].selector_seconds",
        )

    if source_tie:
        conservative_scale = fan["_float_window"]["conservative_scale"]
        if conservative_scale > 0.0:
            tie_window_violation = 1
    return selector_seconds, source_tie, tie_window_violation, phantom_identity


def _verify_target(
    target: Any,
    *,
    direction_index: int,
    target_player: int,
) -> tuple[float, int, int, int]:
    if not isinstance(target, dict) or set(target) != {
        "fan",
        "fan_audit_seconds",
        "float_window",
        "row_library",
        "schedule",
        "target_player",
    } or target["target_player"] != target_player:
        raise ValueError("ADR-0351 target-row schema or order drifted")
    _finite_nonnegative(target["fan_audit_seconds"], field="fan_audit_seconds")
    source_tape, cell_bounds, _ = _verify_fan(
        target["fan"],
        direction_index=direction_index,
        target_player=target_player,
    )
    rows = target["row_library"]
    row_library = _verify_row_library(rows, cell_bounds=cell_bounds)
    window = target["float_window"]
    if not isinstance(window, dict) or set(window) != {
        "conservative_not_beyond_exact",
        "conservative_scale",
        "exact_source_action_ties_float",
        "first_switch_competing_action",
        "first_switch_information_key",
        "first_switch_source_action",
        "selector_comparisons",
        "selector_margin_allowance",
        "zero_allowance_breakpoint_error",
        "zero_allowance_scale",
    }:
        raise ValueError("ADR-0351 Float64 selector-window schema drifted")
    upper = _EXPECTED_SOURCE_UPPERS[direction_index][target_player]
    conservative = _finite_nonnegative(
        window["conservative_scale"], field="window.conservative_scale"
    )
    if (
        window["conservative_not_beyond_exact"] is not True
        or conservative > float(upper)
        or window["selector_margin_allowance"] != 1e-12
        or window["selector_comparisons"] != 20
        or _finite_nonnegative(
            window["zero_allowance_breakpoint_error"],
            field="window.zero_allowance_breakpoint_error",
        )
        != 0.0
        or window["zero_allowance_scale"] != float(upper)
        or isinstance(window["exact_source_action_ties_float"], bool)
        or not isinstance(window["exact_source_action_ties_float"], int)
        or window["exact_source_action_ties_float"] < 0
    ):
        raise ValueError("ADR-0351 Float64 selector-window values drifted")
    fan_for_schedule = dict(target["fan"])
    fan_for_schedule["_row_records"] = rows
    fan_for_schedule["_float_window"] = window
    return _verify_schedule(
        target["schedule"],
        fan=fan_for_schedule,
        source_tape=source_tape,
        row_library=row_library,
    )


def verify_adr0351_legal_h4_selector_fan_record(
    record: dict[str, Any],
) -> Mapping[str, Any]:
    """Rebind the retained map and reject its recorded successor authority."""

    if not isinstance(record, dict) or set(record) != _EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("ADR-0351 top-level result schema drifted")
    environment = record["environment"]
    git = environment.get("git", {}) if isinstance(environment, dict) else {}
    if (
        record["schema_version"] != 1
        or record["status"] != "legal_responder_raise_h4_selector_window_executed"
        or record["passed"] is not True
        or record["decision"]
        != "authorize_legal_h4_selector_stable_affine_integration_preregistration"
        or record["strategy_quality_claim"] is not None
        or record["strategy_labels_generated"] != 0
        or record["quality_rows_serialized"] != 0
        or record["config_sha256"] != ADR0351_CONFIG_SHA256
        or record["implementation_sha256"]
        != _EXPECTED_SOURCE_HASHES["expected_implementation_sha256"]
        or record["root_public_state_sha256"] != ADR0351_ROOT_PUBLIC_STATE_SHA256
        or record["public_schema_sha256"] != ADR0351_PUBLIC_SCHEMA_SHA256
        or record["game_structural_sha256"] != ADR0351_GAME_STRUCTURAL_SHA256
        or record["game_provenance_sha256"] != ADR0351_GAME_PROVENANCE_SHA256
        or record["source_policy_sha256"] != ADR0351_SOURCE_POLICY_SHA256
        or git
        != {
            "commit": ADR0351_INVOCATION_SOURCE_COMMIT,
            "dirty": False,
            "strict_status": True,
        }
        or not isinstance(environment, dict)
        or set(environment) != {"git", "platform", "python", "runtime"}
        or environment["runtime"]
        != {"backend": "cpu_float64_production_plus_fraction_fan_teacher"}
    ):
        raise ValueError("ADR-0351 retained identity drifted")
    if record["methodology"] != {
        "behavioral_identity": "reachable_support_reporting_only",
        "betting_authority": "NoLimitBettingState",
        "certificate_identity": "total_function",
        "direction_compiler": "selector_free_regret_vertices_and_retained_master",
        "quality_rows": 0,
        "strategy_labels": 0,
        "subject": "production_best_response_on_untouched_dyadic_schedule",
        "teacher": "fraction_exact_sequence_form_normal_fan",
    } or record["limitations"] != [
        "This is one finite h4 checked-to heads-up river selector map.",
        "Tie-unresolved regions remain unresolved and no tolerance elects a tape.",
        "Reachable-support identity is descriptive; total tapes gate certificates.",
        "The selector wall is laboratory infrastructure, not action-clock latency.",
        "No full-width, multiway, action, strategy-quality, or poker-strength result is emitted.",
    ]:
        raise ValueError("ADR-0351 methodology or limitations drifted")
    if record["fan_semantics"] != {
        "certificate_identity_authority": "total_function_only",
        "legacy_differential_scope": "every_frozen_one_public_history_ray_reproduces_exact_margin_over_closing_slope_breakpoint",
        "reachable_tape_identity": "complete_sorted_positive_support_information_key_action_behavior",
        "row_envelope_direction": "best_response_gain_is_maximum_of_fixed_tape_affine_gain_rows_with_master_epigraph_constraints_z_greater_equal_row",
        "section_coordinate": "sequence_form_realization_interpolation",
        "states": ["fixed", "tie_unresolved", "switched"],
        "tie_measure_semantics": "exact_fraction_lebesgue_interval_measure_plus_separate_zero_measure_points",
        "total_tape_identity": "complete_sorted_information_key_action_total_function",
    } or record["schedule"] != {
        "denominator": 16,
        "numerators": list(range(17)),
        "points": 17,
    }:
        raise ValueError("ADR-0351 fan semantics or schedule drifted")
    if record["direction_descriptors"] != list(_DIRECTION_DESCRIPTORS):
        raise ValueError("ADR-0351 direction descriptors drifted")
    gates = record["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _EXPECTED_GATE_KEYS
        or any(value is not True for value in gates.values())
    ):
        raise ValueError("ADR-0351 recorded gate vector drifted")

    controls = record["engineered_controls"]
    expected_controls = {
        "crossing_breakpoint": {"denominator": 2, "numerator": 1},
        "crossing_fixed_measure": {"denominator": 2, "numerator": 1},
        "crossing_legacy_breakpoint": {"denominator": 2, "numerator": 1},
        "crossing_switched_measure": {"denominator": 2, "numerator": 1},
        "crossing_tie_measure": {"denominator": 1, "numerator": 0},
        "crossing_tie_points": [{"denominator": 2, "numerator": 1}],
        "degenerate_reachable_tie_measure": {"denominator": 1, "numerator": 1},
        "degenerate_total_fixed_measure": {"denominator": 1, "numerator": 0},
        "degenerate_total_switched_measure": {"denominator": 1, "numerator": 0},
        "degenerate_total_tie_measure": {"denominator": 1, "numerator": 1},
    }
    if controls != expected_controls:
        raise ValueError("ADR-0351 engineered controls drifted")

    directions = record["directions"]
    if not isinstance(directions, list) or len(directions) != 4:
        raise ValueError("ADR-0351 direction inventory drifted")
    selector_seconds = 0.0
    source_ties = 0
    tie_window_violations = 0
    phantom_identities = 0
    for direction_index, (direction, descriptor) in enumerate(
        zip(directions, _DIRECTION_DESCRIPTORS, strict=True)
    ):
        if not isinstance(direction, dict) or set(direction) != {
            "changed_public_histories",
            "direction_class",
            "endpoint_policy_sha256",
            "label",
            "target_rows",
        } or {key: direction[key] for key in descriptor} != descriptor:
            raise ValueError("ADR-0351 direction identity drifted")
        targets = direction["target_rows"]
        if not isinstance(targets, list) or len(targets) != 2:
            raise ValueError("ADR-0351 target-player inventory drifted")
        for target_player, target in enumerate(targets):
            seconds, tied, violation, phantom = _verify_target(
                target,
                direction_index=direction_index,
                target_player=target_player,
            )
            selector_seconds += seconds
            source_ties += tied
            tie_window_violations += violation
            phantom_identities += phantom

    if (source_ties, tie_window_violations, phantom_identities) != (4, 4, 2):
        raise ValueError("ADR-0351 corrected tie/identity assessment drifted")
    scientific_payload = {
        "directions": directions,
        "engineered_controls": controls,
    }
    scientific_bytes = len(
        json.dumps(
            scientific_payload,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
    )
    aggregate = record["aggregate"]
    expected_aggregate_keys = {
        "affine_row_activation",
        "conservative_total_tape_window",
        "exact_tape_optimality",
        "fixed_tape_value_identity",
        "identity_columns",
        "legacy_breakpoint_identity",
        "maximum_breakpoint_error",
        "maximum_value_error",
        "scientific_payload_bytes",
        "selector_calls",
        "selector_seconds",
        "three_state_partition",
        "total_seconds",
        "unique_selector_agreement",
        "upper_envelope_direction",
    }
    if (
        not isinstance(aggregate, dict)
        or set(aggregate) != expected_aggregate_keys
        or any(
            aggregate[field] is not True
            for field in (
                "affine_row_activation",
                "conservative_total_tape_window",
                "exact_tape_optimality",
                "fixed_tape_value_identity",
                "identity_columns",
                "legacy_breakpoint_identity",
                "three_state_partition",
                "unique_selector_agreement",
                "upper_envelope_direction",
            )
        )
        or aggregate["maximum_breakpoint_error"] != 0.0
        or aggregate["maximum_value_error"] != 0.0
        or aggregate["scientific_payload_bytes"] != scientific_bytes != 998_246
        or aggregate["selector_calls"] != 136
        or aggregate["selector_seconds"] != selector_seconds
        or aggregate["total_seconds"] != record["total_seconds"]
        or aggregate["total_seconds"] > 120.0
        or aggregate["selector_seconds"] > 60.0
    ):
        raise ValueError("ADR-0351 aggregate or infrastructure ledger drifted")
    return _deep_freeze(record)


def verify_adr0351_legal_h4_selector_fan_result_artifact(
    path: Path | None = None,
) -> RetainedLegalH4SelectorFanResult:
    """Rebind ADR-0350's artifact and deny its recorded authorization."""

    verify_adr0351_result_source_and_dependencies()
    artifact_path = _ROOT / ADR0351_ARTIFACT_RELATIVE_PATH if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0351_ARTIFACT_BYTES:
        raise ValueError("ADR-0351 artifact byte count drifted")
    if sha256(raw).hexdigest() != ADR0351_ARTIFACT_SHA256:
        raise ValueError("ADR-0351 artifact SHA-256 drifted")
    record = _decode_strict_object(raw, source=str(artifact_path))
    if (
        json.dumps(record, allow_nan=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
        != raw
    ):
        raise ValueError("ADR-0351 artifact is not canonical retained JSON")
    frozen = verify_adr0351_legal_h4_selector_fan_record(record)
    return RetainedLegalH4SelectorFanResult(
        record=frozen,
        source_commit=ADR0351_INVOCATION_SOURCE_COMMIT,
        total_seconds=float(record["total_seconds"]),
        selector_seconds=float(record["aggregate"]["selector_seconds"]),
        sections=8,
        source_tie_sections=4,
        recorded_source_tie_window_violations=4,
        corrected_certificate_pass=False,
        successor_authorized=False,
    )


__all__ = [
    "ADR0351_ARTIFACT_BYTES",
    "ADR0351_ARTIFACT_RELATIVE_PATH",
    "ADR0351_ARTIFACT_SHA256",
    "ADR0351_CONFIG_SHA256",
    "ADR0351_GAME_PROVENANCE_SHA256",
    "ADR0351_GAME_STRUCTURAL_SHA256",
    "ADR0351_INVOCATION_SOURCE_COMMIT",
    "ADR0351_PUBLIC_SCHEMA_SHA256",
    "ADR0351_RESULT_PROTOCOL",
    "ADR0351_RESULT_PROTOCOL_SHA256",
    "ADR0351_ROOT_PUBLIC_STATE_SHA256",
    "ADR0351_SOURCE_POLICY_SHA256",
    "RetainedLegalH4SelectorFanResult",
    "verify_adr0351_legal_h4_selector_fan_record",
    "verify_adr0351_legal_h4_selector_fan_result_artifact",
    "verify_adr0351_result_source_and_dependencies",
]
