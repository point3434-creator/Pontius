"""Independent reader for ADR-0453 selective-separation evidence.

This module deliberately does not import the producing implementation.  It
reconstructs the reduced exact domains, prices, prefix bounds, searches, and
work receipts from the frozen config before accepting a result.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import heapq
from itertools import combinations
import json
from math import comb
from pathlib import Path
import re


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-selective-certified-separation-v1.json"
)
CONFIG_SHA256 = "80e821708763ee53ad34c19999b838be4f9428113136a315bbe53ed23edef2c0"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_selective_certified_separation_v1.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
SCHEMA = "legal-river-quotient-selective-certified-separation-v1"
WIDTH = 6
MAX_SUBSET_LEVEL = 4
COEFFICIENTS = (30, -120, 360, -720, 720)
DOMAINS = (10, 12)
FAMILIES = (
    "all_zero_tie",
    "all_nonpositive",
    "late_positive",
    "source_base_spike",
    "signed_cancellation_loose_bound",
    "deterministic_mixed_hash",
)
DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0452-retain-the-literal-45-fit-projection-rejection.md",
    "docs/decisions/ADR-0453-preregister-selective-certified-global-separation.md",
    "docs/decisions/ADR-0454-source-seal-selective-certified-global-separation.md",
    "run_legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_selective_certified_separation_runner.py",
    "src/pontius/legal_river_quotient_selective_certified_separation_result.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_outcome.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "experiments/configs/legal-river-quotient-fixed-width-work-comparison-v1.json",
    "tests/test_legal_river_quotient_selective_certified_separation.py",
    "artifacts/work_preflight/.gitattributes",
)


def _canonical_lf(raw: bytes) -> bytes:
    normalized = bytearray()
    index = 0
    while index < len(raw):
        current = raw[index]
        if current == 13 and index + 1 < len(raw) and raw[index + 1] == 10:
            normalized.append(10)
            index += 2
        else:
            normalized.append(current)
            index += 1
    return bytes(normalized)


def _canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"selective-separation reader dependency absent: {path}")
    return sha256(_canonical_lf(path.read_bytes())).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate selective-separation result key: {key}")
        result[key] = value
    return result


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"selective-separation reader {label} must be an object")
    return value


def verify_independent_contract() -> None:
    path = ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if len(raw) > 1_048_576 or sha256(_canonical_lf(raw)).hexdigest() != CONFIG_SHA256:
        raise ValueError("selective-separation reader config identity differs")
    config = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(config, dict):
        raise ValueError("selective-separation reader config is not an object")
    scope = _object(config.get("scope"), "scope")
    price = _object(config.get("exact_price_contract"), "price contract")
    identity = _object(config.get("prospective_identity"), "identity")
    if (
        config.get("schema_version")
        != "legal-river-quotient-selective-certified-separation-config-v1"
        or scope.get("available_card_domains") != list(DOMAINS)
        or scope.get("source_card_width") != WIDTH
        or scope.get("subset_level_maximum") != MAX_SUBSET_LEVEL
        or price.get("level_coefficients_zero_through_four") != list(COEFFICIENTS)
        or tuple(config.get("frozen_families", ())) != FAMILIES
        or identity.get("result_relative_path") != RESULT_RELATIVE_PATH
        or identity.get("result_open_mode") != "exclusive_xb"
    ):
        raise ValueError("selective-separation reader contract differs")


def _mask(cards: Sequence[int]) -> int:
    value = 0
    previous = -1
    for card in cards:
        if isinstance(card, bool) or not isinstance(card, int) or card <= previous:
            raise ValueError("selective-separation reader card sequence differs")
        value |= 1 << card
        previous = card
    return value


def _cards(mask: int) -> tuple[int, ...]:
    if isinstance(mask, bool) or not isinstance(mask, int) or mask < 0:
        raise ValueError("selective-separation reader mask differs")
    return tuple(index for index in range(mask.bit_length()) if mask & (1 << index))


def _colex(mask: int) -> int:
    return sum(comb(card, offset) for offset, card in enumerate(_cards(mask), 1))


def _masks(cards: int, width: int) -> tuple[int, ...]:
    return tuple(
        sorted((_mask(row) for row in combinations(range(cards), width)), key=_colex)
    )


def _subset_domain(cards: int) -> tuple[int, ...]:
    return tuple(mask for level in range(MAX_SUBSET_LEVEL + 1) for mask in _masks(cards, level))


def _source_subsets(source: int) -> tuple[int, ...]:
    rows = []
    current = source
    while True:
        if current.bit_count() <= MAX_SUBSET_LEVEL:
            rows.append(current)
        if current == 0:
            break
        current = (current - 1) & source
    rows.sort(key=lambda value: (value.bit_count(), _colex(value)))
    if len(rows) != 57 or len(set(rows)) != 57:
        raise AssertionError("selective-separation reader 57-subset domain differs")
    return tuple(rows)


def _hash_value(family: str, cards: int, kind: str, mask: int) -> int:
    frame = f"{SCHEMA}|{family}|{cards}|{kind}|{mask.bit_count()}|{mask}".encode("ascii")
    return int.from_bytes(sha256(frame).digest()[:8], "big") % 4097 - 2048


def _instance(cards: int, family: str) -> tuple[tuple[int, ...], tuple[int, ...], dict[int, int], dict[int, int]]:
    sources = _masks(cards, WIDTH)
    subsets = _subset_domain(cards)
    if family == "all_zero_tie":
        bases = {source: 0 for source in sources}
        scalars = {subset: 0 for subset in subsets}
    elif family == "all_nonpositive":
        bases = {source: -1 - _colex(source) % 7 for source in sources}
        scalars = {subset: 0 for subset in subsets}
    elif family == "late_positive":
        bases = {source: -1 for source in sources}
        bases[sources[-1]] = 1
        scalars = {subset: 0 for subset in subsets}
    elif family == "source_base_spike":
        bases = {source: _hash_value(family, cards, "base", source) for source in sources}
        bases[sources[len(sources) // 2]] = 1_000_000_000
        scalars = {subset: _hash_value(family, cards, "subset", subset) for subset in subsets}
    elif family == "signed_cancellation_loose_bound":
        scalars = {
            subset: 1 if COEFFICIENTS[subset.bit_count()] > 0 else -1
            for subset in subsets
        }
        positive_sum = sum(
            comb(WIDTH, level) * abs(COEFFICIENTS[level])
            for level in range(MAX_SUBSET_LEVEL + 1)
        )
        bases = {source: -positive_sum - 1 for source in sources}
    elif family == "deterministic_mixed_hash":
        bases = {source: _hash_value(family, cards, "base", source) for source in sources}
        scalars = {subset: _hash_value(family, cards, "subset", subset) for subset in subsets}
    else:
        raise ValueError("selective-separation reader family differs")
    return sources, subsets, bases, scalars


def _price(source: int, bases: Mapping[int, int], scalars: Mapping[int, int]) -> int:
    value = bases[source]
    rows = _source_subsets(source)
    for subset in rows:
        value += COEFFICIENTS[subset.bit_count()] * scalars[subset]
    return value


def _prefix_data(
    cards: int,
    sources: tuple[int, ...],
    bases: Mapping[int, int],
    scalars: Mapping[int, int],
) -> tuple[dict[tuple[int, ...], dict[str, object]], str]:
    members: dict[tuple[int, ...], list[int]] = defaultdict(list)
    child_sets: dict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    for source in sources:
        row = _cards(source)
        for length in range(WIDTH + 1):
            prefix = row[:length]
            members[prefix].append(source)
            if length < WIDTH:
                child_sets[prefix].add(row[: length + 1])
    nodes: dict[tuple[int, ...], dict[str, object]] = {}
    for prefix, source_rows_list in members.items():
        source_rows = tuple(source_rows_list)
        prefix_mask = _mask(prefix)
        remaining = WIDTH - len(prefix)
        floor = prefix[-1] + 1 if prefix else 0
        upper = max(bases[source] for source in source_rows)
        for subset in scalars:
            term = COEFFICIENTS[subset.bit_count()] * scalars[subset]
            if subset & ~prefix_mask == 0:
                upper += term
                continue
            needed = _cards(subset & ~prefix_mask)
            possible = (
                len(needed) <= remaining
                and all(card >= floor for card in needed)
                and cards - floor - len(needed) >= remaining - len(needed)
            )
            if possible and term > 0:
                upper += term
        children = tuple(sorted(child_sets.get(prefix, ())))
        nodes[prefix] = {
            "prefix": prefix,
            "upper": upper,
            "descendant_count": len(source_rows),
            "first_colex_rank": min(_colex(source) for source in source_rows),
            "children": children,
            "members": source_rows,
        }
    serial = [
        {
            "prefix": node["prefix"],
            "upper": node["upper"],
            "descendant_count": node["descendant_count"],
            "first_colex_rank": node["first_colex_rank"],
            "children": node["children"],
        }
        for _, node in sorted(nodes.items(), key=lambda item: (len(item[0]), item[0]))
    ]
    digest = sha256(json.dumps(serial, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    return nodes, digest


def _search(
    nodes: Mapping[tuple[int, ...], Mapping[str, object]],
    bases: Mapping[int, int],
    scalars: Mapping[int, int],
    cards: int,
    mode: str,
    *,
    allow_pruning: bool = True,
) -> dict[str, object]:
    root = nodes[()]
    frontier: list[tuple[int, int, tuple[int, ...]]] = [
        (-int(root["upper"]), int(root["first_colex_rank"]), ())
    ]
    popped = leaves = reads = pruned = 0
    maximum_frontier = 1
    maximum: int | None = None
    maximizers: list[int] = []
    positives: list[int] = []
    proposal_coordinate: int | None = None
    proposal_price: int | None = None
    stopped = False
    while frontier:
        _, _, prefix = heapq.heappop(frontier)
        popped += 1
        node = nodes[prefix]
        upper = int(node["upper"])
        if allow_pruning:
            if mode == "exact_argmax" and maximum is not None and upper < maximum:
                pruned += int(node["descendant_count"])
                continue
            if mode in ("final_global_closure", "proposal_separation") and upper <= 0:
                pruned += int(node["descendant_count"])
                continue
        children = tuple(tuple(row) for row in node["children"])
        if children:
            for child in children:
                child_node = nodes[child]
                heapq.heappush(
                    frontier,
                    (-int(child_node["upper"]), int(child_node["first_colex_rank"]), child),
                )
            maximum_frontier = max(maximum_frontier, len(frontier))
            continue
        source = _mask(prefix)
        value = _price(source, bases, scalars)
        leaves += 1
        reads += 57
        if maximum is None or value > maximum:
            maximum = value
            maximizers = [source]
        elif value == maximum:
            maximizers.append(source)
        if value > 0:
            positives.append(source)
            if mode == "proposal_separation":
                proposal_coordinate = source
                proposal_price = value
                stopped = True
                break
    total = comb(cards, WIDTH)
    return {
        "mode": mode,
        "allow_pruning": allow_pruning,
        "maximum_price": maximum,
        "maximizers": sorted(maximizers, key=_colex),
        "positive_coordinates": sorted(positives, key=_colex),
        "proposal_coordinate": proposal_coordinate,
        "proposal_price": proposal_price,
        "prefix_nodes_popped": popped,
        "exact_leaf_prices": leaves,
        "selective_subset_scalar_reads": reads,
        "pruned_source_leaves": pruned,
        "visited_source_leaves": leaves,
        "maximum_frontier_nodes": maximum_frontier,
        "complete_domain_covered": not stopped and leaves + pruned == total,
    }


def _sequence_digest(values: Sequence[int]) -> str:
    digest = sha256()
    for value in values:
        encoded = str(value).encode("ascii")
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
    return digest.hexdigest()


def _expected_row(cards: int, family: str) -> dict[str, object]:
    sources, subsets, bases, scalars = _instance(cards, family)
    prices = tuple((source, _price(source, bases, scalars)) for source in sources)
    maximum = max(value for _, value in prices)
    maximizers = tuple(source for source, value in prices if value == maximum)
    positives = tuple(source for source, value in prices if value > 0)
    nodes, node_digest = _prefix_data(cards, sources, bases, scalars)
    for node in nodes.values():
        members = tuple(int(value) for value in node["members"])
        upper = int(node["upper"])
        if any(_price(source, bases, scalars) > upper for source in members):
            raise ArithmeticError("selective-separation reader found a low bound")
        if len(tuple(node["prefix"])) == WIDTH and upper != _price(members[0], bases, scalars):
            raise ArithmeticError("selective-separation reader found a nonexact leaf")
    argmax = _search(nodes, bases, scalars, cards, "exact_argmax")
    closure = _search(nodes, bases, scalars, cards, "final_global_closure")
    proposal = _search(nodes, bases, scalars, cards, "proposal_separation")
    no_prune = _search(
        nodes, bases, scalars, cards, "final_global_closure", allow_pruning=False
    )
    gates = {
        "selective_price_exact": True,
        "node_bounds_conservative": True,
        "leaf_bounds_exact": True,
        "argmax_exact": (
            argmax["maximum_price"] == maximum
            and tuple(argmax["maximizers"]) == maximizers
        ),
        "closure_exact": tuple(closure["positive_coordinates"]) == positives,
        "proposal_sound": (
            (not positives and proposal["proposal_coordinate"] is None)
            or (
                proposal["proposal_coordinate"] in positives
                and isinstance(proposal["proposal_price"], int)
                and int(proposal["proposal_price"]) > 0
            )
        ),
        "domain_covered": bool(argmax["complete_domain_covered"])
        and bool(closure["complete_domain_covered"]),
        "no_prune_control_exact": (
            no_prune["exact_leaf_prices"] == len(sources)
            and no_prune["pruned_source_leaves"] == 0
            and tuple(no_prune["positive_coordinates"]) == positives
        ),
    }
    instance_payload = {
        "available_cards": cards,
        "family": family,
        "source_bases": tuple((source, bases[source]) for source in sources),
        "subset_scalars": tuple((subset, scalars[subset]) for subset in subsets),
    }
    return {
        "available_cards": cards,
        "family": family,
        "instance_sha256": sha256(
            json.dumps(instance_payload, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
        "source_count": len(sources),
        "subset_scalar_count": len(subsets),
        "compiled_node_sha256": node_digest,
        "compile_ledger": {
            "source_base_values_read": len(sources),
            "prefix_nodes_bound": len(nodes),
            "possible_subset_terms_examined_for_bounds": len(nodes) * len(subsets),
            "leaf_bound_equalities": len(sources),
            "descendant_domination_comparisons": (WIDTH + 1) * len(sources),
        },
        "exhaustive": {
            "maximum_price": maximum,
            "maximizer_count": len(maximizers),
            "maximizers_sha256": _sequence_digest(maximizers),
            "positive_count": len(positives),
            "positive_coordinates_sha256": _sequence_digest(positives),
            "exact_leaf_prices": len(sources),
            "selective_subset_scalar_reads": 57 * len(sources),
        },
        "exact_argmax": argmax,
        "final_global_closure": closure,
        "proposal_separation": proposal,
        "unpruned_closure_control": no_prune,
        "gates": gates,
    }


def _claims() -> dict[str, object]:
    return {
        "exact_global_separation_mechanism": True,
        "material_pruning": None,
        "literal_45_fit": None,
        "candidate_selected": None,
        "resolver_iteration_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "blueprint_result": None,
        "poker_strength_result": None,
    }


@dataclass(frozen=True, slots=True)
class ReboundSelectiveSeparation:
    source_commit: str
    terminal: str
    row_count: int
    some_pruning: bool


def rebind_selective_separation_bytes(
    raw: bytes,
    *,
    validate_dependencies: bool = True,
) -> ReboundSelectiveSeparation:
    if type(raw) is not bytes or not raw or len(raw) > 16_777_216:
        raise ValueError("selective-separation result byte envelope differs")
    if b"\r" in raw or not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise ValueError("selective-separation result framing differs")
    try:
        document = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("selective-separation result JSON differs") from error
    if not isinstance(document, dict):
        raise ValueError("selective-separation result is not an object")
    commit = document.get("source_commit")
    if (
        document.get("schema_version")
        != "legal-river-quotient-selective-certified-separation-result-v1"
        or re.fullmatch(r"[0-9a-f]{40}", commit if isinstance(commit, str) else "") is None
        or document.get("config_sha256") != CONFIG_SHA256
    ):
        raise ValueError("selective-separation result identity differs")
    dependencies = _object(document.get("dependency_hashes"), "dependencies")
    if tuple(sorted(dependencies)) != tuple(sorted(DEPENDENCY_RELATIVE_PATHS)):
        raise ValueError("selective-separation dependency domain differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        digest = dependencies.get(relative)
        if re.fullmatch(r"[0-9a-f]{64}", digest if isinstance(digest, str) else "") is None:
            raise ValueError("selective-separation dependency digest differs")
        if validate_dependencies and digest != _canonical_lf_sha256(ROOT / relative):
            raise ValueError(f"selective-separation dependency changed: {relative}")
    rows = document.get("rows")
    if not isinstance(rows, list) or len(rows) != len(DOMAINS) * len(FAMILIES):
        raise ValueError("selective-separation result rows differ")
    expected_rows = [_expected_row(cards, family) for cards in DOMAINS for family in FAMILIES]
    if rows != expected_rows:
        raise ValueError("selective-separation independently reconstructed rows differ")
    some_pruning = any(
        int(_object(row["final_global_closure"], "closure")["pruned_source_leaves"]) > 0
        for row in rows
    )
    terminal = (
        "completed_exact_separation_with_pruning"
        if some_pruning
        else "completed_exact_separation_no_material_pruning"
    )
    if (
        document.get("row_count") != len(rows)
        or document.get("all_gates_passed") is not True
        or document.get("terminal") != terminal
        or document.get("claims") != _claims()
    ):
        raise ValueError("selective-separation result verdict differs")
    return ReboundSelectiveSeparation(str(commit), terminal, len(rows), some_pruning)


def rebind_selective_separation_file(
    path: Path = RESULT_PATH,
) -> ReboundSelectiveSeparation:
    if path != RESULT_PATH:
        raise ValueError("selective-separation result path differs")
    verify_independent_contract()
    return rebind_selective_separation_bytes(path.read_bytes())


__all__ = [
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "ReboundSelectiveSeparation",
    "rebind_selective_separation_bytes",
    "rebind_selective_separation_file",
    "verify_independent_contract",
]
