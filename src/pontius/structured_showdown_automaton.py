"""Exact sparse deterministic automata for multiway showdown payoff tensors."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .tensor_train import TensorTrain
from .tensor_train_algebra import add_tensor_trains

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]
State: TypeAlias = tuple[int, int, int]

_EMPTY_STATE: State = (-1, 0, 0)


def _readonly(values: object, dtype: np.dtype[object]) -> NDArray[object]:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


@dataclass(frozen=True, slots=True)
class StructuredShowdownAutomaton:
    """A sparse TT with one deterministic transition per state and hand."""

    shape: tuple[int, ...]
    contenders: tuple[int, ...]
    target_player: int
    contributed: bool
    final_pot: float
    sunk_value: float
    transitions: tuple[IntArray, ...]
    bond_states: tuple[IntArray, ...]
    terminal_winner_values: FloatArray
    construction_array_shapes: tuple[tuple[int, ...], ...]
    constant_winner_shortcut: bool

    @property
    def num_players(self) -> int:
        return len(self.shape)

    @property
    def state_ranks(self) -> tuple[int, ...]:
        return (1, *(len(states) for states in self.bond_states), 1)

    @property
    def maximum_state_rank(self) -> int:
        return max(self.state_ranks)

    @property
    def transition_records(self) -> int:
        return sum(values.size for values in self.transitions)

    @property
    def runtime_numeric_bytes(self) -> int:
        return (
            sum(values.nbytes for values in self.transitions)
            + self.terminal_winner_values.nbytes
            + np.dtype(np.float64).itemsize
        )

    @property
    def state_metadata_bytes(self) -> int:
        return sum(values.nbytes for values in self.bond_states)

    @property
    def numeric_bytes(self) -> int:
        return self.runtime_numeric_bytes + self.state_metadata_bytes

    @property
    def maximum_construction_array_ndim(self) -> int:
        return max((len(shape) for shape in self.construction_array_shapes), default=0)

    @property
    def maximum_construction_array_elements(self) -> int:
        return max(
            (math.prod(shape) for shape in self.construction_array_shapes),
            default=0,
        )

    @property
    def transition_run_count(self) -> int:
        return sum(_row_run_count(values) for values in self.transitions)

    @property
    def terminal_weight_run_count(self) -> int:
        return _row_run_count(self.terminal_winner_values)

    @property
    def dense_tt_export_bytes(self) -> int:
        """Bytes of the signed dense-core TT produced without SVD."""

        if self.constant_winner_shortcut:
            return sum(size * np.dtype(np.float64).itemsize for size in self.shape)
        ranks = self.state_ranks
        signed_ranks = (1, *(rank + 1 for rank in ranks[1:-1]), 1)
        return sum(
            left * size * right * np.dtype(np.float64).itemsize
            for left, size, right in zip(
                signed_ranks[:-1],
                self.shape,
                signed_ranks[1:],
                strict=True,
            )
        )

    @property
    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(
            repr(
                (
                    self.shape,
                    self.contenders,
                    self.target_player,
                    self.contributed,
                    self.final_pot,
                    self.sunk_value,
                    self.constant_winner_shortcut,
                )
            ).encode("utf-8")
        )
        for values in (*self.transitions, *self.bond_states, self.terminal_winner_values):
            digest.update(repr((values.shape, values.dtype.str)).encode("ascii"))
            digest.update(values.tobytes(order="C"))
        return digest.hexdigest()

    def evaluate_assignments(self, assignments: object) -> FloatArray:
        """Evaluate one or more Cartesian hand-index tuples without densifying."""

        indices = np.ascontiguousarray(assignments, dtype=np.int32)
        if indices.ndim != 2 or indices.shape[1] != self.num_players:
            raise ValueError("showdown assignments must have one column per player")
        if any(
            np.any(indices[:, player] < 0)
            or np.any(indices[:, player] >= self.shape[player])
            for player in range(self.num_players)
        ):
            raise ValueError("showdown assignment index is outside a hand axis")
        state_ids = np.zeros(len(indices), dtype=np.int32)
        for mode, transition in enumerate(self.transitions):
            state_ids = transition[state_ids, indices[:, mode]]
        winner = self.terminal_winner_values[
            state_ids,
            indices[:, self.num_players - 1],
        ]
        return np.ascontiguousarray(winner + self.sunk_value, dtype=np.float64)

    def to_dense(self) -> FloatArray:
        """Materialize a small control tensor; never use this on the wide arm."""

        assignments = np.indices(self.shape, dtype=np.int32).reshape(
            self.num_players,
            -1,
        ).T
        return self.evaluate_assignments(assignments).reshape(self.shape)

    def to_tensor_train(self) -> TensorTrain:
        """Export direct one-hot cores plus a rank-one sunk tensor without SVD."""

        constant = _constant_tensor_train(self.shape, self.sunk_value)
        if self.constant_winner_shortcut:
            return constant
        winner_cores = []
        for mode, transition in enumerate(self.transitions):
            next_rank = len(self.bond_states[mode])
            core = np.zeros(
                (transition.shape[0], transition.shape[1], next_rank),
                dtype=np.float64,
                order="C",
            )
            previous, hands = np.indices(transition.shape, dtype=np.int32)
            core[previous, hands, transition] = 1.0
            winner_cores.append(core)
        winner_cores.append(self.terminal_winner_values[:, :, None])
        winner = TensorTrain(
            shape=self.shape,
            cores=tuple(winner_cores),
            decomposition_singular_values=tuple(
                np.empty(0, dtype=np.float64) for _ in range(self.num_players - 1)
            ),
        )
        return add_tensor_trains(winner, constant)

    def transition_mismatches(self, strength_codes: object) -> int:
        """Independently replay every compiled transition and final output."""

        strengths = _validate_strength_codes(strength_codes)
        if tuple(len(values) for values in strengths) != self.shape:
            raise ValueError("validation strength axes differ from automaton shape")
        if self.constant_winner_shortcut:
            expected_zero = np.zeros_like(self.terminal_winner_values)
            return int(
                any(np.any(values != 0) for values in self.transitions)
                or np.any(self.terminal_winner_values != expected_zero)
            )

        mismatches = 0
        previous_states = np.asarray([_EMPTY_STATE], dtype=np.int32)
        for mode, transition_ids in enumerate(self.transitions):
            next_states = self.bond_states[mode]
            for previous_id, supplied_state in enumerate(previous_states):
                state = tuple(int(value) for value in supplied_state)
                for hand_index, strength in enumerate(strengths[mode]):
                    expected = _advance_state(
                        state,
                        player=mode,
                        strength=int(strength),
                        contenders=self.contenders,
                        target_player=self.target_player,
                    )
                    actual = tuple(
                        int(value)
                        for value in next_states[transition_ids[previous_id, hand_index]]
                    )
                    mismatches += int(actual != expected)
            previous_states = next_states

        final_mode = self.num_players - 1
        for previous_id, supplied_state in enumerate(previous_states):
            state = tuple(int(value) for value in supplied_state)
            for hand_index, strength in enumerate(strengths[final_mode]):
                final_state = _advance_state(
                    state,
                    player=final_mode,
                    strength=int(strength),
                    contenders=self.contenders,
                    target_player=self.target_player,
                )
                expected = self.final_pot * _winner_share(final_state)
                mismatches += int(
                    self.terminal_winner_values[previous_id, hand_index] != expected
                )
        return mismatches


def build_structured_showdown_automaton(
    *,
    strength_codes: object,
    contenders: tuple[int, ...],
    target_player: int,
    contributed: bool,
    pot: float,
    bet_size: float,
) -> StructuredShowdownAutomaton:
    """Compile a showdown payoff without SVD or a Cartesian payoff tensor."""

    strengths = _validate_strength_codes(strength_codes)
    players = len(strengths)
    shape = tuple(len(values) for values in strengths)
    if target_player not in range(players):
        raise ValueError("showdown target player is outside the seat axis")
    if (
        not contenders
        or tuple(sorted(set(contenders))) != contenders
        or any(player not in range(players) for player in contenders)
    ):
        raise ValueError("showdown contenders must be sorted unique player indices")
    if not isinstance(contributed, bool):
        raise ValueError("showdown contributed flag must be Boolean")
    if not math.isfinite(pot) or pot <= 0.0:
        raise ValueError("showdown pot must be finite and positive")
    if not math.isfinite(bet_size) or bet_size < 0.0:
        raise ValueError("showdown bet size must be finite and nonnegative")

    final_pot = pot + (bet_size * len(contenders) if contributed else 0.0)
    sunk_value = -pot / players - (
        bet_size if contributed and target_player in contenders else 0.0
    )
    array_shapes: list[tuple[int, ...]] = []
    if target_player not in contenders:
        transitions = tuple(
            _record_array(
                np.zeros((1, shape[mode]), dtype=np.int32),
                array_shapes,
            )
            for mode in range(players - 1)
        )
        bond_states = tuple(
            _record_array(
                np.asarray([_EMPTY_STATE], dtype=np.int32),
                array_shapes,
            )
            for _ in range(players - 1)
        )
        terminal = _record_array(
            np.zeros((1, shape[-1]), dtype=np.float64),
            array_shapes,
        )
        return StructuredShowdownAutomaton(
            shape=shape,
            contenders=contenders,
            target_player=target_player,
            contributed=contributed,
            final_pot=final_pot,
            sunk_value=sunk_value,
            transitions=transitions,
            bond_states=bond_states,
            terminal_winner_values=terminal,
            construction_array_shapes=tuple(array_shapes),
            constant_winner_shortcut=True,
        )

    current_states: tuple[State, ...] = (_EMPTY_STATE,)
    transitions_list: list[IntArray] = []
    state_tables: list[IntArray] = []
    for mode in range(players - 1):
        next_state_set = {
            _advance_state(
                state,
                player=mode,
                strength=int(strength),
                contenders=contenders,
                target_player=target_player,
            )
            for state in current_states
            for strength in strengths[mode]
        }
        next_states = tuple(sorted(next_state_set, key=_state_sort_key))
        state_to_id = {state: index for index, state in enumerate(next_states)}
        transition = np.empty(
            (len(current_states), shape[mode]),
            dtype=np.int32,
            order="C",
        )
        for previous_id, state in enumerate(current_states):
            transition[previous_id] = tuple(
                state_to_id[
                    _advance_state(
                        state,
                        player=mode,
                        strength=int(strength),
                        contenders=contenders,
                        target_player=target_player,
                    )
                ]
                for strength in strengths[mode]
            )
        transitions_list.append(_record_array(transition, array_shapes))
        state_tables.append(
            _record_array(np.asarray(next_states, dtype=np.int32), array_shapes)
        )
        current_states = next_states

    final_mode = players - 1
    terminal = np.empty(
        (len(current_states), shape[final_mode]),
        dtype=np.float64,
        order="C",
    )
    for previous_id, state in enumerate(current_states):
        terminal[previous_id] = tuple(
            final_pot
            * _winner_share(
                _advance_state(
                    state,
                    player=final_mode,
                    strength=int(strength),
                    contenders=contenders,
                    target_player=target_player,
                )
            )
            for strength in strengths[final_mode]
        )
    terminal = _record_array(terminal, array_shapes)
    return StructuredShowdownAutomaton(
        shape=shape,
        contenders=contenders,
        target_player=target_player,
        contributed=contributed,
        final_pot=final_pot,
        sunk_value=sunk_value,
        transitions=tuple(transitions_list),
        bond_states=tuple(state_tables),
        terminal_winner_values=terminal,
        construction_array_shapes=tuple(array_shapes),
        constant_winner_shortcut=False,
    )


def _validate_strength_codes(supplied: object) -> tuple[IntArray, ...]:
    try:
        raw = tuple(supplied)  # type: ignore[arg-type]
    except TypeError as error:
        raise ValueError("strength codes require one vector per player") from error
    if len(raw) < 2:
        raise ValueError("strength codes require at least two players")
    result = []
    for values in raw:
        array = np.ascontiguousarray(values, dtype=np.int32)
        if array.ndim != 1 or len(array) == 0 or np.any(array < 0):
            raise ValueError("strength codes must be nonempty nonnegative vectors")
        result.append(_readonly(array, np.dtype(np.int32)))
    return tuple(result)  # type: ignore[return-value]


def _advance_state(
    state: State,
    *,
    player: int,
    strength: int,
    contenders: tuple[int, ...],
    target_player: int,
) -> State:
    if player not in contenders:
        return state
    maximum, multiplicity, target_in_argmax = state
    is_target = int(player == target_player)
    if maximum < 0 or strength > maximum:
        return (strength, 1, is_target)
    if strength == maximum:
        return (maximum, multiplicity + 1, int(bool(target_in_argmax or is_target)))
    return state


def _winner_share(state: State) -> float:
    _, multiplicity, target_in_argmax = state
    if not target_in_argmax:
        return 0.0
    if multiplicity <= 0:
        raise AssertionError("winning automaton state has no maximum multiplicity")
    return 1.0 / multiplicity


def _state_sort_key(state: State) -> tuple[int, int, int]:
    return state


def _record_array(
    values: np.ndarray,
    shapes: list[tuple[int, ...]],
) -> NDArray[object]:
    result = _readonly(values, values.dtype)
    shapes.append(tuple(int(size) for size in result.shape))
    return result


def _row_run_count(values: np.ndarray) -> int:
    if values.ndim != 2 or values.shape[1] == 0:
        return 0
    return int(values.shape[0] + np.count_nonzero(values[:, 1:] != values[:, :-1]))


def _constant_tensor_train(shape: tuple[int, ...], value: float) -> TensorTrain:
    cores = [np.ones((1, size, 1), dtype=np.float64) for size in shape]
    cores[-1] *= value
    return TensorTrain(
        shape=shape,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            np.empty(0, dtype=np.float64) for _ in range(len(shape) - 1)
        ),
    )
