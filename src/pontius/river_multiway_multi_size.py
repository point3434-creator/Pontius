"""Exact two-to-six-player river hold'em with sized opening bets.

This additive game widens :mod:`pontius.river_multiway` without changing its
frozen one-bet contract.  Any seat may check or choose one configured opening
bet.  After a bet, every other seat responds once in cyclic order with fold or
call.  Raises, all-ins, side pots, and unmatched calls are intentionally absent.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from itertools import product as cartesian_product
from math import fsum, isfinite, prod
from typing import TypeAlias

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER
from .river import (
    CALL,
    CHECK,
    FOLD,
    Card,
    HoleCards,
    _canonical_hole,
    _format_hole,
    _validate_card,
    _validate_marginal_weights,
    distribution_total_variation,
    evaluate_seven,
    format_card,
)
from .river_multi_size import BetAction
from .river_multiway import (
    MultiwayRiverDeal,
    _deal_token,
    _normalized_multiway_joint_weights,
)

MultiwayMultiSizeAction: TypeAlias = str | BetAction


def _strictly_increasing(values: tuple[float, ...]) -> bool:
    return all(left < right for left, right in zip(values, values[1:]))


@dataclass(frozen=True, slots=True)
class MultiwayMultiSizeRiverHoldem:
    """Exact multiway river game with sized opening bets and no raises."""

    board: tuple[Card, ...]
    pot: float
    stacks: tuple[float, ...]
    bet_sizes: tuple[float, ...]
    deals: tuple[tuple[MultiwayRiverDeal, float], ...]
    _bet_actions: tuple[BetAction, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        board = tuple(sorted(self.board))
        if len(board) != 5 or len(set(board)) != 5:
            raise ValueError("the river board must contain five distinct cards")
        for card in board:
            _validate_card(card)

        stacks = tuple(float(stack) for stack in self.stacks)
        if not 2 <= len(stacks) <= 6:
            raise ValueError("two to six finite nonnegative stacks are required")
        if any(not isfinite(stack) or stack < 0.0 for stack in stacks):
            raise ValueError("two to six finite nonnegative stacks are required")
        pot = float(self.pot)
        if not isfinite(pot) or pot <= 0.0:
            raise ValueError("pot must be positive and finite")

        bet_sizes = tuple(float(amount) for amount in self.bet_sizes)
        if not bet_sizes:
            raise ValueError("at least one bet size is required")
        if any(not isfinite(amount) or amount <= 0.0 for amount in bet_sizes):
            raise ValueError("bet sizes must be positive and finite")
        if not _strictly_increasing(bet_sizes):
            raise ValueError("bet sizes must be strictly increasing")
        if bet_sizes[-1] > min(stacks):
            raise ValueError("every bet size must fit every remaining stack")

        raw_weights: dict[MultiwayRiverDeal, float] = {}
        for deal, probability in self.deals:
            raw_weights[deal] = raw_weights.get(deal, 0.0) + float(probability)
        deals = _normalized_multiway_joint_weights(
            board,
            len(stacks),
            raw_weights,
        )

        object.__setattr__(self, "board", board)
        object.__setattr__(self, "pot", pot)
        object.__setattr__(self, "stacks", stacks)
        object.__setattr__(self, "bet_sizes", bet_sizes)
        object.__setattr__(self, "deals", deals)
        object.__setattr__(
            self,
            "_bet_actions",
            tuple(BetAction(amount) for amount in bet_sizes),
        )

    @property
    def num_players(self) -> int:
        return len(self.stacks)

    @property
    def bet_actions(self) -> tuple[BetAction, ...]:
        return self._bet_actions

    @classmethod
    def from_joint_weights(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: Iterable[float],
        bet_sizes: Iterable[float],
        joint_weights: Mapping[MultiwayRiverDeal, float],
    ) -> MultiwayMultiSizeRiverHoldem:
        canonical_board = tuple(sorted(board))
        canonical_stacks = tuple(stacks)
        deals = _normalized_multiway_joint_weights(
            canonical_board,
            len(canonical_stacks),
            joint_weights,
        )
        return cls(
            board=canonical_board,
            pot=pot,
            stacks=canonical_stacks,
            bet_sizes=tuple(bet_sizes),
            deals=deals,
        )

    @classmethod
    def from_independent_ranges(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: Iterable[float],
        bet_sizes: Iterable[float],
        player_weights: Iterable[Mapping[HoleCards, float]],
    ) -> MultiwayMultiSizeRiverHoldem:
        canonical_board = tuple(sorted(board))
        if len(canonical_board) != 5 or len(set(canonical_board)) != 5:
            raise ValueError("the river board must contain five distinct cards")
        for card in canonical_board:
            _validate_card(card)
        canonical_stacks = tuple(stacks)
        ranges = tuple(player_weights)
        if len(ranges) != len(canonical_stacks):
            raise ValueError("one marginal range is required per player")
        if not 2 <= len(ranges) <= 6:
            raise ValueError("two to six marginal ranges are required")
        validated = tuple(
            _validate_marginal_weights(weights, canonical_board, f"player {player}")
            for player, weights in enumerate(ranges)
        )

        joint_weights: dict[MultiwayRiverDeal, float] = {}
        for selected in cartesian_product(*validated):
            hands = tuple(hand for hand, _ in selected)
            private_cards = tuple(card for hand in hands for card in hand)
            if len(set(private_cards)) != len(private_cards):
                continue
            deal = MultiwayRiverDeal(hands)
            joint_weights[deal] = joint_weights.get(deal, 0.0) + prod(
                weight for _, weight in selected
            )
        if not joint_weights:
            raise ValueError("card removal eliminated every joint deal")
        return cls.from_joint_weights(
            board=canonical_board,
            pot=pot,
            stacks=canonical_stacks,
            bet_sizes=bet_sizes,
            joint_weights=joint_weights,
        )

    def with_joint_weights(
        self,
        joint_weights: Mapping[MultiwayRiverDeal, float],
    ) -> MultiwayMultiSizeRiverHoldem:
        return type(self).from_joint_weights(
            board=self.board,
            pot=self.pot,
            stacks=self.stacks,
            bet_sizes=self.bet_sizes,
            joint_weights=joint_weights,
        )

    def initial_state(self) -> MultiwayMultiSizeRiverState:
        return MultiwayMultiSizeRiverState(game=self)

    def joint_distribution(self) -> dict[MultiwayRiverDeal, float]:
        return dict(self.deals)

    def marginal_distribution(self, player: int) -> dict[HoleCards, float]:
        if player not in range(self.num_players):
            raise ValueError(f"invalid player index {player}")
        result: dict[HoleCards, float] = {}
        for deal, probability in self.deals:
            hand = deal.hand(player)
            result[hand] = result.get(hand, 0.0) + probability
        return dict(sorted(result.items()))

    def conditional_other_hands_distribution(
        self,
        player: int,
        own_hand: HoleCards,
    ) -> dict[tuple[HoleCards, ...], float]:
        if player not in range(self.num_players):
            raise ValueError(f"invalid player index {player}")
        canonical_hand = _canonical_hole(own_hand)
        result: dict[tuple[HoleCards, ...], float] = {}
        own_mass = 0.0
        for deal, probability in self.deals:
            if deal.hand(player) != canonical_hand:
                continue
            others = tuple(
                hand for seat, hand in enumerate(deal.hands) if seat != player
            )
            result[others] = result.get(others, 0.0) + probability
            own_mass += probability
        if own_mass <= 0.0:
            raise ValueError("private hand has zero probability under this range")
        return {
            hands: probability / own_mass
            for hands, probability in sorted(result.items())
        }

    @property
    def structural_digest(self) -> str:
        fields = (
            "river-multiway-multi-size-v1",
            str(self.num_players),
            ",".join(format_card(card) for card in self.board),
            self.pot.hex(),
            ",".join(stack.hex() for stack in self.stacks),
            ",".join(amount.hex() for amount in self.bet_sizes),
        )
        return sha256("|".join(fields).encode("ascii")).hexdigest()

    @property
    def provenance_digest(self) -> str:
        range_payload = ";".join(
            f"{_deal_token(deal)}={probability.hex()}"
            for deal, probability in self.deals
        )
        return sha256(
            f"{self.structural_digest}|{range_payload}".encode("ascii")
        ).hexdigest()

    def total_variation(self, other: MultiwayMultiSizeRiverHoldem) -> float:
        self._require_same_structure(other)
        return distribution_total_variation(
            self.joint_distribution(),
            other.joint_distribution(),
        )

    @property
    def payoff_span(self) -> float:
        return self.pot + self.num_players * self.bet_sizes[-1]

    def fixed_policy_value_bound(
        self,
        other: MultiwayMultiSizeRiverHoldem,
    ) -> float:
        return self.payoff_span * self.total_variation(other)

    def _require_same_structure(self, other: MultiwayMultiSizeRiverHoldem) -> None:
        if not isinstance(other, MultiwayMultiSizeRiverHoldem):
            raise TypeError("range comparison requires another sized multiway game")
        if self.structural_digest != other.structural_digest:
            raise ValueError("range comparison requires identical game structure")


@dataclass(frozen=True, slots=True)
class MultiwayMultiSizeRiverState:
    """Immutable state in :class:`MultiwayMultiSizeRiverHoldem`."""

    game: MultiwayMultiSizeRiverHoldem
    deal: MultiwayRiverDeal | None = None
    history: tuple[tuple[int, MultiwayMultiSizeAction], ...] = ()
    next_player: int | None = None
    bettor: int | None = None
    opening_bet: BetAction | None = None
    pending_responders: tuple[int, ...] = ()
    callers: frozenset[int] = field(default_factory=frozenset)
    folded: frozenset[int] = field(default_factory=frozenset)
    terminal: bool = False

    @property
    def current_player(self) -> int:
        if self.deal is None:
            return CHANCE_PLAYER
        if self.terminal:
            return TERMINAL_PLAYER
        if self.next_player is None:
            raise ValueError("nonterminal dealt state has no next player")
        return self.next_player

    def legal_actions(self) -> tuple[MultiwayMultiSizeAction, ...]:
        if self.current_player < 0:
            return ()
        if self.bettor is None:
            return (CHECK, *self.game.bet_actions)
        return (FOLD, CALL)

    def chance_outcomes(self) -> tuple[tuple[MultiwayRiverDeal, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        return self.game.deals

    def apply_action(self, action: Action) -> MultiwayMultiSizeRiverState:
        player = self.current_player
        if player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal state")
        if player == CHANCE_PLAYER:
            if (
                not isinstance(action, MultiwayRiverDeal)
                or action not in dict(self.game.deals)
            ):
                raise ValueError(f"invalid multiway river deal {action!r}")
            return MultiwayMultiSizeRiverState(
                game=self.game,
                deal=action,
                next_player=0,
            )

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"illegal action {action!r}; legal actions are {legal!r}")
        assert isinstance(action, (str, BetAction))
        history = (*self.history, (player, action))

        if self.bettor is None:
            if action == CHECK:
                if player == self.game.num_players - 1:
                    return MultiwayMultiSizeRiverState(
                        game=self.game,
                        deal=self.deal,
                        history=history,
                        terminal=True,
                    )
                return MultiwayMultiSizeRiverState(
                    game=self.game,
                    deal=self.deal,
                    history=history,
                    next_player=player + 1,
                )

            if not isinstance(action, BetAction):
                raise AssertionError("an unopened non-check action must be a sized bet")
            responders = tuple(
                (player + offset) % self.game.num_players
                for offset in range(1, self.game.num_players)
            )
            return MultiwayMultiSizeRiverState(
                game=self.game,
                deal=self.deal,
                history=history,
                next_player=responders[0],
                bettor=player,
                opening_bet=action,
                pending_responders=responders,
                callers=frozenset({player}),
            )

        if not self.pending_responders or self.pending_responders[0] != player:
            raise ValueError("response order is inconsistent with pending responders")
        remaining = self.pending_responders[1:]
        callers = self.callers | ({player} if action == CALL else set())
        folded = self.folded | ({player} if action == FOLD else set())
        return MultiwayMultiSizeRiverState(
            game=self.game,
            deal=self.deal,
            history=history,
            next_player=remaining[0] if remaining else None,
            bettor=self.bettor,
            opening_bet=self.opening_bet,
            pending_responders=remaining,
            callers=frozenset(callers),
            folded=frozenset(folded),
            terminal=not remaining,
        )

    def _public_history(self) -> str:
        if not self.history:
            return "root"
        return "/".join(f"p{seat}:{action}" for seat, action in self.history)

    def information_state_key(self, player: int) -> str:
        if self.deal is None:
            raise ValueError("chance state has no player information set")
        if player != self.current_player or player not in range(self.game.num_players):
            raise ValueError(
                f"information key requested for player {player} while player "
                f"{self.current_player} acts"
            )
        return (
            f"river-multiway|structure={self.game.structural_digest}|p{player}|"
            f"hand={_format_hole(self.deal.hand(player))}|"
            f"history={self._public_history()}"
        )

    def coalition_information_state_key(self, coalition: tuple[int, ...]) -> str:
        if self.deal is None:
            raise ValueError("chance state has no coalition information set")
        members = tuple(sorted(coalition))
        if not members or len(set(members)) != len(members):
            raise ValueError("coalition members must be unique and nonempty")
        if any(player not in range(self.game.num_players) for player in members):
            raise ValueError("coalition contains an invalid player")
        if self.current_player not in members:
            raise ValueError("the acting player must belong to the coalition")
        private = ",".join(
            f"p{player}:{_format_hole(self.deal.hand(player))}"
            for player in members
        )
        return (
            f"river-multiway-team|structure={self.game.structural_digest}|"
            f"acting=p{self.current_player}|members={','.join(map(str, members))}|"
            f"hands={private}|history={self._public_history()}"
        )

    def terminal_descriptor(self) -> tuple[tuple[int, ...], float]:
        """Return sorted showdown contenders and their common contribution."""

        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("terminal descriptor is available only at a terminal")
        if self.opening_bet is None:
            return tuple(range(self.game.num_players)), 0.0
        return tuple(sorted(self.callers)), self.opening_bet.amount

    def returns(self) -> tuple[float, ...]:
        if self.current_player != TERMINAL_PLAYER or self.deal is None:
            raise ValueError("returns are available only at terminal states")

        contenders, contribution = self.terminal_descriptor()
        contributions = [0.0] * self.game.num_players
        if contribution > 0.0:
            for player in contenders:
                contributions[player] = contribution

        ranks = {
            player: evaluate_seven((*self.game.board, *self.deal.hand(player)))
            for player in contenders
        }
        best_rank = max(ranks.values())
        winners = tuple(
            player for player, rank in ranks.items() if rank == best_rank
        )
        final_pot = self.game.pot + fsum(contributions)
        winner_share = final_pot / len(winners)
        sunk_share = self.game.pot / self.game.num_players
        utilities = [
            -sunk_share - contributions[player]
            for player in range(self.game.num_players)
        ]
        for winner in winners:
            utilities[winner] += winner_share
        if abs(fsum(utilities)) > 1e-10:
            raise AssertionError("sized multiway terminal utilities must sum to zero")
        return tuple(utilities)
