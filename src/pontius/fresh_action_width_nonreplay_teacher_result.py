"""Solver-free result owner for ADR-0335's retained non-replay teacher.

The one-shot value owner is closed.  This module accepts only the exact retained
JSONL bytes, invokes the independently sealed journal rebinder, and derives a
typed population curve without a consumer, solver, campaign, or action path.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from statistics import median
from types import MappingProxyType

from .certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from .durable_evidence_journal import canonical_journal_json_bytes
from .fresh_action_width_nonreplay_qualification_result import (
    ADR0334_QUALIFIED_PANEL_SHA256,
)
from .fresh_action_width_nonreplay_teacher import (
    ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH,
    ADR0335_TEACHER_PROTOCOL_SHA256,
    ADR0335_TEACHER_TASK_COUNT,
    NonReplayTeacherEvidenceKind,
    NonReplayTeacherJournalResult,
    NonReplayTeacherStopReason,
    NonReplayTeacherWidthResult,
    rebind_adr0335_teacher_journal,
)
from .fresh_action_width_nonreplay_teacher_seal import (
    ADR0335_TEACHER_SCHEDULE_SHA256,
    ADR0335_TEACHER_SOURCE_MANIFEST,
)
from .fresh_action_width_structures import ADR0323_RAISE_WIDTHS, RaiseActionWidth


ADR0336_TEACHER_ARTIFACT_BYTES = 8_027_171
ADR0336_TEACHER_ARTIFACT_SHA256 = (
    "3f20b204bca428c2b9e99266688709b6aba65de2f2bff3d38c6f523828c94444"
)
ADR0336_TEACHER_CAMPAIGN_SHA256 = (
    "a6f1c1604d77f8eabd31da7c9e754d4248fab3505073fed7cbe82db8221c71f7"
)
ADR0336_TEACHER_TERMINAL_SHA256 = (
    "392eca27cb7a240d6ae38c4dbdbd51df96ef5cbe701d02ee41957d22b08594bb"
)
ADR0336_TEACHER_RECORD_COUNT = 2_115
ADR0336_TEACHER_EVIDENCE_COUNT = 2_113
ADR0336_TEACHER_CONTEXT_COUNT = 16
ADR0336_TEACHER_PUBLIC_CALL_COUNT = 2_113
ADR0336_TEACHER_MAX_CERTIFICATE_GAP_HEX = "0x1.6f32000000000p-38"
ADR0336_MEDIAN_LOWER_REGRET_KNEE_WIDTH = 3
ADR0336_FIRST_FULL_REGRET_GATE_PASSING_WIDTH = 3
ADR0336_FIRST_ALL_CONTEXTS_ZERO_LOWER_WIDTH = 4
ADR0336_MEDIAN_KNEE_POSITIVE_TAIL_CONTEXT_POSITIONS = (9, 11)

ADR0336_TEACHER_CONTEXT_RESULT_SHA256S = (
    "9590c21e5dabc02f63631ed26ac7a7a710b8a0530c216e4de48611d0f80ddd4a",
    "8811fde8767af16a22c67e866df949562738d189b1822cd2806163e4bddbbbea",
    "58ddc60e33bf83012a0b182e9f9df7bfd35d3aa126226702291254c3c21da8bf",
    "7c154c395b62d35473823fe3444b7e4e609ebae99ded2d8c998422ca05cb0ab4",
    "c593a2fd2c891893240c5dce16d9209157d4aac6a2b5faa2646641319286ac33",
    "d5135bffbe7c4738f317f7fab4cb1fc03a1e1d554cb49c2f8cba9775c8ebc2e6",
    "bdfaab4091b90c4e13f8286a0ce5efb7461b2d9982e96a48a11aeff51c244512",
    "a4bb9d0315eeab275ad0c924ddb50e00457b39b4a7a97c0dbd6bf340e9a7ece1",
    "c50cd6867231fe41ece42c652395307c742581eccac52497eed45a79f0aa10d0",
    "f4f361df7afe619e396e8fb9a663f2f030e91a0c5e5a7984f27257632e8acba3",
    "9c8ec1f0b945463527af0301dc99a904b8201bed478be7c548ef07e4cac91a7e",
    "ea135ec1ff954f2451b593ce92c3c59c7ccc0fbc61d0dc626a4e8cd9660a5c01",
    "a58bd71fcac99416bffa4a8c49f6abacafc8712726f12d2465fdeb6876ed188f",
    "8d8c59edf1c3c700d0460cead1fa37f584c10c1c44c4788eb3763b4333b49220",
    "0e21fc48999f6ddf6b748f8a3165ea8a2c115c027a075d03990f179c4c351642",
    "e1ed1d5b9368b489e71d6a7399b01e3e188e5e8249d06d3cfa815b872fd7146c",
)

# Each row is width, median lower/upper, inherited-arithmetic mean lower/upper,
# maximum lower/upper, contexts with a certified-positive lower regret,
# contexts with a sole survivor, and the nondominated/equivalent cardinality
# histograms.  Hex strings preserve exact binary64 diagnostics and do not
# become decision tolerances.
ADR0336_TEACHER_WIDTH_SUMMARY_SPECS = (
    (
        2,
        "0x1.e46da0141d4d9p-12",
        "0x1.e46da01621302p-12",
        "0x1.0cbf85ff3d5cep-10",
        "0x1.0cbf85ffadbedp-10",
        "0x1.85dcaf0afb7bcp-9",
        "0x1.85dcaf0b5653cp-9",
        tuple(range(16)),
        tuple(range(16)),
        ((1, 16),),
        ((1, 16),),
    ),
    (
        3,
        "0x0.0p+0",
        "0x1.95cb01288b013p-44",
        "0x1.8ed0cb68a0f90p-16",
        "0x1.8ed0cb83575a5p-16",
        "0x1.df6f959389697p-13",
        "0x1.df6f95978e3c4p-13",
        (9, 11),
        tuple(range(16)),
        ((1, 16),),
        ((1, 16),),
    ),
    (
        4,
        "0x0.0p+0",
        "0x1.86f52b52b52b6p-44",
        "0x0.0p+0",
        "0x1.a3950a0053ef1p-44",
        "0x0.0p+0",
        "0x1.5970f0f0f0f0fp-43",
        (),
        (9, 11),
        ((1, 2), (4, 3), (6, 6), (8, 5)),
        ((1, 2), (4, 3), (6, 6), (8, 5)),
    ),
    (
        5,
        "0x0.0p+0",
        "0x1.86fdb3db3db3ep-44",
        "0x0.0p+0",
        "0x1.a3950a0053ef1p-44",
        "0x0.0p+0",
        "0x1.5970f0f0f0f0fp-43",
        (),
        (),
        ((3, 1), (5, 1), (6, 3), (15, 6), (28, 5)),
        ((3, 1), (5, 1), (6, 3), (15, 6), (28, 5)),
    ),
    (
        6,
        "0x0.0p+0",
        "0x1.86f52b52b52b6p-44",
        "0x0.0p+0",
        "0x1.a39307fe51ed1p-44",
        "0x0.0p+0",
        "0x1.5970f0f0f0f0fp-43",
        (),
        (),
        ((3, 1), (4, 3), (10, 1), (20, 6), (56, 5)),
        ((3, 1), (4, 3), (10, 1), (20, 6), (56, 5)),
    ),
)

ADR0336_TEACHER_RESULT_SHA256 = (
    "e4347dbfc6663a636572199f11dcad517fe715d062dcee022566419382f193b0"
)


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_positions(value: object, *, label: str) -> tuple[int, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{label} must be an immutable tuple")
    if any(
        isinstance(position, bool)
        or not isinstance(position, int)
        or not 0 <= position < ADR0336_TEACHER_CONTEXT_COUNT
        for position in value
    ):
        raise ValueError(f"{label} contains an invalid context position")
    if tuple(sorted(set(value))) != value:
        raise ValueError(f"{label} must be increasing and unique")
    return value


def _require_cardinality_counts(
    value: object,
    *,
    label: str,
    allow_zero_cardinality: bool = False,
) -> tuple[tuple[int, int], ...]:
    if not isinstance(value, tuple) or not value:
        raise TypeError(f"{label} must be a nonempty immutable tuple")
    if not isinstance(allow_zero_cardinality, bool):
        raise TypeError("cardinality zero policy must be Boolean")
    minimum = 0 if allow_zero_cardinality else 1
    previous = minimum - 1
    total = 0
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(f"{label} contains a malformed pair")
        cardinality, count = item
        if (
            isinstance(cardinality, bool)
            or not isinstance(cardinality, int)
            or cardinality < minimum
            or cardinality <= previous
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count <= 0
        ):
            raise ValueError(f"{label} contains invalid counts")
        previous = cardinality
        total += count
    if total != ADR0336_TEACHER_CONTEXT_COUNT:
        raise ValueError(f"{label} does not cover all contexts")
    return value


@dataclass(frozen=True, slots=True)
class TeacherMaximumNormalizedFullRegretLimit:
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, float) or not isfinite(self.value) or self.value < 0.0:
            raise ValueError("teacher maximum-regret limit must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class TeacherMeanNormalizedFullRegretLimit:
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, float) or not isfinite(self.value) or self.value < 0.0:
            raise ValueError("teacher mean-regret limit must be finite and nonnegative")


ADR0336_TEACHER_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT = (
    TeacherMaximumNormalizedFullRegretLimit(0.005)
)
ADR0336_TEACHER_MEAN_NORMALIZED_FULL_REGRET_LIMIT = (
    TeacherMeanNormalizedFullRegretLimit(0.001)
)


@dataclass(frozen=True, slots=True)
class RetainedNonReplayTeacherWidthSummary:
    raise_width: RaiseActionWidth
    context_width_sha256s: tuple[str, ...]
    median_normalized_lower: float
    median_normalized_upper: float
    mean_normalized_lower: float
    mean_normalized_upper: float
    maximum_normalized_lower: float
    maximum_normalized_upper: float
    certified_positive_lower_context_positions: tuple[int, ...]
    unique_survivor_context_positions: tuple[int, ...]
    nondominated_cardinality_counts: tuple[tuple[int, int], ...]
    equivalent_cardinality_counts: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("teacher summary width must be semantic")
        if (
            not isinstance(self.context_width_sha256s, tuple)
            or len(self.context_width_sha256s) != ADR0336_TEACHER_CONTEXT_COUNT
        ):
            raise TypeError("teacher summary requires all context-width digests")
        for digest in self.context_width_sha256s:
            _require_digest(digest, label="teacher context-width result")
        if len(set(self.context_width_sha256s)) != len(self.context_width_sha256s):
            raise ValueError("teacher summary repeats a context-width result")
        diagnostics = (
            self.median_normalized_lower,
            self.median_normalized_upper,
            self.mean_normalized_lower,
            self.mean_normalized_upper,
            self.maximum_normalized_lower,
            self.maximum_normalized_upper,
        )
        if any(
            not isinstance(value, float) or not isfinite(value) or value < 0.0
            for value in diagnostics
        ):
            raise ValueError("teacher summary diagnostics must be finite and nonnegative")
        if (
            self.median_normalized_lower > self.median_normalized_upper
            or self.mean_normalized_lower > self.mean_normalized_upper
            or self.maximum_normalized_lower > self.maximum_normalized_upper
            or self.median_normalized_lower > self.maximum_normalized_lower
            or self.median_normalized_upper > self.maximum_normalized_upper
            or self.mean_normalized_lower > self.maximum_normalized_lower
            or self.mean_normalized_upper > self.maximum_normalized_upper
        ):
            raise ValueError("teacher summary interval order is invalid")
        _require_positions(
            self.certified_positive_lower_context_positions,
            label="teacher positive-lower contexts",
        )
        _require_positions(
            self.unique_survivor_context_positions,
            label="teacher unique-survivor contexts",
        )
        nondominated = _require_cardinality_counts(
            self.nondominated_cardinality_counts,
            label="teacher nondominated cardinalities",
        )
        _require_cardinality_counts(
            self.equivalent_cardinality_counts,
            label="teacher equivalent cardinalities",
            allow_zero_cardinality=True,
        )
        unique_count = dict(nondominated).get(1, 0)
        if unique_count != len(self.unique_survivor_context_positions):
            raise ValueError("teacher sole-survivor count disagrees with cardinalities")

    @property
    def digest(self) -> str:
        return sha256(
            canonical_journal_json_bytes(
                {
                    "certified_positive_lower_context_positions": (
                        self.certified_positive_lower_context_positions
                    ),
                    "context_width_sha256s": self.context_width_sha256s,
                    "equivalent_cardinality_counts": (
                        self.equivalent_cardinality_counts
                    ),
                    "maximum_normalized_lower_hex": (
                        self.maximum_normalized_lower.hex()
                    ),
                    "maximum_normalized_upper_hex": (
                        self.maximum_normalized_upper.hex()
                    ),
                    "mean_normalized_lower_hex": self.mean_normalized_lower.hex(),
                    "mean_normalized_upper_hex": self.mean_normalized_upper.hex(),
                    "median_normalized_lower_hex": self.median_normalized_lower.hex(),
                    "median_normalized_upper_hex": self.median_normalized_upper.hex(),
                    "nondominated_cardinality_counts": (
                        self.nondominated_cardinality_counts
                    ),
                    "raise_width": self.raise_width.count,
                    "unique_survivor_context_positions": (
                        self.unique_survivor_context_positions
                    ),
                    "version": "adr0336-nonreplay-teacher-width-summary-v1",
                }
            )
        ).hexdigest()

    @property
    def maximum_full_regret_pass(self) -> bool:
        return self.maximum_normalized_upper <= (
            ADR0336_TEACHER_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value
        )

    @property
    def mean_full_regret_pass(self) -> bool:
        return self.mean_normalized_upper <= (
            ADR0336_TEACHER_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value
        )

    @property
    def full_regret_gate_pass(self) -> bool:
        return self.maximum_full_regret_pass and self.mean_full_regret_pass


@dataclass(frozen=True, slots=True)
class RetainedNonReplayTeacherResult:
    journal: NonReplayTeacherJournalResult
    width_summaries: tuple[RetainedNonReplayTeacherWidthSummary, ...]
    median_lower_regret_knee: RaiseActionWidth
    first_full_regret_gate_passing_width: RaiseActionWidth
    first_all_contexts_zero_lower_width: RaiseActionWidth
    median_knee_positive_tail_context_positions: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.journal, NonReplayTeacherJournalResult):
            raise TypeError("retained teacher result requires its semantic journal")
        if (
            self.journal.campaign_sha256 != ADR0336_TEACHER_CAMPAIGN_SHA256
            or self.journal.journal_sha256 != ADR0336_TEACHER_ARTIFACT_SHA256
            or self.journal.terminal_sha256 != ADR0336_TEACHER_TERMINAL_SHA256
            or self.journal.stop_reason is not NonReplayTeacherStopReason.COMPLETED
            or self.journal.synthetic
            or not self.journal.invocation_count_complete
        ):
            raise ValueError("retained teacher result belongs to another journal")
        if not isinstance(self.width_summaries, tuple) or any(
            not isinstance(item, RetainedNonReplayTeacherWidthSummary)
            for item in self.width_summaries
        ):
            raise TypeError("retained teacher summaries must be semantic")
        if (
            tuple(item.raise_width for item in self.width_summaries)
            != ADR0323_RAISE_WIDTHS
        ):
            raise ValueError("retained teacher summaries require widths two through six")
        if any(
            summary.context_width_sha256s
            != tuple(context.widths[index].digest for context in self.journal.contexts)
            for index, summary in enumerate(self.width_summaries)
        ):
            raise ValueError("retained teacher summaries cross journal width results")
        if not isinstance(self.median_lower_regret_knee, RaiseActionWidth):
            raise TypeError("teacher median knee must be a semantic raise width")
        if not isinstance(self.first_full_regret_gate_passing_width, RaiseActionWidth):
            raise TypeError("teacher gate boundary must be a semantic raise width")
        if not isinstance(
            self.first_all_contexts_zero_lower_width,
            RaiseActionWidth,
        ):
            raise TypeError("teacher all-context boundary must be a semantic raise width")
        expected_median_knee = next(
            item.raise_width
            for item in self.width_summaries
            if item.median_normalized_lower == 0.0
        )
        expected_all_contexts = next(
            item.raise_width
            for item in self.width_summaries
            if not item.certified_positive_lower_context_positions
        )
        expected_gate_width = next(
            item.raise_width for item in self.width_summaries if item.full_regret_gate_pass
        )
        knee_summary = self.width_summaries[
            ADR0323_RAISE_WIDTHS.index(self.median_lower_regret_knee)
        ]
        if (
            self.median_lower_regret_knee != expected_median_knee
            or self.first_full_regret_gate_passing_width != expected_gate_width
            or self.first_all_contexts_zero_lower_width != expected_all_contexts
            or self.median_knee_positive_tail_context_positions
            != knee_summary.certified_positive_lower_context_positions
        ):
            raise ValueError("retained teacher knee diagnostics drifted")
        _require_positions(
            self.median_knee_positive_tail_context_positions,
            label="teacher median-knee positive tail",
        )

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
                    "first_all_contexts_zero_lower_width": (
                        self.first_all_contexts_zero_lower_width.count
                    ),
                    "first_full_regret_gate_passing_width": (
                        self.first_full_regret_gate_passing_width.count
                    ),
                    "median_knee_positive_tail_context_positions": (
                        self.median_knee_positive_tail_context_positions
                    ),
                    "median_lower_regret_knee": self.median_lower_regret_knee.count,
                    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
                    "schedule_sha256": ADR0335_TEACHER_SCHEDULE_SHA256,
                    "teacher_source_sha256": ADR0335_TEACHER_SOURCE_MANIFEST[
                        "fresh_action_width_nonreplay_teacher.py"
                    ],
                    "terminal_sha256": self.journal.terminal_sha256,
                    "version": "adr0336-nonreplay-teacher-retained-result-v1",
                    "width_summary_sha256s": tuple(
                        item.digest for item in self.width_summaries
                    ),
                }
            )
        ).hexdigest()


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[2] / ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH


def _summary_spec(
    summary: RetainedNonReplayTeacherWidthSummary,
) -> tuple[object, ...]:
    return (
        summary.raise_width.count,
        summary.median_normalized_lower.hex(),
        summary.median_normalized_upper.hex(),
        summary.mean_normalized_lower.hex(),
        summary.mean_normalized_upper.hex(),
        summary.maximum_normalized_lower.hex(),
        summary.maximum_normalized_upper.hex(),
        summary.certified_positive_lower_context_positions,
        summary.unique_survivor_context_positions,
        summary.nondominated_cardinality_counts,
        summary.equivalent_cardinality_counts,
    )


def _summarize_width(
    journal: NonReplayTeacherJournalResult,
    *,
    width_index: int,
) -> RetainedNonReplayTeacherWidthSummary:
    rows: tuple[NonReplayTeacherWidthResult, ...] = tuple(
        context.widths[width_index] for context in journal.contexts
    )
    lowers = tuple(
        row.normalized_full_minus_teacher_regret.lower for row in rows
    )
    uppers = tuple(
        row.normalized_full_minus_teacher_regret.upper for row in rows
    )
    return RetainedNonReplayTeacherWidthSummary(
        raise_width=ADR0323_RAISE_WIDTHS[width_index],
        context_width_sha256s=tuple(row.digest for row in rows),
        median_normalized_lower=median(lowers),
        median_normalized_upper=median(uppers),
        mean_normalized_lower=sum(lowers) / len(lowers),
        mean_normalized_upper=sum(uppers) / len(uppers),
        maximum_normalized_lower=max(lowers),
        maximum_normalized_upper=max(uppers),
        certified_positive_lower_context_positions=tuple(
            context.panel_position
            for context, row in zip(journal.contexts, rows, strict=True)
            if row.normalized_full_minus_teacher_regret.lower > 0.0
        ),
        unique_survivor_context_positions=tuple(
            context.panel_position
            for context, row in zip(journal.contexts, rows, strict=True)
            if row.envelope.unique_best_subset_index is not None
        ),
        nondominated_cardinality_counts=tuple(
            sorted(
                Counter(
                    len(row.envelope.nondominated_subset_indices) for row in rows
                ).items()
            )
        ),
        equivalent_cardinality_counts=tuple(
            sorted(
                Counter(
                    len(row.envelope.equivalent_subset_indices) for row in rows
                ).items()
            )
        ),
    )


def _rebind_retained_result(raw: bytes) -> RetainedNonReplayTeacherResult:
    rebound = rebind_adr0335_teacher_journal(raw, synthetic=False)
    if not isinstance(rebound, NonReplayTeacherJournalResult):
        raise TypeError("ADR-0336 teacher journal lacks an exact terminal result")
    if (
        rebound.campaign_sha256 != ADR0336_TEACHER_CAMPAIGN_SHA256
        or rebound.journal_sha256 != ADR0336_TEACHER_ARTIFACT_SHA256
        or rebound.journal_byte_count != ADR0336_TEACHER_ARTIFACT_BYTES
        or rebound.terminal_sha256 != ADR0336_TEACHER_TERMINAL_SHA256
        or len(rebound.evidences) != ADR0336_TEACHER_EVIDENCE_COUNT
        or len(rebound.contexts) != ADR0336_TEACHER_CONTEXT_COUNT
        or rebound.known_public_call_count != ADR0336_TEACHER_PUBLIC_CALL_COUNT
        or not rebound.invocation_count_complete
        or rebound.synthetic
        or rebound.stop_reason is not NonReplayTeacherStopReason.COMPLETED
        or rebound.completed_widths
        or rebound.incomplete_observations
        or rebound.pending_full_evidence_sha256 is not None
    ):
        raise ValueError("ADR-0336 teacher terminal identity drifted")
    if any(
        evidence.kind is not NonReplayTeacherEvidenceKind.ACCEPTED
        or evidence.synthetic
        or evidence.public_call_count != 1
        for evidence in rebound.evidences
    ):
        raise ValueError("ADR-0336 teacher arm acceptance drifted")
    if tuple(context.digest for context in rebound.contexts) != (
        ADR0336_TEACHER_CONTEXT_RESULT_SHA256S
    ):
        raise ValueError("ADR-0336 teacher context reductions drifted")
    gaps = tuple(
        float.fromhex(evidence.core["result"]["certified_gap_hex"])
        for evidence in rebound.evidences
    )
    if max(gaps).hex() != ADR0336_TEACHER_MAX_CERTIFICATE_GAP_HEX:
        raise ValueError("ADR-0336 teacher certificate diagnostic drifted")
    summaries = tuple(
        _summarize_width(rebound, width_index=index)
        for index in range(len(ADR0323_RAISE_WIDTHS))
    )
    if tuple(_summary_spec(item) for item in summaries) != (
        ADR0336_TEACHER_WIDTH_SUMMARY_SPECS
    ):
        raise ValueError("ADR-0336 teacher population curve drifted")
    result = RetainedNonReplayTeacherResult(
        journal=rebound,
        width_summaries=summaries,
        median_lower_regret_knee=RaiseActionWidth(
            ADR0336_MEDIAN_LOWER_REGRET_KNEE_WIDTH
        ),
        first_full_regret_gate_passing_width=RaiseActionWidth(
            ADR0336_FIRST_FULL_REGRET_GATE_PASSING_WIDTH
        ),
        first_all_contexts_zero_lower_width=RaiseActionWidth(
            ADR0336_FIRST_ALL_CONTEXTS_ZERO_LOWER_WIDTH
        ),
        median_knee_positive_tail_context_positions=(
            ADR0336_MEDIAN_KNEE_POSITIVE_TAIL_CONTEXT_POSITIONS
        ),
    )
    return result


_RESULT_PROTOCOL_PAYLOAD = {
    "artifact_bytes": ADR0336_TEACHER_ARTIFACT_BYTES,
    "artifact_relative_path": ADR0335_TEACHER_ARTIFACT_RELATIVE_PATH,
    "artifact_sha256": ADR0336_TEACHER_ARTIFACT_SHA256,
    "campaign_sha256": ADR0336_TEACHER_CAMPAIGN_SHA256,
    "context_count": ADR0336_TEACHER_CONTEXT_COUNT,
    "context_result_sha256s": ADR0336_TEACHER_CONTEXT_RESULT_SHA256S,
    "evidence_count": ADR0336_TEACHER_EVIDENCE_COUNT,
    "first_all_contexts_zero_lower_width": (
        ADR0336_FIRST_ALL_CONTEXTS_ZERO_LOWER_WIDTH
    ),
    "first_full_regret_gate_passing_width": (
        ADR0336_FIRST_FULL_REGRET_GATE_PASSING_WIDTH
    ),
    "maximum_certificate_gap_hex": ADR0336_TEACHER_MAX_CERTIFICATE_GAP_HEX,
    "median_knee_positive_tail_context_positions": (
        ADR0336_MEDIAN_KNEE_POSITIVE_TAIL_CONTEXT_POSITIONS
    ),
    "median_lower_regret_knee_width": ADR0336_MEDIAN_LOWER_REGRET_KNEE_WIDTH,
    "panel_sha256": ADR0334_QUALIFIED_PANEL_SHA256,
    "public_call_count": ADR0336_TEACHER_PUBLIC_CALL_COUNT,
    "rebind": (
        "exact-bytes+durable-chain+policy-lower+dual-upper+regrets+normalization+"
        "set-envelopes+population-curve-without-solving"
    ),
    "record_count": ADR0336_TEACHER_RECORD_COUNT,
    "result_sha256": ADR0336_TEACHER_RESULT_SHA256,
    "schedule_sha256": ADR0335_TEACHER_SCHEDULE_SHA256,
    "stop_reason": "completed",
    "teacher_protocol_sha256": ADR0335_TEACHER_PROTOCOL_SHA256,
    "teacher_maximum_normalized_full_regret_limit_hex": (
        ADR0336_TEACHER_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT.value.hex()
    ),
    "teacher_mean_normalized_full_regret_limit_hex": (
        ADR0336_TEACHER_MEAN_NORMALIZED_FULL_REGRET_LIMIT.value.hex()
    ),
    "teacher_source_sha256": ADR0335_TEACHER_SOURCE_MANIFEST[
        "fresh_action_width_nonreplay_teacher.py"
    ],
    "terminal_sha256": ADR0336_TEACHER_TERMINAL_SHA256,
    "width_summary_specs": ADR0336_TEACHER_WIDTH_SUMMARY_SPECS,
    "version": "adr0336-nonreplay-teacher-result-protocol-v1",
}
ADR0336_TEACHER_RESULT_PROTOCOL = MappingProxyType(_RESULT_PROTOCOL_PAYLOAD)
ADR0336_TEACHER_RESULT_PROTOCOL_SHA256 = sha256(
    canonical_journal_json_bytes(_RESULT_PROTOCOL_PAYLOAD)
).hexdigest()


def verify_adr0336_teacher_result_source_and_dependencies() -> str:
    from .fresh_action_width_nonreplay_teacher_result_seal import (
        ADR0336_TEACHER_RESULT_PROTOCOL_SHA256 as sealed_protocol,
        ADR0336_TEACHER_RESULT_SOURCE_MANIFEST,
    )

    root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(root / name)
        for name in ADR0336_TEACHER_RESULT_SOURCE_MANIFEST
    }
    if actual != ADR0336_TEACHER_RESULT_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0336 teacher-result source closure drifted")
    if sealed_protocol != ADR0336_TEACHER_RESULT_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0336 teacher-result protocol drifted")
    return actual["fresh_action_width_nonreplay_teacher_result.py"]


def verify_adr0336_nonreplay_teacher_result_artifact(
    path: Path | None = None,
) -> RetainedNonReplayTeacherResult:
    """Verify exact retained bytes and rederive all diagnostics without solving."""

    verify_adr0336_teacher_result_source_and_dependencies()
    artifact_path = _artifact_path() if path is None else path
    raw = artifact_path.read_bytes()
    if len(raw) != ADR0336_TEACHER_ARTIFACT_BYTES:
        raise ValueError("ADR-0336 teacher journal byte count drifted")
    if sha256(raw).hexdigest() != ADR0336_TEACHER_ARTIFACT_SHA256:
        raise ValueError("ADR-0336 teacher journal SHA-256 drifted")
    if (
        raw.count(b"\n") != ADR0336_TEACHER_RECORD_COUNT
        or not raw.endswith(b"\n")
        or raw.endswith(b"\n\n")
    ):
        raise ValueError("ADR-0336 teacher journal record shape drifted")
    result = _rebind_retained_result(raw)
    if result.digest != ADR0336_TEACHER_RESULT_SHA256:
        raise ValueError("ADR-0336 retained teacher result identity drifted")
    return result


__all__ = [
    "ADR0336_FIRST_ALL_CONTEXTS_ZERO_LOWER_WIDTH",
    "ADR0336_FIRST_FULL_REGRET_GATE_PASSING_WIDTH",
    "ADR0336_MEDIAN_KNEE_POSITIVE_TAIL_CONTEXT_POSITIONS",
    "ADR0336_MEDIAN_LOWER_REGRET_KNEE_WIDTH",
    "ADR0336_TEACHER_ARTIFACT_BYTES",
    "ADR0336_TEACHER_ARTIFACT_SHA256",
    "ADR0336_TEACHER_CAMPAIGN_SHA256",
    "ADR0336_TEACHER_CONTEXT_COUNT",
    "ADR0336_TEACHER_CONTEXT_RESULT_SHA256S",
    "ADR0336_TEACHER_EVIDENCE_COUNT",
    "ADR0336_TEACHER_MAX_CERTIFICATE_GAP_HEX",
    "ADR0336_TEACHER_MAXIMUM_NORMALIZED_FULL_REGRET_LIMIT",
    "ADR0336_TEACHER_MEAN_NORMALIZED_FULL_REGRET_LIMIT",
    "ADR0336_TEACHER_PUBLIC_CALL_COUNT",
    "ADR0336_TEACHER_RECORD_COUNT",
    "ADR0336_TEACHER_RESULT_PROTOCOL",
    "ADR0336_TEACHER_RESULT_PROTOCOL_SHA256",
    "ADR0336_TEACHER_RESULT_SHA256",
    "ADR0336_TEACHER_TERMINAL_SHA256",
    "ADR0336_TEACHER_WIDTH_SUMMARY_SPECS",
    "RetainedNonReplayTeacherResult",
    "RetainedNonReplayTeacherWidthSummary",
    "TeacherMaximumNormalizedFullRegretLimit",
    "TeacherMeanNormalizedFullRegretLimit",
    "verify_adr0336_nonreplay_teacher_result_artifact",
    "verify_adr0336_teacher_result_source_and_dependencies",
]
