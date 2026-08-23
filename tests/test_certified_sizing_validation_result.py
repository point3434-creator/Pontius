from __future__ import annotations

import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

from pontius.certified_sizing_validation_runner import (
    build_adr0319_canonical_validation_plan,
)


_ROOT = Path(__file__).resolve().parents[1]
_CAMPAIGN = _ROOT / "experiments/results/certified-sizing-canonical-validation-v1.json"
_ASSESSMENT = (
    _ROOT
    / "experiments/results/certified-sizing-canonical-validation-assessment-v1.json"
)
_CAMPAIGN_SHA256 = "5a2a75a9cf0ddaf60795597aa6ff3f788d4bfc7ccf5519813f37856dad02f9f5"
_ASSESSMENT_SHA256 = "a3c360c61ae6edd28eb2df68b83339a549d6726a151c60fee46bc488dc54bfd9"
_RUNNER_SHA256 = "5116c1d4b2632da76cf83e6d7d015b190e061330094d27b3c9719631a89252e1"
_CORPUS_SHA256 = "4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3"
_SCHEDULE_SHA256 = "36f34eb820bfaa4b58747201c9b27779553d0f8e250c73786da34542b5d8cba4"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _fields(value: object, expected_dataclass: str | None = None) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("retained dataclass record must be a mapping")
    if expected_dataclass is not None and value.get("dataclass") != expected_dataclass:
        raise ValueError("retained dataclass identity drifted")
    result = value.get("fields")
    if not isinstance(result, dict):
        raise TypeError("retained dataclass fields must be a mapping")
    return result


def _float(value: object) -> float:
    if not isinstance(value, dict) or set(value) != {"float_hex"}:
        raise TypeError("retained float must use the exact hexadecimal schema")
    encoded = value["float_hex"]
    if not isinstance(encoded, str):
        raise TypeError("retained hexadecimal float must be text")
    return float.fromhex(encoded)


class CertifiedSizingValidationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.campaign_bytes = _CAMPAIGN.read_bytes()
        cls.assessment_bytes = _ASSESSMENT.read_bytes()
        cls.campaign = json.loads(cls.campaign_bytes)
        cls.assessment = json.loads(cls.assessment_bytes)
        cls.campaign_fields = _fields(
            cls.campaign,
            (
                "pontius.certified_sizing_validation_runner."
                "CanonicalValidationCampaign"
            ),
        )
        cls.assessment_fields = _fields(
            cls.assessment,
            (
                "pontius.certified_sizing_validation_runner."
                "CanonicalValidationAssessment"
            ),
        )
        cls.observations = [
            _fields(
                observation,
                (
                    "pontius.certified_sizing_validation_runner."
                    "CanonicalValidationObservation"
                ),
            )
            for observation in cls.campaign_fields["observations"]
        ]
        cls.plan = build_adr0319_canonical_validation_plan()

    def test_retained_bytes_and_hashes_are_exact(self) -> None:
        self.assertEqual(len(self.campaign_bytes), 5_022_120)
        self.assertEqual(
            hashlib.sha256(self.campaign_bytes).hexdigest(),
            _CAMPAIGN_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(self.assessment_bytes).hexdigest(),
            _ASSESSMENT_SHA256,
        )
        self.assertEqual(_canonical_json_bytes(self.campaign), self.campaign_bytes)
        self.assertEqual(_canonical_json_bytes(self.assessment), self.assessment_bytes)

    def test_campaign_provenance_matches_the_source_seal_and_exact_schedule(self) -> None:
        fields = self.campaign_fields
        self.assertEqual(
            fields["runner_version"],
            "certified-sizing-canonical-validation-runner-v1",
        )
        self.assertEqual(fields["runner_source_sha256"], _RUNNER_SHA256)
        self.assertEqual(fields["corpus_sha256"], _CORPUS_SHA256)
        self.assertEqual(fields["schedule_sha256"], _SCHEDULE_SHA256)
        self.assertIs(fields["sealed_adr0319"], True)
        environment = _fields(
            fields["environment"],
            "pontius.native_simplex_audit_runner.AuditEnvironmentIdentity",
        )
        self.assertEqual(
            environment,
            {
                "highs_version": "1.12.0",
                "numpy_version": "2.5.2",
                "python_implementation": "CPython",
                "python_version": "3.14.6",
                "scipy_version": "1.18.0",
            },
        )
        self.assertEqual(len(self.observations), 177)
        self.assertEqual(self.plan.schedule_digest, _SCHEDULE_SHA256)

    def test_every_observation_matches_its_value_free_task_and_one_call_contract(self) -> None:
        for retained, task in zip(self.observations, self.plan.tasks, strict=True):
            self.assertEqual(retained["ordinal"], task.ordinal)
            self.assertEqual(retained["base_id"], task.base.base_id)
            self.assertEqual(retained["base_sha256"], task.base.digest)
            self.assertEqual(retained["family"], task.base.family.value)
            self.assertEqual(retained["path"], task.path.value)
            self.assertEqual(
                retained["canonical_linear_program_sha256"],
                task.materialized.digest,
            )
            self.assertEqual(retained["public_highs_ds_invocation_count"], 1)
            self.assertEqual(retained["failures"], [])
        self.assertEqual(
            Counter(observation["path"] for observation in self.observations),
            {"exact-micro-highs-ds": 48, "certified-sizing-adapter": 129},
        )
        self.assertEqual(
            Counter(observation["family"] for observation in self.observations),
            {
                "exact-micro": 48,
                "fresh-reduced-sizing": 128,
                "known-regression": 1,
            },
        )

    def test_all_micro_results_are_exactly_verified(self) -> None:
        micro = [
            observation
            for observation in self.observations
            if observation["path"] == "exact-micro-highs-ds"
        ]
        exact_errors: list[float] = []
        certificate_gaps: list[float] = []
        for observation in micro:
            self.assertIsNone(observation["sizing_adapter_result"])
            self.assertIsNone(observation["sizing_independent_verification"])
            raw = _fields(
                observation["micro_backend_result"],
                "pontius.native_simplex_audit_runner.BackendRawResult",
            )
            self.assertEqual(raw["backend"], "highs-ds")
            self.assertEqual(raw["termination"], "optimal")
            self.assertEqual(raw["status_code"], 0)
            self.assertIsNone(raw["exception"])
            exact = _fields(
                observation["exact_micro_work"],
                "pontius.native_simplex_audit_runner.ExactMicroEnumeration",
            )
            verification = _fields(
                observation["micro_verification"],
                "pontius.native_simplex_audit_runner.MicroAuditVerification",
            )
            self.assertEqual(exact["case_id"], observation["base_id"])
            self.assertEqual(verification["failures"], [])
            self.assertEqual(
                _fields(verification["certificate"])[
                    "inequality_multiplier_sign_clips"
                ],
                0,
            )
            exact_errors.append(abs(_float(verification["exact_objective_error"])))
            certificate_gaps.append(
                abs(_float(verification["certified_gap_above_exact"]))
            )
        self.assertEqual(max(exact_errors), 1.4210854715202004e-14)
        self.assertEqual(max(certificate_gaps), 1.7053025658242404e-13)

    def test_all_sizing_results_pass_both_authorities_without_repair(self) -> None:
        sizing = [
            observation
            for observation in self.observations
            if observation["path"] == "certified-sizing-adapter"
        ]
        gaps: list[float] = []
        for observation in sizing:
            self.assertIsNone(observation["micro_backend_result"])
            self.assertIsNone(observation["exact_micro_work"])
            self.assertIsNone(observation["micro_verification"])
            adapter = _fields(
                observation["sizing_adapter_result"],
                (
                    "pontius.certified_reduced_sizing_highs."
                    "CertifiedReducedSizingSolution"
                ),
            )
            independent = _fields(
                observation["sizing_independent_verification"],
                "pontius.native_simplex_audit_runner.SizingAuditVerification",
            )
            self.assertEqual(adapter["highs_status_code"], 0)
            self.assertEqual(adapter["policy_clips"], [])
            self.assertEqual(independent["policy_clips"], [])
            self.assertEqual(independent["failures"], [])
            self.assertEqual(
                adapter["raw_primal_variables"],
                independent["canonical_primal"],
            )
            self.assertEqual(
                adapter["raw_inequality_multipliers"],
                _fields(independent["dual_hint"])["raw_variant_hint"],
            )
            self.assertEqual(
                adapter["responder_best_actions"],
                independent["responder_best_actions"],
            )
            self.assertEqual(adapter["certificate"], independent["certificate"])
            self.assertEqual(
                adapter["signed_certificate_gap_chips"],
                independent["certified_optimality_gap_chips"],
            )
            self.assertEqual(
                _fields(adapter["certificate"])[
                    "inequality_multiplier_sign_clips"
                ],
                0,
            )
            gap = _float(adapter["signed_certificate_gap_chips"])
            self.assertGreater(gap, 0.0)
            gaps.append(gap)
        self.assertEqual(max(gaps), 8.493117320540478e-11)

    def test_frozen_assessment_opens_only_bounded_consumer_eligibility(self) -> None:
        fields = self.assessment_fields
        self.assertIs(fields["complete_schedule"], True)
        self.assertIs(fields["one_public_call_per_base"], True)
        self.assertEqual(fields["passed_observation_count"], 177)
        self.assertEqual(fields["failed_observation_count"], 0)
        self.assertEqual(fields["passed_micro_count"], 48)
        self.assertEqual(fields["passed_sizing_count"], 129)
        self.assertEqual(fields["failed_base_ids"], [])
        self.assertEqual(
            _float(fields["maximum_absolute_micro_exact_error"]),
            1.4210854715202004e-14,
        )
        self.assertEqual(
            _float(fields["maximum_absolute_micro_certificate_gap"]),
            1.7053025658242404e-13,
        )
        self.assertEqual(
            _float(fields["maximum_absolute_sizing_certificate_gap_chips"]),
            8.493117320540478e-11,
        )
        self.assertIs(fields["certified_v2_consumer_eligible"], True)


if __name__ == "__main__":
    unittest.main()
