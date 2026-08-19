"""Exact heads-up river game with multiple bet and raise-to sizes.

This module widens action branching without changing the frozen fixed-size
``RiverHoldem`` control.  The game has one opening action, at most one raise,
and exact sized public actions.  It intentionally excludes re-raises, side
pots, and unmatched all-in calls; every configured contribution fits both
remaining stacks.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import TypeAlias

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER
from .river import (
    CALL,
    CHECK,
    FOLD,
    Card,
    HoleCards,
    RiverDeal,
    RiverHoldem,
    _canonical_hole,
    _format_hole,
    _normalized_joint_weights,
    _validate_card,
    _validate_marginal_weights,
    distribution_total_variation,
    evaluate_seven,
)


def _positive_amount(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive finite number")
    try:
        amount = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a positive finite number") from error
    if not isfinite(amount) or amount <= 0.0:
        raise ValueError(f"{label} must be a positive finite number")
    return amount


@dataclass(frozen=True, slots=True, order=True)
class BetAction:
    """An opening bet carrying its exact contribution amount."""

    amount: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "amount",
            _positive_amount(self.amount, "bet amount"),
        )

    def __str__(self) -> str:
        return f"bet:{self.amount.hex()}"


@dataclass(frozen=True, slots=True, order=True)
class RaiseToAction:
    """A raise carrying the player's exact total contribution."""

    amount: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "amount",
            _positive_amount(self.amount, "raise-to amount"),
        )

    def __str__(self) -> str:
        return f"raise-to:{self.amount.hex()}"


MultiSizeAction: TypeAlias = str | BetAction | RaiseToAction


def _strictly_increasing(values: tuple[float, ...]) -> bool:
    return all(left < right for left, right in zip(values, values[1:]))


@dataclass(frozen=True, slots=True)
class MultiSizeRiverHoldem:
    """Exact river game with configurable opening bets and one raise layer."""

    board: tuple[Card, ...]
    pot: float
    stacks: tuple[float, float]
    bet_sizes: tuple[float, ...]
    raise_to_sizes: tuple[float, ...]
    deals: tuple[tuple[RiverDeal, float], ...]
    num_players: int = 2
    _bet_actions: tuple[BetAction, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _raise_actions: tuple[RaiseToAction, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        board = tuple(self.board)
        if len(board) != 5 or len(set(board)) != 5:
            raise ValueError("the river board must contain five distinct cards")
        for card in board:
            _validate_card(card)
        if self.num_players != 2:
            raise ValueError("the multi-size river game is heads-up")

        pot = _positive_amount(self.pot, "pot")
        if len(self.stacks) != 2:
            raise ValueError("two finite nonnegative stacks are required")
        stacks = tuple(float(stack) for stack in self.stacks)
        if any(not isfinite(stack) or stack < 0.0 for stack in stacks):
            raise ValueError("two finite nonnegative stacks are required")
        effective_stack = min(stacks)

        bet_sizes = tuple(
            _positive_amount(value, "bet size") for value in self.bet_sizes
        )
        raise_sizes = tuple(
            _positive_amount(value, "raise-to size")
            for value in self.raise_to_sizes
        )
        if not bet_sizes:
            raise ValueError("at least one bet size is required")
        if not _strictly_increasing(bet_sizes):
            raise ValueError("bet sizes must be strictly increasing")
        if not _strictly_increasing(raise_sizes):
            raise ValueError("raise-to sizes must be strictly increasing")
        if any(amount > effective_stack for amount in (*bet_sizes, *raise_sizes)):
            raise ValueError("every bet and raise-to must fit both remaining stacks")
        if any(raise_to < 2.0 * bet_sizes[0] for raise_to in raise_sizes):
            raise ValueError("every raise-to size must be legal after at least one bet")

        raw_weights: dict[RiverDeal, float] = {}
        for deal, probability in self.deals:
            raw_weights[deal] = raw_weights.get(deal, 0.0) + float(probability)
        normalized = _normalized_joint_weights(board, raw_weights)

        object.__setattr__(self, "board", board)
        object.__setattr__(self, "pot", pot)
        object.__setattr__(self, "stacks", stacks)
        object.__setattr__(self, "bet_sizes", bet_sizes)
        object.__setattr__(self, "raise_to_sizes", raise_sizes)
        object.__setattr__(self, "deals", normalized)
        object.__setattr__(
            self,
            "_bet_actions",
            tuple(BetAction(amount) for amount in bet_sizes),
        )
        object.__setattr__(
            self,
            "_raise_actions",
            tuple(RaiseToAction(amount) for amount in raise_sizes),
        )

    @classmethod
    def from_joint_weights(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: tuple[float, float],
        bet_sizes: Iterable[float],
        raise_to_sizes: Iterable[float],
        joint_weights: Mapping[RiverDeal, float],
    ) -> MultiSizeRiverHoldem:
        """Build a multi-size game from an explicit normalized joint range."""

        canonical_board = tuple(sorted(board))
        deals = _normalized_joint_weights(canonical_board, joint_weights)
        return cls(
            board=canonical_board,
            pot=pot,
            stacks=stacks,
            bet_sizes=tuple(bet_sizes),
            raise_to_sizes=tuple(raise_to_sizes),
            deals=deals,
        )

    @classmethod
    def from_independent_ranges(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: tuple[float, float],
        bet_sizes: Iterable[float],
        raise_to_sizes: Iterable[float],
        player0_weights: Mapping[HoleCards, float],
        player1_weights: Mapping[HoleCards, float],
    ) -> MultiSizeRiverHoldem:
        """Multiply marginals, remove blocked deals, and normalize exactly."""

        canonical_board = tuple(sorted(board))
        if len(canonical_board) != 5 or len(set(canonical_board)) != 5:
            raise ValueError("the river board must contain five distinct cards")
        for card in canonical_board:
            _validate_card(card)
        player0 = _validate_marginal_weights(
            player0_weights,
            canonical_board,
            "player 0",
        )
        player1 = _validate_marginal_weights(
            player1_weights,
            canonical_board,
            "player 1",
        )
        joint_weights = {
            RiverDeal(hand0, hand1): weight0 * weight1
            for hand0, weight0 in player0
            for hand1, weight1 in player1
            if not set(hand0) & set(hand1)
        }
        if not joint_weights:
            raise ValueError("card removal eliminated every joint deal")
        return cls.from_joint_weights(
            board=canonical_board,
            pot=pot,
            stacks=stacks,
            bet_sizes=bet_sizes,
            raise_to_sizes=raise_to_sizes,
            joint_weights=joint_weights,
        )

    @classmethod
    def from_river_game(
        cls,
        game: RiverHoldem,
        *,
        bet_sizes: Iterable[float],
        raise_to_sizes: Iterable[float],
    ) -> MultiSizeRiverHoldem:
        """Reuse a fixed-size context's cards, stacks, pot, and joint range."""

        if not isinstance(game, RiverHoldem):
            raise TypeError("conversion requires a RiverHoldem game")
        return cls.from_joint_weights(
            board=game.board,
            pot=game.pot,
            stacks=game.stacks,
            bet_sizes=bet_sizes,
            raise_to_sizes=raise_to_sizes,
            joint_weights=game.joint_distribution(),
        )

    def with_joint_weights(
        self,
        joint_weights: Mapping[RiverDeal, float],
    ) -> MultiSizeRiverHoldem:
        """Return a structurally identical game with a new joint range."""

        return type(self).from_joint_weights(
            board=self.board,
            pot=self.pot,
            stacks=self.stacks,
            bet_sizes=self.bet_sizes,
            raise_to_sizes=self.raise_to_sizes,
            joint_weights=joint_weights,
        )

    def initial_state(self) -> MultiSizeRiverState:
        return MultiSizeRiverState(game=self)

    @property
    def bet_actions(self) -> tuple[BetAction, ...]:
        return self._bet_actions

    @property
    def raise_actions(self) -> tuple[RaiseToAction, ...]:
        return self._raise_actions

    def legal_raises(self, bet: BetAction) -> tuple[RaiseToAction, ...]:
        if bet not in self._bet_actions:
            raise ValueError(f"unknown opening bet {bet!r}")
        return tuple(
            action
            for action in self._raise_actions
            if action.amount >= 2.0 * bet.amount
        )

    def joint_distribution(self) -> dict[RiverDeal, float]:
        return dict(self.deals)

    def marginal_distribution(self, player: int) -> dict[HoleCards, float]:
        if player not in (0, 1):
            raise ValueError(f"invalid player index {player}")
        result: dict[HoleCards, float] = {}
        for deal, probability in self.deals:
            hand = deal.hand(player)
            result[hand] = result.get(hand, 0.0) + probability
        return dict(sorted(result.items()))

    def conditional_opponent_distribution(
        self,
        player: int,
        own_hand: HoleCards,
    ) -> dict[HoleCards, float]:
        if player not in (0, 1):
            raise ValueError(f"invalid player index {player}")
        canonical_hand = _canonical_hole(own_hand)
        opponent_weights: dict[HoleCards, float] = {}
        own_mass = 0.0
        for deal, probability in self.deals:
            if deal.hand(player) != canonical_hand:
                continue
            opponent = deal.hand(1 - player)
            opponent_weights[opponent] = (
                opponent_weights.get(opponent, 0.0) + probability
            )
            own_mass += probability
        if own_mass <= 0.0:
            raise ValueError("private hand has zero probability under this range")
        return {
            hand: probability / own_mass
            for hand, probability in sorted(opponent_weights.items())
        }

    @property
    def structural_digest(self) -> str:
        fields = (
            "river-multi-size-v1",
            ",".join(str(card) for card in self.board),
            self.pot.hex(),
            self.stacks[0].hex(),
            self.stacks[1].hex(),
            ",".join(amount.hex() for amount in self.bet_sizes),
            ",".join(amount.hex() for amount in self.raise_to_sizes),
        )
        return sha256("|".join(fields).encode("ascii")).hexdigest()

    @property
    def provenance_digest(self) -> str:
        range_payload = ";".join(
            f"{_format_hole(deal.player0)}/{_format_hole(deal.player1)}={probability.hex()}"
            for deal, probability in self.deals
        )
        payload = f"{self.structural_digest}|{range_payload}"
        return sha256(payload.encode("ascii")).hexdigest()

    def total_variation(self, other: MultiSizeRiverHoldem) -> float:
        self._require_same_structure(other)
        return distribution_total_variation(
            self.joint_distribution(),
            other.joint_distribution(),
        )

    def conditional_opponent_total_variation(
        self,
        other: MultiSizeRiverHoldem,
        *,
        player: int,
        own_hand: HoleCards,
    ) -> float:
        self._require_same_structure(other)
        return distribution_total_variation(
            self.conditional_opponent_distribution(player, own_hand),
            other.conditional_opponent_distribution(player, own_hand),
        )

    @property
    def payoff_span(self) -> float:
        maximum = max((*self.bet_sizes, *self.raise_to_sizes))
        return self.pot + 2.0 * maximum

    def fixed_policy_value_bound(self, other: MultiSizeRiverHoldem) -> float:
        return self.payoff_span * self.total_variation(other)

    def _require_same_structure(self, other: MultiSizeRiverHoldem) -> None:
        if not isinstance(other, MultiSizeRiverHoldem):
            raise TypeError("range comparison requires another multi-size game")
        if self.structural_digest != other.structural_digest:
            raise ValueError("range comparison requires identical game structure")


def _public_action_token(action: MultiSizeAction) -> str:
    if action in (CHECK, FOLD, CALL):
        return str(action)
    if isinstance(action, (BetAction, RaiseToAction)):
        return str(action)
    raise ValueError(f"invalid multi-size public action {action!r}")


@dataclass(frozen=True, slots=True)
class MultiSizeRiverState:
    """Immutable state in :class:`MultiSizeRiverHoldem`."""

    game: MultiSizeRiverHoldem
    deal: RiverDeal | None = None
    history: tuple[tuple[int, MultiSizeAction], ...] = ()
    terminal: bool = False

    @property
    def current_player(self) -> int:
        if self.deal is None:
            return CHANCE_PLAYER
        if self.terminal:
            return TERMINAL_PLAYER
        if not self.history:
            return 0
        if (
            len(self.history) == 1
            and self.history[0][0] == 0
            and isinstance(self.history[0][1], BetAction)
        ):
            return 1
        if (
            len(self.history) == 2
            and self.history[0][0] == 0
            and isinstance(self.history[0][1], BetAction)
            and self.history[1][0] == 1
            and isinstance(self.history[1][1], RaiseToAction)
        ):
            return 0
        raise ValueError(f"invalid nonterminal multi-size history {self.history!r}")

    def legal_actions(self) -> tuple[MultiSizeAction, ...]:
        player = self.current_player
        if player == 0 and not self.history:
            return (CHECK, *self.game.bet_actions)
        if player == 1:
            bet = self.history[0][1]
            assert isinstance(bet, BetAction)
            return (FOLD, CALL, *self.game.legal_raises(bet))
        if player == 0:
            return (FOLD, CALL)
        return ()

    def chance_outcomes(self) -> tuple[tuple[RiverDeal, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        return self.game.deals

    def apply_action(self, action: Action) -> MultiSizeRiverState:
        player = self.current_player
        if player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal state")
        if player == CHANCE_PLAYER:
            if not isinstance(action, RiverDeal) or action not in dict(self.game.deals):
                raise ValueError(f"invalid river deal {action!r}")
            return MultiSizeRiverState(game=self.game, deal=action)

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"illegal action {action!r}; legal actions are {legal!r}")
        assert isinstance(action, (str, BetAction, RaiseToAction))
        history = (*self.history, (player, action))
        return MultiSizeRiverState(
            game=self.game,
            deal=self.deal,
            history=history,
            terminal=action in (CHECK, FOLD, CALL),
        )

    def information_state_key(self, player: int) -> str:
        if self.deal is None:
            raise ValueError("chance state has no player information set")
        if player != self.current_player or player not in (0, 1):
            raise ValueError(
                f"information key requested for player {player} while player "
                f"{self.current_player} acts"
            )
        history = "root" if not self.history else "/".join(
            f"p{seat}:{_public_action_token(action)}"
            for seat, action in self.history
        )
        return (
            f"river-multi-size|structure={self.game.structural_digest}|p{player}|"
            f"hand={_format_hole(self.deal.hand(player))}|history={history}"
        )

    def returns(self) -> tuple[float, float]:
        if self.current_player != TERMINAL_PLAYER or self.deal is None:
            raise ValueError("returns are available only at terminal states")
        actions = tuple(action for _, action in self.history)

        if actions == (CHECK,):
            utility0 = self._showdown_utility(self.game.pot / 2.0)
        elif (
            len(actions) == 2
            and isinstance(actions[0], BetAction)
            and actions[1] == FOLD
        ):
            utility0 = self.game.pot / 2.0
        elif (
            len(actions) == 2
            and isinstance(actions[0], BetAction)
            and actions[1] == CALL
        ):
            utility0 = self._showdown_utility(
                self.game.pot / 2.0 + actions[0].amount
            )
        elif (
            len(actions) == 3
            and isinstance(actions[0], BetAction)
            and isinstance(actions[1], RaiseToAction)
            and actions[2] == FOLD
        ):
            utility0 = -(self.game.pot / 2.0 + actions[0].amount)
        elif (
            len(actions) == 3
            and isinstance(actions[0], BetAction)
            and isinstance(actions[1], RaiseToAction)
            and actions[2] == CALL
        ):
            utility0 = self._showdown_utility(
                self.game.pot / 2.0 + actions[1].amount
            )
        else:
            raise ValueError(f"invalid terminal multi-size history {self.history!r}")
        return (utility0, -utility0)

    def _showdown_utility(self, stake: float) -> float:
        assert self.deal is not None
        rank0 = evaluate_seven((*self.game.board, *self.deal.player0))
        rank1 = evaluate_seven((*self.game.board, *self.deal.player1))
        if rank0 == rank1:
            return 0.0
        return stake if rank0 > rank1 else -stake
