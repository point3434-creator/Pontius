"""Independent reader for the ADR-0466 deferred-science-import successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from threading import RLock

from . import legal_river_quotient_compiled_global_separation_calibration_result as _parent
from .durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)


ROOT = Path(__file__).parents[2]
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v5-deferred-science-import.json"
)
RECOVERY_CONFIG_SHA256 = (
    "f61d236530e8add3e5eb063f9f3afa641e205defd9cdefaa56fd9a2de53c8d1f"
)
AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v6-invocation-authorization.json"
)
AUTHORIZATION_CONFIG_PATH = ROOT / AUTHORIZATION_CONFIG_RELATIVE_PATH
AUTHORIZATION_COMMIT_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md",
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
PARENT_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
)
ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json"
)
ATTEMPT_PATH = ROOT / ATTEMPT_RELATIVE_PATH
LAUNCH_PENDING_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json"
)
LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json"
)
LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json"
)
LAUNCH_PENDING_PATH = ROOT / LAUNCH_PENDING_RELATIVE_PATH
LAUNCH_CONSUMED_PATH = ROOT / LAUNCH_CONSUMED_RELATIVE_PATH
LAUNCH_ABORTED_PATH = ROOT / LAUNCH_ABORTED_RELATIVE_PATH
REJECTED_V3_SOURCE_SEAL_COMMIT = "77feb7c78990ca53e70b1302a6866fe5d781411f"
REJECTED_V3_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v3.jsonl"
)
REJECTED_V3_RESULT_PATH = ROOT / REJECTED_V3_RESULT_RELATIVE_PATH
CONSUMED_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v2.jsonl"
)
CONSUMED_RESULT_PATH = ROOT / CONSUMED_RESULT_RELATIVE_PATH
CONSUMED_RESULT_BYTES = 3_299_268
CONSUMED_RESULT_SHA256 = (
    "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d"
)
PREREGISTRATION_COMMIT = "001b7e1e18424e4b47c218876bccd7c9aa09ad59"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0466-deferred-science-import-owner-v4"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0466-deferred-science-import-campaign-v4"
).hexdigest()
SCIENTIFIC_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
)
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
)
PARENT_SCIENTIFIC_SOURCE_SHA256 = (
    "d38e96fd445f01a70113a8598094d0449a18271fa4d6ce992c781f0253ae821e"
)
EFFECTIVE_SCIENTIFIC_SOURCE_SHA256 = (
    "7c63e2706f5aa28c37f25bfa58d09f03d2f5fe26f3a3312fe2baf7b849cec3fc"
)
CUDA_SOURCE_SHA256 = (
    "4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7"
)
KERNEL_SIGNATURE_MANIFEST_SHA256 = (
    "8c25833e55a75a76a226251166a564b6ab8e52efdbb543958c33b93e8b7c63f8"
)
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"
_REJECTED_CLAIMS = {
    "compiled_calibration_result": None,
    "production_base_classification": "producer_absent",
    "production_base_numerical_admission": None,
    "material_zeta_speed_claim": None,
    "symbolic_45_primitive_projection": None,
    "candidate_selected": None,
    "topology_selected": None,
    "arithmetic_schedule_selected": None,
    "literal_45_numerical_result": None,
    "resolver_iteration_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}
PUBLIC_WALL_NS = 1_800_000_000_000
LABORATORY_WALL_NS = 1_500_000_000_000
OUTSIDE_LABORATORY_WALL_NS = 300_000_000_000
_OBSERVATION_KEYS = {
    "schema_version",
    "event_index",
    "kind",
    "event",
    "source_commit",
}
_REJECTION_EVENT_KEYS = {
    "schema_version",
    "terminal",
    "passed",
    "reason",
    "laboratory_elapsed_ns",
    "candidate_selected",
    "topology_selected",
    "arithmetic_schedule_selected",
    "claims",
    "executed_science_identity",
    "science_import_completed",
    "science_identity_validated",
    "science_execution_started",
}
_SUCCESS_EVENT_KEYS = {
    "schema_version",
    "terminal",
    "passed",
    "laboratory_elapsed_ns",
    "scientific_call_count",
    "warmup_call_count",
    "measured_call_count",
    "differential_count",
    "complete_positive_differential_count",
    "authority_sha256",
    "fit_projection_sha256",
    "production_base_classification",
    "candidate_selected",
    "topology_selected",
    "arithmetic_schedule_selected",
    "claims",
    "executed_science_identity",
    "science_import_completed",
    "science_identity_validated",
    "science_execution_started",
}
_OWNER_TERMINAL_KEYS = {
    "schema_version",
    "terminal",
    "passed",
    "reason",
    "event_count",
    "public_elapsed_ns",
    "public_wall_ns",
    "laboratory_elapsed_ns",
    "laboratory_wall_ns",
    "outside_laboratory_elapsed_ns",
    "outside_laboratory_wall_ns",
    "candidate_selected",
    "topology_selected",
    "arithmetic_schedule_selected",
    "claims",
}
_STARTED_REJECTION_TERMINALS = {
    "compiled_reduced_calibration_rejected",
    "compiler_rejected",
    "cubin_identity_rejected",
    "cubin_rejected",
    "cuda_source_materialization_rejected",
    "deferred_science_import_rejected",
    "device_memory_admission_rejected",
    "hardware_identity_rejected",
    "hybrid_switch_control_rejected",
    "kernel_launch_arity_rejected",
    "laboratory_wall_rejected",
    "phase_partition_rejected",
    "production_base_boundary_rejected",
    "resource_ceiling_rejected",
    "resource_instrument_rejected",
    "rrns_channel_fault_detected",
    "tool_identity_rejected",
    "work_receipt_rejected",
    "workspace_preparation_rejected",
}

DEPENDENCY_RELATIVE_PATHS = (
    RECOVERY_CONFIG_RELATIVE_PATH,
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v4-launch-abi-completeness.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v3-launch-abi.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v2-absolute-git.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v1.json",
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0459-retain-the-unjournaled-absolute-git-infrastructure-rejection.md",
    "docs/decisions/ADR-0460-preregister-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0462-retain-the-timed-rrns-direct-launch-arity-rejection.md",
    "docs/decisions/ADR-0463-preregister-the-kernel-launch-arity-successor.md",
    "docs/decisions/ADR-0464-correct-the-launch-arity-successor-before-source-seal.md",
    "docs/decisions/ADR-0465-source-seal-the-kernel-launch-arity-successor.md",
    "docs/decisions/ADR-0466-reject-the-v3-source-seal-and-preregister-deferred-science-import.md",
    "docs/decisions/ADR-0467-source-seal-the-deferred-science-import-successor.md",
    "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v4.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v4.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
    "run_legal_river_quotient_compiled_global_separation_calibration_v2.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_result.py",
    "run_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py",
    "src/pontius/legal_river_quotient_base_provenance.py",
    "src/pontius/legal_river_quotient_global_separation_topologies.py",
    "src/pontius/legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_cuda_consumer.py",
    "src/pontius/gpu_occupied_card_quotient.py",
    "src/pontius/factor_tt_contraction.py",
    "src/pontius/occupied_card_quotient.py",
    "src/pontius/structured_showdown_automaton.py",
    "src/pontius/legal_river_quotient_bridge.py",
    "src/pontius/legal_river_quotient_consumer_capacity.py",
    "src/pontius/tensor_train.py",
    "src/pontius/tensor_train_algebra.py",
    "src/pontius/action_clock.py",
    "src/pontius/factorized_belief.py",
    "src/pontius/full_width_belief.py",
    "src/pontius/full_width_reference_policy.py",
    "src/pontius/game.py",
    "src/pontius/holdem_cards.py",
    "src/pontius/immutable_blueprint.py",
    "src/pontius/legal_decision_spine_v2.py",
    "src/pontius/no_limit_betting.py",
    "src/pontius/preparation_bank.py",
    "src/pontius/river.py",
    "src/pontius/street_deadline.py",
    "src/pontius/cfr.py",
    "src/pontius/coalition.py",
    "src/pontius/dependency_tape.py",
    "src/pontius/evaluation.py",
    "src/pontius/kuhn.py",
    "src/pontius/legal_decision_spine.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/reference_hand_replay.py",
    "src/pontius/river_incremental.py",
    "src/pontius/river_multi_size.py",
    "src/pontius/river_multiway.py",
    "src/pontius/updates.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/__init__.py",
    "src/pontius/cuda_dll_bootstrap.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_PARENT_BINDINGS = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "verify_independent_contract",
)
_LOCK = RLock()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _expected_child_runtime() -> dict[str, object]:
    raw = CONSUMED_RESULT_PATH.read_bytes()
    if (
        len(raw) != CONSUMED_RESULT_BYTES
        or sha256(raw).hexdigest() != CONSUMED_RESULT_SHA256
    ):
        raise ValueError("reader runtime authority bytes differ")
    lines = raw.splitlines()
    if len(lines) < 2:
        raise ValueError("reader runtime authority lacks bootstrap")
    envelope = _mapping(json.loads(lines[1]), label="runtime authority envelope")
    body = _mapping(envelope.get("body"), label="runtime authority body")
    wrapper = _mapping(body.get("payload"), label="runtime authority wrapper")
    event = _mapping(wrapper.get("event"), label="runtime authority event")
    runtime = _mapping(
        event.get("child_runtime_environment"), label="runtime authority"
    )
    if (
        body.get("kind") != "observation"
        or wrapper.get("kind") != "bootstrap_handshake"
        or event.get("schema_version") != "pontius-adr0457-bootstrap-v1"
        or runtime.get("schema_version")
        != "legal-river-fixed-width-child-runtime-v1"
    ):
        raise ValueError("reader runtime authority identity differs")
    return {
        **dict(runtime),
        "v4_python_safe_path": True,
        "v4_fresh_pycache_prefix": True,
        "v4_repo_bytecode_loaded": False,
    }


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"reader authorization JSON repeats key {key!r}")
        value[key] = item
    return value


def _absolute_git(*arguments: str) -> bytes:
    if (
        not GIT_PATH.is_file()
        or GIT_PATH.stat().st_size != GIT_BYTES
        or sha256(GIT_PATH.read_bytes()).hexdigest() != GIT_SHA256
    ):
        raise RuntimeError("reader absolute Git executable identity differs")
    completed = subprocess.run(
        [str(GIT_PATH), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        timeout=30.0,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", "replace"
        )[:4096]
        raise RuntimeError(f"reader absolute Git command failed: {detail}")
    return completed.stdout


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("reader canonical input must be bytes")
    output = bytearray()
    previous_was_cr = False
    for value in raw:
        if previous_was_cr:
            if value == 10:
                output.append(10)
                previous_was_cr = False
                continue
            output.append(13)
            previous_was_cr = False
        if value == 13:
            previous_was_cr = True
        else:
            output.append(value)
    if previous_was_cr:
        output.append(13)
    return bytes(output)


def _dependency_hashes_at_commit(commit: str) -> dict[str, str]:
    return {
        relative: sha256(
            _canonical_lf(_absolute_git("show", f"{commit}:{relative}"))
        ).hexdigest()
        for relative in DEPENDENCY_RELATIVE_PATHS
    }


def _manifest_sha256(signatures: Mapping[str, object]) -> str:
    normalized: dict[str, list[str]] = {}
    for name, parameters in signatures.items():
        if not isinstance(name, str) or not isinstance(parameters, list):
            raise TypeError("reader kernel signature row differs")
        if any(not isinstance(parameter, str) for parameter in parameters):
            raise TypeError("reader kernel signature parameter differs")
        normalized[name] = list(parameters)
    return sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _expected_executed_science_identity() -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0466-executed-science-identity-v1",
        "module": SCIENTIFIC_MODULE,
        "parent_scientific_source_canonical_lf_sha256": (
            PARENT_SCIENTIFIC_SOURCE_SHA256
        ),
        "effective_scientific_source_sha256": EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        "literal_cuda_source_sha256": CUDA_SOURCE_SHA256,
        "kernel_signature_manifest_sha256": KERNEL_SIGNATURE_MANIFEST_SHA256,
        "kernel_count": 28,
        "central_pre_driver_guard": True,
        "preloaded_execution_modules": [
            "pontius.legal_river_quotient_fixed_width_device_preflight",
            "pontius.legal_river_quotient_exact_integer_operator",
            "pontius.legal_river_quotient_cuda_compensated_tiles",
            "pontius.legal_river_quotient_fixed_width_work_comparison",
            "pontius.legal_river_quotient_base_provenance",
        ],
    }


def _attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": "pontius-adr0466-public-attempt-v1",
            "protocol_sha256": PROTOCOL_SHA256,
            "campaign_sha256": CAMPAIGN_SHA256,
            "result_relative_path": RESULT_RELATIVE_PATH,
            "rejected_v3_result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
        }
    )


def _launch_marker_bytes(
    identity: Mapping[str, object], *, state: str
) -> bytes:
    if state not in {"pending", "consumed", "aborted"}:
        raise ValueError("reader launch marker state differs")
    return canonical_journal_json_bytes({**dict(identity), "state": state})


def _authorization_config() -> tuple[Mapping[str, object], str]:
    raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError("float in JSON")),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constant in JSON")),
    )
    if not isinstance(value, Mapping):
        raise TypeError("reader invocation authorization must be an object")
    source_seal = value.get("source_seal_commit")
    if (
        set(value)
        != {"schema_version", "source_seal_commit", "authorization_commit_paths"}
        or value.get("schema_version")
        != "pontius-adr0468-one-commit-authorization-v1"
        or type(source_seal) is not str
        or len(source_seal) != 40
        or any(character not in "0123456789abcdef" for character in source_seal)
        or value.get("authorization_commit_paths")
        != list(AUTHORIZATION_COMMIT_PATHS)
    ):
        raise ValueError("reader invocation authorization fields differ")
    return value, sha256(_canonical_lf(raw)).hexdigest()


def _validate_authorization_git(
    authorization_commit: object,
    source_seal_commit: object,
    dependency_hashes: Mapping[str, object],
) -> None:
    for value, label in (
        (authorization_commit, "authorization"),
        (source_seal_commit, "source seal"),
    ):
        if (
            type(value) is not str
            or len(value) != 40
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"reader {label} commit identity differs")
    authorization = str(authorization_commit)
    source_seal = str(source_seal_commit)
    parent_row = (
        _absolute_git("rev-list", "--parents", "-n", "1", authorization)
        .decode("ascii")
        .strip()
        .split()
    )
    changed = tuple(
        row.replace("\\", "/")
        for row in _absolute_git(
            "diff", "--name-only", "--no-renames", source_seal, authorization
        )
        .decode("utf-8")
        .splitlines()
        if row
    )
    if (
        parent_row != [authorization, source_seal]
        or tuple(sorted(changed)) != tuple(sorted(AUTHORIZATION_COMMIT_PATHS))
        or dict(dependency_hashes) != _dependency_hashes_at_commit(authorization)
    ):
        raise ValueError("reader authorization Git identity differs")


def _validate_semantic_identities(recovery: object) -> None:
    records = getattr(recovery, "records", None)
    if not isinstance(records, tuple):
        raise TypeError("deferred-import recovery records differ")
    for record in records:
        payload = _mapping(record.body.payload, label="journal payload")
        expected_semantic = sha256(
            canonical_journal_json_bytes(dict(payload))
        ).hexdigest()
        if record.body.semantic_identity_sha256 != expected_semantic:
            raise ValueError("deferred-import semantic identity differs")


def _validate_deferred_header(raw: bytes) -> None:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or not recovery.records:
        raise ValueError("deferred-import journal is incomplete")
    _validate_semantic_identities(recovery)
    first = recovery.records[0]
    if first.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("deferred-import journal omits header")
    header = first.body.payload
    header_claims = _mapping(header.get("claims"), label="header claims")
    if (
        set(header)
        != {
            "schema_version",
            "protocol_sha256",
            "campaign_sha256",
            "config_sha256",
            "preregistration_commit",
            "source_seal_git",
            "dependency_hashes",
            "result_relative_path",
            "literal_worker_module",
            "scientific_module",
            "calls_under_one_public_owner",
            "claims",
            "launch_abi_recovery",
            "deferred_science_import_authorization",
        }
        or header.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or header.get("scientific_module") != SCIENTIFIC_MODULE
        or dict(header_claims) != _REJECTED_CLAIMS
    ):
        raise ValueError("deferred-import header domain differs")
    identity = _mapping(header.get("launch_abi_recovery"), label="launch ABI identity")
    if (
        set(identity)
        != {
            "schema_version",
            "config_relative_path",
            "config_canonical_lf_sha256",
            "predecessor",
            "rejected_v3",
            "bootstrap_before_science_import",
            "module_aliasing_used",
            "executed_science_identity",
            "launch_arity_contract",
        }
        or identity.get("schema_version")
        != "pontius-adr0466-deferred-science-import-recovery-v1"
        or identity.get("config_relative_path") != RECOVERY_CONFIG_RELATIVE_PATH
        or identity.get("config_canonical_lf_sha256") != RECOVERY_CONFIG_SHA256
        or identity.get("bootstrap_before_science_import") is not True
        or identity.get("module_aliasing_used") is not False
    ):
        raise ValueError("deferred-import recovery identity differs")
    predecessor = _mapping(identity.get("predecessor"), label="predecessor")
    if predecessor != {
        "source_seal_commit": "08bb6857f47f9669b8f531c65079d4decd52a573",
        "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
        "result_bytes": CONSUMED_RESULT_BYTES,
        "result_raw_sha256": CONSUMED_RESULT_SHA256,
        "terminal": "compiled_reduced_calibration_rejected",
        "scientific_call_count": 1,
        "measured_call_count": 0,
        "failure_code": "CUDA_ERROR_INVALID_VALUE",
        "invocation_count": 1,
    }:
        raise ValueError("deferred-import predecessor differs")
    if (
        not CONSUMED_RESULT_PATH.is_file()
        or CONSUMED_RESULT_PATH.stat().st_size != CONSUMED_RESULT_BYTES
        or sha256(CONSUMED_RESULT_PATH.read_bytes()).hexdigest()
        != CONSUMED_RESULT_SHA256
    ):
        raise ValueError("deferred-import predecessor bytes differ")
    rejected = _mapping(identity.get("rejected_v3"), label="rejected v3")
    if rejected != {
        "source_seal_commit": REJECTED_V3_SOURCE_SEAL_COMMIT,
        "result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
        "result_exists": False,
        "public_invocation_count": 0,
    }:
        raise ValueError("deferred-import rejected-v3 identity differs")
    if identity.get("executed_science_identity") != _expected_executed_science_identity():
        raise ValueError("deferred-import header science identity differs")
    contract = _mapping(identity.get("launch_arity_contract"), label="launch contract")
    signatures = _mapping(contract.get("kernel_signatures"), label="kernel signatures")
    recomputed = _manifest_sha256(signatures)
    if (
        set(contract)
        != {
            "schema_version",
            "parent_scientific_source_canonical_lf_sha256",
            "effective_scientific_source_sha256",
            "literal_cuda_source_sha256",
            "kernel_count",
            "kernel_signatures",
            "manifest_sha256",
            "timed_direct_source_count_expression",
            "selected_leaf_extraneous_scan_count_removed",
            "complete_differential_source_count_expression",
            "central_pre_driver_guard",
        }
        or contract.get("schema_version")
        != "pontius-adr0463-kernel-launch-arity-contract-v1"
        or contract.get("parent_scientific_source_canonical_lf_sha256")
        != PARENT_SCIENTIFIC_SOURCE_SHA256
        or contract.get("kernel_count") != 28
        or len(signatures) != 28
        or recomputed != KERNEL_SIGNATURE_MANIFEST_SHA256
        or contract.get("manifest_sha256") != recomputed
        or contract.get("effective_scientific_source_sha256")
        != EFFECTIVE_SCIENTIFIC_SOURCE_SHA256
        or contract.get("literal_cuda_source_sha256") != CUDA_SOURCE_SHA256
        or contract.get("timed_direct_source_count_expression")
        != "np.uint64(scan_count)"
        or contract.get("selected_leaf_extraneous_scan_count_removed") is not True
        or contract.get("complete_differential_source_count_expression")
        != "np.uint64(prepared.source_rows)"
        or contract.get("central_pre_driver_guard") is not True
    ):
        raise ValueError("deferred-import launch contract differs")
    stored_auth = _mapping(
        header.get("deferred_science_import_authorization"),
        label="deferred-import authorization",
    )
    source_git = _mapping(header.get("source_seal_git"), label="source-seal Git")
    dependency_hashes = _mapping(
        header.get("dependency_hashes"), label="dependency hashes"
    )
    launch_claim = _mapping(source_git.get("launch_claim"), label="launch claim")
    config, config_hash = _authorization_config()
    if (
        set(source_git)
        != {
            "commit",
            "dirty",
            "strict_status",
            "authorization",
            "attempt_marker_sha256",
            "launch_claim",
            "launch_marker_sha256",
            "authorized_dependency_hashes",
        }
        or set(stored_auth)
        != {
            "schema_version",
            "config_relative_path",
            "config_canonical_lf_sha256",
            "source_seal_commit",
            "authorization_commit",
            "authorization_commit_paths",
            "single_generation_only",
        }
        or stored_auth.get("authorization_commit") != source_git.get("commit")
        or source_git.get("authorization") != stored_auth
        or stored_auth.get("schema_version")
        != "pontius-adr0468-one-commit-authorization-v1"
        or stored_auth.get("config_relative_path")
        != AUTHORIZATION_CONFIG_RELATIVE_PATH
        or stored_auth.get("config_canonical_lf_sha256") != config_hash
        or stored_auth.get("source_seal_commit") != config.get("source_seal_commit")
        or stored_auth.get("authorization_commit_paths")
        != list(AUTHORIZATION_COMMIT_PATHS)
        or config.get("authorization_commit_paths")
        != list(AUTHORIZATION_COMMIT_PATHS)
        or stored_auth.get("single_generation_only") is not True
        or source_git.get("attempt_marker_sha256")
        != sha256(_attempt_bytes()).hexdigest()
        or set(launch_claim)
        != {
            "schema_version",
            "token_sha256",
            "authorization_commit",
            "result_relative_path",
        }
        or launch_claim.get("schema_version")
        != "pontius-adr0467-one-use-child-launch-v1"
        or not isinstance(launch_claim.get("token_sha256"), str)
        or len(str(launch_claim.get("token_sha256"))) != 64
        or any(
            character not in "0123456789abcdef"
            for character in str(launch_claim.get("token_sha256"))
        )
        or launch_claim.get("authorization_commit") != source_git.get("commit")
        or launch_claim.get("result_relative_path") != RESULT_RELATIVE_PATH
        or source_git.get("launch_marker_sha256")
        != sha256(_launch_marker_bytes(launch_claim, state="pending")).hexdigest()
        or source_git.get("authorized_dependency_hashes") != dependency_hashes
        or set(dependency_hashes) != set(DEPENDENCY_RELATIVE_PATHS)
        or dependency_hashes.get(AUTHORIZATION_CONFIG_RELATIVE_PATH) != config_hash
    ):
        raise ValueError("deferred-import authorization header differs")
    _validate_authorization_git(
        source_git.get("commit"),
        config.get("source_seal_commit"),
        dependency_hashes,
    )


def _expected_success_claims(materiality: bool) -> dict[str, object]:
    claims = {**_REJECTED_CLAIMS, "source_seal": True}
    claims["compiled_calibration_result"] = True
    claims["material_zeta_speed_claim"] = materiality
    claims["symbolic_45_primitive_projection"] = True
    return claims


def _validate_executed_terminal_identity(
    raw: bytes, *, expected_materiality: bool | None = None
) -> Mapping[str, object] | None:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    bootstrap_events = []
    terminal_events = []
    bootstrap_positions = []
    terminal_positions = []
    observation_kinds = []
    observation_index = 0
    for position, record in enumerate(recovery.records):
        if record.body.kind is not JournalRecordKind.OBSERVATION:
            continue
        payload = record.body.payload
        event_payload = _mapping(payload.get("event"), label="observation event")
        if (
            set(payload) != _OBSERVATION_KEYS
            or payload.get("schema_version")
            != "pontius-adr0457-owner-observation-v1"
            or payload.get("event_index") != observation_index
            or not isinstance(payload.get("kind"), str)
        ):
            raise ValueError("deferred-import observation wrapper differs")
        observation_index += 1
        observation_kinds.append(payload.get("kind"))
        if payload.get("kind") == "bootstrap_handshake":
            bootstrap_positions.append(position)
            bootstrap_events.append(event_payload)
        if payload.get("kind") == "terminal_evidence":
            terminal_positions.append(position)
            terminal_events.append(event_payload)
    if len(bootstrap_events) > 1 or len(terminal_events) > 1:
        raise ValueError("deferred-import child lifecycle observations differ")
    if not bootstrap_events:
        if observation_kinds:
            raise ValueError("deferred-import observation precedes bootstrap")
        last = recovery.records[-1]
        if (
            last.body.kind is not JournalRecordKind.TERMINAL
            or last.body.payload.get("passed") is not False
        ):
            raise ValueError("deferred-import pre-bootstrap terminal differs")
        return None
    bootstrap = bootstrap_events[0]
    runtime = _mapping(
        bootstrap.get("child_runtime_environment"), label="child runtime"
    )
    if (
        set(bootstrap)
        != {
            "schema_version",
            "literal_worker_module",
            "python_no_bytecode",
            "child_runtime_environment",
            "cupy_loaded",
            "scientific_source_loaded",
            "parent_journal_present",
        }
        or bootstrap.get("schema_version") != "pontius-adr0457-bootstrap-v1"
        or bootstrap.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or bootstrap.get("python_no_bytecode") is not True
        or bootstrap.get("cupy_loaded") is not False
        or bootstrap.get("scientific_source_loaded") is not False
        or bootstrap.get("parent_journal_present") is not True
        or dict(runtime) != _expected_child_runtime()
    ):
        raise ValueError("deferred-import bootstrap evidence differs")
    if not terminal_events:
        last = recovery.records[-1]
        if (
            observation_kinds[0] != "bootstrap_handshake"
            or last.body.kind is not JournalRecordKind.TERMINAL
            or last.body.payload.get("passed") is not False
        ):
            raise ValueError("deferred-import interrupted child lifecycle differs")
        return None
    if len(terminal_events) != 1:
        raise ValueError("deferred-import bootstrap lacks exclusive terminal evidence")
    if (
        bootstrap_positions[0] >= terminal_positions[0]
        or observation_kinds[0] != "bootstrap_handshake"
        or observation_kinds[-1] != "terminal_evidence"
    ):
        raise ValueError("deferred-import terminal precedes bootstrap")
    event = terminal_events[0]
    terminal = event.get("terminal")
    passed = event.get("passed")
    laboratory_elapsed = event.get("laboratory_elapsed_ns")
    claims = _mapping(event.get("claims"), label="terminal claims")
    if (
        set(event)
        != (_SUCCESS_EVENT_KEYS if passed is True else _REJECTION_EVENT_KEYS)
        or event.get("schema_version")
        != "pontius-adr0457-compiled-calibration-terminal-evidence-v1"
        or not isinstance(terminal, str)
        or not isinstance(passed, bool)
        or passed
        is not (
            terminal
            == "completed_reduced_compiled_calibration_production_base_absent"
        )
        or isinstance(laboratory_elapsed, bool)
        or not isinstance(laboratory_elapsed, int)
        or laboratory_elapsed < 0
        or not {
            "executed_science_identity",
            "science_import_completed",
            "science_identity_validated",
            "science_execution_started",
        }.issubset(event)
        or event.get("candidate_selected") is not None
        or event.get("topology_selected") is not None
        or event.get("arithmetic_schedule_selected") is not None
        or claims.get("production_base_classification") != "producer_absent"
        or claims.get("candidate_selected") is not None
        or claims.get("topology_selected") is not None
        or claims.get("arithmetic_schedule_selected") is not None
        or (
            passed is True
            and dict(claims)
            not in (
                _expected_success_claims(False),
                _expected_success_claims(True),
            )
        )
        or (
            passed is True
            and expected_materiality is not None
            and dict(claims) != _expected_success_claims(expected_materiality)
        )
        or (passed is False and dict(claims) != _REJECTED_CLAIMS)
        or (
            passed is False
            and (
                not isinstance(event.get("reason"), str)
                or not event.get("reason")
                or len(str(event.get("reason"))) > 4096
            )
        )
    ):
        raise ValueError("deferred-import terminal science fields are absent")
    if passed is True:
        if laboratory_elapsed > LABORATORY_WALL_NS:
            raise ValueError("deferred-import successful child crossed laboratory wall")
        fixtures = [
            _mapping(record.body.payload.get("event"), label="fixture authority")
            for record in recovery.records
            if record.body.kind is JournalRecordKind.OBSERVATION
            and record.body.payload.get("kind") == "fixture_authority"
        ]
        fits = [
            _mapping(record.body.payload.get("event"), label="fit projection")
            for record in recovery.records
            if record.body.kind is JournalRecordKind.OBSERVATION
            and record.body.payload.get("kind") == "fit_projection"
        ]
        if len(fixtures) != 1 or len(fits) != 1:
            raise ValueError("deferred-import success digest authorities differ")
        manifests = fixtures[0].get("manifests")
        if not isinstance(manifests, list):
            raise ValueError("deferred-import fixture manifests differ")
        authority_sha256 = sha256(
            json.dumps(
                manifests, sort_keys=True, separators=(",", ":")
            ).encode("ascii")
        ).hexdigest()
        fit_sha256 = sha256(
            json.dumps(
                dict(fits[0]), sort_keys=True, separators=(",", ":")
            ).encode("ascii")
        ).hexdigest()
        if (
            event.get("scientific_call_count") != 2_880
            or event.get("warmup_call_count") != 480
            or event.get("measured_call_count") != 2_400
            or event.get("differential_count") != 2_880
            or event.get("complete_positive_differential_count") != 60
            or event.get("authority_sha256") != authority_sha256
            or fixtures[0].get("authority_sha256") != authority_sha256
            or event.get("fit_projection_sha256") != fit_sha256
            or event.get("production_base_classification") != "producer_absent"
        ):
            raise ValueError("deferred-import success terminal counts or digests differ")
    imported = event.get("science_import_completed")
    validated = event.get("science_identity_validated")
    started = event.get("science_execution_started")
    identity = event.get("executed_science_identity")
    if started is True:
        if (
            imported is not True
            or validated is not True
            or identity != _expected_executed_science_identity()
            or (
                passed is False
                and terminal not in _STARTED_REJECTION_TERMINALS
            )
        ):
            raise ValueError("deferred-import executed science identity differs")
    elif started is False:
        if (
            type(imported) is not bool
            or validated is not False
            or identity is not None
            or event.get("terminal") != "deferred_science_import_rejected"
            or event.get("passed") is not False
        ):
            raise ValueError("deferred-import pre-science failure identity differs")
    else:
        raise ValueError("deferred-import science-execution discriminator differs")
    return event


def _expected_owner_success_claims() -> dict[str, object]:
    claims = dict(_REJECTED_CLAIMS)
    claims["compiled_calibration_result"] = True
    claims["symbolic_45_primitive_projection"] = True
    return claims


def _validate_owner_terminal_binding(
    raw: bytes, child_terminal: Mapping[str, object] | None
) -> Mapping[str, object]:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    terminal = recovery.records[-1].body.payload
    name = terminal.get("terminal")
    passed = terminal.get("passed")
    reason = terminal.get("reason")
    claims = _mapping(terminal.get("claims"), label="owner terminal claims")
    public = terminal.get("public_elapsed_ns")
    laboratory = terminal.get("laboratory_elapsed_ns")
    outside = terminal.get("outside_laboratory_elapsed_ns")
    event_count = sum(
        record.body.kind is JournalRecordKind.OBSERVATION
        for record in recovery.records
    )
    if (
        recovery.records[-1].body.kind is not JournalRecordKind.TERMINAL
        or set(terminal) != _OWNER_TERMINAL_KEYS
        or terminal.get("schema_version") != "pontius-adr0457-owner-terminal-v1"
        or not isinstance(name, str)
        or type(passed) is not bool
        or passed
        is not (
            name
            == "completed_reduced_compiled_calibration_production_base_absent"
        )
        or not isinstance(reason, str)
        or not reason
        or len(reason) > 4096
        or type(terminal.get("event_count")) is not int
        or terminal.get("event_count") != event_count
        or type(public) is not int
        or public < 0
        or (
            laboratory is not None
            and (type(laboratory) is not int or laboratory < 0)
        )
        or (
            outside is not None
            and (type(outside) is not int or outside < 0)
        )
        or ((laboratory is None) is not (outside is None))
        or (
            laboratory is not None
            and outside != public - laboratory
        )
        or terminal.get("public_wall_ns") != PUBLIC_WALL_NS
        or terminal.get("laboratory_wall_ns") != LABORATORY_WALL_NS
        or terminal.get("outside_laboratory_wall_ns")
        != OUTSIDE_LABORATORY_WALL_NS
        or terminal.get("candidate_selected") is not None
        or terminal.get("topology_selected") is not None
        or terminal.get("arithmetic_schedule_selected") is not None
        or dict(claims)
        != (_expected_owner_success_claims() if passed else _REJECTED_CLAIMS)
    ):
        raise ValueError("deferred-import owner terminal domain differs")
    if name == "public_wall_rejected" and public <= PUBLIC_WALL_NS:
        raise ValueError("deferred-import public-wall terminal lacks a crossing")
    if name == "laboratory_wall_rejected" and (
        public > PUBLIC_WALL_NS
        or laboratory is None
        or laboratory <= LABORATORY_WALL_NS
    ):
        raise ValueError("deferred-import laboratory-wall terminal lacks a crossing")
    if name == "outside_laboratory_wall_rejected" and (
        public > PUBLIC_WALL_NS
        or laboratory is None
        or laboratory > LABORATORY_WALL_NS
        or outside is None
        or outside <= OUTSIDE_LABORATORY_WALL_NS
    ):
        raise ValueError("deferred-import outside-wall terminal lacks a crossing")
    if child_terminal is None:
        if passed or name not in {
            "compiled_reduced_calibration_rejected",
            "public_wall_rejected",
        } or laboratory is not None:
            raise ValueError("deferred-import pre-science owner terminal differs")
        return terminal
    child_passed = child_terminal.get("passed")
    child_name = child_terminal.get("terminal")
    if laboratory != child_terminal.get("laboratory_elapsed_ns"):
        raise ValueError("deferred-import owner/child laboratory wall differs")
    if child_passed is False:
        if passed or name != child_name:
            raise ValueError("deferred-import rejecting terminal sum differs")
    elif child_passed is True:
        if name not in {
            "completed_reduced_compiled_calibration_production_base_absent",
            "public_wall_rejected",
            "laboratory_wall_rejected",
            "outside_laboratory_wall_rejected",
        }:
            raise ValueError("deferred-import successful child owner terminal differs")
    else:
        raise ValueError("deferred-import child terminal pass bit differs")
    return terminal


def _scientific_success_validation_view(raw: bytes) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    original = recovery.records[-1]
    terminal = dict(original.body.payload)
    terminal.update(
        {
            "terminal": (
                "completed_reduced_compiled_calibration_production_base_absent"
            ),
            "passed": True,
            "reason": "reader-only scientific validation view",
            "public_elapsed_ns": 0,
            "laboratory_elapsed_ns": 0,
            "outside_laboratory_elapsed_ns": 0,
            "claims": _expected_owner_success_claims(),
        }
    )
    semantic = sha256(canonical_journal_json_bytes(terminal)).hexdigest()
    body = build_journal_record_body(
        protocol_sha256=PROTOCOL_SHA256,
        campaign_sha256=CAMPAIGN_SHA256,
        kind=JournalRecordKind.TERMINAL,
        sequence=original.body.sequence,
        previous_record_sha256=original.body.previous_record_sha256,
        semantic_identity_sha256=semantic,
        payload=terminal,
    )
    replacement = JournalRecordEnvelope(body=body)
    return b"".join(
        record.line_bytes for record in recovery.records[:-1]
    ) + replacement.line_bytes


@contextmanager
def _configured_parent_reader() -> Iterator[object]:
    with _LOCK:
        original = {name: getattr(_parent, name) for name in _PARENT_BINDINGS}
        inherited_verify = _parent.verify_independent_contract

        def verify_independent_contract() -> None:
            fresh_result = _parent.RESULT_RELATIVE_PATH
            _parent.RESULT_RELATIVE_PATH = PARENT_RESULT_RELATIVE_PATH
            try:
                inherited_verify()
            finally:
                _parent.RESULT_RELATIVE_PATH = fresh_result

        replacements = {
            "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
            "PROTOCOL_SHA256": PROTOCOL_SHA256,
            "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
            "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
            "verify_independent_contract": verify_independent_contract,
        }
        for name, value in replacements.items():
            setattr(_parent, name, value)
        try:
            yield _parent
        finally:
            for name, value in original.items():
                setattr(_parent, name, value)


def assess_calibration_bytes(raw: bytes):
    _validate_deferred_header(raw)
    terminal_event = _validate_executed_terminal_identity(raw)
    owner_terminal = _validate_owner_terminal_binding(raw, terminal_event)
    with _configured_parent_reader() as reader:
        assessed = reader.assess_calibration_bytes(raw)
    if terminal_event is not None and terminal_event.get("passed") is True:
        if owner_terminal.get("passed") is True:
            if assessed.passed is not True:
                raise ValueError("deferred-import successful owner was not assessed")
            materiality = assessed.material_zeta_speed_claim
        else:
            with _configured_parent_reader() as reader:
                scientific = reader.assess_calibration_bytes(
                    _scientific_success_validation_view(raw)
                )
            if scientific.passed is not True:
                raise ValueError("deferred-import wall-rejected science is invalid")
            materiality = scientific.material_zeta_speed_claim
        _validate_executed_terminal_identity(
            raw, expected_materiality=materiality
        )
    return assessed


def _validate_local_lifecycle(raw: bytes) -> None:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.records or recovery.records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("deferred-import local journal header differs")
    header = recovery.records[0].body.payload
    git = _mapping(header.get("source_seal_git"), label="local source-seal Git")
    launch_claim = _mapping(git.get("launch_claim"), label="local launch claim")
    if (
        REJECTED_V3_RESULT_PATH.exists()
        or not ATTEMPT_PATH.is_file()
        or ATTEMPT_PATH.read_bytes() != _attempt_bytes()
        or LAUNCH_PENDING_PATH.exists()
    ):
        raise ValueError("deferred-import retained local lifecycle differs")
    markers = {
        "consumed": LAUNCH_CONSUMED_PATH,
        "aborted": LAUNCH_ABORTED_PATH,
    }
    present = [state for state, marker in markers.items() if marker.exists()]
    if len(present) != 1:
        raise ValueError("deferred-import local launch terminal differs")
    state = present[0]
    marker = markers[state]
    if (
        not marker.is_file()
        or marker.is_symlink()
        or marker.read_bytes() != _launch_marker_bytes(launch_claim, state=state)
    ):
        raise ValueError("deferred-import local launch marker differs")
    observations = [
        record
        for record in recovery.records
        if record.body.kind is JournalRecordKind.OBSERVATION
    ]
    if state == "aborted" and observations:
        raise ValueError("aborted deferred-import launch contains child observations")


def assess_calibration_file(path: Path = RESULT_PATH):
    if not isinstance(path, Path):
        raise TypeError("deferred-import result path must be a Path")
    if path.resolve() != RESULT_PATH.resolve():
        raise ValueError("deferred-import file assessment requires the public result path")
    raw = path.read_bytes()
    _validate_local_lifecycle(raw)
    assessed = assess_calibration_bytes(raw)
    final_raw = path.read_bytes()
    if final_raw != raw:
        raise ValueError("deferred-import result changed during assessment")
    _validate_local_lifecycle(final_raw)
    return assessed


__all__ = [
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_calibration_bytes",
    "assess_calibration_file",
]
