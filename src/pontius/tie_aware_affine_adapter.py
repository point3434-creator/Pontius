"""Choose between a v2 single-tape certificate and an exact active-row envelope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .exact_tie_aware_affine_envelope import (
    ExactTieAwareAffineSection,
    ResponseTape,
)
from .selector_window import ConservativeSelectorWindow, FixedResponseSelectorScores
from .selector_window_v2 import fail_closed_affine_selector_window


@dataclass(frozen=True, slots=True)
class TieAwareAffineAdapterResult:
    """Typed integration mode with total-tape certificate authority."""

    mode: str
    source_active_tapes: tuple[ResponseTape, ...]
    envelope_row_tapes: tuple[ResponseTape, ...]
    v2_windows: tuple[tuple[ResponseTape, ConservativeSelectorWindow], ...]
    single_tape_scale_limit: float
    certificate_identity_authority: str


def choose_tie_aware_affine_mode(
    section: ExactTieAwareAffineSection,
    score_endpoints: Mapping[
        ResponseTape,
        tuple[FixedResponseSelectorScores, FixedResponseSelectorScores],
    ],
    *,
    selector_margin_allowance: float,
) -> TieAwareAffineAdapterResult:
    """Use v2 only for an exact singleton; otherwise retain the full envelope."""

    source_active = section.source_active_tapes
    if set(score_endpoints) != set(source_active):
        raise ValueError("tie-aware adapter score endpoints omit an active source tape")
    windows = tuple(
        (
            tape,
            fail_closed_affine_selector_window(
                *score_endpoints[tape],
                selector_margin_allowance=selector_margin_allowance,
            ),
        )
        for tape in source_active
    )
    envelope_tapes = tuple(row.response_tape for row in section.rows)
    if len(source_active) == 1:
        window = windows[0][1]
        mode = "v2_single_tape" if window.scale_limit > 0.0 else "fail_closed"
        limit = window.scale_limit
    else:
        if any(window.scale_limit != 0.0 for _, window in windows):
            raise ArithmeticError(
                "exact source tie did not fail closed in selector-window v2"
            )
        mode = "tie_aware_maximum_envelope"
        limit = 0.0
    return TieAwareAffineAdapterResult(
        mode=mode,
        source_active_tapes=source_active,
        envelope_row_tapes=envelope_tapes,
        v2_windows=windows,
        single_tape_scale_limit=limit,
        certificate_identity_authority="total_function_only",
    )


__all__ = ["TieAwareAffineAdapterResult", "choose_tie_aware_affine_mode"]
