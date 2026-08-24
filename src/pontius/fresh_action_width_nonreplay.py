"""Value-free ADR-0331 population and synthetic evidence exercise.

This source constructs a new deterministic h4 population, rejects semantic
overlap with every ADR-0323 development context, and exercises the exact
402-record journal shape required before any replacement sizing value.  It
imports no solver, sizing result, transfer, preparation, or action owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import comb
from pathlib import Path
from types import MappingProxyType

from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalAppendReceipt,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from .fresh_action_width_structures import (
    ADR0323_DEVELOPMENT_CONTEXT_COUNT,
    ADR0323_GENERATOR_VERSION,
    ADR0323_POTS,
    ADR0323_RAISE_WIDTHS,
    ADR0323_STACKS,
    ADR0323_STRUCTURAL_FILTER_VERSION,
    ADR0323_STRUCTURE_PROTOCOL_SHA256,
    ActionWidthSubsetWorkLedger,
    FreshActionWidthContext,
    _DigestStream,
    _kernel_raise_universe,
    _private_pairs,
    _river_opening_state,
    _showdown_signs,
    _shuffled_deck,
    _structurally_admissible,
    build_adr0323_development_pool,
)
from .fresh_action_width_structures_seal import (
    ADR0323_DEVELOPMENT_POOL_SHA256,
)


ADR0331_RECOVERY_BASELINE_COMMIT = "49044e58fc3a2a582fda11daba4f641da5b3e646"
ADR0331_PREREGISTRATION_COMMIT = "de166d81d5f91df48e6ec0ecea27000e04fd4f30"
ADR0331_POPULATION_SEED = (
    "pontius|adr-0331|fresh-action-width-nonreplay|population|"
    f"recovery-commit={ADR0331_RECOVERY_BASELINE_COMMIT}"
)
ADR0331_POPULATION_SEED_SHA256 = (
    "a419d1651708dae88c451546dae5639c8d1c2840a4441b93b712802a9b2541ba"
)
ADR0331_POPULATION_CONTEXT_COUNT = ADR0323_DEVELOPMENT_CONTEXT_COUNT
ADR0331_SYNTHETIC_OBSERVATION_COUNT = 400
ADR0331_SYNTHETIC_RECORD_COUNT = 402
ADR0331_SYNTHETIC_INITIAL_CALL_COUNT = 16
ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH = (
    (3, 120),
    (4, 104),
    (5, 88),
    (6, 72),
)
ADR0331_SYNTHETIC_GATE_FIELDS = (
    "maximum_normalized_full_regret_upper",
    "mean_normalized_full_regret_upper",
    "minimum_aggregate_recovery_lower",
    "maximum_normalized_teacher_excess_upper",
    "mean_normalized_teacher_excess_upper",
)

_PRIVATE_RANGE_WIDTH = 4
_POPULATION_VERSION = "adr0331-fresh-action-width-nonreplay-pool-v1"
_SYNTHETIC_HEADER_VERSION = "adr0331-synthetic-journal-header-v1"
_SYNTHETIC_OBSERVATION_VERSION = "adr0331-synthetic-observation-v1"
_SYNTHETIC_SUMMARY_VERSION = "adr0331-synthetic-width-summary-v1"
_SYNTHETIC_TERMINAL_VERSION = "adr0331-synthetic-terminal-v1"

_ADR0331_NONREPLAY_PROTOCOL_PAYLOAD = {
    "excluded_pool_sha256": ADR0323_DEVELOPMENT_POOL_SHA256,
    "generator_distribution_protocol_sha256": ADR0323_STRUCTURE_PROTOCOL_SHA256,
    "generator_version": ADR0323_GENERATOR_VERSION,
    "journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    "population_context_count": ADR0331_POPULATION_CONTEXT_COUNT,
    "population_seed": ADR0331_POPULATION_SEED,
    "population_seed_sha256": ADR0331_POPULATION_SEED_SHA256,
    "population_version": _POPULATION_VERSION,
    "preregistration_commit": ADR0331_PREREGISTRATION_COMMIT,
    "recovery_baseline_commit": ADR0331_RECOVERY_BASELINE_COMMIT,
    "structural_filter_version": ADR0323_STRUCTURAL_FILTER_VERSION,
    "synthetic_candidate_counts_by_width": (
        ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH
    ),
    "synthetic_gate_fields": ADR0331_SYNTHETIC_GATE_FIELDS,
    "synthetic_header_version": _SYNTHETIC_HEADER_VERSION,
    "synthetic_initial_call_count": ADR0331_SYNTHETIC_INITIAL_CALL_COUNT,
    "synthetic_observation_count": ADR0331_SYNTHETIC_OBSERVATION_COUNT,
    "synthetic_observation_version": _SYNTHETIC_OBSERVATION_VERSION,
    "synthetic_record_count": ADR0331_SYNTHETIC_RECORD_COUNT,
    "synthetic_summary_version": _SYNTHETIC_SUMMARY_VERSION,
    "synthetic_terminal_version": _SYNTHETIC_TERMINAL_VERSION,
    "version": "adr0331-value-free-nonreplay-protocol-v1",
}
ADR0331_NONREPLAY_PROTOCOL = MappingProxyType(
    _ADR0331_NONREPLAY_PROTOCOL_PAYLOAD
)
ADR0331_NONREPLAY_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_ADR0331_NONREPLAY_PROTOCOL_PAYLOAD)
).hexdigest()


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_count(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < minimum:
        raise ValueError(f"{label} is below its minimum")
    return value


def _sealed_payload(
    core: dict[str, object],
    *,
    digest_field: str,
) -> dict[str, object]:
    if digest_field in core:
        raise ValueError("self-free payload core already contains its digest field")
    digest = sha256(canonical_journal_json_bytes(core)).hexdigest()
    return {**core, digest_field: digest}


def _verify_sealed_payload(
    payload: dict[str, object],
    *,
    digest_field: str,
    label: str,
) -> dict[str, object]:
    if digest_field not in payload:
        raise ValueError(f"{label} lacks its self-free digest")
    claimed = _require_digest(payload[digest_field], label=f"{label} digest")
    core = {key: value for key, value in payload.items() if key != digest_field}
    actual = sha256(canonical_journal_json_bytes(core)).hexdigest()
    if claimed != actual:
        raise ValueError(f"{label} digest differs from its self-free core")
    return core


@dataclass(frozen=True, slots=True)
class FreshActionWidthNonReplayPool:
    seed: str
    generator_version: str
    structural_filter_version: str
    candidate_attempts: int
    excluded_pool_sha256: str
    excluded_context_semantic_digests: tuple[str, ...]
    contexts: tuple[FreshActionWidthContext, ...]

    def __post_init__(self) -> None:
        if self.seed != ADR0331_POPULATION_SEED:
            raise ValueError("non-replay pool seed differs from ADR-0331")
        if sha256(self.seed.encode("ascii")).hexdigest() != ADR0331_POPULATION_SEED_SHA256:
            raise AssertionError("non-replay pool seed digest drifted")
        if self.generator_version != ADR0323_GENERATOR_VERSION:
            raise ValueError("non-replay generator differs from ADR-0323")
        if self.structural_filter_version != ADR0323_STRUCTURAL_FILTER_VERSION:
            raise ValueError("non-replay structural filter differs from ADR-0323")
        _require_count(
            self.candidate_attempts,
            label="non-replay candidate attempts",
            minimum=ADR0331_POPULATION_CONTEXT_COUNT,
        )
        if self.excluded_pool_sha256 != ADR0323_DEVELOPMENT_POOL_SHA256:
            raise ValueError("non-replay excluded-pool identity drifted")
        if (
            not isinstance(self.excluded_context_semantic_digests, tuple)
            or len(self.excluded_context_semantic_digests)
            != ADR0323_DEVELOPMENT_CONTEXT_COUNT
        ):
            raise TypeError("non-replay pool must bind all 96 excluded contexts")
        for digest in self.excluded_context_semantic_digests:
            _require_digest(digest, label="excluded context semantic identity")
        if len(set(self.excluded_context_semantic_digests)) != len(
            self.excluded_context_semantic_digests
        ):
            raise ValueError("non-replay excluded-context list repeats an identity")
        reproduced_excluded_pool = build_adr0323_development_pool()
        reproduced_excluded_digests = tuple(
            context.semantic_digest for context in reproduced_excluded_pool.contexts
        )
        if (
            reproduced_excluded_pool.digest != self.excluded_pool_sha256
            or self.excluded_context_semantic_digests
            != reproduced_excluded_digests
        ):
            raise ValueError("non-replay pool does not bind the exact excluded population")
        if (
            not isinstance(self.contexts, tuple)
            or len(self.contexts) != ADR0331_POPULATION_CONTEXT_COUNT
            or any(
                not isinstance(context, FreshActionWidthContext)
                for context in self.contexts
            )
        ):
            raise TypeError("non-replay pool must contain 96 semantic contexts")
        expected_ids = tuple(
            f"adr0331-nonreplay-{index:03d}"
            for index in range(ADR0331_POPULATION_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("non-replay context ids or ordering drifted")
        semantic_digests = tuple(context.semantic_digest for context in self.contexts)
        if len(set(semantic_digests)) != len(semantic_digests):
            raise ValueError("non-replay pool repeats a semantic context")
        if not set(semantic_digests).isdisjoint(
            self.excluded_context_semantic_digests
        ):
            raise ValueError("non-replay pool overlaps the ADR-0323 population")

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_journal_json_bytes(
            {
                "candidate_attempts": self.candidate_attempts,
                "context_ids": tuple(context.context_id for context in self.contexts),
                "context_semantic_digests": tuple(
                    context.semantic_digest for context in self.contexts
                ),
                "excluded_context_semantic_digests": (
                    self.excluded_context_semantic_digests
                ),
                "excluded_pool_sha256": self.excluded_pool_sha256,
                "generator_version": self.generator_version,
                "protocol_sha256": ADR0331_NONREPLAY_PROTOCOL_SHA256,
                "seed": self.seed,
                "structural_filter_version": self.structural_filter_version,
                "version": _POPULATION_VERSION,
            }
        )

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()

    @property
    def subset_work_ledger(self) -> ActionWidthSubsetWorkLedger:
        counts = tuple(
            (
                width,
                sum(
                    comb(
                        len(context.complete_raise_to_totals) - 2,
                        width.count - 2,
                    )
                    for context in self.contexts
                ),
            )
            for width in ADR0323_RAISE_WIDTHS
        )
        return ActionWidthSubsetWorkLedger(
            context_count=len(self.contexts),
            subset_counts_by_raise_width=counts,
            total_subset_count=sum(count for _, count in counts),
        )


def build_adr0331_nonreplay_pool() -> FreshActionWidthNonReplayPool:
    """Build the new value-free population and prove all-population exclusion."""

    excluded_pool = build_adr0323_development_pool()
    if excluded_pool.digest != ADR0323_DEVELOPMENT_POOL_SHA256:
        raise RuntimeError("sealed ADR-0323 excluded population did not reproduce")
    excluded_digests = tuple(
        context.semantic_digest for context in excluded_pool.contexts
    )
    excluded_set = frozenset(excluded_digests)

    stream = _DigestStream(ADR0331_POPULATION_SEED)
    contexts: list[FreshActionWidthContext] = []
    attempts = 0
    while len(contexts) < ADR0331_POPULATION_CONTEXT_COUNT:
        attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs(deck[5:13])
        responder_hands = _private_pairs(deck[13:21])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible(signs):
            continue
        pot = ADR0323_POTS[stream.randbelow(len(ADR0323_POTS))]
        effective_stack = ADR0323_STACKS[stream.randbelow(len(ADR0323_STACKS))]
        weights = tuple(
            1 + stream.randbelow(9)
            for _ in range(_PRIVATE_RANGE_WIDTH * _PRIVATE_RANGE_WIDTH)
        )
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                Fraction(
                    weights[row * _PRIVATE_RANGE_WIDTH + column],
                    denominator,
                )
                for column in range(_PRIVATE_RANGE_WIDTH)
            )
            for row in range(_PRIVATE_RANGE_WIDTH)
        )
        state = _river_opening_state(pot=pot, effective_stack=effective_stack)
        context = FreshActionWidthContext(
            context_id=f"adr0331-nonreplay-{len(contexts):03d}",
            betting=state,
            board=board,
            opener_hands=opener_hands,
            responder_hands=responder_hands,
            joint_probabilities=probabilities,
            showdown_signs=signs,
            complete_raise_to_totals=_kernel_raise_universe(state),
        )
        if context.semantic_digest in excluded_set:
            continue
        contexts.append(context)

    return FreshActionWidthNonReplayPool(
        seed=ADR0331_POPULATION_SEED,
        generator_version=ADR0323_GENERATOR_VERSION,
        structural_filter_version=ADR0323_STRUCTURAL_FILTER_VERSION,
        candidate_attempts=attempts,
        excluded_pool_sha256=ADR0323_DEVELOPMENT_POOL_SHA256,
        excluded_context_semantic_digests=excluded_digests,
        contexts=tuple(contexts),
    )


def _synthetic_campaign_sha256(pool: FreshActionWidthNonReplayPool) -> str:
    if not isinstance(pool, FreshActionWidthNonReplayPool):
        raise TypeError("synthetic campaign requires the sealed population type")
    return sha256(
        canonical_journal_json_bytes(
            {
                "journal_protocol_sha256": (
                    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
                ),
                "nonreplay_protocol_sha256": ADR0331_NONREPLAY_PROTOCOL_SHA256,
                "population_sha256": pool.digest,
                "purpose": "fully-populated-systems-only-success-fixture",
                "version": "adr0331-synthetic-journal-campaign-v1",
            }
        )
    ).hexdigest()


def _synthetic_header_payload(
    pool: FreshActionWidthNonReplayPool,
) -> dict[str, object]:
    core = {
        "candidate_counts_by_width": ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH,
        "excluded_pool_sha256": pool.excluded_pool_sha256,
        "initial_call_count": ADR0331_SYNTHETIC_INITIAL_CALL_COUNT,
        "nonreplay_protocol_sha256": ADR0331_NONREPLAY_PROTOCOL_SHA256,
        "observation_count": ADR0331_SYNTHETIC_OBSERVATION_COUNT,
        "population_seed_sha256": ADR0331_POPULATION_SEED_SHA256,
        "population_sha256": pool.digest,
        "record_count": ADR0331_SYNTHETIC_RECORD_COUNT,
        "synthetic": True,
        "version": _SYNTHETIC_HEADER_VERSION,
    }
    return _sealed_payload(core, digest_field="header_sha256")


def _synthetic_phase(ordinal: int) -> tuple[str, int, int, int]:
    _require_count(ordinal, label="synthetic observation ordinal")
    if ordinal >= ADR0331_SYNTHETIC_OBSERVATION_COUNT:
        raise ValueError("synthetic observation ordinal is out of range")
    if ordinal < ADR0331_SYNTHETIC_INITIAL_CALL_COUNT:
        return "initial-width-two", 2, ordinal, ordinal
    cursor = ordinal - ADR0331_SYNTHETIC_INITIAL_CALL_COUNT
    for width, count in ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH:
        if cursor < count:
            return "candidate-block", width, cursor, cursor % 16
        cursor -= count
    raise AssertionError("synthetic observation phase partition drifted")


def _synthetic_observation_payload(
    *,
    pool: FreshActionWidthNonReplayPool,
    ordinal: int,
) -> tuple[str, dict[str, object]]:
    phase, width, phase_ordinal, context_index = _synthetic_phase(ordinal)
    context = pool.contexts[context_index]
    task_core = {
        "context_semantic_sha256": context.semantic_digest,
        "observation_ordinal": ordinal,
        "phase": phase,
        "phase_ordinal": phase_ordinal,
        "population_sha256": pool.digest,
        "target_raise_width": width,
        "version": "adr0331-synthetic-task-identity-v1",
    }
    task_sha256 = sha256(canonical_journal_json_bytes(task_core)).hexdigest()
    menu_seed = f"adr0331|synthetic|menu|{ordinal}|width={width}".encode("ascii")
    closure_seed = f"adr0331|synthetic|closure|{ordinal}".encode("ascii")
    core = {
        "candidate_raise_to_total_chips": (
            None if phase == "initial-width-two" else 2 + (phase_ordinal % 11)
        ),
        "certified_value_interval": {
            "lower_chips_hex": f"0x1.{ordinal:013x}p-8",
            "upper_chips_hex": f"0x1.{ordinal + 1:013x}p-8",
        },
        "context_index": context_index,
        "context_semantic_sha256": context.semantic_digest,
        "incumbent_menu_sha256": sha256(menu_seed + b"|incumbent").hexdigest(),
        "observation_ordinal": ordinal,
        "phase": phase,
        "phase_ordinal": phase_ordinal,
        "proposal_menu_sha256": sha256(menu_seed + b"|proposal").hexdigest(),
        "public_call_ordinal": ordinal,
        "response_closure_sha256": sha256(closure_seed).hexdigest(),
        "synthetic": True,
        "target_raise_width": width,
        "task_sha256": task_sha256,
        "version": _SYNTHETIC_OBSERVATION_VERSION,
    }
    return task_sha256, _sealed_payload(
        core,
        digest_field="observation_sha256",
    )


def _synthetic_width_summary(*, width: int, observation_count: int) -> dict[str, object]:
    if width not in (3, 4, 5, 6):
        raise ValueError("synthetic width summary has an unknown width")
    _require_count(
        observation_count,
        label="synthetic width observation count",
        minimum=1,
    )
    metrics = {
        "maximum_normalized_full_regret_upper": f"0x1.{width:013x}p-9",
        "maximum_normalized_teacher_excess_upper": f"0x1.{width + 1:013x}p-11",
        "mean_normalized_full_regret_upper": f"0x1.{width + 2:013x}p-12",
        "mean_normalized_teacher_excess_upper": f"0x1.{width + 3:013x}p-14",
        "minimum_aggregate_recovery_lower": f"0x1.{width + 4:013x}p-1",
    }
    gate_results = {
        field: ((width + index) % 3 != 0)
        for index, field in enumerate(ADR0331_SYNTHETIC_GATE_FIELDS)
    }
    core = {
        "context_count": 16,
        "eligible": all(gate_results.values()),
        "gate_results": gate_results,
        "metrics": metrics,
        "observation_count": observation_count,
        "selected_menus_sha256": sha256(
            f"adr0331|synthetic|selected-menus|width={width}".encode("ascii")
        ).hexdigest(),
        "synthetic": True,
        "version": _SYNTHETIC_SUMMARY_VERSION,
        "width": width,
    }
    return _sealed_payload(core, digest_field="summary_sha256")


def _synthetic_terminal_payload(
    *,
    pool: FreshActionWidthNonReplayPool,
    final_observation_line_sha256: str,
) -> dict[str, object]:
    _require_digest(
        final_observation_line_sha256,
        label="synthetic final-observation line",
    )
    summaries = tuple(
        _synthetic_width_summary(width=width, observation_count=count)
        for width, count in ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH
    )
    gate_definitions = {
        "maximum_normalized_full_regret_upper": {
            "direction": "less-than-or-equal",
            "synthetic_threshold_hex": "0x1.0000000000000p-7",
        },
        "mean_normalized_full_regret_upper": {
            "direction": "less-than-or-equal",
            "synthetic_threshold_hex": "0x1.0000000000000p-9",
        },
        "minimum_aggregate_recovery_lower": {
            "direction": "greater-than-or-equal",
            "synthetic_threshold_hex": "0x1.0000000000000p-1",
        },
        "maximum_normalized_teacher_excess_upper": {
            "direction": "less-than-or-equal",
            "synthetic_threshold_hex": "0x1.0000000000000p-10",
        },
        "mean_normalized_teacher_excess_upper": {
            "direction": "less-than-or-equal",
            "synthetic_threshold_hex": "0x1.0000000000000p-12",
        },
    }
    if tuple(gate_definitions) != ADR0331_SYNTHETIC_GATE_FIELDS:
        raise AssertionError("synthetic terminal gate-field ordering drifted")
    core = {
        "final_observation_line_sha256": final_observation_line_sha256,
        "gate_definitions": gate_definitions,
        "journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        "nonreplay_protocol_sha256": ADR0331_NONREPLAY_PROTOCOL_SHA256,
        "observation_count": ADR0331_SYNTHETIC_OBSERVATION_COUNT,
        "population_sha256": pool.digest,
        "record_count": ADR0331_SYNTHETIC_RECORD_COUNT,
        "synthetic": True,
        "synthetic_selected_width": 3,
        "version": _SYNTHETIC_TERMINAL_VERSION,
        "width_summaries": summaries,
    }
    return _sealed_payload(core, digest_field="terminal_sha256")


def _envelope_from_spec(
    *,
    campaign_sha256: str,
    kind: JournalRecordKind,
    sequence: int,
    previous_line_sha256: str | None,
    semantic_identity_sha256: str,
    payload: dict[str, object],
) -> JournalRecordEnvelope:
    return JournalRecordEnvelope(
        body=build_journal_record_body(
            protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
            campaign_sha256=campaign_sha256,
            kind=kind,
            sequence=sequence,
            previous_record_sha256=previous_line_sha256,
            semantic_identity_sha256=semantic_identity_sha256,
            payload=payload,
        )
    )


def build_adr0331_synthetic_journal_records(
    pool: FreshActionWidthNonReplayPool,
) -> tuple[JournalRecordEnvelope, ...]:
    """Build the full deterministic record fixture without touching the filesystem."""

    if not isinstance(pool, FreshActionWidthNonReplayPool):
        raise TypeError("synthetic journal fixture requires the non-replay pool")
    campaign_sha256 = _synthetic_campaign_sha256(pool)
    records: list[JournalRecordEnvelope] = []

    header_payload = _synthetic_header_payload(pool)
    header = _envelope_from_spec(
        campaign_sha256=campaign_sha256,
        kind=JournalRecordKind.HEADER,
        sequence=0,
        previous_line_sha256=None,
        semantic_identity_sha256=header_payload["header_sha256"],
        payload=header_payload,
    )
    records.append(header)

    for ordinal in range(ADR0331_SYNTHETIC_OBSERVATION_COUNT):
        task_sha256, payload = _synthetic_observation_payload(
            pool=pool,
            ordinal=ordinal,
        )
        records.append(
            _envelope_from_spec(
                campaign_sha256=campaign_sha256,
                kind=JournalRecordKind.OBSERVATION,
                sequence=len(records),
                previous_line_sha256=records[-1].line_sha256,
                semantic_identity_sha256=task_sha256,
                payload=payload,
            )
        )

    terminal_payload = _synthetic_terminal_payload(
        pool=pool,
        final_observation_line_sha256=records[-1].line_sha256,
    )
    records.append(
        _envelope_from_spec(
            campaign_sha256=campaign_sha256,
            kind=JournalRecordKind.TERMINAL,
            sequence=len(records),
            previous_line_sha256=records[-1].line_sha256,
            semantic_identity_sha256=terminal_payload["terminal_sha256"],
            payload=terminal_payload,
        )
    )
    if len(records) != ADR0331_SYNTHETIC_RECORD_COUNT:
        raise AssertionError("synthetic journal record count drifted")
    return tuple(records)


@dataclass(frozen=True, slots=True)
class SyntheticJournalWriteResult:
    campaign_sha256: str
    receipts: tuple[JournalAppendReceipt, ...]
    journal_sha256: str
    journal_byte_count: int

    def __post_init__(self) -> None:
        _require_digest(self.campaign_sha256, label="synthetic campaign")
        if (
            not isinstance(self.receipts, tuple)
            or len(self.receipts) != ADR0331_SYNTHETIC_RECORD_COUNT
            or any(
                not isinstance(receipt, JournalAppendReceipt)
                for receipt in self.receipts
            )
        ):
            raise TypeError("synthetic write result requires all 402 receipts")
        if tuple(receipt.sequence for receipt in self.receipts) != tuple(
            range(ADR0331_SYNTHETIC_RECORD_COUNT)
        ):
            raise ValueError("synthetic write receipts are not contiguous")
        _require_digest(self.journal_sha256, label="synthetic journal")
        _require_count(
            self.journal_byte_count,
            label="synthetic journal byte count",
            minimum=1,
        )


def write_adr0331_synthetic_journal(
    path: Path,
    *,
    pool: FreshActionWidthNonReplayPool,
) -> SyntheticJournalWriteResult:
    """Exercise exclusive append/flush/fsync for the complete success shape."""

    if not isinstance(path, Path):
        raise TypeError("synthetic journal output path must be a Path")
    if not isinstance(pool, FreshActionWidthNonReplayPool):
        raise TypeError("synthetic journal write requires the non-replay pool")
    campaign_sha256 = _synthetic_campaign_sha256(pool)
    receipts: list[JournalAppendReceipt] = []
    with DurableEvidenceJournalWriter.create(
        path=path,
        protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        campaign_sha256=campaign_sha256,
    ) as writer:
        header_payload = _synthetic_header_payload(pool)
        receipts.append(
            writer.append(
                kind=JournalRecordKind.HEADER,
                semantic_identity_sha256=header_payload["header_sha256"],
                payload=header_payload,
            )
        )
        for ordinal in range(ADR0331_SYNTHETIC_OBSERVATION_COUNT):
            task_sha256, payload = _synthetic_observation_payload(
                pool=pool,
                ordinal=ordinal,
            )
            receipts.append(
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=task_sha256,
                    payload=payload,
                )
            )
        terminal_payload = _synthetic_terminal_payload(
            pool=pool,
            final_observation_line_sha256=receipts[-1].line_sha256,
        )
        receipts.append(
            writer.append(
                kind=JournalRecordKind.TERMINAL,
                semantic_identity_sha256=terminal_payload["terminal_sha256"],
                payload=terminal_payload,
            )
        )
    raw = path.read_bytes()
    return SyntheticJournalWriteResult(
        campaign_sha256=campaign_sha256,
        receipts=tuple(receipts),
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
    )


@dataclass(frozen=True, slots=True)
class SyntheticJournalRebinding:
    campaign_sha256: str
    record_count: int
    observation_count: int
    width_summary_canonical_json: tuple[bytes, ...]
    terminal_sha256: str
    journal_sha256: str

    def __post_init__(self) -> None:
        _require_digest(self.campaign_sha256, label="rebound synthetic campaign")
        if self.record_count != ADR0331_SYNTHETIC_RECORD_COUNT:
            raise ValueError("rebound synthetic record count drifted")
        if self.observation_count != ADR0331_SYNTHETIC_OBSERVATION_COUNT:
            raise ValueError("rebound synthetic observation count drifted")
        if (
            not isinstance(self.width_summary_canonical_json, tuple)
            or len(self.width_summary_canonical_json) != 4
            or any(
                not isinstance(value, bytes)
                for value in self.width_summary_canonical_json
            )
        ):
            raise TypeError("rebound synthetic result requires four immutable summaries")
        _require_digest(self.terminal_sha256, label="rebound synthetic terminal")
        _require_digest(self.journal_sha256, label="rebound synthetic journal")


def rebind_adr0331_synthetic_journal(
    raw: bytes,
    *,
    pool: FreshActionWidthNonReplayPool,
) -> SyntheticJournalRebinding:
    """Reconstruct and validate the complete synthetic success journal from bytes."""

    if not isinstance(raw, bytes):
        raise TypeError("synthetic journal rebinding requires immutable bytes")
    if not isinstance(pool, FreshActionWidthNonReplayPool):
        raise TypeError("synthetic journal rebinding requires the non-replay pool")
    campaign_sha256 = _synthetic_campaign_sha256(pool)
    recovered = recover_journal_bytes(
        raw,
        expected_protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        expected_campaign_sha256=campaign_sha256,
    )
    if not recovered.is_complete:
        reason = recovered.failure.reason if recovered.failure is not None else "incomplete"
        raise ValueError(f"synthetic journal is not a complete valid chain: {reason}")
    records = recovered.records
    if len(records) != ADR0331_SYNTHETIC_RECORD_COUNT:
        raise ValueError("synthetic journal does not contain exactly 402 records")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("synthetic journal lacks its header")
    observations = records[1:-1]
    if len(observations) != ADR0331_SYNTHETIC_OBSERVATION_COUNT or any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in observations
    ):
        raise ValueError("synthetic journal lacks exactly 400 observations")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("synthetic journal lacks its terminal record")

    header = records[0].body.payload
    _verify_sealed_payload(
        header,
        digest_field="header_sha256",
        label="synthetic header",
    )
    for ordinal, record in enumerate(observations):
        payload = record.body.payload
        _verify_sealed_payload(
            payload,
            digest_field="observation_sha256",
            label=f"synthetic observation {ordinal}",
        )
        if payload["task_sha256"] != record.body.semantic_identity_sha256:
            raise ValueError("synthetic observation identity differs from its task")

    terminal = records[-1].body.payload
    _verify_sealed_payload(
        terminal,
        digest_field="terminal_sha256",
        label="synthetic terminal",
    )
    if terminal["terminal_sha256"] != records[-1].body.semantic_identity_sha256:
        raise ValueError("synthetic terminal identity differs from its payload")
    if terminal["final_observation_line_sha256"] != observations[-1].line_sha256:
        raise ValueError("synthetic terminal does not bind its final observation")
    summaries = terminal["width_summaries"]
    if not isinstance(summaries, list) or len(summaries) != 4:
        raise ValueError("synthetic terminal does not contain four width summaries")
    summary_bytes: list[bytes] = []
    observed_widths: list[int] = []
    for index, value in enumerate(summaries):
        if not isinstance(value, dict):
            raise TypeError("synthetic width summary must be an object")
        _verify_sealed_payload(
            value,
            digest_field="summary_sha256",
            label=f"synthetic width summary {index}",
        )
        metrics = value.get("metrics")
        gates = value.get("gate_results")
        if not isinstance(metrics, dict) or tuple(metrics) != tuple(
            sorted(ADR0331_SYNTHETIC_GATE_FIELDS)
        ):
            raise ValueError("synthetic width metrics do not expose all five gates")
        if not isinstance(gates, dict) or tuple(gates) != tuple(
            sorted(ADR0331_SYNTHETIC_GATE_FIELDS)
        ):
            raise ValueError("synthetic width gate results do not expose all five gates")
        width = value.get("width")
        if isinstance(width, bool) or not isinstance(width, int):
            raise TypeError("synthetic width summary width must be an integer")
        observed_widths.append(width)
        summary_bytes.append(canonical_journal_json_bytes(value))
    if tuple(observed_widths) != (3, 4, 5, 6):
        raise ValueError("synthetic width summaries are not ordered widths three to six")
    gate_definitions = terminal["gate_definitions"]
    if not isinstance(gate_definitions, dict) or tuple(gate_definitions) != tuple(
        sorted(ADR0331_SYNTHETIC_GATE_FIELDS)
    ):
        raise ValueError("synthetic terminal does not define five distinct gates")

    expected_records = build_adr0331_synthetic_journal_records(pool)
    expected_raw = b"".join(record.line_bytes for record in expected_records)
    if raw != expected_raw:
        raise ValueError("synthetic journal differs from the frozen populated fixture")

    return SyntheticJournalRebinding(
        campaign_sha256=campaign_sha256,
        record_count=len(records),
        observation_count=len(observations),
        width_summary_canonical_json=tuple(summary_bytes),
        terminal_sha256=terminal["terminal_sha256"],
        journal_sha256=sha256(raw).hexdigest(),
    )


__all__ = [
    "ADR0331_NONREPLAY_PROTOCOL",
    "ADR0331_NONREPLAY_PROTOCOL_SHA256",
    "ADR0331_POPULATION_CONTEXT_COUNT",
    "ADR0331_POPULATION_SEED",
    "ADR0331_POPULATION_SEED_SHA256",
    "ADR0331_PREREGISTRATION_COMMIT",
    "ADR0331_RECOVERY_BASELINE_COMMIT",
    "ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH",
    "ADR0331_SYNTHETIC_GATE_FIELDS",
    "ADR0331_SYNTHETIC_INITIAL_CALL_COUNT",
    "ADR0331_SYNTHETIC_OBSERVATION_COUNT",
    "ADR0331_SYNTHETIC_RECORD_COUNT",
    "FreshActionWidthNonReplayPool",
    "SyntheticJournalRebinding",
    "SyntheticJournalWriteResult",
    "build_adr0331_nonreplay_pool",
    "build_adr0331_synthetic_journal_records",
    "rebind_adr0331_synthetic_journal",
    "write_adr0331_synthetic_journal",
]
