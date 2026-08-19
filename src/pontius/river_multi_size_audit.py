"""Independent contribution-based payoff audit for multi-size river games."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .game import CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .river import CALL, CHECK, FOLD, RiverDeal, evaluate_seven
from .river_multi_size import (
    BetAction,
    MultiSizeAction,
    MultiSizeRiverHoldem,
    MultiSizeRiverState,
    RaiseToAction,
)


@dataclass(frozen=True, slots=True)
class MultiSizePayoffAudit:
    deals: int
    terminal_histories: int
    maximum_absolute_error: float
    passed: bool


def _independent_returns(
    game: MultiSizeRiverHoldem,
    deal: RiverDeal,
    history: tuple[tuple[int, MultiSizeAction], ...],
) -> tuple[float, float]:
    """Compute terminal utility from contributions, not state payoff cases."""

    contributions = [0.0, 0.0]
    folded: int | None = None
    showdown = False
    for index, (player, action) in enumerate(history):
        if action == CHECK:
            if index != 0 or player != 0:
                raise ValueError("check appears outside the opening action")
            showdown = True
        elif isinstance(action, BetAction):
            if index != 0 or player != 0:
                raise ValueError("sized bet appears outside the opening action")
            contributions[0] = action.amount
        elif isinstance(action, RaiseToAction):
            if index != 1 or player != 1:
                raise ValueError("raise-to appears outside the response action")
            contributions[1] = action.amount
        elif action == FOLD:
            folded = player
        elif action == CALL:
            if player == 1 and index == 1:
                contributions[1] = contributions[0]
            elif player == 0 and index == 2:
                contributions[0] = contributions[1]
            else:
                raise ValueError("call appears outside a facing-wager action")
            showdown = True
        else:
            raise ValueError(f"unknown action in payoff audit: {action!r}")

    if folded is not None:
        winner = 1 - folded
        loser_contribution = contributions[folded]
        magnitude = game.pot / 2.0 + loser_contribution
        utility0 = magnitude if winner == 0 else -magnitude
    elif showdown:
        if contributions[0] != contributions[1]:
            raise ValueError("showdown contributions are not matched")
        rank0 = evaluate_seven((*game.board, *deal.player0))
        rank1 = evaluate_seven((*game.board, *deal.player1))
        if rank0 == rank1:
            utility0 = 0.0
        else:
            magnitude = game.pot / 2.0 + contributions[0]
            utility0 = magnitude if rank0 > rank1 else -magnitude
    else:
        raise ValueError("payoff audit received a nonterminal history")
    return (utility0, -utility0)


def audit_multi_size_payoffs(
    game: MultiSizeRiverHoldem,
    *,
    tolerance: float = 1e-12,
) -> MultiSizePayoffAudit:
    """Enumerate every terminal history and compare both payoff implementations."""

    if not isinstance(game, MultiSizeRiverHoldem):
        raise TypeError("payoff audit requires MultiSizeRiverHoldem")
    if not isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("payoff audit tolerance must be finite and nonnegative")

    terminals = 0
    maximum_error = 0.0

    def walk(state: GameState, deal: RiverDeal) -> None:
        nonlocal terminals, maximum_error
        if state.current_player == TERMINAL_PLAYER:
            if not isinstance(state, MultiSizeRiverState):
                raise TypeError("multi-size traversal produced an unexpected state")
            actual = state.returns()
            expected = _independent_returns(game, deal, state.history)
            maximum_error = max(
                maximum_error,
                *(abs(left - right) for left, right in zip(actual, expected, strict=True)),
            )
            terminals += 1
            return
        if state.current_player == CHANCE_PLAYER:
            raise ValueError("payoff audit expects a dealt state")
        for action in state.legal_actions():
            walk(state.apply_action(action), deal)

    root = game.initial_state()
    for deal, _ in root.chance_outcomes():
        walk(root.apply_action(deal), deal)
    return MultiSizePayoffAudit(
        deals=len(game.deals),
        terminal_histories=terminals,
        maximum_absolute_error=maximum_error,
        passed=maximum_error <= tolerance,
    )
