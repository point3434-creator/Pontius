from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from pontius.evidence.errors import (
    AuthorizationPhaseError,
    EvidenceConfigurationError,
    EvidenceError,
    EvidenceIntegrityError,
    LifecycleStateError,
    RuntimeContractError,
)
from pontius.evidence.model import (
    AuthorizationPolicy,
    EvidenceFileIdentity,
    FileIdentity,
    GitIndexEntry,
    GitTreeEntry,
    HistoricalBlobIdentity,
    HistoricalBlobsManifest,
    HistoricalSnapshot,
    LiveAuthorizationState,
    LoadedRetainedV7Manifest,
    PreauthorizationState,
    RetainedV7Assessment,
    RetainedV7Manifest,
    SealedCurrentAbsenceEntry,
    SealedCurrentAbsencesManifest,
    SealedCurrentFileEntry,
    SealedCurrentFilesManifest,
)


SHA256 = "a" * 64
COMMIT = "b" * 40


class EvidenceErrorsAndModelTests(unittest.TestCase):
    def test_public_errors_keep_stable_fields_and_immutable_context(self) -> None:
        for error_type in (
            AuthorizationPhaseError,
            EvidenceConfigurationError,
            EvidenceIntegrityError,
            LifecycleStateError,
            RuntimeContractError,
        ):
            error = error_type(
                "authorization_live_state_required",
                "live authorization is required",
                context={"phase": "preauthorization", "paths": ["a", "b"], "nested": {"roles": {"b", "a"}}},
            )
            self.assertIsInstance(error, EvidenceError)
            self.assertEqual(error.code, "authorization_live_state_required")
            self.assertEqual(error.message, "live authorization is required")
            self.assertEqual(error.context["paths"], ("a", "b"))
            self.assertEqual(error.context["nested"]["roles"], frozenset({"a", "b"}))
            self.assertEqual(tuple(error.context), ("nested", "paths", "phase"))
            with self.assertRaises(TypeError):
                error.context["phase"] = "live_authorization"  # type: ignore[index]

    def test_error_context_rejects_unsupported_values_before_construction(self) -> None:
        with self.assertRaises(TypeError):
            EvidenceIntegrityError("bad_context", "bad context", context={"unsupported": object()})

    def test_evidence_file_identity_is_frozen_normalized_and_validated(self) -> None:
        identity = EvidenceFileIdentity("docs\\artifact.txt", 3, SHA256, "result")
        self.assertEqual(identity.relative_path, "docs/artifact.txt")
        with self.assertRaises(FrozenInstanceError):
            identity.role = "attempt"  # type: ignore[misc]
        for bad_path in ("/absolute.txt", "C:/absolute.txt", "../outside.txt", "docs/../outside.txt"):
            with self.subTest(bad_path=bad_path), self.assertRaises(ValueError):
                EvidenceFileIdentity(bad_path, 3, SHA256, "result")
        for bad_length in (-1, True):
            with self.subTest(bad_length=bad_length), self.assertRaises(ValueError):
                EvidenceFileIdentity("artifact.txt", bad_length, SHA256, "result")
        with self.assertRaises(ValueError):
            EvidenceFileIdentity("artifact.txt", 3, SHA256.upper(), "result")

    def test_identity_and_git_values_reject_boolean_or_invalid_identity_values(self) -> None:
        with self.assertRaises(ValueError):
            FileIdentity("posix", True, 2, 3, 4, 5, 6, None)
        with self.assertRaises(ValueError):
            FileIdentity("windows", 1, 2, 3, 4, 5, 6, None)
        with self.assertRaises(ValueError):
            GitTreeEntry("100644", "blob", COMMIT.upper(), "file.txt")
        with self.assertRaises(ValueError):
            GitIndexEntry("100644", COMMIT, True, "file.txt")

    def test_authorization_models_normalize_paths_and_enforce_exact_values(self) -> None:
        policy = AuthorizationPolicy("config\\authorization.toml", "v1", ("b.toml", "a.toml"))
        self.assertEqual(policy.config_path, "config/authorization.toml")
        self.assertEqual(policy.authorization_commit_paths, ("a.toml", "b.toml"))
        for paths, size in ((("same.toml", "same.toml"), 1), (("one.toml",), 0), (("one.toml",), True)):
            with self.subTest(paths=paths, size=size), self.assertRaises(ValueError):
                AuthorizationPolicy("config.toml", "v1", paths, size)
        with self.assertRaises(ValueError):
            PreauthorizationState(COMMIT, "config.toml", present=0)
        live = LiveAuthorizationState(COMMIT, COMMIT, COMMIT, "config.toml", SHA256, SHA256, ("b.toml", "a.toml"))
        self.assertEqual(live.authorization_commit_paths, ("a.toml", "b.toml"))

    def test_manifest_and_assessment_models_are_frozen_and_type_checked(self) -> None:
        file_entry = SealedCurrentFileEntry("src\\one.py", 1, SHA256, "source", "ADR-1", "owner")
        absence_entry = SealedCurrentAbsenceEntry("src/absent.py", "absence", "ADR-2", "owner")
        snapshot = HistoricalSnapshot("source", COMMIT, COMMIT, "ADR-3")
        blob = HistoricalBlobIdentity(COMMIT, "src/one.py", COMMIT, SHA256, "source", "source", "ADR-3")
        current_files = SealedCurrentFilesManifest("pontius-sealed-current-files-v1", COMMIT, 1, (file_entry,))
        current_absences = SealedCurrentAbsencesManifest("pontius-sealed-current-absences-v1", COMMIT, 1, (absence_entry,))
        historical = HistoricalBlobsManifest("pontius-historical-blobs-v1", COMMIT, 1, 1, SHA256, SHA256, (snapshot,), (blob,))
        self.assertEqual(current_files.files[0].relative_path, "src/one.py")
        self.assertEqual(current_absences.entry_count, 1)
        self.assertEqual(historical.snapshots[0].phase, "source")
        with self.assertRaises(ValueError):
            SealedCurrentFilesManifest("pontius-sealed-current-files-v1", COMMIT, 0, (file_entry,))
        with self.assertRaises(ValueError):
            SealedCurrentAbsencesManifest("pontius-sealed-current-absences-v1", COMMIT, 0, (absence_entry,))
        with self.assertRaises(ValueError):
            HistoricalBlobsManifest("pontius-historical-blobs-v1", COMMIT, 0, 0, SHA256, SHA256, (snapshot,), (blob,))
        manifest = self._retained_manifest()
        loaded = LoadedRetainedV7Manifest(manifest, EvidenceFileIdentity("docs/manifest.toml", 1, SHA256, "manifest"), SHA256)
        assessment = RetainedV7Assessment(SHA256, "terminal", True, False, 0, 0, False, COMMIT)
        self.assertEqual(loaded.semantic_sha256, SHA256)
        self.assertFalse(assessment.scientific_campaign_complete)
        with self.assertRaises(FrozenInstanceError):
            assessment.passed = True  # type: ignore[misc]
        with self.assertRaises(ValueError):
            RetainedV7Assessment(SHA256, "terminal", 1, False, 0, 0, False, COMMIT)

    @staticmethod
    def _retained_manifest() -> RetainedV7Manifest:
        identity = EvidenceFileIdentity("docs/result.json", 1, SHA256, "result")
        return RetainedV7Manifest(
            "pontius-retained-v7-v1", COMMIT, COMMIT, COMMIT, SHA256, SHA256,
            1, 0, 0, 0, 0, "terminal", True, False, 0, 0, False,
            1, 2, 3, 4, 5, 6, False, "classification", False, False, False,
            False, "docs/historical.toml", (), (), identity, identity, identity,
        )


if __name__ == "__main__":
    unittest.main()
