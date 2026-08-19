"""Exact two-player Kuhn poker.

Cards are integers ordered J=0, Q=1, K=2. Each player antes one chip. There is
one betting opportunity of one chip. The public action names are deliberately
verbose because these states are the executable specification for later games.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER

CHECK = "check"
BET = "bet"
FOLD = "fold"
CALL = "call"

_TERMINAL_HISTORIES = {
    (CHECK, CHECK),
    (BET, FOLD),
    (BET, CALL),
    (CHECK, BET, FOLD),
    (CHECK, BET, CALL),
}


@dataclass(frozen=True, slots=True)
class KuhnState:
    """Immutable state for two-player Kuhn poker."""

    cards: tuple[int, int] | None = None
    history: tuple[str, ...] = ()

    @property
    def current_player(self) -> int:
        if self.cards is None:
            return CHANCE_PLAYER
        if self.history in _TERMINAL_HISTORIES:
            return TERMINAL_PLAYER
        if self.history == ():
            return 0
        if self.history in {(CHECK,), (BET,)}:
            return 1
        if self.history == (CHECK, BET):
            return 0
        raise ValueError(f"invalid Kuhn history: {self.history!r}")

    def legal_actions(self) -> tuple[str, ...]:
        if self.current_player < 0:
            return ()
        if self.history in {(), (CHECK,)}:
            return (CHECK, BET)
        if self.history in {(BET,), (CHECK, BET)}:
            return (FOLD, CALL)
        raise ValueError(f"no legal-action definition for history {self.history!r}")

    def chance_outcomes(self) -> tuple[tuple[tuple[int, int], float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        deals = tuple(permutations(range(3), 2))
        probability = 1.0 / len(deals)
        return tuple((deal, probability) for deal in deals)

    def apply_action(self, action: Action) -> KuhnState:
        if self.current_player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal state")
        if self.current_player == CHANCE_PLAYER:
            if (
                not isinstance(action, tuple)
                or len(action) != 2
                or any(not isinstance(card, int) for card in action)
                or len(set(action)) != 2
                or any(card not in range(3) for card in action)
            ):
                raise ValueError(f"invalid Kuhn deal: {action!r}")
            return KuhnState(cards=action, history=())

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"illegal action {action!r}; legal actions are {legal!r}")
        assert isinstance(action, str)
        return KuhnState(cards=self.cards, history=self.history + (action,))

    def information_state_key(self, player: int) -> str:
        if self.cards is None:
            raise ValueError("chance state has no player information set")
        if player != self.current_player or player < 0:
            raise ValueError(
                f"information key requested for player {player} while player "
                f"{self.current_player} acts"
            )
        history = "/".join(self.history) if self.history else "root"
        return f"p{player}|card={self.cards[player]}|history={history}"

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER or self.cards is None:
            raise ValueError("returns are available only at terminal states")

        if self.history == (BET, FOLD):
            winner, magnitude = 0, 1.0
        elif self.history == (CHECK, BET, FOLD):
            winner, magnitude = 1, 1.0
        elif self.history == (CHECK, CHECK):
            winner = 0 if self.cards[0] > self.cards[1] else 1
            magnitude = 1.0
        elif self.history in {(BET, CALL), (CHECK, BET, CALL)}:
            winner = 0 if self.cards[0] > self.cards[1] else 1
            magnitude = 2.0
        else:
            raise ValueError(f"invalid terminal history: {self.history!r}")

        return (magnitude, -magnitude) if winner == 0 else (-magnitude, magnitude)


class KuhnPoker:
    """Two-player Kuhn poker game factory."""

    num_players = 2

    def initial_state(self) -> KuhnState:
        return KuhnState()

