"""Solver-free ADR-0343 owner for the retained width-three transfer result.

The one-shot value owner is closed.  This module reads only the exact retained
JSONL journal, invokes ADR-0342's independently sealed semantic rebinder, and
publishes the result only when every retained identity, witness, context, and
gate diagnostic reconstructs exactly.
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
from .fresh_action_width_transfer_confirmation import (
    TransferConfirmationEvidenceKind,
    TransferConfirmationJournalResult,
    TransferConfirmationStopReason,
    rebind_adr0342_transfer_confirmation_journal,
)
from .fresh_action_width_transfer_confirmation_seal import (
    ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH,
    ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT,
    ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256,
    ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST,
)
from .fresh_action_width_transfer_qualification_result import (
    ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
    ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
)


ADR0343_INVOCATION_SOURCE_COMMIT = (
    "45dc67c5e36fc222620449117eaa33948fcb47ef"
)
ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES = 445_731
ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256 = (
    "c7fb4405177d46f751812c957e5a503c3430fb48427456e333a871e486969130"
)
ADR0343_TRANSFER_CONFIRMATION_CAMPAIGN_SHA256 = (
    "f32f5141c588ad017be77257802759ce48cad24cbb0837b390a54b235eae577e"
)
ADR0343_TRANSFER_CONFIRMATION_TERMINAL_SHA256 = (
    "a6e9e9c6ee6c9236610a90da47bd590848551ee6c8b5f56a56084551e37a97e8"
)
ADR0343_TRANSFER_CONFIRMATION_RECORD_COUNT = 128
ADR0343_TRANSFER_CONFIRMATION_EVIDENCE_COUNT = 126
ADR0343_TRANSFER_CONFIRMATION_CONTEXT_COUNT = 16
ADR0343_TRANSFER_CONFIRMATION_PUBLIC_CALL_COUNT = 126
ADR0343_TRANSFER_CONFIRMATION_GATE_SHA256 = (
    "76b69d77d6974a0415a3c53396c02eb8219fd970fef21f0fbcbca5902e98f673"
)
ADR0343_MAX_CERTIFICATE_GAP_HEX = "0x1.6780000000000p-41"
ADR0343_MAXIMUM_NORMALIZED_FULL_REGRET_UPPER_HEX = (
    "0x1.51e5e623b20f1p-12"
)
ADR0343_MEAN_NORMALIZED_FULL_REGRET_LOWER_HEX = "0x1.9ca80879f1e48p-15"
ADR0343_MEAN_NORMALIZED_FULL_REGRET_UPPER_HEX = "0x1.9ca808891f06dp-15"
ADR0343_AGGREGATE_RECOVERY_LOWER_HEX = "0x1.f1d2979a0006dp-1"
ADR0343_AGGREGATE_RECOVERY_UPPER_HEX = "0x1.f1d2979a9b3d4p-1"
ADR0343_ACHIEVED_GAIN_LOWER_CHIPS_HEX = "0x1.ec3af180f7142p-1"
ADR0343_ACHIEVED_GAIN_UPPER_CHIPS_HEX = "0x1.ec3af1810db01p-1"
ADR0343_AVAILABLE_GAIN_LOWER_CHIPS_HEX = "0x1.fa3f945f5ef9ep-1"
ADR0343_AVAILABLE_GAIN_UPPER_CHIPS_HEX = "0x1.fa3f945fe5901p-1"
ADR0343_MAXIMUM_NORMALIZED_TEACHER_EXCESS_UPPER_HEX = (
    "0x1.174b4b4b4b4b5p-46"
)
ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_LOWER_HEX = "0x0.0p+0"
ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_UPPER_HEX = "0x1.c8d7df69724dap-47"
ADR0343_CONTEXT_CANDIDATE_COUNTS = (
    9,
    7,
    9,
    7,
    7,
    7,
    7,
    9,
    9,
    9,
    9,
    7,
    7,
    9,
    9,
    5,
)
ADR0343_CONTEXT_SELECTED_CANDIDATE_POSITIONS = (
    0,
    0,
    3,
    3,
    3,
    1,
    2,
    4,
    2,
    1,
    2,
    3,
    0,
    0,
    0,
    1,
)
ADR0343_CONTEXT_SELECTED_RAISE_TO_TOTALS = (
    (2, 3, 12),
    (2, 3, 10),
    (2, 6, 12),
    (2, 6, 10),
    (2, 6, 10),
    (2, 4, 10),
    (2, 5, 10),
    (2, 7, 12),
    (2, 5, 12),
    (2, 4, 12),
    (2, 5, 12),
    (2, 6, 10),
    (2, 3, 10),
    (2, 3, 12),
    (2, 3, 12),
    (2, 4, 8),
)
ADR0343_CONTEXT_RESULT_SHA256S = (
    "b8c42f4c9264d9fe0469620c34633d336482e3716ecbacbcac4796ebac9a81c9",
    "93e6b775bdac443ff998419f9c4740caa3579f85d3bc823e09b22d1b579f7836",
    "87963588881bef65ca84dbd22215cf5fbd029088299904784b2155ab888f3922",
    "9602c6f858abc64d4effc9a7cb02fd205e361941542acdb7afbd40fc9202cf74",
    "351c9c9c098ca737724aba5de7ead71103ef1075a4c3bc2f5595fcf46610672a",
    "34801bd9a11c27ae2d9a5c6c4ee7ca59c32f9bd7a84b7e5e36a12794d2ac5c59",
    "d3f7afbce93c4efe899a7fc35b2b74ca5ecfc80f83b28a7a83a6993b5290d456",
    "b15fc7f1bf9f54af361432ea30106358ff738f933799d8d4d8bf250b01c8410f",
    "4ea7ddf49e6396bb690d14a271343e261d9d6b2e64f0865ec99c4ba745aa06fc",
    "55bb050ac169aeb79e9fba1d5fd020d13be8178930ea37451a0b54a2b701bd5b",
    "c58f49f3ede253cc2355fb6b9a57f0c8e87c0774f377d2e704e3503b87454d48",
    "fd6155c94b12cae24427c27062c5f61fcde4cbb0aef2dd4e6ee619583ccdad64",
    "8d0a0cfb3085e775b3a488a45402d02e4be16ecf6367b1dd93fa33e91937a791",
    "df7206a596c8b9d8495ab69b358420ca67b6468522055ecc149bd740d542404b",
    "6843c507cb1ae830d05ed2ee0ba633fcb052a407fd0ff9b55c5bf33ad8376368",
    "aba9a2940e43021d58a6965a36ebdcb845a048a32ca9b924d62ed200439fddc8",
)


@dataclass(frozen=True, slots=True)
class RetainedTransferConfirmationResult:
    journal: TransferConfirmationJournalResult
    maximum_certificate_gap_chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.journal, TransferConfirmationJournalResult):
            raise TypeError("retained confirmation requires a semantic journal")
        if (
            self.journal.stop_reason
            is not TransferConfirmationStopReason.COMPLETED_CONFIRMED
            or self.journal.gate is None
            or not self.journal.gate.passes
            or self.journal.unrestricted_transfer_confirmed is not True
        ):
            raise ValueError("retained confirmation lacks all five transfer conjuncts")
        if (
            not isinstance(self.maximum_certificate_gap_chips, float)
            or not isfinite(self.maximum_certificate_gap_chips)
            or self.maximum_certificate_gap_chips < 0.0
        ):
            raise ValueError("retained confirmation certificate gap is invalid")


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256,
    "campaign_sha256": ADR0343_TRANSFER_CONFIRMATION_CAMPAIGN_SHA256,
    "context_candidate_counts": ADR0343_CONTEXT_CANDIDATE_COUNTS,
    "context_result_sha256s": ADR0343_CONTEXT_RESULT_SHA256S,
    "context_selected_candidate_positions": (
        ADR0343_CONTEXT_SELECTED_CANDIDATE_POSITIONS
    ),
    "context_selected_raise_to_totals": ADR0343_CONTEXT_SELECTED_RAISE_TO_TOTALS,
    "gate_sha256": ADR0343_TRANSFER_CONFIRMATION_GATE_SHA256,
    "gate_metric_hexes": (
        ADR0343_MAXIMUM_NORMALIZED_FULL_REGRET_UPPER_HEX,
        ADR0343_MEAN_NORMALIZED_FULL_REGRET_LOWER_HEX,
        ADR0343_MEAN_NORMALIZED_FULL_REGRET_UPPER_HEX,
        ADR0343_AGGREGATE_RECOVERY_LOWER_HEX,
        ADR0343_AGGREGATE_RECOVERY_UPPER_HEX,
        ADR0343_ACHIEVED_GAIN_LOWER_CHIPS_HEX,
        ADR0343_ACHIEVED_GAIN_UPPER_CHIPS_HEX,
        ADR0343_AVAILABLE_GAIN_LOWER_CHIPS_HEX,
        ADR0343_AVAILABLE_GAIN_UPPER_CHIPS_HEX,
        ADR0343_MAXIMUM_NORMALIZED_TEACHER_EXCESS_UPPER_HEX,
        ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_LOWER_HEX,
        ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_UPPER_HEX,
    ),
    "invocation_source_commit": ADR0343_INVOCATION_SOURCE_COMMIT,
    "maximum_certificate_gap_hex": ADR0343_MAX_CERTIFICATE_GAP_HEX,
    "panel_sha256": ADR0341_TRANSFER_QUALIFIED_PANEL_SHA256,
    "prior_pool_indices": ADR0341_TRANSFER_QUALIFIED_POOL_INDICES,
    "prospective_call_count": ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT,
    "record_count": ADR0343_TRANSFER_CONFIRMATION_RECORD_COUNT,
    "schedule_sha256": ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256,
    "stop_reason": TransferConfirmationStopReason.COMPLETED_CONFIRMED.value,
    "terminal_sha256": ADR0343_TRANSFER_CONFIRMATION_TERMINAL_SHA256,
    "version": "adr0343-transfer-confirmation-result-protocol-v1",
}
ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL = MappingProxyType(
    _RESULT_PROTOCOL_PAYLOAD
)
ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_RESULT_PROTOCOL_PAYLOAD)
).hexdigest()


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH
    )


def verify_adr0343_transfer_result_source_and_dependencies() -> str:
    from .fresh_action_width_transfer_confirmation_result_seal import (
        ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0343_TRANSFER_CONFIRMATION_RESULT_SOURCE_MANIFEST,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0343_TRANSFER_CONFIRMATION_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0343_TRANSFER_CONFIRMATION_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0343 transfer-result source closure drifted")
    if sealed_protocol != ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0343 transfer-result protocol drifted")
    return actual["fresh_action_width_transfer_confirmation_result.py"]


def _gate_metric_hexes(journal: TransferConfirmationJournalResult) -> tuple[str, ...]:
    gate = journal.gate
    if gate is None:
        raise ValueError("ADR-0343 transfer result lacks a complete gate")
    recovery = gate.aggregate_recovery
    return (
        gate.maximum_normalized_full_regret_upper.hex(),
        gate.mean_normalized_full_regret_lower.hex(),
        gate.mean_normalized_full_regret_upper.hex(),
        recovery.lower.hex(),
        recovery.upper.hex(),
        recovery.achieved_gain_lower_chips.hex(),
        recovery.achieved_gain_upper_chips.hex(),
        recovery.available_gain_lower_chips.hex(),
        recovery.available_gain_upper_chips.hex(),
        gate.maximum_normalized_teacher_excess_upper.hex(),
        gate.mean_normalized_teacher_excess_lower.hex(),
        gate.mean_normalized_teacher_excess_upper.hex(),
    )


def verify_adr0343_transfer_confirmation_result_artifact(
    path: Path | None = None,
) -> RetainedTransferConfirmationResult:
    """Rebind the exact retained confirmation journal without a solver call."""

    verify_adr0343_transfer_result_source_and_dependencies()
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES:
        raise ValueError("ADR-0343 transfer journal byte count drifted")
    if sha256(raw).hexdigest() != ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256:
        raise ValueError("ADR-0343 transfer journal SHA-256 drifted")
    if raw.count(b"\n") != ADR0343_TRANSFER_CONFIRMATION_RECORD_COUNT or not raw.endswith(
        b"\n"
    ):
        raise ValueError("ADR-0343 transfer journal record shape drifted")

    rebound = rebind_adr0342_transfer_confirmation_journal(raw, synthetic=False)
    if not isinstance(rebound, TransferConfirmationJournalResult):
        raise TypeError("ADR-0343 transfer journal lacks an exact terminal")
    if (
        rebound.campaign_sha256 != ADR0343_TRANSFER_CONFIRMATION_CAMPAIGN_SHA256
        or rebound.journal_sha256 != ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256
        or rebound.journal_byte_count != ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES
        or rebound.terminal_sha256 != ADR0343_TRANSFER_CONFIRMATION_TERMINAL_SHA256
        or len(rebound.evidences) != ADR0343_TRANSFER_CONFIRMATION_EVIDENCE_COUNT
        or len(rebound.contexts) != ADR0343_TRANSFER_CONFIRMATION_CONTEXT_COUNT
        or rebound.known_public_call_count
        != ADR0343_TRANSFER_CONFIRMATION_PUBLIC_CALL_COUNT
        or not rebound.invocation_count_complete
        or rebound.synthetic
        or rebound.failure_stage is not None
        or rebound.failure_exception_chain
        or rebound.stop_reason
        is not TransferConfirmationStopReason.COMPLETED_CONFIRMED
        or rebound.unrestricted_transfer_confirmed is not True
    ):
        raise ValueError("ADR-0343 transfer terminal identity drifted")

    counts = Counter(evidence.kind for evidence in rebound.evidences)
    if counts != {TransferConfirmationEvidenceKind.ACCEPTED: 126} or any(
        evidence.synthetic
        or evidence.public_call_count != 1
        or not evidence.invocation_count_complete
        for evidence in rebound.evidences
    ):
        raise ValueError("ADR-0343 transfer arm acceptance drifted")

    gate = rebound.gate
    if gate is None or not gate.passes:
        raise ValueError("ADR-0343 transfer gate is not confirmed")
    expected_gate_hexes = tuple(_RESULT_PROTOCOL_PAYLOAD["gate_metric_hexes"])
    if (
        gate.digest != ADR0343_TRANSFER_CONFIRMATION_GATE_SHA256
        or _gate_metric_hexes(rebound) != expected_gate_hexes
        or not all(
            (
                gate.maximum_full_regret_pass,
                gate.mean_full_regret_pass,
                gate.aggregate_recovery_pass,
                gate.maximum_teacher_excess_pass,
                gate.mean_teacher_excess_pass,
            )
        )
    ):
        raise ValueError("ADR-0343 transfer gate diagnostics drifted")

    contexts = rebound.contexts
    if (
        tuple(item.pool_index for item in contexts)
        != ADR0341_TRANSFER_QUALIFIED_POOL_INDICES
        or tuple(item.digest for item in contexts) != ADR0343_CONTEXT_RESULT_SHA256S
        or tuple(len(item.candidates) for item in contexts)
        != ADR0343_CONTEXT_CANDIDATE_COUNTS
        or tuple(item.selected_candidate_position for item in contexts)
        != ADR0343_CONTEXT_SELECTED_CANDIDATE_POSITIONS
        or tuple(
            item.selected.transition.augmented.raise_to_totals for item in contexts
        )
        != ADR0343_CONTEXT_SELECTED_RAISE_TO_TOTALS
        or any(
            item.teacher.nondominated_subset_indices
            != (item.selected_candidate_position,)
            or item.teacher.equivalent_subset_indices
            != (item.selected_candidate_position,)
            or item.teacher.unique_best_subset_index
            != item.selected_candidate_position
            for item in contexts
        )
    ):
        raise ValueError("ADR-0343 transfer context results drifted")

    maximum_gap = max(
        float.fromhex(evidence.core["result"]["certified_gap_hex"])
        for evidence in rebound.evidences
    )
    if maximum_gap.hex() != ADR0343_MAX_CERTIFICATE_GAP_HEX:
        raise ValueError("ADR-0343 transfer certificate diagnostics drifted")
    return RetainedTransferConfirmationResult(
        journal=rebound,
        maximum_certificate_gap_chips=maximum_gap,
    )


__all__ = [
    "ADR0343_ACHIEVED_GAIN_LOWER_CHIPS_HEX",
    "ADR0343_ACHIEVED_GAIN_UPPER_CHIPS_HEX",
    "ADR0343_AGGREGATE_RECOVERY_LOWER_HEX",
    "ADR0343_AGGREGATE_RECOVERY_UPPER_HEX",
    "ADR0343_AVAILABLE_GAIN_LOWER_CHIPS_HEX",
    "ADR0343_AVAILABLE_GAIN_UPPER_CHIPS_HEX",
    "ADR0343_CONTEXT_CANDIDATE_COUNTS",
    "ADR0343_CONTEXT_RESULT_SHA256S",
    "ADR0343_CONTEXT_SELECTED_CANDIDATE_POSITIONS",
    "ADR0343_CONTEXT_SELECTED_RAISE_TO_TOTALS",
    "ADR0343_INVOCATION_SOURCE_COMMIT",
    "ADR0343_MAX_CERTIFICATE_GAP_HEX",
    "ADR0343_MAXIMUM_NORMALIZED_FULL_REGRET_UPPER_HEX",
    "ADR0343_MAXIMUM_NORMALIZED_TEACHER_EXCESS_UPPER_HEX",
    "ADR0343_MEAN_NORMALIZED_FULL_REGRET_LOWER_HEX",
    "ADR0343_MEAN_NORMALIZED_FULL_REGRET_UPPER_HEX",
    "ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_LOWER_HEX",
    "ADR0343_MEAN_NORMALIZED_TEACHER_EXCESS_UPPER_HEX",
    "ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_BYTES",
    "ADR0343_TRANSFER_CONFIRMATION_ARTIFACT_SHA256",
    "ADR0343_TRANSFER_CONFIRMATION_CAMPAIGN_SHA256",
    "ADR0343_TRANSFER_CONFIRMATION_CONTEXT_COUNT",
    "ADR0343_TRANSFER_CONFIRMATION_EVIDENCE_COUNT",
    "ADR0343_TRANSFER_CONFIRMATION_GATE_SHA256",
    "ADR0343_TRANSFER_CONFIRMATION_PUBLIC_CALL_COUNT",
    "ADR0343_TRANSFER_CONFIRMATION_RECORD_COUNT",
    "ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL",
    "ADR0343_TRANSFER_CONFIRMATION_RESULT_PROTOCOL_SHA256",
    "ADR0343_TRANSFER_CONFIRMATION_TERMINAL_SHA256",
    "RetainedTransferConfirmationResult",
    "verify_adr0343_transfer_confirmation_result_artifact",
    "verify_adr0343_transfer_result_source_and_dependencies",
]
