"""Exact two-to-six-player river hold'em with one fixed bet.

The game is a deliberately small multiplayer reference.  It preserves exact
joint ranges, card removal, private information, cyclic response order, and
multiway showdown payoffs while excluding raises and side pots.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from itertools import product as cartesian_product
from math import fsum, isfinite, prod

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER
from .river import (
    BET,
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


@dataclass(frozen=True, slots=True, order=True)
class MultiwayRiverDeal:
    """One compatible private hand for every player, in seat order."""

    hands: tuple[HoleCards, ...]

    def __post_init__(self) -> None:
        canonical = tuple(_canonical_hole(hand) for hand in self.hands)
        if not 2 <= len(canonical) <= 6:
            raise ValueError("a multiway river deal requires two to six hands")
        private_cards = tuple(card for hand in canonical for card in hand)
        if len(set(private_cards)) != len(private_cards):
            raise ValueError("players' private hands overlap")
        object.__setattr__(self, "hands", canonical)

    @property
    def num_players(self) -> int:
        return len(self.hands)

    def hand(self, player: int) -> HoleCards:
        if player not in range(self.num_players):
            raise ValueError(f"invalid player index {player}")
        return self.hands[player]


def _normalized_multiway_joint_weights(
    board: tuple[Card, ...],
    num_players: int,
    joint_weights: Mapping[MultiwayRiverDeal, float],
) -> tuple[tuple[MultiwayRiverDeal, float], ...]:
    if not joint_weights:
        raise ValueError("joint range must contain at least one deal")
    board_cards = set(board)
    accumulated: dict[MultiwayRiverDeal, float] = {}
    for deal, supplied_weight in joint_weights.items():
        if not isinstance(deal, MultiwayRiverDeal):
            raise TypeError("joint range keys must be MultiwayRiverDeal instances")
        if deal.num_players != num_players:
            raise ValueError("every deal must contain one hand per player")
        if board_cards & {card for hand in deal.hands for card in hand}:
            raise ValueError("private cards overlap the public board")
        weight = float(supplied_weight)
        if not isfinite(weight) or weight < 0.0:
            raise ValueError("joint weights must be finite and nonnegative")
        if weight > 0.0:
            accumulated[deal] = accumulated.get(deal, 0.0) + weight
    total = fsum(accumulated.values())
    if not isfinite(total) or total <= 0.0:
        raise ValueError("joint range must have positive finite mass")
    return tuple(
        (deal, weight / total)
        for deal, weight in sorted(accumulated.items())
    )


def _deal_token(deal: MultiwayRiverDeal) -> str:
    return "/".join(_format_hole(hand) for hand in deal.hands)


@dataclass(frozen=True, slots=True)
class MultiwayRiverHoldem:
    """Exact multiway river game with a single fixed bet and no raises."""

    board: tuple[Card, ...]
    pot: float
    stacks: tuple[float, ...]
    bet_size: float
    deals: tuple[tuple[MultiwayRiverDeal, float], ...]

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
        bet_size = float(self.bet_size)
        if not isfinite(pot) or pot <= 0.0:
            raise ValueError("pot must be positive and finite")
        if not isfinite(bet_size) or bet_size <= 0.0:
            raise ValueError("bet size must be positive and finite")
        if bet_size > min(stacks):
            raise ValueError("bet size cannot exceed any remaining stack")

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
        object.__setattr__(self, "bet_size", bet_size)
        object.__setattr__(self, "deals", deals)

    @property
    def num_players(self) -> int:
        return len(self.stacks)

    @classmethod
    def from_joint_weights(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: Iterable[float],
        bet_size: float,
        joint_weights: Mapping[MultiwayRiverDeal, float],
    ) -> MultiwayRiverHoldem:
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
            bet_size=bet_size,
            deals=deals,
        )

    @classmethod
    def from_independent_ranges(
        cls,
        *,
        board: Iterable[Card],
        pot: float,
        stacks: Iterable[float],
        bet_size: float,
        player_weights: Iterable[Mapping[HoleCards, float]],
    ) -> MultiwayRiverHoldem:
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
            bet_size=bet_size,
            joint_weights=joint_weights,
        )

    def with_joint_weights(
        self,
        joint_weights: Mapping[MultiwayRiverDeal, float],
    ) -> MultiwayRiverHoldem:
        return type(self).from_joint_weights(
            board=self.board,
            pot=self.pot,
            stacks=self.stacks,
            bet_size=self.bet_size,
            joint_weights=joint_weights,
        )

    def initial_state(self) -> MultiwayRiverState:
        return MultiwayRiverState(game=self)

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
        """Return the exact joint range of all other seats given one hand."""

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
            "river-multiway-v1",
            str(self.num_players),
            ",".join(format_card(card) for card in self.board),
            self.pot.hex(),
            ",".join(stack.hex() for stack in self.stacks),
            self.bet_size.hex(),
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

    def total_variation(self, other: MultiwayRiverHoldem) -> float:
        self._require_same_structure(other)
        return distribution_total_variation(
            self.joint_distribution(),
            other.joint_distribution(),
        )

    @property
    def payoff_span(self) -> float:
        return self.pot + self.num_players * self.bet_size

    def fixed_policy_value_bound(self, other: MultiwayRiverHoldem) -> float:
        return self.payoff_span * self.total_variation(other)

    def _require_same_structure(self, other: MultiwayRiverHoldem) -> None:
        if not isinstance(other, MultiwayRiverHoldem):
            raise TypeError("range comparison requires another multiway river game")
        if self.structural_digest != other.structural_digest:
            raise ValueError("range comparison requires identical game structure")


@dataclass(frozen=True, slots=True)
class MultiwayRiverState:
    """Immutable state in :class:`MultiwayRiverHoldem`."""

    game: MultiwayRiverHoldem
    deal: MultiwayRiverDeal | None = None
    history: tuple[tuple[int, str], ...] = ()
    next_player: int | None = None
    bettor: int | None = None
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

    def legal_actions(self) -> tuple[str, ...]:
        if self.current_player < 0:
            return ()
        return (CHECK, BET) if self.bettor is None else (FOLD, CALL)

    def chance_outcomes(self) -> tuple[tuple[MultiwayRiverDeal, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        return self.game.deals

    def apply_action(self, action: Action) -> MultiwayRiverState:
        player = self.current_player
        if player == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal state")
        if player == CHANCE_PLAYER:
            if (
                not isinstance(action, MultiwayRiverDeal)
                or action not in dict(self.game.deals)
            ):
                raise ValueError(f"invalid multiway river deal {action!r}")
            return MultiwayRiverState(game=self.game, deal=action, next_player=0)

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"illegal action {action!r}; legal actions are {legal!r}")
        assert isinstance(action, str)
        history = (*self.history, (player, action))

        if self.bettor is None:
            if action == CHECK:
                if player == self.game.num_players - 1:
                    return MultiwayRiverState(
                        game=self.game,
                        deal=self.deal,
                        history=history,
                        terminal=True,
                    )
                return MultiwayRiverState(
                    game=self.game,
                    deal=self.deal,
                    history=history,
                    next_player=player + 1,
                )

            responders = tuple(
                (player + offset) % self.game.num_players
                for offset in range(1, self.game.num_players)
            )
            return MultiwayRiverState(
                game=self.game,
                deal=self.deal,
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
        return MultiwayRiverState(
            game=self.game,
            deal=self.deal,
            history=history,
            next_player=remaining[0] if remaining else None,
            bettor=self.bettor,
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
        """Return the shared-private-information key for a team controller."""

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

    def returns(self) -> tuple[float, ...]:
        if self.current_player != TERMINAL_PLAYER or self.deal is None:
            raise ValueError("returns are available only at terminal states")

        if self.bettor is None:
            contenders = set(range(self.game.num_players))
        else:
            contenders = set(self.callers)
        if not contenders:
            raise ValueError("terminal state has no showdown contender")

        contributions = [0.0] * self.game.num_players
        if self.bettor is not None:
            for player in self.callers:
                contributions[player] = self.game.bet_size

        ranks = {
            player: evaluate_seven(
                (*self.game.board, *self.deal.hand(player))
            )
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
            -sunk_share - contribution for contribution in contributions
        ]
        for winner in winners:
            utilities[winner] += winner_share
        if abs(fsum(utilities)) > 1e-10:
            raise AssertionError("multiway river terminal utilities must sum to zero")
        return tuple(utilities)
