from __future__ import annotations

import ast
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pontius.native_simplex_audit_reanalysis as reanalysis
from pontius.native_simplex_audit_reanalysis import (
    ADR0315_RETAINED_AUDIT_CONTRACT,
    CrossBackendSizingAllowance,
    CrossVariantSizingAllowance,
    KnownRegressionSignature,
    MicroVariantComparisonAllowance,
    RetainedAuditContract,
    canonical_lf_source_sha256,
    reanalyze_retained_audit_bytes,
    reanalyze_sealed_adr0314_artifact,
)

_CAMPAIGN = "pontius.native_simplex_audit_runner.AuditCampaignResult"
_OBSERVATION = "pontius.native_simplex_audit_runner.AuditInvocationObservation"
_INVOCATION = "pontius.native_simplex_audit_runner.ScheduledAuditInvocation"
_BACKEND_RESULT = "pontius.native_simplex_audit_runner.BackendRawResult"
_EXCEPTION = "pontius.native_simplex_audit_runner.AuditExceptionRecord"
_TRACE = "pontius.native_simplex_audit_runner.NativeVerificationTrace"
_COORDINATES = "pontius.native_simplex_audit_runner.NativeFailureCoordinates"
_MICRO = "pontius.native_simplex_audit_runner.MicroAuditVerification"
_SIZING = "pontius.native_simplex_audit_runner.SizingAuditVerification"
_COORDINATE_DIAGNOSTICS = "pontius.native_simplex_audit_runner.BackendCoordinateDiagnostics"
_CERTIFICATE_DIAGNOSTICS = "pontius.native_simplex_audit_runner.BackendCertificateDiagnostics"
_EXACT_MICRO = "pontius.native_simplex_audit_runner.ExactMicroEnumeration"
_BACKENDS = ("native", "highs-ds", "highs-ipm")
_VARIANTS = (
    "canonical",
    "row-permutation",
    "variable-permutation",
    "dyadic-row-scaling",
    "redundancy",
)
_RUNNER_VERSION = "toy-runner-v1"
_RUNNER_SHA256 = "1" * 64
_CORPUS_SHA256 = "2" * 64
_ANALYZER_SHA256 = "a" * 64
_KNOWN_BASE = "toy-known-sizing"
_MICRO_BASE = "toy-exact-micro"
_KNOWN_VARIANT = f"{_KNOWN_BASE}--canonical"


def _wrapped(name: str, **fields: object) -> dict[str, object]:
    return {"dataclass": name, "fields": fields}


def _float(value: float) -> dict[str, str]:
    return {"float_hex": value.hex()}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _backend_result(backend: str, *, known_exception: bool) -> dict[str, object]:
    exception = None
    trace = None
    if known_exception:
        exception = _wrapped(
            _EXCEPTION,
            stage="backend-invocation",
            module="builtins",
            qualname="AssertionError",
            message="toy native verification failure",
            arguments=["toy native verification failure"],
            traceback_frames=[],
        )
        trace = _wrapped(
            _TRACE,
            primal_variant_coordinates=[_float(0.0)],
            raw_maximization_objective=_float(1.0),
            dual_hint_variant_rows=[_float(0.0)] * 4,
            pivots=7,
            constraint_residuals_variant_rows=[
                _float(1.0),
                _float(2.0),
                _float(0.0),
                _float(4.0),
            ],
            verification_allowance=_float(0.1),
        )
    optimal = not known_exception
    return _wrapped(
        _BACKEND_RESULT,
        backend=backend,
        termination="optimal" if optimal else "exception",
        status_code=0 if optimal else None,
        status_text="optimal" if optimal else "exception",
        message="optimal" if optimal else "toy native verification failure",
        iterations=2 if optimal else 7,
        crossover_iterations=0 if optimal else None,
        primal_variant_coordinates=[_float(0.5)] if optimal else None,
        reported_maximization_objective=_float(1.0) if optimal else None,
        dual_hint_variant_rows=[_float(0.0)] if optimal else None,
        dual_hint_convention="toy" if optimal else None,
        elapsed_seconds=_float(0.001),
        exception=exception,
        native_verification_trace=trace,
    )


def _verification(family: str) -> dict[str, object]:
    if family == "micro":
        return _wrapped(
            _MICRO,
            failures=[],
            reconstructed_objective=_float(1.0),
        )
    return _wrapped(
        _SIZING,
        failures=[],
        behavioral_lower_bound_chips=_float(1.0),
        certified_upper_bound_chips=_float(2.0),
    )


def _build_campaign() -> dict[str, object]:
    observations: list[object] = []
    task_index = 0
    for base_id, family in ((_KNOWN_BASE, "sizing"), (_MICRO_BASE, "micro")):
        for variant_kind in _VARIANTS:
            variant_id = f"{base_id}--{variant_kind}"
            for backend in _BACKENDS:
                known_exception = variant_id == _KNOWN_VARIANT and backend == "native"
                observations.append(
                    _wrapped(
                        _OBSERVATION,
                        invocation=_wrapped(
                            _INVOCATION,
                            ordinal=len(observations),
                            task_index=task_index,
                            base_id=base_id,
                            variant_id=variant_id,
                            backend=backend,
                        ),
                        backend_result=_backend_result(
                            backend,
                            known_exception=known_exception,
                        ),
                        exact_micro_work=(_wrapped(_EXACT_MICRO) if family == "micro" else None),
                        coordinate_diagnostics=(
                            None if known_exception else _wrapped(_COORDINATE_DIAGNOSTICS)
                        ),
                        certificate_diagnostics=(
                            None if known_exception else _wrapped(_CERTIFICATE_DIAGNOSTICS)
                        ),
                        micro_verification=(_verification("micro") if family == "micro" else None),
                        sizing_verification=(
                            _verification("sizing") if family == "sizing" else None
                        ),
                        native_failure_coordinates=(
                            _wrapped(
                                _COORDINATES,
                                failing_variant_rows=[0, 1, 3],
                                failing_canonical_rows=[0, 1, 3],
                                maximum_variant_residual=_float(4.0),
                                verification_allowance=_float(0.1),
                            )
                            if known_exception
                            else None
                        ),
                        runner_failures=[],
                    )
                )
            task_index += 1
    return _wrapped(
        _CAMPAIGN,
        runner_version=_RUNNER_VERSION,
        runner_source_sha256=_RUNNER_SHA256,
        corpus_sha256=_CORPUS_SHA256,
        environment={"identity": "synthetic-only"},
        protocol={"schedule": "two-base-five-variant-three-backend"},
        observations=observations,
        sealed_adr0311=True,
    )


def _known_signature() -> KnownRegressionSignature:
    return KnownRegressionSignature(
        base_id=_KNOWN_BASE,
        variant_id=_KNOWN_VARIANT,
        exception_module="builtins",
        exception_qualname="AssertionError",
        exception_message="toy native verification failure",
        pivots=7,
        verification_allowance_hex=(0.1).hex(),
        maximum_residual_hex=(4.0).hex(),
        required_unique_maximum_row=3,
    )


def _contract_for(
    campaign: dict[str, object],
    *,
    raw: bytes | None = None,
    signature: KnownRegressionSignature | None = None,
    micro_allowance: float = 0.1,
    backend_allowance: float = 0.1,
    variant_allowance: float = 0.1,
) -> tuple[bytes, RetainedAuditContract]:
    if raw is None:
        raw = _canonical_bytes(campaign)
    campaign_fields = campaign["fields"]
    assert isinstance(campaign_fields, dict)
    return raw, RetainedAuditContract(
        artifact_sha256=hashlib.sha256(raw).hexdigest(),
        artifact_bytes=len(raw),
        runner_version=_RUNNER_VERSION,
        runner_source_sha256=_RUNNER_SHA256,
        corpus_sha256=_CORPUS_SHA256,
        environment_subtree_sha256=hashlib.sha256(
            _canonical_bytes(campaign_fields["environment"])
        ).hexdigest(),
        protocol_subtree_sha256=hashlib.sha256(
            _canonical_bytes(campaign_fields["protocol"])
        ).hexdigest(),
        expected_observation_count=30,
        expected_variant_count=10,
        expected_base_count=2,
        expected_micro_base_count=1,
        expected_sizing_base_count=1,
        micro_variant_allowance=MicroVariantComparisonAllowance(micro_allowance),
        cross_backend_sizing_allowance=CrossBackendSizingAllowance(backend_allowance),
        cross_variant_sizing_allowance=CrossVariantSizingAllowance(variant_allowance),
        known_regression=signature or _known_signature(),
    )


def _observations(campaign: dict[str, object]) -> list[dict[str, object]]:
    campaign_fields = campaign["fields"]
    assert isinstance(campaign_fields, dict)
    values = campaign_fields["observations"]
    assert isinstance(values, list)
    return values


def _fields(wrapper: dict[str, object]) -> dict[str, object]:
    value = wrapper["fields"]
    assert isinstance(value, dict)
    return value


def _analyze(campaign: dict[str, object], **contract_options: object):
    raw, contract = _contract_for(campaign, **contract_options)
    return reanalyze_retained_audit_bytes(
        raw,
        contract=contract,
        analyzer_source_sha256=_ANALYZER_SHA256,
    )


class NativeSimplexAuditReanalysisTests(unittest.TestCase):
    def test_multirow_failure_and_unique_maximum_are_distinct_semantics(self) -> None:
        campaign = _build_campaign()
        assessment = _analyze(campaign)

        self.assertTrue(assessment.highs_dual_simplex_eligible)
        self.assertTrue(assessment.known_native_regression_reproduced)
        self.assertEqual(assessment.failures, ())
        self.assertEqual(assessment.observation_count, 30)
        self.assertEqual(assessment.variant_count, 10)
        self.assertEqual(assessment.base_count, 2)
        self.assertEqual(assessment.native_verified_count, 9)
        self.assertEqual(assessment.native_exception_count, 1)
        self.assertEqual(assessment.highs_ds_verified_count, 10)
        self.assertEqual(assessment.highs_ipm_verified_count, 10)
        self.assertIsNotNone(assessment.known_native_regression)
        assert assessment.known_native_regression is not None
        self.assertEqual(assessment.known_native_regression.failing_rows, (0, 1, 3))
        self.assertEqual(assessment.known_native_regression.unique_maximum_rows, (3,))
        second = _analyze(campaign)
        self.assertEqual(assessment.canonical_bytes, second.canonical_bytes)
        self.assertEqual(assessment.digest, second.digest)

        exclusive = replace(
            _known_signature(),
            expected_complete_failing_rows=(3,),
        )
        rejected = _analyze(campaign, signature=exclusive)
        self.assertFalse(rejected.highs_dual_simplex_eligible)
        self.assertEqual(
            tuple(failure.code for failure in rejected.failures),
            ("known-native-regression-mismatch",),
        )

    def test_tied_maximum_does_not_satisfy_unique_maximum_signature(self) -> None:
        campaign = _build_campaign()
        known = _fields(_observations(campaign)[0])
        result = _fields(known["backend_result"])
        trace = _fields(result["native_verification_trace"])
        trace["constraint_residuals_variant_rows"] = [
            _float(1.0),
            _float(2.0),
            _float(4.0),
            _float(4.0),
        ]
        coordinates = _fields(known["native_failure_coordinates"])
        coordinates["failing_variant_rows"] = [0, 1, 2, 3]
        coordinates["failing_canonical_rows"] = [0, 1, 2, 3]

        assessment = _analyze(campaign)

        self.assertFalse(assessment.known_native_regression_reproduced)
        assert assessment.known_native_regression is not None
        self.assertEqual(assessment.known_native_regression.unique_maximum_rows, (2, 3))

    def test_trace_coordinates_and_pivots_must_be_self_consistent(self) -> None:
        for mutation, expected in (
            ("stored-rows", "failure rows disagree"),
            ("trace-pivots", "trace pivots disagree"),
        ):
            with self.subTest(mutation=mutation):
                campaign = _build_campaign()
                known = _fields(_observations(campaign)[0])
                result = _fields(known["backend_result"])
                if mutation == "stored-rows":
                    coordinates = _fields(known["native_failure_coordinates"])
                    coordinates["failing_variant_rows"] = [3]
                else:
                    trace = _fields(result["native_verification_trace"])
                    trace["pivots"] = 8
                raw, contract = _contract_for(campaign)
                with self.assertRaisesRegex(ValueError, expected):
                    reanalyze_retained_audit_bytes(
                        raw,
                        contract=contract,
                        analyzer_source_sha256=_ANALYZER_SHA256,
                    )

    def test_each_unchanged_highs_gate_remains_binding(self) -> None:
        cases = []

        def fail_instance(campaign: dict[str, object]) -> None:
            observation = _fields(_observations(campaign)[1])
            verification = _fields(observation["sizing_verification"])
            verification["failures"] = ["synthetic failure"]

        cases.append(("instance", fail_instance, ("highs-instance-failed",)))

        def spread_micro(campaign: dict[str, object]) -> None:
            observation = _fields(_observations(campaign)[16])
            verification = _fields(observation["micro_verification"])
            verification["reconstructed_objective"] = _float(1.2)

        cases.append(("micro", spread_micro, ("micro-variant-disagreement",)))

        def empty_intersection(campaign: dict[str, object]) -> None:
            for index in (1, 2):
                observation = _fields(_observations(campaign)[index])
                verification = _fields(observation["sizing_verification"])
                verification["behavioral_lower_bound_chips"] = _float(3.0)
                verification["certified_upper_bound_chips"] = _float(3.1)

        cases.append(("intersection", empty_intersection, ("sizing-interval-intersection-empty",)))

        def backend_disagreement(campaign: dict[str, object]) -> None:
            observation = _fields(_observations(campaign)[2])
            verification = _fields(observation["sizing_verification"])
            verification["behavioral_lower_bound_chips"] = _float(1.25)

        cases.append(("backend", backend_disagreement, ("sizing-cross-backend-disagreement",)))

        for label, mutate, expected in cases:
            with self.subTest(gate=label):
                campaign = _build_campaign()
                mutate(campaign)
                assessment = _analyze(campaign)
                self.assertFalse(assessment.highs_dual_simplex_eligible)
                self.assertEqual(
                    tuple(failure.code for failure in assessment.failures),
                    expected,
                )

    def test_allowance_types_are_distinct_and_change_only_their_gate(self) -> None:
        with self.assertRaisesRegex(TypeError, "nonsemantic field"):
            replace(
                _contract_for(_build_campaign())[1],
                cross_backend_sizing_allowance=CrossVariantSizingAllowance(0.1),
            )

        campaign = _build_campaign()
        observation = _fields(_observations(campaign)[16])
        verification = _fields(observation["micro_verification"])
        verification["reconstructed_objective"] = _float(1.2)
        failed = _analyze(campaign)
        passed = _analyze(campaign, micro_allowance=0.3)
        self.assertEqual(
            tuple(failure.code for failure in failed.failures),
            ("micro-variant-disagreement",),
        )
        self.assertTrue(passed.highs_dual_simplex_eligible)

    def test_exact_boundary_rejects_noncanonical_duplicate_and_raw_float_json(self) -> None:
        campaign = _build_campaign()
        pretty = json.dumps(campaign, sort_keys=True, indent=2).encode("ascii")
        pretty_raw, pretty_contract = _contract_for(campaign, raw=pretty)
        with self.assertRaisesRegex(ValueError, "not canonical JSON"):
            reanalyze_retained_audit_bytes(
                pretty_raw,
                contract=pretty_contract,
                analyzer_source_sha256=_ANALYZER_SHA256,
            )

        duplicate = b'{"duplicate":1,"duplicate":2}'
        duplicate_raw, duplicate_contract = _contract_for(campaign, raw=duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reanalyze_retained_audit_bytes(
                duplicate_raw,
                contract=duplicate_contract,
                analyzer_source_sha256=_ANALYZER_SHA256,
            )

        raw_float_campaign = _build_campaign()
        raw_float_fields = _fields(raw_float_campaign)
        raw_float_fields["unreachable_float"] = 1.5
        raw, contract = _contract_for(raw_float_campaign)
        with self.assertRaisesRegex(TypeError, "raw JSON float"):
            reanalyze_retained_audit_bytes(
                raw,
                contract=contract,
                analyzer_source_sha256=_ANALYZER_SHA256,
            )

    def test_schedule_and_schema_mutations_fail_closed(self) -> None:
        for label in ("ordinal", "backend", "variant", "schema"):
            with self.subTest(mutation=label):
                campaign = _build_campaign()
                observation = _fields(_observations(campaign)[1])
                invocation = _fields(observation["invocation"])
                if label == "ordinal":
                    invocation["ordinal"] = 99
                elif label == "backend":
                    invocation["backend"] = "highs-ipm"
                elif label == "variant":
                    invocation["variant_id"] = "unexpected-representation"
                else:
                    del observation["runner_failures"]
                raw, contract = _contract_for(campaign)
                with self.assertRaises((TypeError, ValueError)):
                    reanalyze_retained_audit_bytes(
                        raw,
                        contract=contract,
                        analyzer_source_sha256=_ANALYZER_SHA256,
                    )

    def test_real_contract_records_unique_max_without_exclusive_failure_claim(self) -> None:
        contract = ADR0315_RETAINED_AUDIT_CONTRACT
        self.assertEqual(contract.known_regression.required_unique_maximum_row, 215)
        self.assertIsNone(contract.known_regression.expected_complete_failing_rows)
        self.assertIsInstance(
            contract.micro_variant_allowance,
            MicroVariantComparisonAllowance,
        )
        self.assertIsInstance(
            contract.cross_backend_sizing_allowance,
            CrossBackendSizingAllowance,
        )
        self.assertIsInstance(
            contract.cross_variant_sizing_allowance,
            CrossVariantSizingAllowance,
        )

    def test_analyzer_import_graph_and_effect_surface_are_artifact_only(self) -> None:
        source_path = Path(reanalysis.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        attributes: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)

        self.assertTrue(
            imported.isdisjoint(
                {
                    "scipy",
                    "pontius.linear_program",
                    "pontius.native_simplex_audit_runner",
                    "pontius.native_simplex_audit_corpus",
                }
            )
        )
        self.assertTrue(
            attributes.isdisjoint(
                {
                    "write_bytes",
                    "write_text",
                    "unlink",
                    "rename",
                }
            )
        )

    def test_source_seal_is_line_ending_stable_and_checked_before_artifact_read(self) -> None:
        from pontius.native_simplex_audit_reanalysis_seal import (
            ADR0315_ANALYZER_SOURCE_SHA256,
        )

        source_path = Path(reanalysis.__file__)
        self.assertEqual(
            canonical_lf_source_sha256(source_path),
            ADR0315_ANALYZER_SOURCE_SHA256,
        )
        with tempfile.TemporaryDirectory() as directory:
            crlf_copy = Path(directory) / "reanalyzer.py"
            normalized = source_path.read_bytes().replace(b"\r\n", b"\n")
            crlf_copy.write_bytes(normalized.replace(b"\n", b"\r\n"))
            self.assertEqual(
                canonical_lf_source_sha256(crlf_copy),
                ADR0315_ANALYZER_SOURCE_SHA256,
            )

        with (
            patch(
                "pontius.native_simplex_audit_reanalysis_seal.ADR0315_ANALYZER_SOURCE_SHA256",
                "f" * 64,
            ),
            self.assertRaisesRegex(RuntimeError, "differs from its committed seal"),
        ):
            reanalyze_sealed_adr0314_artifact(Path("does-not-exist.json"))


if __name__ == "__main__":
    unittest.main()
