"""Solver-free result owner for ADR-0337's retained direct mechanism.

The one-shot value owner is closed.  This module accepts only the exact retained
JSONL bytes, invokes the independently sealed journal rebinder, and publishes a
typed development-width result without a consumer, solver, campaign, writer,
latency claim, transfer path, or action path.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from .certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from .durable_evidence_journal import canonical_journal_json_bytes
from .fresh_action_width_greedy import GreedyWidthGateResult
from .fresh_action_width_nonreplay_greedy import (
    ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH,
    ADR0337_GREEDY_CALL_COUNT,
    ADR0337_GREEDY_COMPLETED_RECORD_COUNT,
    ADR0337_GREEDY_PROTOCOL_SHA256,
    NonReplayGreedyEvidenceKind,
    NonReplayGreedyJournalResult,
    NonReplayGreedyStopReason,
    rebind_adr0337_greedy_journal,
)
from .fresh_action_width_nonreplay_greedy_seal import (
    ADR0337_GREEDY_SCHEDULE_SHA256,
    ADR0337_GREEDY_SOURCE_MANIFEST,
)
from .fresh_action_width_nonreplay_qualification_result import (
    ADR0334_QUALIFIED_PANEL_SHA256,
)
from .fresh_action_width_nonreplay_teacher_result import (
    ADR0336_TEACHER_RESULT_SHA256,
)
from .fresh_action_width_structures import RaiseActionWidth


ADR0338_GREEDY_ARTIFACT_BYTES = 1_437_835
ADR0338_GREEDY_ARTIFACT_SHA256 = (
    "8e53b303ddfce361458a725ab1167249b34c5c2321c954ccfa92b7bba07daa4b"
)
ADR0338_GREEDY_CAMPAIGN_SHA256 = (
    "4938393e22be03349afcd6845d2102a9d1d232f4427b05802fc00ef2ad7efd3e"
)
ADR0338_GREEDY_TERMINAL_SHA256 = (
    "57dccc44c403f3557b34724b39d78d78d5896bae705c2cdf4d9f9d90102f95ec"
)
ADR0338_GREEDY_RECORD_COUNT = 378
ADR0338_GREEDY_EVIDENCE_COUNT = 376
ADR0338_GREEDY_CONTEXT_COUNT = 16
ADR0338_GREEDY_PUBLIC_CALL_COUNT = 376
ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH = 3
ADR0338_MAX_CERTIFICATE_GAP_HEX = "0x1.ce00000000000p-40"
ADR0338_MAX_CERTIFICATE_GAP_CALL_INDEX = 213

ADR0338_GREEDY_CONTEXT_RESULT_SHA256S = (
    "16f98a74d2c7e5fce21c34f7677ece4d3103913b5b661497404d812529e9ad26",
    "f1ec7073c41fdcc287101174af3b4b5c11c790f6396f8b222c97a0f782394039",
    "6805c25142c422a543241a3f98e562238d4e52a989ccd2c3ce324bdbab5e2c04",
    "bb20626888058379555b8343e72a8c77bd81a59c1559f60e2844b44bccca08bb",
    "4a1f2a7363d99de0a3e0949e7eca34e62908b8e8cbbc96f9de4b8e582e6b0e36",
    "cd0cd0850191925a4bc3612058918b117bf118b5789f99966f799c45e4a07e62",
    "f782fc1d4950326f6b8bf0bd26a6253c4e9c0c51cfed7b974e548a2696123f1a",
    "72621a7dc906e6a95739dd6911a58ac0a5a34cf918b7786a7dde0e03e2953d1e",
    "d12efc5c2d76833c103dd43dbae477c8c4e78d45dc989b032fcc68ecba93cef3",
    "c8e863a985278d3d3e6793549a3fbf4083315c0abc8b93b1579795088cfc7bac",
    "c1aafeb1b20e1c6bc81c9082741705374c86e9847c0794237b79ee268aa68761",
    "689bcbe59bee00bc6d4500830c5731bccc99a8c81c3d6a8a0c79a9aeeb5f523e",
    "3ad21d01398dff10e53de471e83ae6285874f67d002d0e4f42534d9887d11a3e",
    "3dd87cc45ed251278cb56b4095ab86fd017377de46fad1b5fee97ad001db54a5",
    "a5680f030cf39a6bca22382344831b54244a9ca6dc507c257fde32f79c5acb72",
    "e672189b746434e7f1bf8cbd51426d9dfe17268eb88b1ef56848699699649229",
)

# Initial width two followed by the selected menus at target widths three
# through six.  These are integer raise-to totals, not bet increments.
ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT = (
    ((2, 8), (2, 5, 8), (2, 3, 5, 8), (2, 3, 4, 5, 8), (2, 3, 4, 5, 6, 8)),
    ((2, 10), (2, 6, 10), (2, 3, 6, 10), (2, 3, 4, 6, 10), (2, 3, 4, 5, 6, 10)),
    ((2, 12), (2, 8, 12), (2, 5, 8, 12), (2, 3, 5, 8, 12), (2, 3, 4, 5, 8, 12)),
    ((2, 10), (2, 3, 10), (2, 3, 4, 10), (2, 3, 4, 5, 10), (2, 3, 4, 5, 6, 10)),
    ((2, 10), (2, 3, 10), (2, 3, 4, 10), (2, 3, 4, 5, 10), (2, 3, 4, 5, 6, 10)),
    ((2, 8), (2, 4, 8), (2, 3, 4, 8), (2, 3, 4, 5, 8), (2, 3, 4, 5, 6, 8)),
    ((2, 8), (2, 6, 8), (2, 3, 6, 8), (2, 3, 6, 7, 8), (2, 3, 4, 6, 7, 8)),
    ((2, 10), (2, 5, 10), (2, 3, 5, 10), (2, 3, 4, 5, 10), (2, 3, 4, 5, 6, 10)),
    ((2, 10), (2, 9, 10), (2, 3, 9, 10), (2, 3, 4, 9, 10), (2, 3, 4, 5, 9, 10)),
    ((2, 10), (2, 6, 10), (2, 6, 9, 10), (2, 3, 6, 9, 10), (2, 3, 4, 6, 9, 10)),
    ((2, 12), (2, 4, 12), (2, 4, 5, 12), (2, 3, 4, 5, 12), (2, 3, 4, 5, 6, 12)),
    ((2, 8), (2, 5, 8), (2, 3, 5, 8), (2, 3, 4, 5, 8), (2, 3, 4, 5, 6, 8)),
    ((2, 12), (2, 3, 12), (2, 3, 5, 12), (2, 3, 4, 5, 12), (2, 3, 4, 5, 6, 12)),
    ((2, 10), (2, 8, 10), (2, 3, 8, 10), (2, 3, 4, 8, 10), (2, 3, 4, 5, 8, 10)),
    ((2, 12), (2, 5, 12), (2, 3, 5, 12), (2, 3, 4, 5, 12), (2, 3, 4, 5, 6, 12)),
    ((2, 12), (2, 8, 12), (2, 8, 9, 12), (2, 5, 8, 9, 12), (2, 5, 6, 8, 9, 12)),
)

ADR0338_SELECTED_SUBSET_INDICES_BY_CONTEXT = (
    (2, 1, 0, 0),
    (3, 2, 1, 0),
    (5, 17, 9, 2),
    (0, 0, 0, 0),
    (0, 0, 0, 0),
    (1, 0, 0, 0),
    (3, 2, 5, 2),
    (2, 1, 0, 0),
    (6, 5, 4, 3),
    (3, 17, 11, 6),
    (1, 8, 0, 0),
    (2, 1, 0, 0),
    (0, 1, 0, 0),
    (5, 4, 3, 2),
    (2, 1, 0, 0),
    (5, 30, 58, 95),
)

ADR0338_GREEDY_WIDTH_GATE_SHA256S = (
    "48478cb0a772e71185f6d549bc44e5c38f74398b0d0cc040995ffba712521753",
    "42a65aa5ef5080c5ad0e72d0a5aa8b932b1cacee6c2a02559539734bf9cf97a1",
    "c135d501d86532b1f93e63779b3b6babeb7e3f4820610ba3e9b308c6d9b9afeb",
    "07fed9592662846aa6cbc7a77ea3b402eb8444e3ff801b74c54d6f45d87b17d9",
)

# Width, full-regret maximum/mean interval, aggregate-recovery interval and
# chip endpoints, teacher-excess maximum/mean interval, then the five gates.
ADR0338_GREEDY_WIDTH_GATE_SPECS = (
    (3, "0x1.df6f95978e3c4p-13", "0x1.8ed0cb68a0f90p-16", "0x1.8ed0cb83575a5p-16", "0x1.f49ef41768a00p-1", "0x1.f49ef418609e2p-1", "0x1.159dffe8edfecp-1", "0x1.159dffe9042a0p-1", "0x1.1bed6ac91d301p-1", "0x1.1bed6ac9932a0p-1", "0x1.15d2d2d2d2d2dp-46", "0x0.0p+0", "0x1.b98a96e01df53p-47", True, True, True, True, True),
    (4, "0x1.5970f0f0f0f0fp-43", "0x0.0p+0", "0x1.a3950a0053ef1p-44", "0x1.ffffffff2b44dp-1", "0x1.000000001ce33p+0", "0x1.1bed6ac91d31ep-1", "0x1.1bed6ac93d3a0p-1", "0x1.1bed6ac91d301p-1", "0x1.1bed6ac9932a0p-1", "0x1.ca69696969697p-46", "0x0.0p+0", "0x1.76ea4d868790ep-46", True, True, True, True, True),
    (5, "0x1.5974b4b4b4b4bp-43", "0x0.0p+0", "0x1.a3969389dd78ap-44", "0x1.ffffffff2b442p-1", "0x1.00000000276cep+0", "0x1.1bed6ac91d318p-1", "0x1.1bed6ac948ea0p-1", "0x1.1bed6ac91d301p-1", "0x1.1bed6ac9932a0p-1", "0x1.5dad2d2d2d2d3p-45", "0x0.0p+0", "0x1.2174db9bb1ce2p-45", True, True, True, True, True),
    (6, "0x1.5974b4b4b4b4bp-43", "0x0.0p+0", "0x1.a3947167bb567p-44", "0x1.ffffffff2b450p-1", "0x1.0000000032787p+0", "0x1.1bed6ac91d320p-1", "0x1.1bed6ac9552a0p-1", "0x1.1bed6ac91d301p-1", "0x1.1bed6ac9932a0p-1", "0x1.b807878787878p-45", "0x0.0p+0", "0x1.861ec188877e3p-45", True, True, True, True, True),
)

ADR0338_GREEDY_RESULT_SHA256 = (
    "7317ff19c02efe9fa084802120289286c2a6eb1885b816087ba58b710ca27353"
)


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _gate_spec(gate: GreedyWidthGateResult) -> tuple[object, ...]:
    return (
        gate.raise_width.count,
        gate.maximum_normalized_full_regret_upper.hex(),
        gate.mean_normalized_full_regret_lower.hex(),
        gate.mean_normalized_full_regret_upper.hex(),
        gate.aggregate_recovery.lower.hex(),
        gate.aggregate_recovery.upper.hex(),
        gate.aggregate_recovery.achieved_gain_lower_chips.hex(),
        gate.aggregate_recovery.achieved_gain_upper_chips.hex(),
        gate.aggregate_recovery.available_gain_lower_chips.hex(),
        gate.aggregate_recovery.available_gain_upper_chips.hex(),
        gate.maximum_normalized_teacher_excess_upper.hex(),
        gate.mean_normalized_teacher_excess_lower.hex(),
        gate.mean_normalized_teacher_excess_upper.hex(),
        gate.maximum_full_regret_pass,
        gate.mean_full_regret_pass,
        gate.aggregate_recovery_pass,
        gate.maximum_teacher_excess_pass,
        gate.mean_teacher_excess_pass,
    )


def _selected_menus(
    journal: NonReplayGreedyJournalResult,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(
        (context.initial_task.raise_to_totals,)
        + tuple(
            round_result.selected.transition.augmented.raise_to_totals
            for round_result in context.rounds
        )
        for context in journal.contexts
    )


def _selected_subset_indices(
    journal: NonReplayGreedyJournalResult,
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            round_result.selected.transition.augmented.subset_index
            for round_result in context.rounds
        )
        for context in journal.contexts
    )


def _validate_selected_menus(value: object) -> None:
    if not isinstance(value, tuple) or len(value) != ADR0338_GREEDY_CONTEXT_COUNT:
        raise TypeError("retained greedy menus require all contexts")
    for menus in value:
        if not isinstance(menus, tuple) or len(menus) != 5:
            raise TypeError("retained greedy context requires widths two through six")
        for width, menu in zip(range(2, 7), menus, strict=True):
            if (
                not isinstance(menu, tuple)
                or len(menu) != width
                or any(
                    isinstance(total, bool)
                    or not isinstance(total, int)
                    or total <= 0
                    for total in menu
                )
                or tuple(sorted(set(menu))) != menu
            ):
                raise ValueError("retained greedy menu is not an exact raise-to set")


def _validate_subset_indices(value: object) -> None:
    if not isinstance(value, tuple) or len(value) != ADR0338_GREEDY_CONTEXT_COUNT:
        raise TypeError("retained greedy subset indices require all contexts")
    if any(
        not isinstance(row, tuple)
        or len(row) != 4
        or any(
            isinstance(index, bool) or not isinstance(index, int) or index < 0
            for index in row
        )
        for row in value
    ):
        raise ValueError("retained greedy subset indices are invalid")


@dataclass(frozen=True, slots=True)
class RetainedNonReplayGreedyResult:
    journal: NonReplayGreedyJournalResult
    selected_development_raise_width: RaiseActionWidth
    selected_menu_totals_by_context: tuple[tuple[tuple[int, ...], ...], ...]
    selected_subset_indices_by_context: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.journal, NonReplayGreedyJournalResult):
            raise TypeError("retained greedy result requires its semantic journal")
        if (
            self.journal.campaign_sha256 != ADR0338_GREEDY_CAMPAIGN_SHA256
            or self.journal.journal_sha256 != ADR0338_GREEDY_ARTIFACT_SHA256
            or self.journal.terminal_sha256 != ADR0338_GREEDY_TERMINAL_SHA256
            or self.journal.stop_reason is not NonReplayGreedyStopReason.COMPLETED_SELECTED
            or self.journal.synthetic
            or not self.journal.invocation_count_complete
            or self.journal.partial_context is not None
            or self.journal.failure_stage is not None
            or self.journal.failure_exception_chain
        ):
            raise ValueError("retained greedy result belongs to another journal")
        if not isinstance(self.selected_development_raise_width, RaiseActionWidth):
            raise TypeError("retained greedy width must be semantic")
        passing = tuple(gate for gate in self.journal.width_gates if gate.passes)
        expected_width = None if not passing else passing[0].raise_width
        if (
            self.selected_development_raise_width != expected_width
            or self.journal.selected_raise_width != expected_width
            or self.selected_development_raise_width.count
            != ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH
        ):
            raise ValueError("retained greedy development width drifted")
        _validate_selected_menus(self.selected_menu_totals_by_context)
        _validate_subset_indices(self.selected_subset_indices_by_context)
        if self.selected_menu_totals_by_context != _selected_menus(self.journal):
            raise ValueError("retained greedy menus crossed the journal")
        if self.selected_subset_indices_by_context != _selected_subset_indices(
            self.journal
        ):
            raise ValueError("retained greedy subset indices crossed the journal")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "artifact_sha256": self.journal.journal_sha256,
                    "campaign_sha256": self.journal.campaign_sha256,
                    "context_result_sha256s": tuple(
                        context.digest for context in self.journal.contexts
                    ),
                    "greedy_protocol_sha256": ADR0337_GREEDY_PROTOCOL_SHA256,
                    "greedy_source_sha256": ADR0337_GREEDY_SOURCE_MANIFEST[
                        "fresh_action_width_nonreplay_greedy.py"
                    ],
                    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
                    "schedule_sha256": ADR0337_GREEDY_SCHEDULE_SHA256,
                    "selected_development_raise_width": (
                        self.selected_development_raise_width.count
                    ),
                    "selected_menu_totals_by_context": (
                        self.selected_menu_totals_by_context
                    ),
                    "selected_subset_indices_by_context": (
                        self.selected_subset_indices_by_context
                    ),
                    "teacher_result_sha256": ADR0336_TEACHER_RESULT_SHA256,
                    "terminal_sha256": self.journal.terminal_sha256,
                    "version": "adr0338-nonreplay-greedy-retained-result-v1",
                    "width_gate_sha256s": tuple(
                        gate.digest for gate in self.journal.width_gates
                    ),
                }
            )
        ).hexdigest()


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[2] / ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH


def _rebind_retained_result(raw: bytes) -> RetainedNonReplayGreedyResult:
    rebound = rebind_adr0337_greedy_journal(raw, synthetic=False)
    if not isinstance(rebound, NonReplayGreedyJournalResult):
        raise TypeError("ADR-0338 greedy journal lacks an exact terminal result")
    if (
        rebound.campaign_sha256 != ADR0338_GREEDY_CAMPAIGN_SHA256
        or rebound.journal_sha256 != ADR0338_GREEDY_ARTIFACT_SHA256
        or rebound.journal_byte_count != ADR0338_GREEDY_ARTIFACT_BYTES
        or rebound.terminal_sha256 != ADR0338_GREEDY_TERMINAL_SHA256
        or len(rebound.evidences) != ADR0338_GREEDY_EVIDENCE_COUNT
        or len(rebound.contexts) != ADR0338_GREEDY_CONTEXT_COUNT
        or rebound.known_public_call_count != ADR0338_GREEDY_PUBLIC_CALL_COUNT
        or not rebound.invocation_count_complete
        or rebound.synthetic
        or rebound.stop_reason is not NonReplayGreedyStopReason.COMPLETED_SELECTED
        or rebound.partial_context is not None
        or rebound.failure_stage is not None
        or rebound.failure_exception_chain
    ):
        raise ValueError("ADR-0338 greedy terminal identity drifted")
    if any(
        evidence.kind is not NonReplayGreedyEvidenceKind.ACCEPTED
        or evidence.synthetic
        or evidence.public_call_count != 1
        for evidence in rebound.evidences
    ):
        raise ValueError("ADR-0338 greedy arm acceptance drifted")
    if tuple(context.digest for context in rebound.contexts) != (
        ADR0338_GREEDY_CONTEXT_RESULT_SHA256S
    ):
        raise ValueError("ADR-0338 greedy context reductions drifted")
    if tuple(gate.digest for gate in rebound.width_gates) != (
        ADR0338_GREEDY_WIDTH_GATE_SHA256S
    ) or tuple(_gate_spec(gate) for gate in rebound.width_gates) != (
        ADR0338_GREEDY_WIDTH_GATE_SPECS
    ):
        raise ValueError("ADR-0338 greedy five-gate curve drifted")
    gaps = tuple(
        float.fromhex(evidence.core["result"]["certified_gap_hex"])
        for evidence in rebound.evidences
    )
    max_position = max(range(len(gaps)), key=gaps.__getitem__)
    if (
        gaps[max_position].hex() != ADR0338_MAX_CERTIFICATE_GAP_HEX
        or max_position != ADR0338_MAX_CERTIFICATE_GAP_CALL_INDEX
    ):
        raise ValueError("ADR-0338 greedy certificate diagnostic drifted")
    menus = _selected_menus(rebound)
    subsets = _selected_subset_indices(rebound)
    if menus != ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT:
        raise ValueError("ADR-0338 greedy selected menus drifted")
    if subsets != ADR0338_SELECTED_SUBSET_INDICES_BY_CONTEXT:
        raise ValueError("ADR-0338 greedy selected subsets drifted")
    return RetainedNonReplayGreedyResult(
        journal=rebound,
        selected_development_raise_width=RaiseActionWidth(
            ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH
        ),
        selected_menu_totals_by_context=menus,
        selected_subset_indices_by_context=subsets,
    )


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0338_GREEDY_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0337_GREEDY_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0338_GREEDY_ARTIFACT_SHA256,
    "campaign_sha256": ADR0338_GREEDY_CAMPAIGN_SHA256,
    "claim_boundary": (
        "development-width-only; no production-width, latency, transfer, "
        "response-raise, six-player-response, preparation, or action claim"
    ),
    "context_count": ADR0338_GREEDY_CONTEXT_COUNT,
    "context_result_sha256s": ADR0338_GREEDY_CONTEXT_RESULT_SHA256S,
    "evidence_count": ADR0338_GREEDY_EVIDENCE_COUNT,
    "greedy_protocol_sha256": ADR0337_GREEDY_PROTOCOL_SHA256,
    "greedy_source_sha256": ADR0337_GREEDY_SOURCE_MANIFEST[
        "fresh_action_width_nonreplay_greedy.py"
    ],
    "maximum_certificate_gap_call_index": ADR0338_MAX_CERTIFICATE_GAP_CALL_INDEX,
    "maximum_certificate_gap_hex": ADR0338_MAX_CERTIFICATE_GAP_HEX,
    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
    "public_call_count": ADR0338_GREEDY_PUBLIC_CALL_COUNT,
    "rebind": (
        "exact-bytes+durable-chain+dynamic-branch+policy-lower+dual-upper+"
        "prices+teacher-counterparts+five-gates+menus-without-solving"
    ),
    "record_count": ADR0338_GREEDY_RECORD_COUNT,
    "result_sha256": ADR0338_GREEDY_RESULT_SHA256,
    "schedule_sha256": ADR0337_GREEDY_SCHEDULE_SHA256,
    "selected_development_raise_width": ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH,
    "selected_menu_totals_by_context": ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT,
    "selected_subset_indices_by_context": ADR0338_SELECTED_SUBSET_INDICES_BY_CONTEXT,
    "stop_reason": "completed_selected",
    "teacher_result_sha256": ADR0336_TEACHER_RESULT_SHA256,
    "terminal_sha256": ADR0338_GREEDY_TERMINAL_SHA256,
    "version": "adr0338-nonreplay-greedy-result-protocol-v1",
    "width_gate_sha256s": ADR0338_GREEDY_WIDTH_GATE_SHA256S,
    "width_gate_specs": ADR0338_GREEDY_WIDTH_GATE_SPECS,
}
ADR0338_GREEDY_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0338_GREEDY_RESULT_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_RESULT_PROTOCOL_PAYLOAD)
).hexdigest()


def verify_adr0338_greedy_result_source_and_dependencies() -> str:
    from .fresh_action_width_nonreplay_greedy_result_seal import (
        ADR0338_GREEDY_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0338_GREEDY_RESULT_SOURCE_MANIFEST,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0338_GREEDY_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0338_GREEDY_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0338 greedy-result source closure drifted")
    if sealed_protocol != ADR0338_GREEDY_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0338 greedy-result protocol drifted")
    return actual["fresh_action_width_nonreplay_greedy_result.py"]


def verify_adr0338_nonreplay_greedy_result_artifact(
    path: Path | None = None,
) -> RetainedNonReplayGreedyResult:
    """Verify exact retained bytes and rederive the result without solving."""

    verify_adr0338_greedy_result_source_and_dependencies()
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0338_GREEDY_ARTIFACT_BYTES:
        raise ValueError("ADR-0338 greedy journal byte count drifted")
    if sha256(raw).hexdigest() != ADR0338_GREEDY_ARTIFACT_SHA256:
        raise ValueError("ADR-0338 greedy journal SHA-256 drifted")
    if (
        raw.count(b"\n") != ADR0338_GREEDY_RECORD_COUNT
        or not raw.endswith(b"\n")
        or raw.endswith(b"\n\n")
    ):
        raise ValueError("ADR-0338 greedy journal record shape drifted")
    result = _rebind_retained_result(raw)
    if result.digest != ADR0338_GREEDY_RESULT_SHA256:
        raise ValueError("ADR-0338 retained greedy result identity drifted")
    return result


__all__ = [
    "ADR0338_GREEDY_ARTIFACT_BYTES",
    "ADR0338_GREEDY_ARTIFACT_SHA256",
    "ADR0338_GREEDY_CAMPAIGN_SHA256",
    "ADR0338_GREEDY_CONTEXT_COUNT",
    "ADR0338_GREEDY_CONTEXT_RESULT_SHA256S",
    "ADR0338_GREEDY_EVIDENCE_COUNT",
    "ADR0338_GREEDY_PUBLIC_CALL_COUNT",
    "ADR0338_GREEDY_RECORD_COUNT",
    "ADR0338_GREEDY_RESULT_PROTOCOL",
    "ADR0338_GREEDY_RESULT_PROTOCOL_SHA256",
    "ADR0338_GREEDY_RESULT_SHA256",
    "ADR0338_GREEDY_TERMINAL_SHA256",
    "ADR0338_GREEDY_WIDTH_GATE_SHA256S",
    "ADR0338_GREEDY_WIDTH_GATE_SPECS",
    "ADR0338_MAX_CERTIFICATE_GAP_CALL_INDEX",
    "ADR0338_MAX_CERTIFICATE_GAP_HEX",
    "ADR0338_SELECTED_DEVELOPMENT_RAISE_WIDTH",
    "ADR0338_SELECTED_MENU_TOTALS_BY_CONTEXT",
    "ADR0338_SELECTED_SUBSET_INDICES_BY_CONTEXT",
    "RetainedNonReplayGreedyResult",
    "verify_adr0338_greedy_result_source_and_dependencies",
    "verify_adr0338_nonreplay_greedy_result_artifact",
]
