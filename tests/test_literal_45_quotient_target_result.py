from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    recover_journal_bytes,
)
from pontius.literal_45_quotient_target_result import (
    ALLOCATION_BIRTH_ATTEMPTS,
    ALLOCATION_BIRTH_INVOCATIONS,
    ALLOCATION_BIRTH_LAST_TRANSITION,
    ALLOCATION_BIRTH_ORDER,
    CAMPAIGN_SHA256,
    CLAIMS,
    COMPATIBLE_REFERENCE_BYTES,
    DEVICE_NUMERIC_CAP_BYTES,
    DEVICE_PEAK_BYTES,
    DEVICE_RESERVE_BYTES,
    ERROR_LIMITS,
    EXPECTED_INVOCATIONS,
    EXPECTED_OWNERSHIP,
    FEATURE_WIDTH,
    HOST_NUMERIC_CAP_BYTES,
    HOST_PEAK_BYTES,
    HOST_RESERVE_BYTES,
    MAXIMUM_ARTIFACT_BYTES,
    OWNER_PROTOCOL_SHA256,
    PHASE_POOL_LIMITS,
    QUERY_SAMPLE_FEATURES,
    REQUIRED_RUNTIME,
    SOURCE_REFERENCE_BYTES,
    TELEMETRY_TRANSITIONS,
    chunk_spans,
    rebind_literal_45_quotient_target_journal,
    reconstruct_target_observation,
    target_geometry,
    target_work,
)
from pontius.literal_45_quotient_target_runner import (
    execute_owner_to_path,
    load_public_config,
)


def _semantic_digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


def _row(transition: str, *, release_pool_total: int = 0) -> dict[str, object]:
    return {
        "transition": transition,
        "owned_arrays": list(EXPECTED_OWNERSHIP[transition]),
        "pool_used_bytes": 0,
        "pool_total_bytes": (
            release_pool_total if transition == "released" else 0
        ),
        "pinned_free_blocks": 0,
        "device_free_bytes": 15_000_000_000,
        "device_total_bytes": REQUIRED_RUNTIME["device_total_bytes"],
        "host_available_physical_bytes": 20_000_000_000,
        "process_working_set_bytes": 100_000_000,
        "process_private_bytes": 80_000_000,
        "modeled_pool_limit_bytes": PHASE_POOL_LIMITS[transition],
    }


def synthetic_target(
    kind: str = "pass",
    *,
    allocation_birth: str = "device_source_recurrence",
) -> dict[str, object]:
    model = {
        "host_numeric_cap_bytes": HOST_NUMERIC_CAP_BYTES,
        "device_numeric_cap_bytes": DEVICE_NUMERIC_CAP_BYTES,
        "host_reserve_bytes": HOST_RESERVE_BYTES,
        "device_reserve_bytes": DEVICE_RESERVE_BYTES,
        "host_peak_bytes": HOST_PEAK_BYTES,
        "device_peak_bytes": DEVICE_PEAK_BYTES,
        "source_reference_bytes": SOURCE_REFERENCE_BYTES,
        "compatible_reference_bytes": COMPATIBLE_REFERENCE_BYTES,
        "source_reference_chunks": 125,
        "compatible_reference_chunks": 14,
        "phase_pool_limits": dict(PHASE_POOL_LIMITS),
    }
    telemetry = [_row(name) for name in TELEMETRY_TRANSITIONS]
    admission = {
        "host_total_physical_bytes": 64_000_000_000,
        "host_available_physical_bytes": 20_000_000_000,
        "process_working_set_bytes": 100_000_000,
        "process_private_bytes": 80_000_000,
        "device_free_bytes": 15_000_000_000,
        "device_total_bytes": REQUIRED_RUNTIME["device_total_bytes"],
        "pool_used_bytes": 0,
        "pool_total_bytes": 0,
        "pinned_free_blocks": 0,
        "target_numeric_allocation_calls": 0,
        "target_scientific_call_count": 0,
    }
    identities = {
        "warm_byte_identity": True,
        "source_refresh_byte_identity": True,
        "query_only_byte_identity": True,
        "query_only_source_preserved": True,
        "query_only_compatible_preserved": True,
        "adjoint_byte_identity": True,
        "forward_dot_left": "host_compatible_reference",
        "forward_dot_right": "device_query_covector",
        "transpose_dot_left": "host_source_reference",
        "transpose_dot_right": "device_unique_adjoint",
    }
    target = {
        "schema_version": "literal-45-quotient-target-observation-v1",
        "protocol_sha256": OWNER_PROTOCOL_SHA256,
        "claims": dict(CLAIMS),
        "geometry": target_geometry(),
        "model": model,
        "runtime": dict(REQUIRED_RUNTIME),
        "admission": admission,
        "telemetry": telemetry,
        "work": target_work(),
        "observed_invocations": dict(EXPECTED_INVOCATIONS),
        "counters": {
            "target_execution_calls": 1,
            "target_numeric_allocation_calls": 35,
            "target_scientific_call_count": 19,
        },
        "identities": identities,
        "errors_hex": {key: 0.0.hex() for key in ERROR_LIMITS},
        "timings_hex": {
            key: 1.0.hex()
            for key in (
                "cold",
                "warm",
                "source_refresh",
                "source_refresh_repeat",
                "query_only",
                "query_only_repeat",
                "direct",
                "adjoint",
                "adjoint_repeat",
            )
        },
        "wall_hex": 10.0.hex(),
        "chunks": {
            "source_reference": [
                list(span) for span in chunk_spans(SOURCE_REFERENCE_BYTES)
            ],
            "compatible_forward_dot": [
                list(span) for span in chunk_spans(COMPATIBLE_REFERENCE_BYTES)
            ],
            "source_transpose_dot": [
                list(span) for span in chunk_spans(SOURCE_REFERENCE_BYTES)
            ],
        },
        "digests": {
            "source_before_adjoint": "0" * 64,
            "compatible": "1" * 64,
            "query_covector": "2" * 64,
            "unique_adjoint": "3" * 64,
        },
        "allocation_failure": None,
    }
    if kind == "numerical":
        target["errors_hex"]["source_sample_absolute"] = (1e-3).hex()
    elif kind == "release":
        target["telemetry"][-1] = _row("released", release_pool_total=1)
    elif kind == "live":
        target["admission"]["host_available_physical_bytes"] = 1
        before = _row("before_allocation")
        before["host_available_physical_bytes"] = 1
        target["telemetry"] = [before]
        target["counters"] = {
            "target_execution_calls": 1,
            "target_numeric_allocation_calls": 0,
            "target_scientific_call_count": 0,
        }
        target["observed_invocations"] = {
            key: 0 for key in EXPECTED_INVOCATIONS
        }
        target["identities"] = {key: None for key in identities}
        target["errors_hex"] = {key: None for key in ERROR_LIMITS}
        target["timings_hex"] = {}
        target["chunks"] = {}
        target["digests"] = {}
    elif kind == "allocation":
        if allocation_birth not in ALLOCATION_BIRTH_ATTEMPTS:
            raise ValueError("unknown synthetic allocation birth")
        last = ALLOCATION_BIRTH_LAST_TRANSITION[allocation_birth]
        prefix_stop = TELEMETRY_TRANSITIONS.index(last) + 1
        target["telemetry"] = [
            _row(transition) for transition in TELEMETRY_TRANSITIONS[:prefix_stop]
        ] + [_row("released")]
        target["counters"] = {
            "target_execution_calls": 1,
            "target_numeric_allocation_calls": ALLOCATION_BIRTH_ATTEMPTS[
                allocation_birth
            ],
            "target_scientific_call_count": sum(
                ALLOCATION_BIRTH_INVOCATIONS[allocation_birth][field]
                for field in (
                    "source_build_invocations",
                    "signed_query_invocations",
                    "affine_fold_invocations",
                    "adjoint_invocations",
                    "direct_scan_invocations",
                )
            ),
        }
        target["observed_invocations"] = dict(
            ALLOCATION_BIRTH_INVOCATIONS[allocation_birth]
        )
        target["identities"] = {key: None for key in identities}
        target["errors_hex"] = {key: None for key in ERROR_LIMITS}
        target["timings_hex"] = {}
        target["chunks"] = {}
        target["digests"] = {}
        target["allocation_failure"] = {
            "birth": allocation_birth,
            "failure_type": "OutOfMemoryError",
            "message": "synthetic allocation rejection",
            "last_completed_transition": last,
        }
    elif kind != "pass":
        raise ValueError("unknown synthetic target kind")
    return target


def _git() -> dict[str, object]:
    return {
        "commit": "a" * 40,
        "dirty": False,
        "strict_status": True,
    }


class Literal45TargetResultTests(unittest.TestCase):
    def test_reader_reconstructs_all_five_terminal_classes(self) -> None:
        expected = {
            "pass": "completed_pass",
            "live": "live_admission_rejected",
            "allocation": "allocation_rejected",
            "numerical": "scientific_rejected",
            "release": "infrastructure_failure",
        }
        for kind, terminal in expected.items():
            with self.subTest(kind=kind):
                rebound = reconstruct_target_observation(synthetic_target(kind))
                self.assertEqual(rebound.terminal, terminal)
                self.assertIs(rebound.passed, terminal == "completed_pass")

    def test_owner_header_is_durable_before_every_injected_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.jsonl"
            observed: list[str] = []

            def config_loader():
                recovery = recover_journal_bytes(path.read_bytes())
                self.assertEqual(len(recovery.records), 1)
                self.assertEqual(recovery.records[0].body.kind.value, "header")
                observed.append("config")
                return load_public_config()

            def git_loader():
                self.assertEqual(observed, ["config"])
                self.assertEqual(len(recover_journal_bytes(path.read_bytes()).records), 1)
                observed.append("git")
                return _git()

            def target_executor():
                self.assertEqual(observed, ["config", "git"])
                self.assertEqual(len(recover_journal_bytes(path.read_bytes()).records), 1)
                observed.append("target")
                return synthetic_target("pass")

            execution = execute_owner_to_path(
                output_path=path,
                config_loader=config_loader,
                git_loader=git_loader,
                target_executor=target_executor,
            )
            self.assertEqual(observed, ["config", "git", "target"])
            self.assertEqual(execution.terminal["terminal"], "completed_pass")
            rebound = rebind_literal_45_quotient_target_journal(path.read_bytes())
            self.assertEqual(rebound.terminal, "completed_pass")
            self.assertLess(rebound.journal_byte_count, MAXIMUM_ARTIFACT_BYTES)

    def test_owner_retains_each_synthetic_outcome_and_never_replays(self) -> None:
        expected = {
            "pass": "completed_pass",
            "live": "live_admission_rejected",
            "allocation": "allocation_rejected",
            "numerical": "scientific_rejected",
            "release": "infrastructure_failure",
        }
        loaded = load_public_config()
        for kind, terminal in expected.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "result.jsonl"
                execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda loaded=loaded: loaded,
                    git_loader=_git,
                    target_executor=lambda kind=kind: synthetic_target(kind),
                )
                rebound = rebind_literal_45_quotient_target_journal(
                    path.read_bytes(), expected_config_sha256=loaded.sha256
                )
                self.assertEqual(rebound.terminal, terminal)
                with self.assertRaises(FileExistsError):
                    execute_owner_to_path(
                        output_path=path,
                        config_loader=lambda loaded=loaded: loaded,
                        git_loader=_git,
                        target_executor=lambda: synthetic_target("pass"),
                    )

    def test_pre_observation_exception_and_oversize_are_durable_failures(self) -> None:
        loaded = load_public_config()
        cases = (
            (lambda: (_ for _ in ()).throw(RuntimeError("synthetic boom"))),
            (lambda: (_ for _ in ()).throw(RuntimeError("z" * 900_000))),
            (lambda: {**synthetic_target("pass"), "oversized": "x" * 800_000}),
        )
        for executor in cases:
            with self.subTest(executor=executor), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "result.jsonl"
                execution = execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda loaded=loaded: loaded,
                    git_loader=_git,
                    target_executor=executor,
                )
                self.assertEqual(
                    execution.terminal["terminal"], "infrastructure_failure"
                )
                rebound = rebind_literal_45_quotient_target_journal(path.read_bytes())
                self.assertEqual(rebound.terminal, "infrastructure_failure")
                self.assertIsNone(rebound.target)
                self.assertLess(len(execution.terminal["reason"]), 4_200)

    def test_torn_and_fully_rehashed_semantic_mutations_fail_closed(self) -> None:
        loaded = load_public_config()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.jsonl"
            execute_owner_to_path(
                output_path=path,
                config_loader=lambda: loaded,
                git_loader=_git,
                target_executor=lambda: synthetic_target("pass"),
            )
            raw = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                rebind_literal_45_quotient_target_journal(raw[:-1])

            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=OWNER_PROTOCOL_SHA256,
                expected_campaign_sha256=CAMPAIGN_SHA256,
            )
            payloads = [deepcopy(record.body.payload) for record in recovery.records]
            payloads[1]["target"]["errors_hex"]["source_sample_absolute"] = (1e-3).hex()
            observation_identity = _semantic_digest(payloads[1])
            payloads[2]["observation_semantic_identity_sha256"] = observation_identity
            semantic = (
                _semantic_digest(payloads[0]),
                observation_identity,
                _semantic_digest(payloads[2]),
            )
            lines: list[bytes] = []
            previous: str | None = None
            for index, (record, payload) in enumerate(zip(recovery.records, payloads)):
                body = build_journal_record_body(
                    protocol_sha256=OWNER_PROTOCOL_SHA256,
                    campaign_sha256=CAMPAIGN_SHA256,
                    kind=record.body.kind,
                    sequence=index,
                    previous_record_sha256=previous,
                    semantic_identity_sha256=semantic[index],
                    payload=payload,
                )
                envelope = JournalRecordEnvelope(body=body)
                lines.append(envelope.line_bytes)
                previous = envelope.line_sha256
            with self.assertRaisesRegex(ValueError, "stored terminal differs"):
                rebind_literal_45_quotient_target_journal(b"".join(lines))

    def test_campaign_and_reporting_digests_cannot_be_repurposed(self) -> None:
        target = synthetic_target("pass")
        target["digests"]["source_before_adjoint"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "reporting digest"):
            reconstruct_target_observation(target)
        negative = synthetic_target("pass")
        negative["errors_hex"]["source_sample_absolute"] = (-1e-15).hex()
        self.assertEqual(
            reconstruct_target_observation(negative).terminal,
            "scientific_rejected",
        )
        impossible = synthetic_target("allocation")
        impossible["allocation_failure"]["last_completed_transition"] = (
            "forward_released"
        )
        with self.assertRaisesRegex(ValueError, "birth/transition"):
            reconstruct_target_observation(impossible)
        impossible_count = synthetic_target("allocation")
        impossible_count["counters"]["target_numeric_allocation_calls"] = 1
        self.assertEqual(
            reconstruct_target_observation(impossible_count).terminal,
            "infrastructure_failure",
        )
        impossible_future = synthetic_target("allocation")
        impossible_future["observed_invocations"] = dict(EXPECTED_INVOCATIONS)
        self.assertEqual(
            reconstruct_target_observation(impossible_future).terminal,
            "infrastructure_failure",
        )
        for birth in ALLOCATION_BIRTH_ORDER:
            with self.subTest(allocation_birth=birth):
                exact = reconstruct_target_observation(
                    synthetic_target("allocation", allocation_birth=birth)
                )
                self.assertEqual(exact.terminal, "allocation_rejected")
                self.assertTrue(exact.gates["allocation_attempt_identity"])
                self.assertTrue(
                    exact.gates["partial_invocations_exact_and_future_blank"]
                )
        self.assertEqual(len(QUERY_SAMPLE_FEATURES), 8)
        self.assertEqual(FEATURE_WIDTH, 128)


if __name__ == "__main__":
    unittest.main()
