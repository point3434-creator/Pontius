"""Configurable multiplayer Kuhn poker.

For ``N`` players the deck contains ``N + 1`` ordered cards. Every player antes
one chip. Before a bet, players act once in seat order and may check or make the
only allowed one-chip bet. After a bet, every other player calls or folds in
cyclic order; raises are not allowed. If everyone checks, all players show down.
Otherwise the highest card among the bettor and callers wins the pot.

This is a deliberately explicit benchmark game, not a claim that every paper
using the phrase "multiplayer Kuhn" uses the same betting convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from math import factorial

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER

CHECK = "check"
BET = "bet"
FOLD = "fold"
CALL = "call"


@dataclass(frozen=True, slots=True)
class KuhnState:
    """Immutable state for configurable multiplayer Kuhn poker."""

    num_players: int = 2
    cards: tuple[int, ...] | None = None
    history: tuple[tuple[int, str], ...] = ()
    next_player: int | None = None
    bettor: int | None = None
    pending_responders: tuple[int, ...] = ()
    callers: frozenset[int] = field(default_factory=frozenset)
    folded: frozenset[int] = field(default_factory=frozenset)
    terminal: bool = False

    def __post_init__(self) -> None:
        if not 2 <= self.num_players <= 6:
            raise ValueError("Kuhn benchmark supports between two and six players")
        if self.cards is not None and len(self.cards) != self.num_players:
            raise ValueError("card count must equal player count")
        if self.cards is not None and len(set(self.cards)) != len(self.cards):
            raise ValueError("private cards must be distinct")

    @property
    def current_player(self) -> int:
        if self.cards is None:
            return CHANCE_PLAYER
        if self.terminal:
            return TERMINAL_PLAYER
        if self.next_player is None:
            raise ValueError("nonterminal dealt state has no next player")
        return self.next_player

    def legal_actions(self) -> tuple[str, ...]:
        if self.current_player < 0:
            return ()
        return (CHECK, BET) if self.bettor is None else (FOLD, CALL)

    def chance_outcomes(self) -> tuple[tuple[tuple[int, ...], float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        deals = tuple(permutations(range(self.num_players + 1), self.num_players))
        expected_deals = factorial(self.num_players + 1)
        if len(deals) != expected_deals:
            raise AssertionError("unexpected deal count")
        probability = 1.0 / expected_deals
        return tuple((deal, probability) for deal in deals)

    def apply_action(self, action: Action) -> KuhnState:
        player = self.current_player
        if player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal state")
        if player == CHANCE_PLAYER:
            if (
                not isinstance(action, tuple)
                or len(action) != self.num_players
                or any(not isinstance(card, int) for card in action)
                or len(set(action)) != self.num_players
                or any(card not in range(self.num_players + 1) for card in action)
            ):
                raise ValueError(f"invalid Kuhn deal: {action!r}")
            return KuhnState(
                num_players=self.num_players,
                cards=action,
                next_player=0,
            )

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"illegal action {action!r}; legal actions are {legal!r}")
        assert isinstance(action, str)
        history = self.history + ((player, action),)

        if self.bettor is None:
            if action == CHECK:
                if player == self.num_players - 1:
                    return KuhnState(
                        num_players=self.num_players,
                        cards=self.cards,
                        history=history,
                        terminal=True,
                    )
                return KuhnState(
                    num_players=self.num_players,
                    cards=self.cards,
                    history=history,
                    next_player=player + 1,
                )

            responders = tuple(
                (player + offset) % self.num_players
                for offset in range(1, self.num_players)
            )
            return KuhnState(
                num_players=self.num_players,
                cards=self.cards,
                history=history,
                next_player=responders[0],
                bettor=player,
                pending_responders=responders,
                callers=frozenset({player}),
            )

        if not self.pending_responders or self.pending_responders[0] != player:
            raise ValueError("response order is inconsistent with pending responders")
        remaining = self.pending_responders[1:]
        callers = self.callers | ({player} if action == CALL else set())
        folded = self.folded | ({player} if action == FOLD else set())
        return KuhnState(
            num_players=self.num_players,
            cards=self.cards,
            history=history,
            next_player=remaining[0] if remaining else None,
            bettor=self.bettor,
            pending_responders=remaining,
            callers=frozenset(callers),
            folded=frozenset(folded),
            terminal=not remaining,
        )

    def information_state_key(self, player: int) -> str:
        if self.cards is None:
            raise ValueError("chance state has no player information set")
        if player != self.current_player or player < 0:
            raise ValueError(
                f"information key requested for player {player} while player "
                f"{self.current_player} acts"
            )
        public_history = "/".join(f"p{seat}:{action}" for seat, action in self.history)
        if not public_history:
            public_history = "root"
        return f"p{player}|card={self.cards[player]}|history={public_history}"

    def returns(self) -> tuple[float, ...]:
        if self.current_player != TERMINAL_PLAYER or self.cards is None:
            raise ValueError("returns are available only at terminal states")

        contributions = [1.0] * self.num_players
        if self.bettor is None:
            contenders = set(range(self.num_players))
        else:
            contenders = set(self.callers)
            contributions[self.bettor] += 1.0
            for player in self.callers:
                if player != self.bettor:
                    contributions[player] += 1.0

        if not contenders:
            raise ValueError("terminal state has no showdown contender")
        winner = max(contenders, key=lambda player: self.cards[player])
        pot = sum(contributions)
        utilities = [-contribution for contribution in contributions]
        utilities[winner] += pot
        if abs(sum(utilities)) > 1e-12:
            raise AssertionError("Kuhn terminal utilities must sum to zero")
        return tuple(utilities)


@dataclass(frozen=True, slots=True)
class KuhnPoker:
    """Configurable two-to-six-player Kuhn poker game factory."""

    num_players: int = 2

    def __post_init__(self) -> None:
        if not 2 <= self.num_players <= 6:
            raise ValueError("Kuhn benchmark supports between two and six players")

    def initial_state(self) -> KuhnState:
        return KuhnState(num_players=self.num_players)

