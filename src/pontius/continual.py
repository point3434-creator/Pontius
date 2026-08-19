"""Bayesian public-belief composition for small-game continual resolving."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from math import log

from .cfr import TabularCFR
from .depth_limited import DepthLimitedGame, PolicyContinuationValues
from .evaluation import Policy, collect_information_sets, evaluate_profile, policy_distribution
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .kuhn import KuhnPoker, KuhnState
from .policy import interpolate_policy

SOLVERS = {"cfr", "lcfr", "cfr_plus", "dcfr"}
DEPLOYMENT_GATES = {"always", "positive_local_model_gain"}
PublicHistory = tuple[tuple[int, str], ...]


@dataclass(frozen=True, slots=True)
class PublicBelief:
    """Bayesian distribution over concrete states at one public history."""

    history: PublicHistory
    acting_player: int
    public_reach_probability: float
    states: tuple[tuple[KuhnState, float], ...]

    @property
    def effective_state_count(self) -> float:
        return 1.0 / sum(probability**2 for _, probability in self.states)

    @property
    def entropy_nats(self) -> float:
        return -sum(
            probability * log(probability)
            for _, probability in self.states
            if probability > 0.0
        )


@dataclass(frozen=True, slots=True)
class _PublicBeliefRootState:
    states: tuple[KuhnState, ...] = field(compare=False, hash=False, repr=False)
    probabilities: tuple[float, ...]

    @property
    def current_player(self) -> int:
        return CHANCE_PLAYER

    def legal_actions(self) -> tuple[Action, ...]:
        return ()

    def chance_outcomes(self) -> tuple[tuple[int, float], ...]:
        return tuple(enumerate(self.probabilities))

    def apply_action(self, action: Action) -> GameState:
        if not isinstance(action, int) or action not in range(len(self.states)):
            raise ValueError(f"invalid public-belief root outcome {action!r}")
        return self.states[action]

    def information_state_key(self, player: int) -> str:
        raise ValueError("public-belief chance root has no information state")

    def returns(self) -> tuple[float, ...]:
        raise ValueError("public-belief chance root is not terminal")


@dataclass(frozen=True, slots=True)
class PublicBeliefGame:
    """A subgame whose chance root samples the posterior concrete state."""

    num_players: int
    belief: PublicBelief

    def __post_init__(self) -> None:
        if self.num_players < 2:
            raise ValueError("num_players must be at least two")
        if not self.belief.states:
            raise ValueError("public-belief game requires positive-reach states")
        if self.belief.acting_player not in range(self.num_players):
            raise ValueError("belief acting player is invalid")
        probability_mass = sum(probability for _, probability in self.belief.states)
        if abs(probability_mass - 1.0) > 1e-12:
            raise ValueError("public-belief probabilities must sum to one")
        for state, probability in self.belief.states:
            if probability <= 0.0:
                raise ValueError("public-belief outcomes must have positive probability")
            if state.num_players != self.num_players:
                raise ValueError("public-belief state player count mismatch")
            if state.history != self.belief.history:
                raise ValueError("public-belief states must share one public history")
            if state.current_player != self.belief.acting_player:
                raise ValueError("public-belief states must share one acting player")

    def initial_state(self) -> GameState:
        return _PublicBeliefRootState(
            states=tuple(state for state, _ in self.belief.states),
            probabilities=tuple(probability for _, probability in self.belief.states),
        )


@dataclass(frozen=True, slots=True)
class PublicResolveRecord:
    history: PublicHistory
    acting_player: int
    public_reach_probability: float
    posterior_states: int
    posterior_effective_states: float
    posterior_entropy_nats: float
    root_information_sets: int
    model_information_sets: int
    candidate_deployed: bool
    search_initialization_seconds: float
    search_iteration_seconds: float
    gate_evaluation_seconds: float
    diagnostic_evaluation_seconds: float
    root_candidate_mean_policy_tv: float
    root_candidate_max_policy_tv: float
    root_candidate_model_nash_conv_improvement: float
    full_local_model_nash_conv_improvement: float

    @property
    def search_seconds(self) -> float:
        return self.search_initialization_seconds + self.search_iteration_seconds


@dataclass(frozen=True, slots=True)
class ContinualResolveResult:
    """A coherent full-game policy plus target-free composition telemetry."""

    policy: Policy = field(compare=False, repr=False)
    records: tuple[PublicResolveRecord, ...]
    structural_public_histories: int
    searched_public_histories: int
    deployed_public_histories: int
    skipped_zero_reach_histories: tuple[PublicHistory, ...]
    searched_information_sets: int
    deployed_information_sets: int
    total_search_seconds: float
    total_gate_evaluation_seconds: float
    total_diagnostic_evaluation_seconds: float
    expected_search_seconds_per_hand: float
    expected_gate_evaluation_seconds_per_hand: float
    expected_public_decisions_per_hand: float
    expected_search_seconds_per_public_decision: float
    max_search_seconds_at_one_public_state: float
    continuation_cache_states: int


def _public_reach_records(
    game: KuhnPoker,
    policy: Policy,
) -> dict[PublicHistory, list[tuple[KuhnState, float]]]:
    records: dict[PublicHistory, list[tuple[KuhnState, float]]] = {}

    def walk(state: KuhnState, reach: float) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probability_mass = sum(probability for _, probability in outcomes)
            if not outcomes or abs(probability_mass - 1.0) > 1e-12:
                raise ValueError("invalid Kuhn chance distribution")
            for action, probability in outcomes:
                child = state.apply_action(action)
                walk(child, reach * probability)
            return

        records.setdefault(state.history, []).append((state, reach))
        actions = tuple(state.legal_actions())
        distribution = policy_distribution(
            policy,
            state.information_state_key(acting),
            actions,
        )
        for action, probability in distribution.items():
            walk(state.apply_action(action), reach * probability)

    walk(game.initial_state(), 1.0)
    return records


def public_histories(game: KuhnPoker) -> tuple[PublicHistory, ...]:
    """Return every structurally legal public decision history."""

    records = _public_reach_records(game, {})
    return tuple(sorted(records, key=lambda history: (len(history), history)))


def public_belief(
    game: KuhnPoker,
    policy: Policy,
    history: PublicHistory,
) -> PublicBelief | None:
    """Condition concrete states on reaching ``history`` under ``policy``."""

    records = _public_reach_records(game, policy)
    if history not in records:
        raise ValueError(f"unknown public decision history {history!r}")
    weighted_states = records[history]
    acting_players = {state.current_player for state, _ in weighted_states}
    if len(acting_players) != 1:
        raise ValueError("public history does not identify one acting player")
    public_reach = sum(weight for _, weight in weighted_states)
    if public_reach <= 0.0:
        return None
    states = tuple(
        (state, weight / public_reach)
        for state, weight in sorted(weighted_states, key=lambda item: repr(item[0]))
        if weight > 0.0
    )
    return PublicBelief(
        history=history,
        acting_player=next(iter(acting_players)),
        public_reach_probability=public_reach,
        states=states,
    )


def _information_sets(game: PublicBeliefGame | DepthLimitedGame) -> dict[str, tuple[Action, ...]]:
    result: dict[str, tuple[Action, ...]] = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            previous = result.setdefault(key, actions)
            if previous != actions:
                raise ValueError(f"information-set collision for {key!r}")
    return result


def _root_information_sets(belief: PublicBelief) -> dict[str, tuple[Action, ...]]:
    result: dict[str, tuple[Action, ...]] = {}
    for state, _ in belief.states:
        actions = tuple(state.legal_actions())
        key = state.information_state_key(belief.acting_player)
        previous = result.setdefault(key, actions)
        if previous != actions:
            raise ValueError(f"root information-set collision for {key!r}")
    return result


def _policy_distance(
    left: Policy,
    right: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> tuple[float, float]:
    distances = []
    for key, actions in information_sets.items():
        left_distribution = policy_distribution(left, key, actions)
        right_distribution = policy_distribution(right, key, actions)
        distances.append(
            0.5
            * sum(
                abs(left_distribution[action] - right_distribution[action])
                for action in actions
            )
        )
    if not distances:
        raise ValueError("policy distance requires information sets")
    return sum(distances) / len(distances), max(distances)


def resolve_all_public_histories(
    game: KuhnPoker,
    blueprint: Policy,
    *,
    solver_name: str = "lcfr",
    search_iterations: int = 100,
    depth_limit: int = 2,
    in_search_blueprint_weight: float = 0.99,
    output_candidate_weight: float = 1.0,
    warm_start_regret_mass: float | None = None,
    deployment_gate: str = "always",
) -> ContinualResolveResult:
    """Resolve and deploy exactly one root policy at every public history.

    Histories are processed from the root forward. Each posterior therefore
    uses every already-deployed ancestor strategy. Search sees exact blueprint
    continuation values and never sees full-game evaluation or an oracle no-op
    label. This is a Bayesian composition control, not a multiplayer safety
    theorem.
    """

    if solver_name not in SOLVERS:
        raise ValueError(f"unsupported search solver {solver_name!r}")
    if search_iterations <= 0:
        raise ValueError("search_iterations must be positive")
    if depth_limit < 1:
        raise ValueError("depth_limit must be at least one")
    if not 0.0 <= in_search_blueprint_weight <= 1.0:
        raise ValueError("in_search_blueprint_weight must be in [0, 1]")
    if not 0.0 <= output_candidate_weight <= 1.0:
        raise ValueError("output_candidate_weight must be in [0, 1]")
    if warm_start_regret_mass is not None and warm_start_regret_mass <= 0.0:
        raise ValueError("warm_start_regret_mass must be positive or null")
    if deployment_gate not in DEPLOYMENT_GATES:
        raise ValueError(f"unsupported deployment gate {deployment_gate!r}")

    composed: Policy = {
        key: dict(distribution) for key, distribution in blueprint.items()
    }
    histories = public_histories(game)
    continuation_values = PolicyContinuationValues(game.num_players, blueprint)
    records: list[PublicResolveRecord] = []
    skipped: list[PublicHistory] = []
    searched_keys: set[str] = set()
    deployed_keys: set[str] = set()

    for history in histories:
        belief = public_belief(game, composed, history)
        if belief is None:
            skipped.append(history)
            continue
        belief_game = PublicBeliefGame(game.num_players, belief)
        model_game = DepthLimitedGame(
            belief_game,
            depth_limit,
            continuation_values,
        )
        root_information_sets = _root_information_sets(belief)
        overlap = searched_keys & set(root_information_sets)
        if overlap:
            raise ValueError(f"continual composition would overwrite {sorted(overlap)!r}")

        initialization_start = time.perf_counter()
        solver = TabularCFR(
            model_game,
            variant=solver_name,  # type: ignore[arg-type]
            blueprint_policy=blueprint,
            blueprint_weight=in_search_blueprint_weight,
        )
        if warm_start_regret_mass is not None:
            solver.warm_start(blueprint, warm_start_regret_mass)
        initialization_seconds = time.perf_counter() - initialization_start
        iteration_start = time.perf_counter()
        solver.run(search_iterations)
        iteration_seconds = time.perf_counter() - iteration_start

        candidate = solver.average_strategy()
        local_information_sets = _information_sets(model_game)
        root_candidate = {
            key: candidate[key]
            for key in root_information_sets
            if key in candidate
        }
        if set(root_candidate) != set(root_information_sets):
            missing = set(root_information_sets) - set(root_candidate)
            raise ValueError(f"solver omitted root information sets {sorted(missing)!r}")
        deployed = interpolate_policy(
            composed,
            root_candidate,
            root_information_sets,
            output_candidate_weight,
        )
        local_candidate = interpolate_policy(
            composed,
            candidate,
            local_information_sets,
            output_candidate_weight,
        )

        gate_start = time.perf_counter()
        baseline_evaluation = evaluate_profile(model_game, composed)
        deployed_evaluation = evaluate_profile(model_game, deployed)
        gate_seconds = time.perf_counter() - gate_start
        diagnostic_start = time.perf_counter()
        local_candidate_evaluation = evaluate_profile(model_game, local_candidate)
        diagnostic_seconds = time.perf_counter() - diagnostic_start
        mean_tv, max_tv = _policy_distance(
            deployed,
            composed,
            root_information_sets,
        )
        root_model_gain = (
            baseline_evaluation.nash_conv - deployed_evaluation.nash_conv
        )
        candidate_deployed = (
            deployment_gate == "always" or root_model_gain > 0.0
        )
        records.append(
            PublicResolveRecord(
                history=history,
                acting_player=belief.acting_player,
                public_reach_probability=belief.public_reach_probability,
                posterior_states=len(belief.states),
                posterior_effective_states=belief.effective_state_count,
                posterior_entropy_nats=belief.entropy_nats,
                root_information_sets=len(root_information_sets),
                model_information_sets=len(local_information_sets),
                candidate_deployed=candidate_deployed,
                search_initialization_seconds=initialization_seconds,
                search_iteration_seconds=iteration_seconds,
                gate_evaluation_seconds=gate_seconds,
                diagnostic_evaluation_seconds=diagnostic_seconds,
                root_candidate_mean_policy_tv=mean_tv,
                root_candidate_max_policy_tv=max_tv,
                root_candidate_model_nash_conv_improvement=root_model_gain,
                full_local_model_nash_conv_improvement=(
                    baseline_evaluation.nash_conv
                    - local_candidate_evaluation.nash_conv
                ),
            )
        )
        searched_keys.update(root_information_sets)
        if candidate_deployed:
            composed = deployed
            deployed_keys.update(root_information_sets)

    total_search_seconds = sum(record.search_seconds for record in records)
    expected_search_seconds = sum(
        record.public_reach_probability * record.search_seconds
        for record in records
    )
    expected_gate_seconds = sum(
        record.public_reach_probability * record.gate_evaluation_seconds
        for record in records
    )
    expected_decisions = sum(record.public_reach_probability for record in records)
    return ContinualResolveResult(
        policy=composed,
        records=tuple(records),
        structural_public_histories=len(histories),
        searched_public_histories=len(records),
        deployed_public_histories=sum(
            record.candidate_deployed for record in records
        ),
        skipped_zero_reach_histories=tuple(skipped),
        searched_information_sets=len(searched_keys),
        deployed_information_sets=len(deployed_keys),
        total_search_seconds=total_search_seconds,
        total_gate_evaluation_seconds=sum(
            record.gate_evaluation_seconds for record in records
        ),
        total_diagnostic_evaluation_seconds=sum(
            record.diagnostic_evaluation_seconds for record in records
        ),
        expected_search_seconds_per_hand=expected_search_seconds,
        expected_gate_evaluation_seconds_per_hand=expected_gate_seconds,
        expected_public_decisions_per_hand=expected_decisions,
        expected_search_seconds_per_public_decision=(
            expected_search_seconds / expected_decisions
            if expected_decisions > 0.0
            else 0.0
        ),
        max_search_seconds_at_one_public_state=max(
            (record.search_seconds for record in records),
            default=0.0,
        ),
        continuation_cache_states=continuation_values.cache_size,
    )
