"""Solver-free ADR-0334 rebinder for the retained non-replay qualification.

The value owner is permanently closed.  This module reads only the exact
committed JSONL journal, invokes its independently sealed semantic rebinder,
and exposes a panel only from the preregistered target terminal.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from types import MappingProxyType

from .certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from .durable_evidence_journal import canonical_journal_json_bytes
from .fresh_action_width_nonreplay import (
    FreshActionWidthNonReplayPool,
    build_adr0331_nonreplay_pool,
)
from .fresh_action_width_nonreplay_qualification import (
    ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    ADR0331_QUALIFICATION_TARGET,
    NonReplayQualificationStopReason,
    QualificationEvidenceKind,
    QualificationJournalResult,
    rebind_adr0331_qualification_journal,
)
from .fresh_action_width_nonreplay_qualification_seal import (
    ADR0331_QUALIFICATION_SCHEDULE_SHA256,
    ADR0331_QUALIFICATION_SOURCE_MANIFEST,
)
from .fresh_action_width_nonreplay_seal import ADR0331_POPULATION_POOL_SHA256
from .fresh_action_width_qualification import (
    ActionWidthQualificationClassification,
)


ADR0334_QUALIFICATION_ARTIFACT_BYTES = 391_986
ADR0334_QUALIFICATION_ARTIFACT_SHA256 = (
    "be33cfc4fa5955409ea478552fcdf52de62812ce37fdee94190726537b11f956"
)
ADR0334_QUALIFICATION_CAMPAIGN_SHA256 = (
    "3cd70c6765d735dd36a888a9d2dd66e5d0576930e170eee4117935466afdd948"
)
ADR0334_QUALIFICATION_TERMINAL_SHA256 = (
    "ef824c1ce71c6bb6751b2a89d68aa8dc739bb24b0a519b67cfad2c9093b9f876"
)
ADR0334_QUALIFICATION_RECORD_COUNT = 100
ADR0334_QUALIFICATION_EVIDENCE_COUNT = 98
ADR0334_QUALIFICATION_CONTEXT_COUNT = 49
ADR0334_QUALIFICATION_PUBLIC_CALL_COUNT = 98
ADR0334_QUALIFIED_POOL_INDICES = (
    5,
    6,
    7,
    8,
    12,
    15,
    20,
    23,
    24,
    25,
    30,
    33,
    38,
    42,
    44,
    48,
)
ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S = (
    "eb8fb4437474cc2238b6245449c7a9bd9b402e00272d65c13e3874b5951e0fa4",
    "fd3962a01b9d45742fbdb12ee67b054aad1ad9630188ce187ddda7f9c0a158fa",
    "cc97cd1be49674256598b371f9eadd5b2c620cd0649488172fb5d850ea567b89",
    "36220a806321ceb7e8de6baa64c94e372762998d5519ae0fe4212ca507cd8b60",
    "daeaba7cadb8c1a21c0fb1d17ed8b6ed223faff7dc4299e471f88aae05b257f6",
    "2f7a61bb8e8020ffc0b77f43fcfa26f8b28b5e9fe226ac409069475922d7970e",
    "e36e6312f1053a2afe1df34e38830fe4893057e9e528d797fe0e635a7b8ff207",
    "306d6b19d758de30b463a8a4c76f315663d072f751b0297acff97c970bf8b11d",
    "60c647b3a9a858bcbb1c2bada80ff010966a5a04a29b11914e052cb1cef9ed52",
    "01d93646ebf56d25cf3c3a6316c6902f788b4856a0c39291e09bcc0cc93ba030",
    "905cfee8af03d440176773026320880c3082a5e376a4173f9bd7aab8f319ec19",
    "85ab4c471ee3ac8ef5a01d5e762604bc1f6c696ed2881bf1ec3e3583a859526f",
    "80eb3bf6e13306420032ccec9acac55c85719d2c9c43f2f02126ed78495af552",
    "9fafa7eb8b3c8d40bb9a2373b45cec631d8f4f9d0731a636710c3af43e6299fe",
    "af2ee3be2278d8433ba84b8df694b34b9a900d7968c9b12cbbea1231b9a1685d",
    "cad5a6a7851d85ddbdae812215c32df948a590145fab413c070d3781c59b1bc0",
)
ADR0334_QUALIFIED_PANEL_SHA256 = (
    "4fcdb9927fe7626acdf8752a96c1fb71ab085d61e93ad54bd2c8e72f34dc0b71"
)
ADR0334_MAX_CERTIFICATE_GAP_HEX = "0x1.6f32000000000p-38"
ADR0334_MIN_QUALIFIED_NORMALIZED_LOWER_HEX = "0x1.b0d9450eda666p-14"
ADR0334_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX = "0x1.3022222222222p-43"


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class QualifiedActionWidthNonReplayPanel:
    pool_sha256: str
    qualification_schedule_sha256: str
    qualification_journal_sha256: str
    qualification_terminal_sha256: str
    pool_indices: tuple[int, ...]
    context_semantic_sha256s: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("non-replay panel pool", self.pool_sha256),
            ("non-replay panel schedule", self.qualification_schedule_sha256),
            ("non-replay panel journal", self.qualification_journal_sha256),
            ("non-replay panel terminal", self.qualification_terminal_sha256),
        ):
            _require_digest(value, label=label)
        if (
            not isinstance(self.pool_indices, tuple)
            or len(self.pool_indices) != ADR0331_QUALIFICATION_TARGET
            or any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or not 0 <= index < 96
                for index in self.pool_indices
            )
            or tuple(sorted(self.pool_indices)) != self.pool_indices
            or len(set(self.pool_indices)) != len(self.pool_indices)
        ):
            raise ValueError("non-replay panel requires 16 increasing unique indices")
        if (
            not isinstance(self.context_semantic_sha256s, tuple)
            or len(self.context_semantic_sha256s) != len(self.pool_indices)
        ):
            raise TypeError("non-replay panel contexts must align with its indices")
        for digest in self.context_semantic_sha256s:
            _require_digest(digest, label="non-replay panel context")
        if len(set(self.context_semantic_sha256s)) != len(
            self.context_semantic_sha256s
        ):
            raise ValueError("non-replay panel repeats a semantic context")

    @property
    def core(self) -> dict[str, object]:
        return {
            "context_semantic_sha256s": self.context_semantic_sha256s,
            "pool_indices": self.pool_indices,
            "pool_sha256": self.pool_sha256,
            "qualification_journal_sha256": self.qualification_journal_sha256,
            "qualification_schedule_sha256": self.qualification_schedule_sha256,
            "qualification_terminal_sha256": self.qualification_terminal_sha256,
            "version": "adr0334-qualified-action-width-nonreplay-panel-v1",
        }

    @property
    def digest(self) -> str:
        return sha256(canonical_journal_json_bytes(self.core)).hexdigest()


@dataclass(frozen=True, slots=True)
class RetainedNonReplayQualificationResult:
    journal: QualificationJournalResult
    panel: QualifiedActionWidthNonReplayPanel
    maximum_certificate_gap_chips: float
    minimum_qualified_normalized_lower: float
    maximum_nonqualifying_normalized_upper: float

    def __post_init__(self) -> None:
        if not isinstance(self.journal, QualificationJournalResult):
            raise TypeError("retained non-replay result requires a semantic journal")
        if not isinstance(self.panel, QualifiedActionWidthNonReplayPanel):
            raise TypeError("retained non-replay result requires a semantic panel")
        if (
            self.panel.qualification_journal_sha256 != self.journal.journal_sha256
            or self.panel.qualification_terminal_sha256
            != self.journal.terminal_sha256
            or self.panel.pool_indices != self.journal.qualified_indices
        ):
            raise ValueError("retained non-replay journal and panel identities differ")
        diagnostics = (
            self.maximum_certificate_gap_chips,
            self.minimum_qualified_normalized_lower,
            self.maximum_nonqualifying_normalized_upper,
        )
        if any(
            not isinstance(value, float) or not isfinite(value) or value < 0.0
            for value in diagnostics
        ):
            raise ValueError("retained non-replay diagnostics are invalid")


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0334_QUALIFICATION_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0334_QUALIFICATION_ARTIFACT_SHA256,
    "campaign_sha256": ADR0334_QUALIFICATION_CAMPAIGN_SHA256,
    "classification_counts": (("nonqualifying", 33), ("qualifying", 16)),
    "context_count": ADR0334_QUALIFICATION_CONTEXT_COUNT,
    "evidence_count": ADR0334_QUALIFICATION_EVIDENCE_COUNT,
    "maximum_certificate_gap_hex": ADR0334_MAX_CERTIFICATE_GAP_HEX,
    "maximum_nonqualifying_normalized_upper_hex": (
        ADR0334_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX
    ),
    "minimum_qualified_normalized_lower_hex": (
        ADR0334_MIN_QUALIFIED_NORMALIZED_LOWER_HEX
    ),
    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
    "pool_indices": ADR0334_QUALIFIED_POOL_INDICES,
    "pool_sha256": ADR0331_POPULATION_POOL_SHA256,
    "public_call_count": ADR0334_QUALIFICATION_PUBLIC_CALL_COUNT,
    "qualification_source_sha256": ADR0331_QUALIFICATION_SOURCE_MANIFEST[
        "fresh_action_width_nonreplay_qualification.py"
    ],
    "record_count": ADR0334_QUALIFICATION_RECORD_COUNT,
    "schedule_sha256": ADR0331_QUALIFICATION_SCHEDULE_SHA256,
    "terminal_sha256": ADR0334_QUALIFICATION_TERMINAL_SHA256,
    "version": "adr0334-nonreplay-qualification-result-protocol-v1",
}
ADR0334_QUALIFICATION_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0334_QUALIFICATION_RESULT_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_RESULT_PROTOCOL_PAYLOAD)
).hexdigest()


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0331_QUALIFICATION_ARTIFACT_RELATIVE_PATH
    )


def verify_adr0334_qualification_result_source_and_dependencies() -> str:
    from .fresh_action_width_nonreplay_qualification_result_seal import (
        ADR0334_QUALIFICATION_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0334_QUALIFICATION_RESULT_SOURCE_MANIFEST,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0334_QUALIFICATION_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0334_QUALIFICATION_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0334 qualification-result source closure drifted")
    if sealed_protocol != ADR0334_QUALIFICATION_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0334 qualification-result protocol drifted")
    return actual["fresh_action_width_nonreplay_qualification_result.py"]


def _exact_panel(
    *,
    pool: FreshActionWidthNonReplayPool,
    journal: QualificationJournalResult,
) -> QualifiedActionWidthNonReplayPanel:
    contexts = tuple(
        pool.contexts[index].semantic_digest for index in journal.qualified_indices
    )
    panel = QualifiedActionWidthNonReplayPanel(
        pool_sha256=ADR0331_POPULATION_POOL_SHA256,
        qualification_schedule_sha256=ADR0331_QUALIFICATION_SCHEDULE_SHA256,
        qualification_journal_sha256=ADR0334_QUALIFICATION_ARTIFACT_SHA256,
        qualification_terminal_sha256=ADR0334_QUALIFICATION_TERMINAL_SHA256,
        pool_indices=journal.qualified_indices,
        context_semantic_sha256s=contexts,
    )
    if (
        panel.pool_indices != ADR0334_QUALIFIED_POOL_INDICES
        or panel.context_semantic_sha256s
        != ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S
        or panel.digest != ADR0334_QUALIFIED_PANEL_SHA256
    ):
        raise ValueError("ADR-0334 qualified panel identity drifted")
    return panel


def verify_adr0334_nonreplay_qualification_result_artifact(
    path: Path | None = None,
) -> RetainedNonReplayQualificationResult:
    """Rebind the exact retained journal and panel without a consumer call."""

    verify_adr0334_qualification_result_source_and_dependencies()
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0334_QUALIFICATION_ARTIFACT_BYTES:
        raise ValueError("ADR-0334 qualification journal byte count drifted")
    if sha256(raw).hexdigest() != ADR0334_QUALIFICATION_ARTIFACT_SHA256:
        raise ValueError("ADR-0334 qualification journal SHA-256 drifted")
    if raw.count(b"\n") != ADR0334_QUALIFICATION_RECORD_COUNT or not raw.endswith(
        b"\n"
    ):
        raise ValueError("ADR-0334 qualification journal record shape drifted")

    rebound = rebind_adr0331_qualification_journal(raw, synthetic=False)
    if not isinstance(rebound, QualificationJournalResult):
        raise TypeError("ADR-0334 qualification journal lacks an exact terminal")
    expected_identity = (
        rebound.campaign_sha256 == ADR0334_QUALIFICATION_CAMPAIGN_SHA256
        and rebound.journal_sha256 == ADR0334_QUALIFICATION_ARTIFACT_SHA256
        and rebound.journal_byte_count == ADR0334_QUALIFICATION_ARTIFACT_BYTES
        and rebound.terminal_sha256 == ADR0334_QUALIFICATION_TERMINAL_SHA256
        and len(rebound.evidences) == ADR0334_QUALIFICATION_EVIDENCE_COUNT
        and len(rebound.outcomes) == ADR0334_QUALIFICATION_CONTEXT_COUNT
        and rebound.known_public_call_count
        == ADR0334_QUALIFICATION_PUBLIC_CALL_COUNT
        and rebound.invocation_count_complete
        and not rebound.synthetic
        and rebound.stop_reason is NonReplayQualificationStopReason.TARGET_REACHED
    )
    if not expected_identity:
        raise ValueError("ADR-0334 qualification terminal identity drifted")
    if any(
        evidence.kind is not QualificationEvidenceKind.ACCEPTED
        or evidence.synthetic
        or evidence.public_call_count != 1
        for evidence in rebound.evidences
    ):
        raise ValueError("ADR-0334 qualification arm acceptance drifted")

    counts = Counter(outcome.classification for outcome in rebound.outcomes)
    if counts != {
        ActionWidthQualificationClassification.NONQUALIFYING: 33,
        ActionWidthQualificationClassification.QUALIFYING: 16,
    }:
        raise ValueError("ADR-0334 qualification classification counts drifted")
    if tuple(outcome.context_index for outcome in rebound.outcomes) != tuple(range(49)):
        raise ValueError("ADR-0334 qualification context prefix drifted")

    pool = build_adr0331_nonreplay_pool()
    if pool.digest != ADR0331_POPULATION_POOL_SHA256:
        raise RuntimeError("ADR-0334 qualification pool drifted")
    panel = _exact_panel(pool=pool, journal=rebound)

    gaps = tuple(
        float.fromhex(evidence.core["result"]["certified_gap_hex"])
        for evidence in rebound.evidences
    )
    qualifying = tuple(
        outcome
        for outcome in rebound.outcomes
        if outcome.classification
        is ActionWidthQualificationClassification.QUALIFYING
    )
    nonqualifying = tuple(
        outcome
        for outcome in rebound.outcomes
        if outcome.classification
        is ActionWidthQualificationClassification.NONQUALIFYING
    )
    maximum_gap = max(gaps)
    minimum_qualifying = min(
        outcome.regret.nonnegative_lower_chips
        / pool.contexts[outcome.context_index].payoff_span_chips
        for outcome in qualifying
    )
    maximum_nonqualifying = max(
        outcome.regret.nonnegative_upper_chips
        / pool.contexts[outcome.context_index].payoff_span_chips
        for outcome in nonqualifying
    )
    if (
        maximum_gap.hex() != ADR0334_MAX_CERTIFICATE_GAP_HEX
        or minimum_qualifying.hex()
        != ADR0334_MIN_QUALIFIED_NORMALIZED_LOWER_HEX
        or maximum_nonqualifying.hex()
        != ADR0334_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX
    ):
        raise ValueError("ADR-0334 qualification diagnostics drifted")
    return RetainedNonReplayQualificationResult(
        journal=rebound,
        panel=panel,
        maximum_certificate_gap_chips=maximum_gap,
        minimum_qualified_normalized_lower=minimum_qualifying,
        maximum_nonqualifying_normalized_upper=maximum_nonqualifying,
    )


__all__ = [
    "ADR0334_MAX_CERTIFICATE_GAP_HEX",
    "ADR0334_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX",
    "ADR0334_MIN_QUALIFIED_NORMALIZED_LOWER_HEX",
    "ADR0334_QUALIFICATION_ARTIFACT_BYTES",
    "ADR0334_QUALIFICATION_ARTIFACT_SHA256",
    "ADR0334_QUALIFICATION_CAMPAIGN_SHA256",
    "ADR0334_QUALIFICATION_CONTEXT_COUNT",
    "ADR0334_QUALIFICATION_EVIDENCE_COUNT",
    "ADR0334_QUALIFICATION_PUBLIC_CALL_COUNT",
    "ADR0334_QUALIFICATION_RECORD_COUNT",
    "ADR0334_QUALIFICATION_RESULT_PROTOCOL",
    "ADR0334_QUALIFICATION_RESULT_PROTOCOL_SHA256",
    "ADR0334_QUALIFICATION_TERMINAL_SHA256",
    "ADR0334_QUALIFIED_CONTEXT_SEMANTIC_SHA256S",
    "ADR0334_QUALIFIED_PANEL_SHA256",
    "ADR0334_QUALIFIED_POOL_INDICES",
    "QualifiedActionWidthNonReplayPanel",
    "RetainedNonReplayQualificationResult",
    "verify_adr0334_nonreplay_qualification_result_artifact",
    "verify_adr0334_qualification_result_source_and_dependencies",
]
