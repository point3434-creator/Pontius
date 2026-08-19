"""Exact two-player counterfactual-frontier resolving controls.

The gadget follows the terminate/follow construction of Burch, Johanson, and
Bowling (2014).  It is deliberately specialized to concrete Kuhn public
subgames so every reach factor, frontier value, and finite-solver residual can
be checked against the full game before we generalize the interface.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from math import isfinite, prod

from .cfr import TabularCFR
from .continual import PublicHistory, public_belief, public_histories
from .evaluation import (
    EvaluationResult,
    Policy,
    best_response,
    collect_information_sets,
    evaluate_profile,
    expected_utilities_from_state,
    policy_distribution,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .kuhn import KuhnPoker, KuhnState

TERMINATE = "terminate"
FOLLOW = "follow"
SOLVERS = {"cfr", "lcfr", "cfr_plus", "dcfr"}


@dataclass(frozen=True, slots=True)
class CounterfactualRoot:
    """One concrete subgame root and its reach excluding the opponent."""

    state: KuhnState = field(compare=False, hash=False, repr=False)
    opponent_augmented_key: str
    counterfactual_reach: float


@dataclass(frozen=True, slots=True)
class FrontierEntry:
    """Blueprint safety value for one opponent augmented information set."""

    key: str
    counterfactual_reach: float
    blueprint_cbr_value: float
    terminate_utility: float
    concrete_states: int


@dataclass(frozen=True, slots=True)
class CounterfactualFrontier:
    """Exact opponent counterfactual-best-response summary at a boundary."""

    history: PublicHistory
    resolver_player: int
    opponent_player: int
    total_counterfactual_reach: float
    roots: tuple[CounterfactualRoot, ...]
    entries: tuple[FrontierEntry, ...]

    @property
    def blueprint_values(self) -> dict[str, float]:
        return {entry.key: entry.blueprint_cbr_value for entry in self.entries}

    @property
    def opponent_gadget_value(self) -> float:
        return sum(entry.blueprint_cbr_value for entry in self.entries)


@dataclass(frozen=True, slots=True)
class FrontierComparison:
    key: str
    blueprint_cbr_value: float
    candidate_cbr_value: float
    positive_violation: float


@dataclass(frozen=True, slots=True)
class SafeResolveResult:
    """Resolved policy and an exact certificate for its finite-solver error."""

    policy: Policy = field(compare=False, repr=False)
    frontier: CounterfactualFrontier
    comparisons: tuple[FrontierComparison, ...]
    resolver_information_sets: int
    solver_name: str
    solver_iterations: int
    initialization_seconds: float
    iteration_seconds: float
    certificate_seconds: float
    gadget_evaluation: EvaluationResult
    gadget_opponent_best_response_value: float
    gadget_opponent_security_residual: float
    total_positive_frontier_violation: float
    max_positive_frontier_violation: float

    @property
    def search_seconds(self) -> float:
        return self.initialization_seconds + self.iteration_seconds

    @property
    def decision_compute_seconds(self) -> float:
        return self.search_seconds + self.certificate_seconds

    @property
    def full_game_exploitability_increase_bound(self) -> float:
        """Worst-case increase when the other full-game strategy is fixed."""

        return self.total_positive_frontier_violation / 2.0


@dataclass(frozen=True, slots=True)
class SafePublicResolveRecord:
    history: PublicHistory
    resolver_player: int
    public_reach_probability: float
    opponent_counterfactual_reach: float
    frontier_information_sets: int
    resolver_information_sets: int
    search_seconds: float
    certificate_seconds: float
    candidate_deployed: bool
    gadget_nash_conv: float
    total_positive_frontier_violation: float
    max_positive_frontier_violation: float
    exploitability_increase_bound: float

    @property
    def decision_compute_seconds(self) -> float:
        return self.search_seconds + self.certificate_seconds


@dataclass(frozen=True, slots=True)
class SafeContinualResolveResult:
    """Root-forward safe replacements with an additive residual certificate."""

    policy: Policy = field(compare=False, repr=False)
    records: tuple[SafePublicResolveRecord, ...]
    structural_public_histories: int
    searched_public_histories: int
    skipped_zero_counterfactual_reach_histories: tuple[PublicHistory, ...]
    total_search_seconds: float
    total_certificate_seconds: float
    total_decision_compute_seconds: float
    expected_search_seconds_per_hand: float
    expected_certificate_seconds_per_hand: float
    expected_decision_compute_seconds_per_hand: float
    expected_public_decisions_per_hand: float
    cumulative_exploitability_increase_bound: float
    max_search_seconds_at_one_public_state: float


class ZeroCounterfactualReachError(ValueError):
    """The resolver's fixed trunk strategy cannot reach a public boundary."""


@dataclass(frozen=True, slots=True)
class _RootDistributionState:
    roots: tuple[CounterfactualRoot, ...] = field(
        compare=False,
        hash=False,
        repr=False,
    )
    total_counterfactual_reach: float

    @property
    def current_player(self) -> int:
        return CHANCE_PLAYER

    def legal_actions(self) -> tuple[Action, ...]:
        return ()

    def chance_outcomes(self) -> tuple[tuple[int, float], ...]:
        return tuple(
            (index, root.counterfactual_reach / self.total_counterfactual_reach)
            for index, root in enumerate(self.roots)
        )

    def apply_action(self, action: Action) -> GameState:
        if not isinstance(action, int) or action not in range(len(self.roots)):
            raise ValueError(f"invalid counterfactual-root outcome {action!r}")
        return self.roots[action].state

    def information_state_key(self, player: int) -> str:
        raise ValueError("counterfactual-root chance state has no information set")

    def returns(self) -> tuple[float, ...]:
        raise ValueError("counterfactual-root chance state is not terminal")


@dataclass(frozen=True, slots=True)
class _RootDistributionGame:
    roots: tuple[CounterfactualRoot, ...]
    total_counterfactual_reach: float
    num_players: int = 2

    def initial_state(self) -> GameState:
        return _RootDistributionState(
            self.roots,
            self.total_counterfactual_reach,
        )


@dataclass(frozen=True, slots=True)
class _ScaledSubgameState:
    base: GameState = field(compare=False, hash=False, repr=False)
    scale: float

    @property
    def current_player(self) -> int:
        return self.base.current_player

    def legal_actions(self) -> tuple[Action, ...]:
        return tuple(self.base.legal_actions())

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        return tuple(self.base.chance_outcomes())

    def apply_action(self, action: Action) -> GameState:
        return _ScaledSubgameState(self.base.apply_action(action), self.scale)

    def information_state_key(self, player: int) -> str:
        return self.base.information_state_key(player)

    def returns(self) -> tuple[float, ...]:
        return tuple(self.scale * value for value in self.base.returns())


@dataclass(frozen=True, slots=True)
class _GadgetTerminalState:
    utilities: tuple[float, float]

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER

    def legal_actions(self) -> tuple[Action, ...]:
        return ()

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        return ()

    def apply_action(self, action: Action) -> GameState:
        raise ValueError("cannot act in a gadget terminal state")

    def information_state_key(self, player: int) -> str:
        raise ValueError("gadget terminal state has no information set")

    def returns(self) -> tuple[float, float]:
        return self.utilities


@dataclass(frozen=True, slots=True)
class _OpponentChoiceState:
    root: CounterfactualRoot = field(compare=False, hash=False, repr=False)
    entry: FrontierEntry
    resolver_player: int
    opponent_player: int
    scale: float

    @property
    def current_player(self) -> int:
        return self.opponent_player

    def legal_actions(self) -> tuple[str, str]:
        return (TERMINATE, FOLLOW)

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        return ()

    def apply_action(self, action: Action) -> GameState:
        if action == FOLLOW:
            return _ScaledSubgameState(self.root.state, self.scale)
        if action != TERMINATE:
            raise ValueError(f"invalid resolving-gadget action {action!r}")
        utilities = [0.0, 0.0]
        utilities[self.opponent_player] = self.entry.terminate_utility
        utilities[self.resolver_player] = -self.entry.terminate_utility
        return _GadgetTerminalState((utilities[0], utilities[1]))

    def information_state_key(self, player: int) -> str:
        if player != self.opponent_player:
            raise ValueError("only the opponent acts at a gadget choice state")
        return self.entry.key

    def returns(self) -> tuple[float, ...]:
        raise ValueError("opponent choice state is not terminal")


@dataclass(frozen=True, slots=True)
class _GadgetChanceState:
    frontier: CounterfactualFrontier = field(
        compare=False,
        hash=False,
        repr=False,
    )

    @property
    def current_player(self) -> int:
        return CHANCE_PLAYER

    def legal_actions(self) -> tuple[Action, ...]:
        return ()

    def chance_outcomes(self) -> tuple[tuple[int, float], ...]:
        total = self.frontier.total_counterfactual_reach
        return tuple(
            (index, root.counterfactual_reach / total)
            for index, root in enumerate(self.frontier.roots)
        )

    def apply_action(self, action: Action) -> GameState:
        if not isinstance(action, int) or action not in range(len(self.frontier.roots)):
            raise ValueError(f"invalid resolving-gadget chance outcome {action!r}")
        root = self.frontier.roots[action]
        entries = {entry.key: entry for entry in self.frontier.entries}
        return _OpponentChoiceState(
            root=root,
            entry=entries[root.opponent_augmented_key],
            resolver_player=self.frontier.resolver_player,
            opponent_player=self.frontier.opponent_player,
            scale=self.frontier.total_counterfactual_reach,
        )

    def information_state_key(self, player: int) -> str:
        raise ValueError("resolving-gadget chance state has no information set")

    def returns(self) -> tuple[float, ...]:
        raise ValueError("resolving-gadget chance state is not terminal")


@dataclass(frozen=True, slots=True)
class ResolvingGadgetGame:
    """Two-player zero-sum terminate/follow resolving game."""

    frontier: CounterfactualFrontier
    num_players: int = 2

    def initial_state(self) -> GameState:
        return _GadgetChanceState(self.frontier)


def _augmented_root_key(state: KuhnState, opponent: int) -> str:
    if state.cards is None:
        raise ValueError("a Kuhn subgame root must follow the deal")
    public = "/".join(f"p{seat}:{action}" for seat, action in state.history)
    if not public:
        public = "root"
    return f"safe-root|p{opponent}|card={state.cards[opponent]}|history={public}"


def _counterfactual_roots(
    game: KuhnPoker,
    policy: Policy,
    history: PublicHistory,
    opponent: int,
) -> tuple[CounterfactualRoot, ...]:
    if history not in public_histories(game):
        raise ValueError(f"unknown public decision history {history!r}")
    roots: list[CounterfactualRoot] = []

    def walk(
        state: KuhnState,
        chance_reach: float,
        player_reaches: tuple[float, float],
    ) -> None:
        if state.cards is not None and state.history == history:
            counterfactual_reach = chance_reach * prod(
                reach
                for player, reach in enumerate(player_reaches)
                if player != opponent
            )
            if counterfactual_reach > 0.0:
                roots.append(
                    CounterfactualRoot(
                        state=state,
                        opponent_augmented_key=_augmented_root_key(state, opponent),
                        counterfactual_reach=counterfactual_reach,
                    )
                )
            return

        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, probability in state.chance_outcomes():
                walk(
                    state.apply_action(action),
                    chance_reach * probability,
                    player_reaches,
                )
            return

        if len(state.history) >= len(history):
            return
        if state.history != history[: len(state.history)]:
            return
        actions = tuple(state.legal_actions())
        distribution = policy_distribution(
            policy,
            state.information_state_key(acting),
            actions,
        )
        required_seat, required_action = history[len(state.history)]
        if required_seat != acting or required_action not in actions:
            return
        child_reaches = list(player_reaches)
        child_reaches[acting] *= distribution[required_action]
        walk(
            state.apply_action(required_action),
            chance_reach,
            (child_reaches[0], child_reaches[1]),
        )

    walk(game.initial_state(), 1.0, (1.0, 1.0))
    return tuple(sorted(roots, key=lambda root: repr(root.state)))


def _counterfactual_best_response_values(
    roots: tuple[CounterfactualRoot, ...],
    total_counterfactual_reach: float,
    opponent: int,
    resolver_policy: Policy,
) -> dict[str, float]:
    root_game = _RootDistributionGame(roots, total_counterfactual_reach)
    _, selected_actions = best_response(root_game, resolver_policy, opponent)
    opponent_information_sets = collect_information_sets(root_game, opponent)
    response_policy: Policy = {
        key: dict(distribution) for key, distribution in resolver_policy.items()
    }
    for key, action in selected_actions.items():
        actions = opponent_information_sets[key]
        response_policy[key] = {
            candidate: float(candidate == action) for candidate in actions
        }

    values: dict[str, float] = {}
    for root in roots:
        continuation = expected_utilities_from_state(
            2,
            root.state,
            response_policy,
        )[opponent]
        values[root.opponent_augmented_key] = (
            values.get(root.opponent_augmented_key, 0.0)
            + root.counterfactual_reach * continuation
        )
    return values


def build_counterfactual_frontier(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
) -> CounterfactualFrontier:
    """Build exact blueprint opponent-CBR values at a public boundary."""

    if game.num_players != 2:
        raise ValueError("safe resolving control requires a two-player game")
    if resolver_player not in range(2):
        raise ValueError(f"invalid resolver player {resolver_player}")
    opponent = 1 - resolver_player
    roots = _counterfactual_roots(game, blueprint, history, opponent)
    total_reach = sum(root.counterfactual_reach for root in roots)
    if total_reach <= 0.0:
        raise ZeroCounterfactualReachError(
            "public boundary has zero opponent-counterfactual reach"
        )
    values = _counterfactual_best_response_values(
        roots,
        total_reach,
        opponent,
        blueprint,
    )
    grouped_reach: dict[str, float] = {}
    grouped_states: dict[str, int] = {}
    for root in roots:
        key = root.opponent_augmented_key
        grouped_reach[key] = grouped_reach.get(key, 0.0) + root.counterfactual_reach
        grouped_states[key] = grouped_states.get(key, 0) + 1

    entries = tuple(
        FrontierEntry(
            key=key,
            counterfactual_reach=grouped_reach[key],
            blueprint_cbr_value=values[key],
            terminate_utility=total_reach * values[key] / grouped_reach[key],
            concrete_states=grouped_states[key],
        )
        for key in sorted(grouped_reach)
    )
    if any(
        not isfinite(value)
        for entry in entries
        for value in (
            entry.counterfactual_reach,
            entry.blueprint_cbr_value,
            entry.terminate_utility,
        )
    ):
        raise ValueError("counterfactual frontier contains a non-finite value")
    return CounterfactualFrontier(
        history=history,
        resolver_player=resolver_player,
        opponent_player=opponent,
        total_counterfactual_reach=total_reach,
        roots=roots,
        entries=entries,
    )


def counterfactual_best_response_values(
    frontier: CounterfactualFrontier,
    resolver_policy: Policy,
) -> dict[str, float]:
    """Evaluate exact opponent CBR values using the frontier's fixed trunk reach."""

    return _counterfactual_best_response_values(
        frontier.roots,
        frontier.total_counterfactual_reach,
        frontier.opponent_player,
        resolver_policy,
    )


def resolve_subgame_safely(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
    *,
    solver_name: str = "cfr_plus",
    search_iterations: int = 1_000,
) -> SafeResolveResult:
    """Solve one gadget and deploy only the resolver's subgame strategy.

    Full-game exploitability is intentionally absent from construction. The
    returned frontier violation is an exact one-sided finite-solver residual;
    experiments may compare its implied bound with the hidden full-game target.
    """

    if solver_name not in SOLVERS:
        raise ValueError(f"unsupported search solver {solver_name!r}")
    if search_iterations <= 0:
        raise ValueError("search_iterations must be positive")

    initialization_start = time.perf_counter()
    frontier = build_counterfactual_frontier(
        game,
        blueprint,
        history,
        resolver_player,
    )
    gadget = ResolvingGadgetGame(frontier)
    solver = TabularCFR(gadget, variant=solver_name)  # type: ignore[arg-type]
    initialization_seconds = time.perf_counter() - initialization_start

    iteration_start = time.perf_counter()
    solver.run(search_iterations)
    iteration_seconds = time.perf_counter() - iteration_start
    gadget_policy = solver.average_strategy()

    certificate_start = time.perf_counter()
    resolver_information_sets = collect_information_sets(gadget, resolver_player)
    if not resolver_information_sets:
        raise ValueError("subgame contains no resolver information sets")
    missing = set(resolver_information_sets) - set(gadget_policy)
    if missing:
        raise ValueError(f"solver omitted resolver information sets {sorted(missing)!r}")
    resolved_policy: Policy = {
        key: dict(distribution) for key, distribution in blueprint.items()
    }
    for key in resolver_information_sets:
        resolved_policy[key] = dict(gadget_policy[key])

    candidate_values = counterfactual_best_response_values(
        frontier,
        resolved_policy,
    )
    comparisons = tuple(
        FrontierComparison(
            key=entry.key,
            blueprint_cbr_value=entry.blueprint_cbr_value,
            candidate_cbr_value=candidate_values[entry.key],
            positive_violation=max(
                0.0,
                candidate_values[entry.key] - entry.blueprint_cbr_value,
            ),
        )
        for entry in frontier.entries
    )
    total_violation = sum(item.positive_violation for item in comparisons)
    gadget_evaluation = evaluate_profile(gadget, gadget_policy)
    opponent_best_response_value = gadget_evaluation.best_response_values[
        frontier.opponent_player
    ]
    security_residual = max(
        0.0,
        opponent_best_response_value - frontier.opponent_gadget_value,
    )
    if abs(security_residual - total_violation) > 1e-10:
        raise AssertionError(
            "gadget security residual does not equal frontier violation: "
            f"{security_residual} versus {total_violation}"
        )
    certificate_seconds = time.perf_counter() - certificate_start

    return SafeResolveResult(
        policy=resolved_policy,
        frontier=frontier,
        comparisons=comparisons,
        resolver_information_sets=len(resolver_information_sets),
        solver_name=solver.variant,
        solver_iterations=search_iterations,
        initialization_seconds=initialization_seconds,
        iteration_seconds=iteration_seconds,
        certificate_seconds=certificate_seconds,
        gadget_evaluation=gadget_evaluation,
        gadget_opponent_best_response_value=opponent_best_response_value,
        gadget_opponent_security_residual=security_residual,
        total_positive_frontier_violation=total_violation,
        max_positive_frontier_violation=max(
            (item.positive_violation for item in comparisons),
            default=0.0,
        ),
    )


def resolve_all_public_histories_safely(
    game: KuhnPoker,
    blueprint: Policy,
    *,
    solver_name: str = "cfr_plus",
    search_iterations: int = 1_000,
    max_deployed_frontier_violation: float | None = None,
) -> SafeContinualResolveResult:
    """Compose acting-player safe resolves from public roots to descendants.

    Every boundary is solved against the strategy produced by its ancestors.
    A later nested solve may overwrite a descendant strategy from an earlier
    solve, but its new certificate is relative to that current strategy. The
    sum of one-sided residual bounds therefore certifies the final profile.
    """

    if game.num_players != 2:
        raise ValueError("safe continual resolving requires a two-player game")
    if solver_name not in SOLVERS:
        raise ValueError(f"unsupported search solver {solver_name!r}")
    if search_iterations <= 0:
        raise ValueError("search_iterations must be positive")
    if max_deployed_frontier_violation is not None and (
        not isfinite(max_deployed_frontier_violation)
        or max_deployed_frontier_violation < 0.0
    ):
        raise ValueError(
            "max_deployed_frontier_violation must be finite and nonnegative"
        )

    composed: Policy = {
        key: dict(distribution) for key, distribution in blueprint.items()
    }
    histories = public_histories(game)
    records: list[SafePublicResolveRecord] = []
    skipped: list[PublicHistory] = []
    for history in histories:
        belief = public_belief(game, composed, history)
        public_reach = 0.0 if belief is None else belief.public_reach_probability
        if belief is None:
            structural_belief = public_belief(game, {}, history)
            if structural_belief is None:
                raise AssertionError("uniform policy cannot reach a legal history")
            resolver_player = structural_belief.acting_player
        else:
            resolver_player = belief.acting_player
        try:
            result = resolve_subgame_safely(
                game,
                composed,
                history,
                resolver_player,
                solver_name=solver_name,
                search_iterations=search_iterations,
            )
        except ZeroCounterfactualReachError:
            skipped.append(history)
            continue

        candidate_deployed = (
            max_deployed_frontier_violation is None
            or result.total_positive_frontier_violation
            <= max_deployed_frontier_violation
        )
        records.append(
            SafePublicResolveRecord(
                history=history,
                resolver_player=resolver_player,
                public_reach_probability=public_reach,
                opponent_counterfactual_reach=(
                    result.frontier.total_counterfactual_reach
                ),
                frontier_information_sets=len(result.frontier.entries),
                resolver_information_sets=result.resolver_information_sets,
                search_seconds=result.search_seconds,
                certificate_seconds=result.certificate_seconds,
                candidate_deployed=candidate_deployed,
                gadget_nash_conv=result.gadget_evaluation.nash_conv,
                total_positive_frontier_violation=(
                    result.total_positive_frontier_violation
                ),
                max_positive_frontier_violation=(
                    result.max_positive_frontier_violation
                ),
                exploitability_increase_bound=(
                    result.full_game_exploitability_increase_bound
                    if candidate_deployed
                    else 0.0
                ),
            )
        )
        if candidate_deployed:
            composed = result.policy

    return SafeContinualResolveResult(
        policy=composed,
        records=tuple(records),
        structural_public_histories=len(histories),
        searched_public_histories=len(records),
        skipped_zero_counterfactual_reach_histories=tuple(skipped),
        total_search_seconds=sum(record.search_seconds for record in records),
        total_certificate_seconds=sum(
            record.certificate_seconds for record in records
        ),
        total_decision_compute_seconds=sum(
            record.decision_compute_seconds for record in records
        ),
        expected_search_seconds_per_hand=sum(
            record.public_reach_probability * record.search_seconds
            for record in records
        ),
        expected_certificate_seconds_per_hand=sum(
            record.public_reach_probability * record.certificate_seconds
            for record in records
        ),
        expected_decision_compute_seconds_per_hand=sum(
            record.public_reach_probability * record.decision_compute_seconds
            for record in records
        ),
        expected_public_decisions_per_hand=sum(
            record.public_reach_probability for record in records
        ),
        cumulative_exploitability_increase_bound=sum(
            record.exploitability_increase_bound for record in records
        ),
        max_search_seconds_at_one_public_state=max(
            (record.search_seconds for record in records),
            default=0.0,
        ),
    )
