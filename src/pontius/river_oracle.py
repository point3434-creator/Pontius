"""Independent normal-form equilibrium oracle for the exact river microgame."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod

from .evaluation import Policy, collect_information_sets, evaluate_profile
from .game import CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .matrix_game import MatrixGameSolution, solve_zero_sum_matrix_game
from .river import BET, CALL, CHECK, FOLD, RAISE, RiverHoldem


@dataclass(frozen=True, slots=True)
class RiverOracleSolution:
    """Verified minimax solution and its behavioral realization."""

    value_player0: float
    policy: Policy
    player0_information_sets: int
    player1_information_sets: int
    player0_pure_policies: int
    player1_pure_policies: int
    player0_support_size: int
    player1_support_size: int
    nash_conv: float
    matrix_solution: MatrixGameSolution


def _pure_plans(
    information_sets: dict[str, tuple[str, ...]],
) -> tuple[tuple[str, ...], ...]:
    return tuple(product(*(information_sets[key] for key in information_sets)))


def _behavioral_realization(
    information_sets: dict[str, tuple[str, ...]],
    pure_plans: tuple[tuple[str, ...], ...],
    mixture: tuple[float, ...],
    predecessor_sequences: dict[str, tuple[tuple[str, str], ...]],
) -> Policy:
    """Convert mixed pure plans using perfect-recall sequence conditioning."""

    key_indices = {key: index for index, key in enumerate(information_sets)}
    policy: Policy = {}
    for key_index, (key, actions) in enumerate(information_sets.items()):
        distribution = {action: 0.0 for action in actions}
        eligible_mass = 0.0
        for plan, probability in zip(pure_plans, mixture, strict=True):
            if any(
                plan[key_indices[predecessor_key]] != predecessor_action
                for predecessor_key, predecessor_action in predecessor_sequences[key]
            ):
                continue
            eligible_mass += probability
            distribution[plan[key_index]] += probability
        if eligible_mass <= 1e-15:
            uniform = 1.0 / len(actions)
            policy[key] = {action: uniform for action in actions}
        else:
            policy[key] = {
                action: probability / eligible_mass
                for action, probability in distribution.items()
            }
    return policy


def _predecessor_sequences(
    game: RiverHoldem,
    player: int,
) -> dict[str, tuple[tuple[str, str], ...]]:
    """Collect each information set's remembered own action sequence."""

    sequences: dict[str, tuple[tuple[str, str], ...]] = {}

    def walk(
        state: GameState,
        own_sequence: tuple[tuple[str, str], ...],
    ) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action), own_sequence)
            return
        actions = tuple(str(action) for action in state.legal_actions())
        key = state.information_state_key(acting)
        if acting == player:
            previous = sequences.setdefault(key, own_sequence)
            if previous != own_sequence:
                raise ValueError(f"game violates perfect recall at {key!r}")
            for action in actions:
                walk(state.apply_action(action), (*own_sequence, (key, action)))
            return
        for action in actions:
            walk(state.apply_action(action), own_sequence)

    walk(game.initial_state(), ())
    return sequences


def solve_river_game(
    game: RiverHoldem,
    *,
    max_pure_policies_per_player: int = 4_096,
    max_matrix_entries: int = 1_000_000,
    tolerance: float = 1e-10,
) -> RiverOracleSolution:
    """Solve a river game by enumerating pure plans and applying a matrix LP.

    Rows are player 1's minimizing plans, columns are player 0's maximizing
    plans, and every matrix entry is player 0's expected utility. Mixed plans
    are converted to behavior by conditioning on each information set's own
    predecessor sequence, which remains valid when the opener responds to a
    raise later on the same play path.
    """

    if not isinstance(game, RiverHoldem):
        raise TypeError("the river oracle requires RiverHoldem")
    if max_pure_policies_per_player <= 0:
        raise ValueError("max_pure_policies_per_player must be positive")
    if max_matrix_entries <= 0:
        raise ValueError("max_matrix_entries must be positive")

    information0 = {
        key: tuple(str(action) for action in actions)
        for key, actions in collect_information_sets(game, 0).items()
    }
    information1 = {
        key: tuple(str(action) for action in actions)
        for key, actions in collect_information_sets(game, 1).items()
    }
    pure_count0 = prod(len(actions) for actions in information0.values())
    pure_count1 = prod(len(actions) for actions in information1.values())
    if max(pure_count0, pure_count1) > max_pure_policies_per_player:
        raise ValueError(
            "river normal form exceeds pure-policy limit: "
            f"player0={pure_count0}, player1={pure_count1}, "
            f"limit={max_pure_policies_per_player}"
        )
    matrix_entries = pure_count0 * pure_count1
    if matrix_entries > max_matrix_entries:
        raise ValueError(
            f"river normal form requires {matrix_entries} matrix entries; "
            f"limit is {max_matrix_entries}"
        )

    plans0 = _pure_plans(information0)
    plans1 = _pure_plans(information1)
    key_index0 = {key: index for index, key in enumerate(information0)}
    key_index1 = {key: index for index, key in enumerate(information1)}

    deal_metadata = []
    for deal, probability in game.deals:
        dealt = game.initial_state().apply_action(deal)
        key0 = dealt.information_state_key(0)
        facing_bet = dealt.apply_action(BET)
        key1 = facing_bet.information_state_key(1)
        check_utility = dealt.apply_action(CHECK).returns()[0]
        fold_utility = facing_bet.apply_action(FOLD).returns()[0]
        call_utility = facing_bet.apply_action(CALL).returns()[0]
        raise_index0 = None
        raise_fold_utility = None
        raise_call_utility = None
        if game.raise_to is not None:
            facing_raise = facing_bet.apply_action(RAISE)
            raise_key0 = facing_raise.information_state_key(0)
            raise_index0 = key_index0[raise_key0]
            raise_fold_utility = facing_raise.apply_action(FOLD).returns()[0]
            raise_call_utility = facing_raise.apply_action(CALL).returns()[0]
        deal_metadata.append(
            (
                probability,
                key_index0[key0],
                key_index1[key1],
                check_utility,
                fold_utility,
                call_utility,
                raise_index0,
                raise_fold_utility,
                raise_call_utility,
            )
        )

    payoffs: list[list[float]] = []
    for plan1 in plans1:
        row = []
        for plan0 in plans0:
            value = 0.0
            for (
                probability,
                index0,
                index1,
                check_utility,
                fold_utility,
                call_utility,
                raise_index0,
                raise_fold_utility,
                raise_call_utility,
            ) in deal_metadata:
                if plan0[index0] == CHECK:
                    utility = check_utility
                elif plan1[index1] == FOLD:
                    utility = fold_utility
                elif plan1[index1] == CALL:
                    utility = call_utility
                else:
                    if (
                        plan1[index1] != RAISE
                        or raise_index0 is None
                        or raise_fold_utility is None
                        or raise_call_utility is None
                    ):
                        raise AssertionError("invalid raise metadata")
                    utility = (
                        raise_fold_utility
                        if plan0[raise_index0] == FOLD
                        else raise_call_utility
                    )
                value += probability * utility
            row.append(value)
        payoffs.append(row)

    matrix_solution = solve_zero_sum_matrix_game(payoffs, tolerance=tolerance)
    policy = _behavioral_realization(
        information0,
        plans0,
        matrix_solution.column_strategy,
        _predecessor_sequences(game, 0),
    )
    policy.update(
        _behavioral_realization(
            information1,
            plans1,
            matrix_solution.row_strategy,
            _predecessor_sequences(game, 1),
        )
    )
    evaluation = evaluate_profile(game, policy)
    scale = max(1.0, game.payoff_span)
    allowed_nash_conv = 10_000.0 * tolerance * scale
    if evaluation.nash_conv > allowed_nash_conv:
        raise AssertionError(
            "normal-form solution did not realize a behavioral equilibrium: "
            f"NashConv={evaluation.nash_conv}, allowed={allowed_nash_conv}"
        )
    if abs(evaluation.utilities[0] - matrix_solution.value) > allowed_nash_conv:
        raise AssertionError("behavioral value disagrees with matrix-game value")

    support_tolerance = 100.0 * tolerance
    return RiverOracleSolution(
        value_player0=matrix_solution.value,
        policy=policy,
        player0_information_sets=len(information0),
        player1_information_sets=len(information1),
        player0_pure_policies=pure_count0,
        player1_pure_policies=pure_count1,
        player0_support_size=sum(
            probability > support_tolerance
            for probability in matrix_solution.column_strategy
        ),
        player1_support_size=sum(
            probability > support_tolerance
            for probability in matrix_solution.row_strategy
        ),
        nash_conv=evaluation.nash_conv,
        matrix_solution=matrix_solution,
    )
