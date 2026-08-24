"""Source-only qualification owner for ADR-0339's untouched transfer pool.

The module owns a new pool-bound schedule, campaign, durable journal, semantic
reduction, and target-only panel rebinder.  It reuses ADR-0333's sealed arm-
evidence codec and independent policy/dual witness validator, but never its
population, schedule, runner, artifact, or result.  No transfer value is opened
by importing or synthetically exercising this source.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from .certified_reduced_sizing_consumer_v2 import (
    canonical_lf_source_sha256,
    consume_certified_reduced_sizing_v2,
)
from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    JournalRecovery,
    canonical_journal_json_bytes,
    parse_journal_record_line,
    recover_journal_bytes,
)
from .fresh_action_width_nonreplay_qualification import (
    ADR0331_QUALIFICATION_PROTOCOL_SHA256,
    QualificationArmEvidence,
    QualificationContextOutcome,
    QualificationEvidenceKind,
    _accepted_interval_from_evidence,
    _exception_payload,
    _rebind_evidence,
    _unexpected_evidence,
    _validate_evidence_against_task,
    evidence_from_consumer_result,
    synthetic_accepted_evidence,
    synthetic_rejected_evidence,
    verify_adr0333_qualification_source_and_dependencies,
)
from .fresh_action_width_qualification import (
    ADR0323_NESTED_REVERSAL_ALLOWANCE,
    ADR0323_OPPORTUNITY_FLOOR,
    ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
    ADR0323_QUALIFICATION_TARGET,
    ActionWidthQualificationArm,
    ActionWidthQualificationClassification,
    ActionWidthQualificationTask,
    certified_full_minus_subset_regret,
    classify_action_width_opportunity,
    qualification_requests_for_context,
)
from .fresh_action_width_transfer_structures import (
    ADR0339_TRANSFER_CONTEXT_COUNT,
    ADR0339_TRANSFER_PROTOCOL_SHA256,
    FreshActionWidthTransferPool,
    build_adr0339_transfer_pool,
)
from .fresh_action_width_transfer_structures_seal import (
    ADR0339_COMBINED_EXCLUSION_CONTEXT_COUNT,
    ADR0339_FINITE_NONOVERLAP_EVIDENCE_SHA256,
    ADR0339_TRANSFER_CANDIDATE_ATTEMPTS,
    ADR0339_TRANSFER_POOL_SHA256,
    ADR0339_TRANSFER_PROTOCOL_SHA256 as SEALED_TRANSFER_PROTOCOL_SHA256,
    ADR0339_TRANSFER_SOURCE_MANIFEST,
    ADR0339_TRANSFER_SUBSET_COUNTS_BY_RAISE_WIDTH,
    ADR0339_TRANSFER_TOTAL_SUBSET_COUNT,
)


ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-transfer-qualification-v1.jsonl"
)
ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT = 192
ADR0340_TRANSFER_QUALIFICATION_TARGET = ADR0323_QUALIFICATION_TARGET

_SCHEDULE_VERSION = "adr0340-transfer-qualification-schedule-v1"
_CAMPAIGN_VERSION = "adr0340-transfer-qualification-campaign-v1"
_HEADER_VERSION = "adr0340-transfer-qualification-header-v1"
_TERMINAL_VERSION = "adr0340-transfer-qualification-terminal-v1"
_PANEL_VERSION = "adr0340-transfer-qualified-panel-v1"


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_count(
    value: object,
    *,
    label: str,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} exceeds its maximum")
    return value


def _sealed_payload(
    core: Mapping[str, object],
    *,
    digest_field: str,
) -> dict[str, object]:
    if digest_field in core:
        raise ValueError("self-free core already contains its digest")
    return {
        **core,
        digest_field: sha256(canonical_journal_json_bytes(core)).hexdigest(),
    }


def _verify_sealed_payload(
    value: object,
    *,
    digest_field: str,
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or digest_field not in value:
        raise ValueError(f"{label} lacks its digest")
    claimed = _require_digest(value[digest_field], label=f"{label} digest")
    core = {key: item for key, item in value.items() if key != digest_field}
    if sha256(canonical_journal_json_bytes(core)).hexdigest() != claimed:
        raise ValueError(f"{label} digest differs from its self-free core")
    return core


@dataclass(frozen=True, slots=True)
class TransferQualificationSchedule:
    """The exact full-then-width-two task order for the transfer pool."""

    pool_sha256: str
    tasks: tuple[ActionWidthQualificationTask, ...]

    def __post_init__(self) -> None:
        _require_digest(self.pool_sha256, label="transfer qualification pool")
        if (
            not isinstance(self.tasks, tuple)
            or len(self.tasks) != ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT
            or any(
                not isinstance(task, ActionWidthQualificationTask)
                for task in self.tasks
            )
        ):
            raise TypeError("transfer qualification requires 192 semantic tasks")
        expected = tuple(
            (index, arm)
            for index in range(ADR0339_TRANSFER_CONTEXT_COUNT)
            for arm in (
                ActionWidthQualificationArm.COMPLETE_INTEGER_UNIVERSE,
                ActionWidthQualificationArm.ANCHORED_RAISE_WIDTH_TWO,
            )
        )
        if tuple((task.context_index, task.arm) for task in self.tasks) != expected:
            raise ValueError("transfer qualification task order drifted")
        if len({task.digest for task in self.tasks}) != len(self.tasks):
            raise ValueError("transfer qualification schedule repeats a task")
        pool = build_adr0339_transfer_pool()
        expected_tasks = tuple(
            task
            for index, context in enumerate(pool.contexts)
            for task in qualification_requests_for_context(
                context=context,
                context_index=index,
            )
        )
        if self.pool_sha256 != pool.digest or tuple(
            task.digest for task in self.tasks
        ) != tuple(task.digest for task in expected_tasks):
            raise ValueError("transfer schedule is not bound to the exact pool")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "pool_sha256": self.pool_sha256,
                    "task_digests": tuple(task.digest for task in self.tasks),
                    "version": _SCHEDULE_VERSION,
                }
            )
        ).hexdigest()


def verify_adr0339_transfer_source_and_pool() -> FreshActionWidthTransferPool:
    """Reproduce ADR-0339's source closure and exact value-free pool."""

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0339_TRANSFER_SOURCE_MANIFEST
    }
    if actual != ADR0339_TRANSFER_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0339 transfer source closure drifted")
    if ADR0339_TRANSFER_PROTOCOL_SHA256 != SEALED_TRANSFER_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0339 transfer protocol drifted")
    pool = build_adr0339_transfer_pool()
    ledger = pool.subset_work_ledger
    if (
        pool.digest != ADR0339_TRANSFER_POOL_SHA256
        or pool.candidate_attempts != ADR0339_TRANSFER_CANDIDATE_ATTEMPTS
        or tuple(
            (width.count, count)
            for width, count in ledger.subset_counts_by_raise_width
        )
        != ADR0339_TRANSFER_SUBSET_COUNTS_BY_RAISE_WIDTH
        or ledger.total_subset_count != ADR0339_TRANSFER_TOTAL_SUBSET_COUNT
        or ADR0339_COMBINED_EXCLUSION_CONTEXT_COUNT != 1_244
        or ADR0339_FINITE_NONOVERLAP_EVIDENCE_SHA256
        != "74739a76d3350e7be5a8bf7eb807f577ba7a5bfe7beaaa69536f3f7ffb45c610"
    ):
        raise RuntimeError("ADR-0339 transfer population drifted")
    return pool


def build_adr0340_transfer_qualification_schedule(
) -> TransferQualificationSchedule:
    """Build the complete prospective transfer schedule without opening value."""

    pool = verify_adr0339_transfer_source_and_pool()
    return TransferQualificationSchedule(
        pool_sha256=pool.digest,
        tasks=tuple(
            task
            for index, context in enumerate(pool.contexts)
            for task in qualification_requests_for_context(
                context=context,
                context_index=index,
            )
        ),
    )


_TRANSFER_QUALIFICATION_PROTOCOL_PAYLOAD = {
    "ambiguity_guard_chips_hex": (
        ADR0323_QUALIFICATION_AMBIGUITY_GUARD.chips.hex()
    ),
    "arm_evidence_codec_protocol_sha256": ADR0331_QUALIFICATION_PROTOCOL_SHA256,
    "arm_order": tuple(arm.value for arm in ActionWidthQualificationArm),
    "artifact_relative_path": ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    "classification_order": tuple(
        item.value for item in ActionWidthQualificationClassification
    ),
    "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    "execution_failure_reduction": (
        "exact-raw-journal-plus-last-receipted-semantic-prefix"
    ),
    "execution_phases": (
        "header_append",
        "next_call_authorization",
        "arm_evidence",
        "observation_append",
        "semantic_reduction",
        "terminal_append",
        "journal_close",
        "final_rebind",
    ),
    "nested_reversal_allowance_chips_hex": (
        ADR0323_NESTED_REVERSAL_ALLOWANCE.chips.hex()
    ),
    "opportunity_floor_hex": ADR0323_OPPORTUNITY_FLOOR.value.hex(),
    "partial_transfer_interpretation": (
        "all-unchanged-conjuncts-or-reject-unrestricted-transfer"
    ),
    "pool_sha256": ADR0339_TRANSFER_POOL_SHA256,
    "regret_interval": "[L_full-U_subset,U_full-L_subset]",
    "schedule_version": _SCHEDULE_VERSION,
    "stop_reasons": (
        "target_reached",
        "pool_exhausted",
        "ambiguous",
        "nested_value_reversal",
        "consumer_rejected",
        "unexpected_exception",
    ),
    "target": ADR0340_TRANSFER_QUALIFICATION_TARGET,
    "task_count": ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT,
    "transfer_protocol_sha256": ADR0339_TRANSFER_PROTOCOL_SHA256,
    "unreceipted_invocation_accounting": "unknown-and-excluded",
    "value_witness": (
        "exact-policy-behavioral-reconstruction-plus-dual-certificate-rebind"
    ),
    "version": "adr0340-transfer-qualification-protocol-v1",
}
ADR0340_TRANSFER_QUALIFICATION_PROTOCOL = MappingProxyType(
    _TRANSFER_QUALIFICATION_PROTOCOL_PAYLOAD
)
ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_TRANSFER_QUALIFICATION_PROTOCOL_PAYLOAD)
).hexdigest()


class TransferQualificationStopReason(StrEnum):
    TARGET_REACHED = "target_reached"
    POOL_EXHAUSTED = "pool_exhausted"
    AMBIGUOUS = "ambiguous"
    NESTED_VALUE_REVERSAL = "nested_value_reversal"
    CONSUMER_REJECTED = "consumer_rejected"
    UNEXPECTED_EXCEPTION = "unexpected_exception"


class TransferQualificationExecutionPhase(StrEnum):
    HEADER_APPEND = "header_append"
    NEXT_CALL_AUTHORIZATION = "next_call_authorization"
    ARM_EVIDENCE = "arm_evidence"
    OBSERVATION_APPEND = "observation_append"
    SEMANTIC_REDUCTION = "semantic_reduction"
    TERMINAL_APPEND = "terminal_append"
    JOURNAL_CLOSE = "journal_close"
    FINAL_REBIND = "final_rebind"


def verify_adr0340_transfer_qualification_source_and_dependencies() -> str:
    """Verify this prospective owner and every inherited sealed dependency."""

    from .fresh_action_width_transfer_qualification_seal import (
        ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH as sealed_path,
        ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256 as sealed_protocol,
        ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256,
        ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST,
        ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT as sealed_task_count,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST
    }
    if actual != ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0340 transfer qualification source closure drifted")
    verify_adr0333_qualification_source_and_dependencies()
    if (
        sealed_protocol != ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256
        or sealed_task_count != ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT
        or sealed_path != ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH
        or tuple(ADR0340_TRANSFER_QUALIFICATION_PROTOCOL["stop_reasons"])
        != tuple(item.value for item in TransferQualificationStopReason)
        or tuple(ADR0340_TRANSFER_QUALIFICATION_PROTOCOL["execution_phases"])
        != tuple(item.value for item in TransferQualificationExecutionPhase)
    ):
        raise RuntimeError("ADR-0340 transfer qualification protocol drifted")
    schedule = build_adr0340_transfer_qualification_schedule()
    if schedule.digest != ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0340 transfer qualification schedule drifted")
    attributes = root.parents[1] / ".gitattributes"
    required = f"/{ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH} -text"
    if required not in attributes.read_text(encoding="utf-8").splitlines():
        raise RuntimeError("ADR-0340 transfer artifact lacks its -text rule")
    return actual["fresh_action_width_transfer_qualification.py"]


@dataclass(frozen=True, slots=True)
class _DerivedTransferQualificationState:
    evidences: tuple[QualificationArmEvidence, ...]
    outcomes: tuple[QualificationContextOutcome, ...]
    qualified_indices: tuple[int, ...]
    stop_reason: TransferQualificationStopReason | None
    known_public_call_count: int
    invocation_count_complete: bool


def _derive_transfer_state(
    evidences: tuple[QualificationArmEvidence, ...],
    *,
    pool: FreshActionWidthTransferPool,
) -> _DerivedTransferQualificationState:
    outcomes: list[QualificationContextOutcome] = []
    qualified: list[int] = []
    pending_full: QualificationArmEvidence | None = None
    stop: TransferQualificationStopReason | None = None
    known_calls = 0
    complete_calls = True
    for index, evidence in enumerate(evidences):
        if evidence.task_index != index:
            raise ValueError("transfer evidence is not a contiguous task prefix")
        if stop is not None:
            raise ValueError("transfer evidence continues past a terminal stop")
        if evidence.kind is QualificationEvidenceKind.UNEXPECTED_EXCEPTION:
            stop = TransferQualificationStopReason.UNEXPECTED_EXCEPTION
            complete_calls = False
            continue
        known_calls += evidence.public_call_count
        if evidence.kind is QualificationEvidenceKind.REJECTED:
            stop = TransferQualificationStopReason.CONSUMER_REJECTED
            continue
        if index % 2 == 0:
            pending_full = evidence
            continue
        if pending_full is None or pending_full.task_index != index - 1:
            raise ValueError("transfer width-two evidence lacks its full arm")
        context_index = index // 2
        try:
            regret = certified_full_minus_subset_regret(
                full=_accepted_interval_from_evidence(pending_full),
                subset=_accepted_interval_from_evidence(evidence),
                reversal_allowance=ADR0323_NESTED_REVERSAL_ALLOWANCE,
            )
        except ValueError:
            stop = TransferQualificationStopReason.NESTED_VALUE_REVERSAL
            pending_full = None
            continue
        classification = classify_action_width_opportunity(
            regret=regret,
            payoff_span_chips=pool.contexts[context_index].payoff_span_chips,
            opportunity_floor=ADR0323_OPPORTUNITY_FLOOR,
            ambiguity_guard=ADR0323_QUALIFICATION_AMBIGUITY_GUARD,
        )
        outcomes.append(
            QualificationContextOutcome(
                context_index=context_index,
                full_evidence_sha256=pending_full.digest,
                width_two_evidence_sha256=evidence.digest,
                regret=regret,
                classification=classification,
            )
        )
        pending_full = None
        if classification is ActionWidthQualificationClassification.AMBIGUOUS:
            stop = TransferQualificationStopReason.AMBIGUOUS
        elif classification is ActionWidthQualificationClassification.QUALIFYING:
            qualified.append(context_index)
            if len(qualified) == ADR0340_TRANSFER_QUALIFICATION_TARGET:
                stop = TransferQualificationStopReason.TARGET_REACHED
    if (
        len(evidences) == ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT
        and stop is None
    ):
        if pending_full is not None:
            raise AssertionError("complete transfer schedule ended on a full arm")
        stop = TransferQualificationStopReason.POOL_EXHAUSTED
    return _DerivedTransferQualificationState(
        evidences=evidences,
        outcomes=tuple(outcomes),
        qualified_indices=tuple(qualified),
        stop_reason=stop,
        known_public_call_count=known_calls,
        invocation_count_complete=complete_calls,
    )


def _campaign_sha256(
    *,
    schedule: TransferQualificationSchedule,
    qualification_source_sha256: str,
    synthetic: bool,
) -> str:
    _require_digest(
        qualification_source_sha256,
        label="transfer qualification campaign source",
    )
    return sha256(
        canonical_journal_json_bytes(
            {
                "artifact_relative_path": (
                    ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH
                ),
                "pool_sha256": schedule.pool_sha256,
                "protocol_sha256": ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256,
                "qualification_source_sha256": qualification_source_sha256,
                "schedule_sha256": schedule.digest,
                "synthetic": synthetic,
                "version": _CAMPAIGN_VERSION,
            }
        )
    ).hexdigest()


def _header_payload(
    *,
    schedule: TransferQualificationSchedule,
    qualification_source_sha256: str,
    campaign_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    return _sealed_payload(
        {
            "artifact_relative_path": (
                ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH
            ),
            "campaign_sha256": campaign_sha256,
            "pool_sha256": schedule.pool_sha256,
            "protocol_sha256": ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256,
            "qualification_source_sha256": qualification_source_sha256,
            "schedule_sha256": schedule.digest,
            "synthetic": synthetic,
            "target": ADR0340_TRANSFER_QUALIFICATION_TARGET,
            "task_count": ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT,
            "version": _HEADER_VERSION,
        },
        digest_field="header_sha256",
    )


def _terminal_payload(
    *,
    state: _DerivedTransferQualificationState,
    pool: FreshActionWidthTransferPool,
    schedule: TransferQualificationSchedule,
    qualification_source_sha256: str,
    campaign_sha256: str,
    final_observation_line_sha256: str,
    synthetic: bool,
) -> dict[str, object]:
    if state.stop_reason is None:
        raise ValueError("transfer terminal requires a derived stop")
    _require_digest(
        final_observation_line_sha256,
        label="transfer final observation line",
    )
    return _sealed_payload(
        {
            "campaign_sha256": campaign_sha256,
            "context_outcomes": tuple(value.payload for value in state.outcomes),
            "evidence_sha256s": tuple(value.digest for value in state.evidences),
            "final_observation_line_sha256": final_observation_line_sha256,
            "invocation_count_complete": state.invocation_count_complete,
            "known_public_call_count": state.known_public_call_count,
            "observed_arm_count": len(state.evidences),
            "pool_sha256": pool.digest,
            "qualification_source_sha256": qualification_source_sha256,
            "qualified_context_semantic_sha256s": tuple(
                pool.contexts[index].semantic_digest
                for index in state.qualified_indices
            ),
            "qualified_indices": state.qualified_indices,
            "record_count": len(state.evidences) + 2,
            "schedule_sha256": schedule.digest,
            "stop_reason": state.stop_reason.value,
            "synthetic": synthetic,
            "version": _TERMINAL_VERSION,
        },
        digest_field="terminal_sha256",
    )


@dataclass(frozen=True, slots=True)
class TransferQualificationJournalPrefix:
    recovery: JournalRecovery
    evidences: tuple[QualificationArmEvidence, ...]
    outcomes: tuple[QualificationContextOutcome, ...]
    qualified_indices: tuple[int, ...]
    pending_stop_reason: TransferQualificationStopReason | None
    known_public_call_count: int
    invocation_count_complete: bool

    def __post_init__(self) -> None:
        if not isinstance(self.recovery, JournalRecovery):
            raise TypeError("transfer prefix requires generic journal recovery")
        if self.recovery.is_complete:
            raise ValueError("transfer prefix cannot contain a terminal journal")
        _validate_derived_collections(
            evidences=self.evidences,
            outcomes=self.outcomes,
            qualified_indices=self.qualified_indices,
            known_public_call_count=self.known_public_call_count,
            invocation_count_complete=self.invocation_count_complete,
        )
        if self.pending_stop_reason is not None and not isinstance(
            self.pending_stop_reason,
            TransferQualificationStopReason,
        ):
            raise TypeError("transfer prefix pending stop must be semantic")


@dataclass(frozen=True, slots=True)
class TransferQualificationJournalResult:
    campaign_sha256: str
    journal_sha256: str
    journal_byte_count: int
    terminal_sha256: str
    evidences: tuple[QualificationArmEvidence, ...]
    outcomes: tuple[QualificationContextOutcome, ...]
    qualified_indices: tuple[int, ...]
    stop_reason: TransferQualificationStopReason
    known_public_call_count: int
    invocation_count_complete: bool
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("transfer campaign", self.campaign_sha256),
            ("transfer journal", self.journal_sha256),
            ("transfer terminal", self.terminal_sha256),
        ):
            _require_digest(value, label=label)
        if _require_count(
            self.journal_byte_count,
            label="transfer journal byte count",
        ) == 0:
            raise ValueError("transfer terminal journal cannot be empty")
        if not isinstance(self.stop_reason, TransferQualificationStopReason):
            raise TypeError("transfer journal stop must be semantic")
        if not isinstance(self.synthetic, bool):
            raise TypeError("transfer journal synthetic flag must be boolean")
        _validate_derived_collections(
            evidences=self.evidences,
            outcomes=self.outcomes,
            qualified_indices=self.qualified_indices,
            known_public_call_count=self.known_public_call_count,
            invocation_count_complete=self.invocation_count_complete,
        )
        if not self.evidences:
            raise ValueError("transfer terminal requires at least one evidence record")
        if (
            self.stop_reason is TransferQualificationStopReason.TARGET_REACHED
            and len(self.qualified_indices)
            != ADR0340_TRANSFER_QUALIFICATION_TARGET
        ):
            raise ValueError("transfer target terminal lacks 16 qualifiers")
        if (
            self.stop_reason is not TransferQualificationStopReason.TARGET_REACHED
            and len(self.qualified_indices)
            >= ADR0340_TRANSFER_QUALIFICATION_TARGET
        ):
            raise ValueError("non-target transfer terminal reached the target")
        if (
            self.stop_reason is TransferQualificationStopReason.POOL_EXHAUSTED
            and len(self.evidences) != ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT
        ):
            raise ValueError("transfer exhaustion terminal lacks the full schedule")
        if (
            self.stop_reason is TransferQualificationStopReason.CONSUMER_REJECTED
            and self.evidences[-1].kind is not QualificationEvidenceKind.REJECTED
        ):
            raise ValueError("transfer rejection terminal lacks rejected evidence")
        if (
            self.stop_reason is TransferQualificationStopReason.UNEXPECTED_EXCEPTION
            and self.evidences[-1].kind
            is not QualificationEvidenceKind.UNEXPECTED_EXCEPTION
        ):
            raise ValueError("transfer unexpected terminal lacks exception evidence")


def _validate_derived_collections(
    *,
    evidences: tuple[QualificationArmEvidence, ...],
    outcomes: tuple[QualificationContextOutcome, ...],
    qualified_indices: tuple[int, ...],
    known_public_call_count: int,
    invocation_count_complete: bool,
) -> None:
    if (
        not isinstance(evidences, tuple)
        or len(evidences) > ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT
        or any(
            not isinstance(item, QualificationArmEvidence) for item in evidences
        )
        or tuple(item.task_index for item in evidences)
        != tuple(range(len(evidences)))
    ):
        raise ValueError("transfer evidence is not a contiguous semantic prefix")
    if (
        not isinstance(outcomes, tuple)
        or any(not isinstance(item, QualificationContextOutcome) for item in outcomes)
        or tuple(item.context_index for item in outcomes)
        != tuple(sorted({item.context_index for item in outcomes}))
    ):
        raise ValueError("transfer outcomes are not unique and ordered")
    derived_qualified = tuple(
        item.context_index
        for item in outcomes
        if item.classification is ActionWidthQualificationClassification.QUALIFYING
    )
    if (
        not isinstance(qualified_indices, tuple)
        or qualified_indices != derived_qualified
        or len(qualified_indices) > ADR0340_TRANSFER_QUALIFICATION_TARGET
    ):
        raise ValueError("transfer qualified indices differ from their outcomes")
    expected_calls = sum(item.public_call_count for item in evidences)
    if (
        isinstance(known_public_call_count, bool)
        or not isinstance(known_public_call_count, int)
        or known_public_call_count != expected_calls
    ):
        raise ValueError("transfer known public-call count drifted")
    expected_complete = all(
        item.kind is not QualificationEvidenceKind.UNEXPECTED_EXCEPTION
        for item in evidences
    )
    if invocation_count_complete is not expected_complete:
        raise ValueError("transfer invocation completeness drifted")


TransferQualificationJournalRebinding = (
    TransferQualificationJournalPrefix | TransferQualificationJournalResult
)


def rebind_adr0340_transfer_qualification_journal(
    raw: bytes,
    *,
    synthetic: bool = False,
) -> TransferQualificationJournalRebinding:
    """Reconstruct a transfer prefix or terminal without a solver call."""

    if not isinstance(raw, bytes):
        raise TypeError("transfer journal rebinding requires immutable bytes")
    if not isinstance(synthetic, bool):
        raise TypeError("transfer journal synthetic mode must be boolean")
    qualification_source = (
        verify_adr0340_transfer_qualification_source_and_dependencies()
    )
    pool = verify_adr0339_transfer_source_and_pool()
    schedule = build_adr0340_transfer_qualification_schedule()
    campaign = _campaign_sha256(
        schedule=schedule,
        qualification_source_sha256=qualification_source,
        synthetic=synthetic,
    )
    first_line_end = raw.find(b"\n")
    if first_line_end >= 0:
        try:
            first_record = parse_journal_record_line(raw[: first_line_end + 1])
        except (TypeError, ValueError):
            pass
        else:
            if (
                first_record.body.protocol_sha256
                != ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256
                or first_record.body.campaign_sha256 != campaign
            ):
                raise ValueError(
                    "transfer journal belongs to another protocol or campaign"
                )
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256,
        expected_campaign_sha256=campaign,
    )
    records = recovery.records
    if not records:
        return TransferQualificationJournalPrefix(
            recovery=recovery,
            evidences=(),
            outcomes=(),
            qualified_indices=(),
            pending_stop_reason=None,
            known_public_call_count=0,
            invocation_count_complete=True,
        )
    header = records[0]
    if header.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("transfer journal first record is not its header")
    expected_header = _header_payload(
        schedule=schedule,
        qualification_source_sha256=qualification_source,
        campaign_sha256=campaign,
        synthetic=synthetic,
    )
    if header.body.payload != expected_header:
        raise ValueError("transfer header differs from its sealed schedule")
    if header.body.semantic_identity_sha256 != expected_header["header_sha256"]:
        raise ValueError("transfer header semantic identity drifted")

    terminal_record: JournalRecordEnvelope | None = None
    observation_records = records[1:]
    if (
        observation_records
        and observation_records[-1].body.kind is JournalRecordKind.TERMINAL
    ):
        terminal_record = observation_records[-1]
        observation_records = observation_records[:-1]
    if any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in observation_records
    ):
        raise ValueError("transfer journal has a non-observation inside its prefix")
    if len(observation_records) > ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT:
        raise ValueError("transfer journal exceeds its sealed task count")
    evidences: list[QualificationArmEvidence] = []
    for index, record in enumerate(observation_records):
        evidence = _rebind_evidence(
            record.body.payload,
            task=schedule.tasks[index],
            task_index=index,
            expect_synthetic=synthetic,
        )
        if record.body.semantic_identity_sha256 != evidence.digest:
            raise ValueError("transfer observation semantic identity drifted")
        evidences.append(evidence)
    state = _derive_transfer_state(tuple(evidences), pool=pool)

    if terminal_record is None:
        return TransferQualificationJournalPrefix(
            recovery=recovery,
            evidences=state.evidences,
            outcomes=state.outcomes,
            qualified_indices=state.qualified_indices,
            pending_stop_reason=state.stop_reason,
            known_public_call_count=state.known_public_call_count,
            invocation_count_complete=state.invocation_count_complete,
        )
    if not recovery.is_complete or recovery.invalid_suffix_bytes:
        raise ValueError("transfer terminal has trailing invalid bytes")
    if not evidences:
        raise ValueError("transfer terminal lacks an observation")
    expected_terminal = _terminal_payload(
        state=state,
        pool=pool,
        schedule=schedule,
        qualification_source_sha256=qualification_source,
        campaign_sha256=campaign,
        final_observation_line_sha256=observation_records[-1].line_sha256,
        synthetic=synthetic,
    )
    terminal_payload = terminal_record.body.payload
    _verify_sealed_payload(
        terminal_payload,
        digest_field="terminal_sha256",
        label="transfer terminal",
    )
    if canonical_journal_json_bytes(terminal_payload) != canonical_journal_json_bytes(
        expected_terminal
    ):
        raise ValueError("transfer terminal differs from journal-derived evidence")
    if (
        terminal_record.body.semantic_identity_sha256
        != terminal_payload["terminal_sha256"]
    ):
        raise ValueError("transfer terminal semantic identity drifted")
    if state.stop_reason is None:
        raise AssertionError("transfer terminal validated without a stop")
    return TransferQualificationJournalResult(
        campaign_sha256=campaign,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
        terminal_sha256=terminal_payload["terminal_sha256"],
        evidences=state.evidences,
        outcomes=state.outcomes,
        qualified_indices=state.qualified_indices,
        stop_reason=state.stop_reason,
        known_public_call_count=state.known_public_call_count,
        invocation_count_complete=state.invocation_count_complete,
        synthetic=synthetic,
    )


@dataclass(frozen=True, slots=True)
class TransferQualifiedPanel:
    """A target-only context binding derived from one exact terminal journal."""

    pool_sha256: str
    schedule_sha256: str
    campaign_sha256: str
    journal_sha256: str
    terminal_sha256: str
    qualified_indices: tuple[int, ...]
    context_semantic_sha256s: tuple[str, ...]
    synthetic: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("transfer panel pool", self.pool_sha256),
            ("transfer panel schedule", self.schedule_sha256),
            ("transfer panel campaign", self.campaign_sha256),
            ("transfer panel journal", self.journal_sha256),
            ("transfer panel terminal", self.terminal_sha256),
        ):
            _require_digest(value, label=label)
        if (
            not isinstance(self.qualified_indices, tuple)
            or len(self.qualified_indices) != ADR0340_TRANSFER_QUALIFICATION_TARGET
            or any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                or index >= ADR0339_TRANSFER_CONTEXT_COUNT
                for index in self.qualified_indices
            )
        ):
            raise ValueError("transfer panel requires 16 valid context indices")
        if tuple(sorted(set(self.qualified_indices))) != self.qualified_indices:
            raise ValueError("transfer panel indices must be unique and ordered")
        if (
            not isinstance(self.context_semantic_sha256s, tuple)
            or len(self.context_semantic_sha256s)
            != ADR0340_TRANSFER_QUALIFICATION_TARGET
        ):
            raise TypeError("transfer panel requires 16 semantic identities")
        for digest in self.context_semantic_sha256s:
            _require_digest(digest, label="transfer panel context")
        if len(set(self.context_semantic_sha256s)) != len(
            self.context_semantic_sha256s
        ):
            raise ValueError("transfer panel repeats a semantic context")
        if not isinstance(self.synthetic, bool):
            raise TypeError("transfer panel synthetic flag must be boolean")
        pool = build_adr0339_transfer_pool()
        from .fresh_action_width_transfer_qualification_seal import (
            ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256,
        )

        if (
            self.pool_sha256 != pool.digest
            or self.schedule_sha256
            != ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256
            or self.context_semantic_sha256s
            != tuple(
                pool.contexts[index].semantic_digest
                for index in self.qualified_indices
            )
        ):
            raise ValueError("transfer panel contexts differ from the exact pool")

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_journal_json_bytes(
            {
                "campaign_sha256": self.campaign_sha256,
                "context_semantic_sha256s": self.context_semantic_sha256s,
                "journal_sha256": self.journal_sha256,
                "pool_sha256": self.pool_sha256,
                "qualified_indices": self.qualified_indices,
                "schedule_sha256": self.schedule_sha256,
                "synthetic": self.synthetic,
                "terminal_sha256": self.terminal_sha256,
                "version": _PANEL_VERSION,
            }
        )

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


def bind_adr0340_transfer_target_panel(
    result: TransferQualificationJournalResult,
) -> TransferQualifiedPanel:
    """Bind only an exact target terminal; every other stop fails closed."""

    if not isinstance(result, TransferQualificationJournalResult):
        raise TypeError("transfer panel requires a terminal journal result")
    if (
        result.stop_reason is not TransferQualificationStopReason.TARGET_REACHED
        or len(result.qualified_indices) != ADR0340_TRANSFER_QUALIFICATION_TARGET
    ):
        raise ValueError("transfer panel requires the exact target stop")
    qualifying = tuple(
        outcome.context_index
        for outcome in result.outcomes
        if outcome.classification
        is ActionWidthQualificationClassification.QUALIFYING
    )
    if qualifying != result.qualified_indices:
        raise ValueError("transfer panel qualifier identities drifted")
    pool = verify_adr0339_transfer_source_and_pool()
    schedule = build_adr0340_transfer_qualification_schedule()
    return TransferQualifiedPanel(
        pool_sha256=pool.digest,
        schedule_sha256=schedule.digest,
        campaign_sha256=result.campaign_sha256,
        journal_sha256=result.journal_sha256,
        terminal_sha256=result.terminal_sha256,
        qualified_indices=result.qualified_indices,
        context_semantic_sha256s=tuple(
            pool.contexts[index].semantic_digest
            for index in result.qualified_indices
        ),
        synthetic=result.synthetic,
    )


def rebind_adr0340_transfer_target_panel(
    raw: bytes,
    *,
    synthetic: bool = False,
) -> TransferQualifiedPanel:
    rebound = rebind_adr0340_transfer_qualification_journal(
        raw,
        synthetic=synthetic,
    )
    if not isinstance(rebound, TransferQualificationJournalResult):
        raise ValueError("transfer panel cannot bind a nonterminal prefix")
    return bind_adr0340_transfer_target_panel(rebound)


@dataclass(frozen=True, slots=True)
class TransferQualificationLaunchRejected:
    reason: str
    output_path: Path
    exception_chain: tuple[dict[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("transfer launch rejection reason must be nonempty")
        if not isinstance(self.output_path, Path):
            raise TypeError("transfer launch rejection path must be a Path")
        if not self.exception_chain:
            raise ValueError("transfer launch rejection requires exception evidence")


@dataclass(frozen=True, slots=True)
class TransferQualificationExecutionFailed:
    reason: str
    phase: TransferQualificationExecutionPhase
    output_path: Path
    failed_task_index: int | None
    unreceipted_arm_invocation: bool
    durably_recorded_evidences: tuple[QualificationArmEvidence, ...]
    known_public_call_count: int
    invocation_count_complete: bool
    raw_journal_bytes: bytes | None
    recovery: JournalRecovery | None
    exception_chain: tuple[dict[str, str], ...]
    recovery_exception_chain: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("transfer execution failure reason must be nonempty")
        if not isinstance(self.phase, TransferQualificationExecutionPhase):
            raise TypeError("transfer execution failure phase must be semantic")
        if not isinstance(self.output_path, Path):
            raise TypeError("transfer execution failure path must be a Path")
        if self.failed_task_index is not None:
            _require_count(
                self.failed_task_index,
                label="transfer failed task index",
                maximum=ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT - 1,
            )
        if not isinstance(self.unreceipted_arm_invocation, bool):
            raise TypeError("transfer unreceipted-call flag must be boolean")
        if not isinstance(self.durably_recorded_evidences, tuple) or any(
            not isinstance(item, QualificationArmEvidence)
            for item in self.durably_recorded_evidences
        ):
            raise TypeError("transfer failure evidence is not semantic")
        expected_calls = sum(
            item.public_call_count for item in self.durably_recorded_evidences
        )
        if (
            isinstance(self.known_public_call_count, bool)
            or not isinstance(self.known_public_call_count, int)
            or self.known_public_call_count != expected_calls
        ):
            raise ValueError("transfer failure call count drifted")
        expected_complete = (
            not self.unreceipted_arm_invocation
            and all(
                item.kind is not QualificationEvidenceKind.UNEXPECTED_EXCEPTION
                for item in self.durably_recorded_evidences
            )
        )
        if self.invocation_count_complete is not expected_complete:
            raise ValueError("transfer failure completeness drifted")
        if not self.exception_chain:
            raise ValueError("transfer execution failure requires exception evidence")
        if self.raw_journal_bytes is None:
            if self.recovery is not None or not self.recovery_exception_chain:
                raise ValueError("unreadable transfer journal lacks recovery evidence")
        elif not isinstance(self.raw_journal_bytes, bytes):
            raise TypeError("transfer failure raw journal is mutable")
        elif self.recovery is None:
            if not self.recovery_exception_chain:
                raise ValueError("transfer raw journal lacks recovery evidence")
        elif (
            not isinstance(self.recovery, JournalRecovery)
            or self.recovery.raw_bytes != self.raw_journal_bytes
        ):
            raise ValueError("transfer failure recovery lost raw bytes")

    @property
    def raw_journal_sha256(self) -> str | None:
        if self.raw_journal_bytes is None:
            return None
        return sha256(self.raw_journal_bytes).hexdigest()


TransferQualificationRunResult = (
    TransferQualificationJournalRebinding
    | TransferQualificationLaunchRejected
    | TransferQualificationExecutionFailed
)
_ArmOwner = Callable[[int, ActionWidthQualificationTask], QualificationArmEvidence]


def _execution_failure(
    *,
    writer: DurableEvidenceJournalWriter,
    output_path: Path,
    campaign_sha256: str,
    phase: TransferQualificationExecutionPhase,
    failed_task_index: int | None,
    unreceipted_arm_invocation: bool,
    evidences: tuple[QualificationArmEvidence, ...],
    error: Exception,
) -> TransferQualificationExecutionFailed:
    exception_chain = _exception_payload(error)
    try:
        writer.close()
    except Exception as close_error:
        exception_chain += _exception_payload(close_error)
    raw: bytes | None = None
    recovery: JournalRecovery | None = None
    recovery_exception_chain: tuple[dict[str, str], ...] = ()
    try:
        raw = output_path.read_bytes()
    except Exception as recovery_error:
        recovery_exception_chain = _exception_payload(recovery_error)
    else:
        try:
            recovery = recover_journal_bytes(
                raw,
                expected_protocol_sha256=(
                    ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256
                ),
                expected_campaign_sha256=campaign_sha256,
            )
        except Exception as recovery_error:
            recovery_exception_chain = _exception_payload(recovery_error)
    return TransferQualificationExecutionFailed(
        reason="transfer qualification failed after exclusive journal creation",
        phase=phase,
        output_path=output_path,
        failed_task_index=failed_task_index,
        unreceipted_arm_invocation=unreceipted_arm_invocation,
        durably_recorded_evidences=evidences,
        known_public_call_count=sum(item.public_call_count for item in evidences),
        invocation_count_complete=(
            not unreceipted_arm_invocation
            and all(
                item.kind is not QualificationEvidenceKind.UNEXPECTED_EXCEPTION
                for item in evidences
            )
        ),
        raw_journal_bytes=raw,
        recovery=recovery,
        exception_chain=exception_chain,
        recovery_exception_chain=recovery_exception_chain,
    )


def _execute_transfer_qualification(
    *,
    output_path: Path,
    pool: FreshActionWidthTransferPool,
    schedule: TransferQualificationSchedule,
    qualification_source_sha256: str,
    arm_owner: _ArmOwner,
    synthetic: bool,
) -> TransferQualificationJournalResult | TransferQualificationExecutionFailed:
    """Execute a supplied owner under the prospective durable protocol."""

    if not isinstance(pool, FreshActionWidthTransferPool):
        raise TypeError("transfer execution requires the exact pool type")
    if not isinstance(schedule, TransferQualificationSchedule):
        raise TypeError("transfer execution requires the exact schedule type")
    if (
        pool.digest != ADR0339_TRANSFER_POOL_SHA256
        or schedule.pool_sha256 != pool.digest
    ):
        raise ValueError("transfer execution pool and schedule identities differ")
    campaign = _campaign_sha256(
        schedule=schedule,
        qualification_source_sha256=qualification_source_sha256,
        synthetic=synthetic,
    )
    writer = DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256,
        campaign_sha256=campaign,
    )
    evidences: list[QualificationArmEvidence] = []
    phase = TransferQualificationExecutionPhase.HEADER_APPEND
    failed_task_index: int | None = None
    unreceipted_arm_invocation = False
    try:
        header_payload = _header_payload(
            schedule=schedule,
            qualification_source_sha256=qualification_source_sha256,
            campaign_sha256=campaign,
            synthetic=synthetic,
        )
        authorization = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=header_payload["header_sha256"],
            payload=header_payload,
        )
        for task_index, task in enumerate(schedule.tasks):
            phase = TransferQualificationExecutionPhase.NEXT_CALL_AUTHORIZATION
            failed_task_index = task_index
            expected_kind = (
                JournalRecordKind.HEADER
                if task_index == 0
                else JournalRecordKind.OBSERVATION
            )
            if (
                authorization.sequence != task_index
                or authorization.kind is not expected_kind
            ):
                raise RuntimeError("transfer call lacks its preceding durable receipt")
            phase = TransferQualificationExecutionPhase.ARM_EVIDENCE
            unreceipted_arm_invocation = True
            try:
                evidence = arm_owner(task_index, task)
                if not isinstance(evidence, QualificationArmEvidence):
                    raise TypeError("transfer arm owner returned nonsemantic evidence")
                _validate_evidence_against_task(
                    evidence,
                    task=task,
                    expect_synthetic=synthetic,
                )
            except Exception as error:
                evidence = _unexpected_evidence(
                    task_index=task_index,
                    task=task,
                    error=error,
                    synthetic=synthetic,
                )
                _validate_evidence_against_task(
                    evidence,
                    task=task,
                    expect_synthetic=synthetic,
                )
            phase = TransferQualificationExecutionPhase.OBSERVATION_APPEND
            authorization = writer.append(
                kind=JournalRecordKind.OBSERVATION,
                semantic_identity_sha256=evidence.digest,
                payload=evidence.journal_payload,
            )
            evidences.append(evidence)
            unreceipted_arm_invocation = False
            phase = TransferQualificationExecutionPhase.SEMANTIC_REDUCTION
            state = _derive_transfer_state(tuple(evidences), pool=pool)
            if state.stop_reason is None:
                continue
            terminal_payload = _terminal_payload(
                state=state,
                pool=pool,
                schedule=schedule,
                qualification_source_sha256=qualification_source_sha256,
                campaign_sha256=campaign,
                final_observation_line_sha256=authorization.line_sha256,
                synthetic=synthetic,
            )
            phase = TransferQualificationExecutionPhase.TERMINAL_APPEND
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=terminal_payload["terminal_sha256"],
                payload=terminal_payload,
            )
            break
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_task_index=failed_task_index,
            unreceipted_arm_invocation=unreceipted_arm_invocation,
            evidences=tuple(evidences),
            error=error,
        )
    phase = TransferQualificationExecutionPhase.JOURNAL_CLOSE
    try:
        writer.close()
        phase = TransferQualificationExecutionPhase.FINAL_REBIND
        rebound = rebind_adr0340_transfer_qualification_journal(
            output_path.read_bytes(),
            synthetic=synthetic,
        )
        if not isinstance(rebound, TransferQualificationJournalResult):
            raise RuntimeError("transfer execution ended without a terminal result")
        return rebound
    except Exception as error:
        return _execution_failure(
            writer=writer,
            output_path=output_path,
            campaign_sha256=campaign,
            phase=phase,
            failed_task_index=failed_task_index,
            unreceipted_arm_invocation=False,
            evidences=tuple(evidences),
            error=error,
        )


def _real_arm_owner(
    task_index: int,
    task: ActionWidthQualificationTask,
) -> QualificationArmEvidence:
    result = consume_certified_reduced_sizing_v2(task.request)
    return evidence_from_consumer_result(
        task_index=task_index,
        task=task,
        result=result,
    )


def _artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH
    )


def run_and_retain_adr0339_transfer_qualification(
) -> TransferQualificationRunResult:
    """Open the transfer qualifier only after its committed source seal."""

    output_path = _artifact_path()
    try:
        source = verify_adr0340_transfer_qualification_source_and_dependencies()
        pool = verify_adr0339_transfer_source_and_pool()
        schedule = build_adr0340_transfer_qualification_schedule()
    except Exception as error:
        return TransferQualificationLaunchRejected(
            reason="transfer source or schedule preflight rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )
    try:
        return _execute_transfer_qualification(
            output_path=output_path,
            pool=pool,
            schedule=schedule,
            qualification_source_sha256=source,
            arm_owner=_real_arm_owner,
            synthetic=False,
        )
    except Exception as error:
        return TransferQualificationLaunchRejected(
            reason="transfer exclusive journal launch rejected",
            output_path=output_path,
            exception_chain=_exception_payload(error),
        )


def synthetic_transfer_accepted_evidence(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
    lower_chips: float,
    upper_chips: float,
) -> QualificationArmEvidence:
    """Build inherited fake accepted evidence without a consumer call."""

    return synthetic_accepted_evidence(
        task_index=task_index,
        task=task,
        lower_chips=lower_chips,
        upper_chips=upper_chips,
    )


def synthetic_transfer_rejected_evidence(
    *,
    task_index: int,
    task: ActionWidthQualificationTask,
) -> QualificationArmEvidence:
    """Build inherited fake typed rejection without a consumer call."""

    return synthetic_rejected_evidence(
        task_index=task_index,
        task=task,
    )


__all__ = [
    "ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH",
    "ADR0340_TRANSFER_QUALIFICATION_PROTOCOL",
    "ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256",
    "ADR0340_TRANSFER_QUALIFICATION_TARGET",
    "ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT",
    "TransferQualificationExecutionFailed",
    "TransferQualificationExecutionPhase",
    "TransferQualificationJournalPrefix",
    "TransferQualificationJournalRebinding",
    "TransferQualificationJournalResult",
    "TransferQualificationLaunchRejected",
    "TransferQualificationRunResult",
    "TransferQualificationSchedule",
    "TransferQualificationStopReason",
    "TransferQualifiedPanel",
    "bind_adr0340_transfer_target_panel",
    "build_adr0340_transfer_qualification_schedule",
    "rebind_adr0340_transfer_qualification_journal",
    "rebind_adr0340_transfer_target_panel",
    "run_and_retain_adr0339_transfer_qualification",
    "synthetic_transfer_accepted_evidence",
    "synthetic_transfer_rejected_evidence",
    "verify_adr0339_transfer_source_and_pool",
    "verify_adr0340_transfer_qualification_source_and_dependencies",
]
