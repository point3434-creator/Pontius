"""Solver-free ADR-0341 owner for the retained transfer qualification result.

The one-shot value owner is closed.  This module reads only the exact retained
JSONL journal, invokes ADR-0340's independently sealed semantic rebinder, and
publishes a panel only from the preregistered target terminal.
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
from .fresh_action_width_nonreplay_qualification import QualificationEvidenceKind
from .fresh_action_width_qualification import (
    ADR0323_OPPORTUNITY_FLOOR,
    ActionWidthQualificationClassification,
)
from .fresh_action_width_transfer_qualification import (
    TransferQualificationJournalResult,
    TransferQualificationStopReason,
    TransferQualifiedPanel,
    rebind_adr0340_transfer_qualification_journal,
    rebind_adr0340_transfer_target_panel,
)
from .fresh_action_width_transfer_qualification_seal import (
    ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256,
    ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST,
)
from .fresh_action_width_transfer_structures import build_adr0339_transfer_pool
from .fresh_action_width_transfer_structures_seal import (
    ADR0339_TRANSFER_POOL_SHA256,
)


ADR0341_INVOCATION_SOURCE_COMMIT = (
    "e1c6c14630e3e8cf72be0a40db80b85eed549b58"
)
ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES = 378_108
ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256 = (
    "e6f25068d8362fa2bc9b40fe292506371d6d808b4696bb83c09f75ad3c8d812a"
)
ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256 = (
    "444289ef7f1964b194255a03564ae1628ff207e2eff3cff678755978023f8b78"
)
ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256 = (
    "3770f8dc40a9edbbac5afc7d5986ceb36e566ce552eb35921ead0b644c5575f8"
)
ADR0341_TRANSFER_QUALIFICATION_RECORD_COUNT = 96
ADR0341_TRANSFER_QUALIFICATION_EVIDENCE_COUNT = 94
ADR0341_TRANSFER_QUALIFICATION_CONTEXT_COUNT = 47
ADR0341_TRANSFER_QUALIFICATION_PUBLIC_CALL_COUNT = 94
ADR0341_TRANSFER_QUALIFIED_POOL_INDICES = (
    2,
    3,
    6,
    11,
    13,
    14,
    18,
    21,
    25,
    26,
    28,
    29,
    34,
    35,
    43,
    46,
)
ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S = (
    "e605708fbc3910244b45844a8e9b2ca42e5420d835e3fabacb24d0612988fd63",
    "da3352f36a85c36793c948fe211692c7b2c70fb2c519b95a3ab669b395be66b0",
    "43baebb2a3e270858735790cb8480a3c64db5e97743862f35c704d518e96a54a",
    "d617e442075fcb5babed26209efc9dd9c62d9cd15069fa7484fb2237e602e4f5",
    "feb7c2c21a5b07159a3cd5d750cad9ca967cd035bb0c3a2f94bb16d68a6ef976",
    "481244fd8bb4f1c184118f1d44dd677a664ea82dd2b7f62769c804cdf7e9be03",
    "0626eb8e4d3c25b03306fca098dd9f767fd1822c762f74969cf7d8c8472f37a4",
    "ad37f6640345a47b0db1c099453f5fca8fef557e7e29b523b7d6a265fa0db0e3",
    "245d5ea20be5c7a2ac4eeb9d1115b576cf5791aa290f59e2f92f0cb677b7f6dd",
    "2dcbe672269f72e6c50e1d5717d97d8ff0068065ab91c30ea9c9f6302f1aff88",
    "b5a57321b924414c8af697f008fe8695e0cf8da91bedbf048726b0a838cb4a18",
    "7eca5187154bbe8a9957e624660bf0ab17ccd1c7f90a1f15716854279c9e2ca3",
    "169ee23ba5b5fdf3e4b6a8aefcbaf4f652a80261579b413c1568329c92e8dd4f",
    "b1702ebaa3e6a1e402b797e9cecc7195e69d2612f5f9271b5f889322447299e0",
    "d555a43777cf39a5f494580280a967b74479fd1fcce7022874f6243c149ccfd9",
    "d0653368fee0ec0751248727183d86db825e123be145904a2b1008871945a294",
)
ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256 = (
    "dd46e2917757ae0ba02e620f6298be8eac7629e92db573cea291bf1160b157bf"
)
ADR0341_MAX_CERTIFICATE_GAP_HEX = "0x1.94f0000000000p-38"
ADR0341_MIN_QUALIFIED_NORMALIZED_LOWER_HEX = "0x1.309a93950d746p-13"
ADR0341_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX = "0x1.0662638087287p-14"


@dataclass(frozen=True, slots=True)
class RetainedTransferQualificationResult:
    journal: TransferQualificationJournalResult
    panel: TransferQualifiedPanel
    maximum_certificate_gap_chips: float
    minimum_qualified_normalized_lower: float
    maximum_nonqualifying_normalized_upper: float

    def __post_init__(self) -> None:
        if not isinstance(self.journal, TransferQualificationJournalResult):
            raise TypeError("retained transfer result requires a semantic journal")
        if not isinstance(self.panel, TransferQualifiedPanel):
            raise TypeError("retained transfer result requires a semantic panel")
        if (
            self.panel.campaign_sha256 != self.journal.campaign_sha256
            or self.panel.journal_sha256 != self.journal.journal_sha256
            or self.panel.terminal_sha256 != self.journal.terminal_sha256
            or self.panel.qualified_indices != self.journal.qualified_indices
            or self.panel.synthetic != self.journal.synthetic
        ):
            raise ValueError("retained transfer journal and panel identities differ")
        diagnostics = (
            self.maximum_certificate_gap_chips,
            self.minimum_qualified_normalized_lower,
            self.maximum_nonqualifying_normalized_upper,
        )
        if any(
            not isinstance(value, float) or not isfinite(value) or value < 0.0
            for value in diagnostics
        ):
            raise ValueError("retained transfer diagnostics are invalid")


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256,
    "campaign_sha256": ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256,
    "classification_counts": (("nonqualifying", 31), ("qualifying", 16)),
    "context_count": ADR0341_TRANSFER_QUALIFICATION_CONTEXT_COUNT,
    "evidence_count": ADR0341_TRANSFER_QUALIFICATION_EVIDENCE_COUNT,
    "invocation_source_commit": ADR0341_INVOCATION_SOURCE_COMMIT,
    "maximum_certificate_gap_hex": ADR0341_MAX_CERTIFICATE_GAP_HEX,
    "maximum_nonqualifying_normalized_upper_hex": (
        ADR0341_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX
    ),
    "minimum_qualified_normalized_lower_hex": (
        ADR0341_MIN_QUALIFIED_NORMALIZED_LOWER_HEX
    ),
    "panel_sha256": ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
    "pool_indices": ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
    "pool_sha256": ADR0339_TRANSFER_POOL_SHA256,
    "public_call_count": ADR0341_TRANSFER_QUALIFICATION_PUBLIC_CALL_COUNT,
    "qualification_source_sha256": ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST[
        "fresh_action_width_transfer_qualification.py"
    ],
    "record_count": ADR0341_TRANSFER_QUALIFICATION_RECORD_COUNT,
    "schedule_sha256": ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256,
    "terminal_sha256": ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256,
    "version": "adr0341-transfer-qualification-result-protocol-v1",
}
ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL = MappingProxyType(
    _RESULT_PROTOCOL_PAYLOAD
)
ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_RESULT_PROTOCOL_PAYLOAD)
).hexdigest()


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH
    )


def verify_adr0341_transfer_result_source_and_dependencies() -> str:
    from .fresh_action_width_transfer_qualification_result_seal import (
        ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0341 transfer-result source closure drifted")
    if sealed_protocol != ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0341 transfer-result protocol drifted")
    return actual["fresh_action_width_transfer_qualification_result.py"]


def verify_adr0341_transfer_qualification_result_artifact(
    path: Path | None = None,
) -> RetainedTransferQualificationResult:
    """Rebind the exact retained journal and target panel without a solver call."""

    verify_adr0341_transfer_result_source_and_dependencies()
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES:
        raise ValueError("ADR-0341 transfer journal byte count drifted")
    if sha256(raw).hexdigest() != ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256:
        raise ValueError("ADR-0341 transfer journal SHA-256 drifted")
    if raw.count(b"\n") != ADR0341_TRANSFER_QUALIFICATION_RECORD_COUNT or not raw.endswith(
        b"\n"
    ):
        raise ValueError("ADR-0341 transfer journal record shape drifted")

    rebound = rebind_adr0340_transfer_qualification_journal(raw, synthetic=False)
    if not isinstance(rebound, TransferQualificationJournalResult):
        raise TypeError("ADR-0341 transfer journal lacks an exact terminal")
    expected_identity = (
        rebound.campaign_sha256 == ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256
        and rebound.journal_sha256 == ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256
        and rebound.journal_byte_count == ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES
        and rebound.terminal_sha256
        == ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256
        and len(rebound.evidences)
        == ADR0341_TRANSFER_QUALIFICATION_EVIDENCE_COUNT
        and len(rebound.outcomes) == ADR0341_TRANSFER_QUALIFICATION_CONTEXT_COUNT
        and rebound.known_public_call_count
        == ADR0341_TRANSFER_QUALIFICATION_PUBLIC_CALL_COUNT
        and rebound.invocation_count_complete
        and not rebound.synthetic
        and rebound.stop_reason is TransferQualificationStopReason.TARGET_REACHED
    )
    if not expected_identity:
        raise ValueError("ADR-0341 transfer terminal identity drifted")
    if any(
        evidence.kind is not QualificationEvidenceKind.ACCEPTED
        or evidence.synthetic
        or evidence.public_call_count != 1
        for evidence in rebound.evidences
    ):
        raise ValueError("ADR-0341 transfer arm acceptance drifted")

    counts = Counter(outcome.classification for outcome in rebound.outcomes)
    if counts != {
        ActionWidthQualificationClassification.NONQUALIFYING: 31,
        ActionWidthQualificationClassification.QUALIFYING: 16,
    }:
        raise ValueError("ADR-0341 transfer classification counts drifted")
    if tuple(outcome.context_index for outcome in rebound.outcomes) != tuple(range(47)):
        raise ValueError("ADR-0341 transfer context prefix drifted")
    if rebound.qualified_indices != ADR0341_TRANSFER_QUALIFIED_POOL_INDICES:
        raise ValueError("ADR-0341 transfer qualifier indices drifted")

    pool = build_adr0339_transfer_pool()
    if pool.digest != ADR0339_TRANSFER_POOL_SHA256:
        raise RuntimeError("ADR-0341 transfer pool drifted")
    panel = rebind_adr0340_transfer_target_panel(raw, synthetic=False)
    if (
        panel.pool_sha256 != ADR0339_TRANSFER_POOL_SHA256
        or panel.schedule_sha256 != ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256
        or panel.campaign_sha256 != ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256
        or panel.journal_sha256 != ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256
        or panel.terminal_sha256 != ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256
        or panel.qualified_indices != ADR0341_TRANSFER_QUALIFIED_POOL_INDICES
        or panel.context_semantic_sha256s
        != ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S
        or panel.synthetic
        or panel.digest != ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256
    ):
        raise ValueError("ADR-0341 transfer target-panel identity drifted")

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
        maximum_gap.hex() != ADR0341_MAX_CERTIFICATE_GAP_HEX
        or minimum_qualifying.hex()
        != ADR0341_MIN_QUALIFIED_NORMALIZED_LOWER_HEX
        or maximum_nonqualifying.hex()
        != ADR0341_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX
        or minimum_qualifying <= ADR0323_OPPORTUNITY_FLOOR.value
        or maximum_nonqualifying >= ADR0323_OPPORTUNITY_FLOOR.value
    ):
        raise ValueError("ADR-0341 transfer qualification diagnostics drifted")
    return RetainedTransferQualificationResult(
        journal=rebound,
        panel=panel,
        maximum_certificate_gap_chips=maximum_gap,
        minimum_qualified_normalized_lower=minimum_qualifying,
        maximum_nonqualifying_normalized_upper=maximum_nonqualifying,
    )


__all__ = [
    "ADR0341_INVOCATION_SOURCE_COMMIT",
    "ADR0341_MAX_CERTIFICATE_GAP_HEX",
    "ADR0341_MAX_NONQUALIFYING_NORMALIZED_UPPER_HEX",
    "ADR0341_MIN_QUALIFIED_NORMALIZED_LOWER_HEX",
    "ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_BYTES",
    "ADR0341_TRANSFER_QUALIFICATION_ARTIFACT_SHA256",
    "ADR0341_TRANSFER_QUALIFICATION_CAMPAIGN_SHA256",
    "ADR0341_TRANSFER_QUALIFICATION_CONTEXT_COUNT",
    "ADR0341_TRANSFER_QUALIFICATION_EVIDENCE_COUNT",
    "ADR0341_TRANSFER_QUALIFICATION_PUBLIC_CALL_COUNT",
    "ADR0341_TRANSFER_QUALIFICATION_RECORD_COUNT",
    "ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL",
    "ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256",
    "ADR0341_TRANSFER_QUALIFICATION_TERMINAL_SHA256",
    "ADR0341_TRANSFER_QUALIFIED_CONTEXT_SEMANTIC_SHA256S",
    "ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256",
    "ADR0341_TRANSFER_QUALIFIED_POOL_INDICES",
    "RetainedTransferQualificationResult",
    "verify_adr0341_transfer_qualification_result_artifact",
    "verify_adr0341_transfer_result_source_and_dependencies",
]
