"""Synthetic exact controls for selector-fan ties and crossings."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .exact_selector_fan import map_exact_selector_fan_section
from .game import TERMINAL_PLAYER


LEFT = "left"
RIGHT = "right"
FIRST = "first"
SECOND = "second"


@dataclass(frozen=True, slots=True)
class _ControlState:
    history: tuple[str, ...] = ()
    tied: bool = False

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER if len(self.history) == 2 else len(self.history)

    def legal_actions(self) -> tuple[str, ...]:
        return (LEFT, RIGHT) if not self.history else (FIRST, SECOND)

    def chance_outcomes(self) -> tuple[()]:
        return ()

    def apply_action(self, action: str) -> _ControlState:
        if action not in self.legal_actions():
            raise ValueError("invalid selector-fan control action")
        return _ControlState((*self.history, action), self.tied)

    def information_state_key(self, player: int) -> str:
        if player != self.current_player:
            raise ValueError("selector-fan control information player mismatch")
        return "selector-control-p0" if player == 0 else "selector-control-p1"

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("selector-fan control return requested before terminal")
        target = (
            0.0
            if self.tied
            else float(
                self.history in ((LEFT, FIRST), (RIGHT, SECOND))
            )
        )
        return -target, target


@dataclass(frozen=True, slots=True)
class _ControlGame:
    tied: bool
    num_players: int = 2

    def initial_state(self) -> _ControlState:
        return _ControlState(tied=self.tied)


def run_selector_fan_controls() -> dict[str, object]:
    source = {
        "selector-control-p0": {
            LEFT: Fraction(3, 4),
            RIGHT: Fraction(1, 4),
        },
        "selector-control-p1": {
            FIRST: Fraction(1, 2),
            SECOND: Fraction(1, 2),
        },
    }
    endpoint = {
        **source,
        "selector-control-p0": {
            LEFT: Fraction(1, 4),
            RIGHT: Fraction(3, 4),
        },
    }
    crossing = map_exact_selector_fan_section(
        _ControlGame(False),
        source,
        endpoint,
        acting_player=0,
        target_player=1,
    )
    tied = map_exact_selector_fan_section(
        _ControlGame(True),
        source,
        endpoint,
        acting_player=0,
        target_player=1,
    )
    return {
        "crossing_breakpoint": crossing.source_cell_upper,
        "crossing_legacy_breakpoint": crossing.legacy_source_breakpoint,
        "crossing_tie_points": crossing.total_tie_points,
        "crossing_fixed_measure": crossing.total_fixed_measure,
        "crossing_tie_measure": crossing.total_tie_unresolved_measure,
        "crossing_switched_measure": crossing.total_switched_measure,
        "degenerate_total_tie_measure": tied.total_tie_unresolved_measure,
        "degenerate_reachable_tie_measure": tied.reachable_tie_unresolved_measure,
        "degenerate_total_fixed_measure": tied.total_fixed_measure,
        "degenerate_total_switched_measure": tied.total_switched_measure,
    }


__all__ = ["run_selector_fan_controls"]
