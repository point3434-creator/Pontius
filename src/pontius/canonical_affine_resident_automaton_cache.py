"""Scale-canonical affine resident automaton bases.

The first affine cache divided terminal payoffs by ``final_pot`` and hashed the
resulting Float64 bytes.  Algebraically equal winner shares can differ by one
ULP after multiply-then-divide at different pot scales.  This additive cache
encodes terminal shares by their exact semantic class: zero or tie
multiplicity ``1..N``.  It remains a subtype of the frozen affine cache, so the
existing contraction and CFR bridge consume it without modification.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Mapping

import numpy as np

from .affine_resident_heterogeneous_leaf_contraction import (
    CuPyAffineAutomatonHalfVectors,
    CuPyAffineResidentAutomatonCache,
    _right_coefficients,
)
from .cupy_sparse_incidence import _cupy_modules
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .open_mode_showdown import _automaton_half_vectors
from .structured_showdown_automaton import StructuredShowdownAutomaton


_SHARE_TOLERANCE = 1e-13


def _canonical_winner_share_codes(
    automaton: StructuredShowdownAutomaton,
) -> np.ndarray:
    """Return zero-or-tie-multiplicity codes for the terminal winner basis."""

    if not np.isfinite(automaton.final_pot) or automaton.final_pot <= 0.0:
        raise ValueError("canonical affine basis requires a positive final pot")
    normalized = np.ascontiguousarray(
        automaton.terminal_winner_values / automaton.final_pot,
        dtype=np.float64,
    )
    candidates = np.asarray(
        [0.0, *(1.0 / multiplicity for multiplicity in range(1, automaton.num_players + 1))],
        dtype=np.float64,
    )
    differences = np.abs(normalized[..., None] - candidates)
    codes = np.argmin(differences, axis=-1).astype(np.int32, copy=False)
    errors = np.take_along_axis(differences, codes[..., None], axis=-1)[..., 0]
    if float(np.max(errors, initial=0.0)) > _SHARE_TOLERANCE:
        raise ValueError("terminal winner value is not a semantic tie share")
    return np.ascontiguousarray(codes, dtype=np.int32)


def _canonical_share_values(values: np.ndarray, *, players: int) -> np.ndarray:
    """Snap normalized half-vector values to exact semantic winner shares."""

    candidates = np.asarray(
        [0.0, *(1.0 / multiplicity for multiplicity in range(1, players + 1))],
        dtype=np.float64,
    )
    differences = np.abs(values[..., None] - candidates)
    codes = np.argmin(differences, axis=-1)
    errors = np.take_along_axis(differences, codes[..., None], axis=-1)[..., 0]
    if float(np.max(errors, initial=0.0)) > _SHARE_TOLERANCE:
        raise ValueError("affine half vector is not a semantic tie share")
    return np.ascontiguousarray(candidates[codes], dtype=np.float64)


def canonical_affine_basis_digest(
    automaton: StructuredShowdownAutomaton,
) -> str:
    """Identify the exact amount-independent semantic basis."""

    digest = hashlib.sha256()
    digest.update(
        repr(
            (
                automaton.shape,
                automaton.contenders,
                automaton.target_player,
                automaton.constant_winner_shortcut,
            )
        ).encode("utf-8")
    )
    for values in (
        *automaton.transitions,
        *automaton.bond_states,
        _canonical_winner_share_codes(automaton),
    ):
        digest.update(repr((values.shape, values.dtype.str)).encode("ascii"))
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


class CuPyCanonicalAffineResidentAutomatonCache(
    CuPyAffineResidentAutomatonCache
):
    """Affine cache grouped by scale-canonical semantic winner shares."""

    @classmethod
    def compile(
        cls,
        workspace: OpenModeFactorTTWorkspace,
        automata: Mapping[str, StructuredShowdownAutomaton],
        *,
        target_seat: int,
    ) -> CuPyCanonicalAffineResidentAutomatonCache:
        shape = workspace.topology.base.hand_counts
        if isinstance(target_seat, bool) or target_seat not in range(len(shape)):
            raise ValueError("canonical affine resident target is outside the hand axes")
        if not automata:
            raise ValueError("canonical affine cache requires a terminal library")
        unique = {id(automaton): automaton for automaton in automata.values()}
        if any(automaton.shape != shape for automaton in unique.values()):
            raise ValueError("canonical affine automaton axes differ from workspace")
        if any(automaton.target_player != target_seat for automaton in unique.values()):
            raise ValueError("canonical affine automata differ from the target seat")

        wall_started = time.perf_counter()
        half_started = time.perf_counter()
        groups: dict[str, list[tuple[int, StructuredShowdownAutomaton]]] = {}
        for identifier, automaton in unique.items():
            groups.setdefault(canonical_affine_basis_digest(automaton), []).append(
                (identifier, automaton)
            )

        host_bases: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        host_coefficients: dict[int, np.ndarray] = {}
        topology_by_automaton: dict[int, str] = {}
        for key, rows in groups.items():
            representative = rows[0][1]
            left, right = _automaton_half_vectors(representative, workspace)
            right_basis = np.empty_like(right)
            if representative.constant_winner_shortcut:
                right_basis.fill(1.0)
            else:
                state_rank = right.shape[1] - 1
                normalized = right[:, :state_rank] / representative.final_pot
                right_basis[:, :state_rank] = _canonical_share_values(
                    normalized,
                    players=representative.num_players,
                )
                right_basis[:, state_rank] = 1.0
            right_basis = np.ascontiguousarray(right_basis, dtype=np.float64)
            host_bases[key] = (
                np.ascontiguousarray(left, dtype=np.float64),
                right_basis,
            )
            for row_index, (identifier, automaton) in enumerate(rows):
                if canonical_affine_basis_digest(automaton) != key:
                    raise AssertionError("canonical affine grouping is inconsistent")
                coefficients = _right_coefficients(automaton, right.shape[1])
                if coefficients.shape != (right.shape[1],):
                    raise AssertionError("canonical affine coefficient width differs")
                if row_index == 0:
                    member_left, member_right = left, right
                else:
                    member_left, member_right = _automaton_half_vectors(
                        automaton,
                        workspace,
                    )
                if not np.allclose(member_left, left, atol=1e-13, rtol=0.0):
                    raise AssertionError("canonical affine left basis differs in group")
                reconstructed = right_basis * coefficients[None, :]
                if not np.allclose(
                    reconstructed,
                    member_right,
                    atol=1e-13,
                    rtol=0.0,
                ):
                    raise AssertionError(
                        "canonical affine member failed reconstruction"
                    )
                host_coefficients[identifier] = coefficients
                topology_by_automaton[identifier] = key
        half_prepare_ms = (time.perf_counter() - half_started) * 1000.0

        cp, _ = _cupy_modules()
        upload_started = time.perf_counter()
        device_bases = {
            key: (cp.asarray(left), cp.asarray(right))
            for key, (left, right) in host_bases.items()
        }
        device_coefficients = {
            identifier: cp.asarray(values)
            for identifier, values in host_coefficients.items()
        }
        cp.cuda.runtime.deviceSynchronize()
        upload_ms = (time.perf_counter() - upload_started) * 1000.0
        refs = {
            identifier: CuPyAffineAutomatonHalfVectors(
                topology_key=topology_by_automaton[identifier],
                left_basis=device_bases[topology_by_automaton[identifier]][0],
                right_basis=device_bases[topology_by_automaton[identifier]][1],
                right_coefficients=device_coefficients[identifier],
                middle_rank=int(device_coefficients[identifier].shape[0]),
            )
            for identifier in unique
        }
        ranks = tuple(ref.middle_rank for ref in refs.values())
        basis_bytes = sum(
            int(left.nbytes + right.nbytes) for left, right in device_bases.values()
        )
        coefficient_bytes = sum(
            int(values.nbytes) for values in device_coefficients.values()
        )
        raw_equivalent = sum(
            int(ref.left_basis.nbytes + ref.right_basis.nbytes)
            for ref in refs.values()
        )
        pool = cp.get_default_memory_pool()
        return cls(
            topology=workspace.topology,
            target_seat=target_seat,
            half_vectors=refs,
            automaton_ids=frozenset(unique),
            unique_automata=len(unique),
            shared_topologies=len(device_bases),
            total_middle_rank=sum(ranks),
            stored_topology_middle_rank=sum(
                int(right.shape[1]) for _, right in device_bases.values()
            ),
            maximum_middle_rank=max(ranks),
            half_prepare_ms=half_prepare_ms,
            upload_ms=upload_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            basis_numeric_bytes=basis_bytes,
            coefficient_numeric_bytes=coefficient_bytes,
            numeric_bytes=basis_bytes + coefficient_bytes,
            raw_equivalent_numeric_bytes=raw_equivalent,
            pool_used_bytes=int(pool.used_bytes()),
            pool_total_bytes=int(pool.total_bytes()),
        )
