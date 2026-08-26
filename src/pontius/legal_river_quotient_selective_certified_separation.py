"""CPU-only exact selective pricing and certified prefix separation.

The module implements ADR-0453's reduced-domain algebraic keystone.  Import is
artifact-, process-, NumPy-, CuPy-, and device-free.  Literal-45 entry points do
not exist here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import heapq
from itertools import combinations
import json
from math import comb
from pathlib import Path
import re
from typing import Literal


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
SCHEMA = "legal-river-quotient-selective-certified-separation-v1"
SOURCE_WIDTH = 6
SUBSET_LEVEL_MAXIMUM = 4
LEVEL_COEFFICIENTS = (30, -120, 360, -720, 720)
DOMAINS = (10, 12)
FAMILIES = (
    "all_zero_tie",
    "all_nonpositive",
    "late_positive",
    "source_base_spike",
    "signed_cancellation_loose_bound",
    "deterministic_mixed_hash",
)
SearchMode = Literal["exact_argmax", "final_global_closure", "proposal_separation"]


def _canonical_lf(raw: bytes) -> bytes:
    output = bytearray()
    cursor = 0
    while cursor < len(raw):
        if raw[cursor : cursor + 2] == bytes((13, 10)):
            output.append(10)
            cursor += 2
        else:
            output.append(raw[cursor])
            cursor += 1
    return bytes(output)


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("selective-separation dependency is absent")
    return sha256(_canonical_lf(path.read_bytes())).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate selective-separation JSON key: {key}")
        output[key] = value
    return output


def load_preregistered_config() -> dict[str, object]:
    path = ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if len(raw) > 1_048_576 or sha256(_canonical_lf(raw)).hexdigest() != CONFIG_SHA256:
        raise ValueError("selective-separation config identity differs")
    parsed = json.loads(raw, object_pairs_hook=_unique_object)
    if (
        not isinstance(parsed, dict)
        or parsed.get("schema_version")
        != "legal-river-quotient-selective-certified-separation-config-v1"
        or parsed.get("evidence_stage")
        != "preregistered_after_adr0452_before_successor_source_result_or_values"
    ):
        raise ValueError("selective-separation config schema differs")
    return parsed


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"selective-separation {label} must be an object")
    return value


def verify_preregistered_contract() -> None:
    parsed = load_preregistered_config()
    parents = _mapping(parsed.get("parents"), label="parents")
    bindings = (
        ("adr0452_relative_path", "adr0452_canonical_lf_sha256"),
        ("projection_outcome_relative_path", "projection_outcome_canonical_lf_sha256"),
        ("exact_integer_operator_relative_path", "exact_integer_operator_canonical_lf_sha256"),
        ("fixed_width_work_relative_path", "fixed_width_work_canonical_lf_sha256"),
        ("fixed_width_config_relative_path", "fixed_width_config_canonical_lf_sha256"),
    )
    for path_key, digest_key in bindings:
        relative = parents.get(path_key)
        if (
            not isinstance(relative, str)
            or canonical_lf_sha256(ROOT / relative) != parents.get(digest_key)
        ):
            raise ValueError(f"selective-separation parent differs: {path_key}")
    artifact_relative = parents.get("retained_projection_relative_path")
    if (
        artifact_relative
        != "artifacts/work_preflight/legal_river_quotient_fixed_width_actual45_fit_projection_v1.jsonl"
        or parents.get("retained_projection_bytes") != 55_997
        or parents.get("retained_projection_raw_sha256")
        != "afebfee99349d1e36077084619fc213dbe2b8eee8da8fe8a55c62cc41b0ececa"
    ):
        raise ValueError("selective-separation retained projection binding differs")
    price = _mapping(parsed.get("exact_price_contract"), label="price contract")
    if (
        price.get("level_coefficients_zero_through_four")
        != list(LEVEL_COEFFICIENTS)
        or price.get("selective_price_must_read_exactly_57_distinct_subset_scalars")
        is not True
    ):
        raise ValueError("selective-separation price constants differ")
    scope = _mapping(parsed.get("scope"), label="scope")
    if (
        scope.get("available_card_domains") != list(DOMAINS)
        or scope.get("source_card_width") != SOURCE_WIDTH
        or scope.get("subset_level_maximum") != SUBSET_LEVEL_MAXIMUM
    ):
        raise ValueError("selective-separation reduced scope differs")
    if tuple(parsed.get("frozen_families", ())) != FAMILIES:
        raise ValueError("selective-separation family order differs")
    identity = _mapping(parsed.get("prospective_identity"), label="identity")
    expected_identity = {
        "source_relative_path": "src/pontius/legal_river_quotient_selective_certified_separation.py",
        "runner_relative_path": "src/pontius/legal_river_quotient_selective_certified_separation_runner.py",
        "reader_relative_path": "src/pontius/legal_river_quotient_selective_certified_separation_result.py",
        "controls_relative_path": "tests/test_legal_river_quotient_selective_certified_separation.py",
        "launcher_relative_path": "run_legal_river_quotient_selective_certified_separation.py",
        "result_relative_path": RESULT_RELATIVE_PATH,
    }
    if any(identity.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("selective-separation prospective identity differs")


def mask_from_cards(cards: Sequence[int]) -> int:
    values = tuple(cards)
    if (
        any(isinstance(card, bool) or not isinstance(card, int) or card < 0 for card in values)
        or tuple(sorted(values)) != values
        or len(set(values)) != len(values)
    ):
        raise ValueError("selective-separation cards differ")
    mask = 0
    for card in values:
        mask |= 1 << card
    return mask


def cards_from_mask(mask: int) -> tuple[int, ...]:
    if isinstance(mask, bool) or not isinstance(mask, int) or mask < 0:
        raise TypeError("selective-separation mask must be nonnegative integer")
    return tuple(card for card in range(mask.bit_length()) if mask & (1 << card))


def colex_rank(mask: int) -> int:
    return sum(comb(card, index + 1) for index, card in enumerate(cards_from_mask(mask)))


def complete_masks(available_cards: int, width: int) -> tuple[int, ...]:
    if (
        isinstance(available_cards, bool)
        or isinstance(width, bool)
        or not isinstance(available_cards, int)
        or not isinstance(width, int)
        or width < 0
        or available_cards < width
    ):
        raise ValueError("selective-separation domain geometry differs")
    masks = [mask_from_cards(row) for row in combinations(range(available_cards), width)]
    return tuple(sorted(masks, key=colex_rank))


def subset_masks(available_cards: int) -> tuple[int, ...]:
    rows = []
    for width in range(SUBSET_LEVEL_MAXIMUM + 1):
        rows.extend(complete_masks(available_cards, width))
    return tuple(rows)


def source_subsets(source_mask: int) -> tuple[int, ...]:
    if source_mask.bit_count() != SOURCE_WIDTH:
        raise ValueError("selective-separation source width differs")
    rows = []
    subset = source_mask
    while True:
        if subset.bit_count() <= SUBSET_LEVEL_MAXIMUM:
            rows.append(subset)
        if subset == 0:
            break
        subset = (subset - 1) & source_mask
    rows.sort(key=lambda mask: (mask.bit_count(), colex_rank(mask)))
    if len(rows) != 57 or len(set(rows)) != 57:
        raise AssertionError("selective-separation source does not have 57 subsets")
    return tuple(rows)


def _hash_integer(family: str, cards: int, kind: str, mask: int) -> int:
    framed = (
        f"{SCHEMA}|{family}|{cards}|{kind}|{mask.bit_count()}|{mask}"
    ).encode("ascii")
    return int.from_bytes(sha256(framed).digest()[:8], "big") % 4097 - 2048


@dataclass(frozen=True, slots=True)
class PriceInstance:
    available_cards: int
    family: str
    source_bases: tuple[tuple[int, int], ...]
    subset_scalars: tuple[tuple[int, int], ...]


def make_instance(available_cards: int, family: str) -> PriceInstance:
    if available_cards not in DOMAINS or family not in FAMILIES:
        raise ValueError("selective-separation frozen instance differs")
    sources = complete_masks(available_cards, SOURCE_WIDTH)
    subsets = subset_masks(available_cards)
    bases: dict[int, int]
    scalar: dict[int, int]
    if family == "all_zero_tie":
        bases = {mask: 0 for mask in sources}
        scalar = {mask: 0 for mask in subsets}
    elif family == "all_nonpositive":
        bases = {mask: -1 - colex_rank(mask) % 7 for mask in sources}
        scalar = {mask: 0 for mask in subsets}
    elif family == "late_positive":
        bases = {mask: -1 for mask in sources}
        bases[sources[-1]] = 1
        scalar = {mask: 0 for mask in subsets}
    elif family == "source_base_spike":
        bases = {mask: _hash_integer(family, available_cards, "base", mask) for mask in sources}
        bases[sources[len(sources) // 2]] = 1_000_000_000
        scalar = {
            mask: _hash_integer(family, available_cards, "subset", mask)
            for mask in subsets
        }
    elif family == "signed_cancellation_loose_bound":
        scalar = {
            mask: 1 if LEVEL_COEFFICIENTS[mask.bit_count()] > 0 else -1
            for mask in subsets
        }
        exact_positive_sum = sum(
            comb(SOURCE_WIDTH, level) * abs(LEVEL_COEFFICIENTS[level])
            for level in range(SUBSET_LEVEL_MAXIMUM + 1)
        )
        bases = {mask: -exact_positive_sum - 1 for mask in sources}
    else:
        bases = {
            mask: _hash_integer(family, available_cards, "base", mask)
            for mask in sources
        }
        scalar = {
            mask: _hash_integer(family, available_cards, "subset", mask)
            for mask in subsets
        }
    return PriceInstance(
        available_cards,
        family,
        tuple((mask, bases[mask]) for mask in sources),
        tuple((mask, scalar[mask]) for mask in subsets),
    )


def validate_instance(instance: PriceInstance) -> tuple[dict[int, int], dict[int, int]]:
    if not isinstance(instance, PriceInstance) or instance.available_cards not in DOMAINS:
        raise ValueError("selective-separation instance type or domain differs")
    sources = dict(instance.source_bases)
    subsets = dict(instance.subset_scalars)
    if (
        len(sources) != len(instance.source_bases)
        or tuple(sources) != complete_masks(instance.available_cards, SOURCE_WIDTH)
        or len(subsets) != len(instance.subset_scalars)
        or tuple(subsets) != subset_masks(instance.available_cards)
        or any(isinstance(value, bool) or not isinstance(value, int) for value in (*sources.values(), *subsets.values()))
    ):
        raise ValueError("selective-separation instance domain is incomplete or reordered")
    return sources, subsets


def _selective_price_maps(
    source_mask: int,
    sources: Mapping[int, int],
    subsets: Mapping[int, int],
) -> tuple[int, int]:
    if source_mask not in sources:
        raise ValueError("selective-separation source is absent")
    value = sources[source_mask]
    reads = 0
    for subset in source_subsets(source_mask):
        value += LEVEL_COEFFICIENTS[subset.bit_count()] * subsets[subset]
        reads += 1
    if reads != 57:
        raise AssertionError("selective-separation price did not read 57 subsets")
    return value, reads


def selective_price(instance: PriceInstance, source_mask: int) -> tuple[int, int]:
    sources, subsets = validate_instance(instance)
    return _selective_price_maps(source_mask, sources, subsets)


@dataclass(frozen=True, slots=True)
class Node:
    prefix: tuple[int, ...]
    upper: int
    descendant_count: int
    first_colex_rank: int
    children: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class CompileLedger:
    source_base_values_read: int
    prefix_nodes_bound: int
    possible_subset_terms_examined_for_bounds: int
    leaf_bound_equalities: int
    descendant_domination_comparisons: int


@dataclass(frozen=True, slots=True)
class CompiledSeparation:
    instance: PriceInstance
    nodes: tuple[Node, ...]
    ledger: CompileLedger
    node_digest: str


def _prefix_mask(prefix: Sequence[int]) -> int:
    return mask_from_cards(tuple(prefix))


def _children(prefix: tuple[int, ...], available_cards: int) -> tuple[tuple[int, ...], ...]:
    remaining = SOURCE_WIDTH - len(prefix)
    if remaining == 0:
        return ()
    start = prefix[-1] + 1 if prefix else 0
    return tuple(prefix + (card,) for card in range(start, available_cards - remaining + 1))


def compile_separation(instance: PriceInstance) -> CompiledSeparation:
    sources, subsets = validate_instance(instance)
    base_upper: dict[tuple[int, ...], int] = {}
    descendants: dict[tuple[int, ...], tuple[int, ...]] = {}
    children_by_prefix: dict[tuple[int, ...], tuple[tuple[int, ...], ...]] = {}
    source_base_reads = 0

    def build(prefix: tuple[int, ...]) -> tuple[int, ...]:
        nonlocal source_base_reads
        children = _children(prefix, instance.available_cards)
        children_by_prefix[prefix] = children
        if not children:
            mask = _prefix_mask(prefix)
            if mask not in sources:
                raise AssertionError("selective-separation leaf is outside source domain")
            rows = (mask,)
            base_upper[prefix] = sources[mask]
            source_base_reads += 1
        else:
            rows = tuple(mask for child in children for mask in build(child))
            base_upper[prefix] = max(base_upper[child] for child in children)
        descendants[prefix] = rows
        return rows

    root_descendants = build(())
    if (
        len(root_descendants) != len(sources)
        or len(set(root_descendants)) != len(sources)
        or tuple(sorted(root_descendants, key=colex_rank)) != tuple(sources)
    ):
        raise AssertionError("selective-separation prefix tree differs from colex domain")

    all_cards_mask = (1 << instance.available_cards) - 1
    nodes = []
    subset_examinations = 0
    leaf_equalities = 0
    descendant_comparisons = 0
    for prefix, source_rows in descendants.items():
        prefix_mask = _prefix_mask(prefix)
        remaining = SOURCE_WIDTH - len(prefix)
        start = prefix[-1] + 1 if prefix else 0
        tail_mask = all_cards_mask & ~((1 << start) - 1)
        upper = base_upper[prefix]
        for subset, scalar in subsets.items():
            subset_examinations += 1
            contribution = LEVEL_COEFFICIENTS[subset.bit_count()] * scalar
            missing = subset & ~prefix_mask
            if not missing:
                upper += contribution
                continue
            if missing & ~tail_mask:
                continue
            missing_count = missing.bit_count()
            if missing_count > remaining:
                continue
            if (tail_mask & ~missing).bit_count() < remaining - missing_count:
                continue
            upper += max(0, contribution)
        exact_descendant_prices = [
            _selective_price_maps(mask, sources, subsets)[0] for mask in source_rows
        ]
        descendant_comparisons += len(exact_descendant_prices)
        if any(price > upper for price in exact_descendant_prices):
            raise ArithmeticError("selective-separation prefix upper is not conservative")
        if len(prefix) == SOURCE_WIDTH:
            if len(exact_descendant_prices) != 1 or upper != exact_descendant_prices[0]:
                raise ArithmeticError("selective-separation leaf upper differs from price")
            leaf_equalities += 1
        nodes.append(
            Node(
                prefix,
                upper,
                len(source_rows),
                min(colex_rank(mask) for mask in source_rows),
                children_by_prefix[prefix],
            )
        )
    nodes.sort(key=lambda row: (len(row.prefix), row.prefix))
    node_payload = [asdict(node) for node in nodes]
    node_digest = sha256(
        json.dumps(node_payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return CompiledSeparation(
        instance,
        tuple(nodes),
        CompileLedger(
            source_base_reads,
            len(nodes),
            subset_examinations,
            leaf_equalities,
            descendant_comparisons,
        ),
        node_digest,
    )


@dataclass(frozen=True, slots=True)
class SearchReceipt:
    mode: str
    allow_pruning: bool
    maximum_price: int | None
    maximizers: tuple[int, ...]
    positive_coordinates: tuple[int, ...]
    proposal_coordinate: int | None
    proposal_price: int | None
    prefix_nodes_popped: int
    exact_leaf_prices: int
    selective_subset_scalar_reads: int
    pruned_source_leaves: int
    visited_source_leaves: int
    maximum_frontier_nodes: int
    complete_domain_covered: bool


def search(
    compiled: CompiledSeparation,
    mode: SearchMode,
    *,
    allow_pruning: bool = True,
) -> SearchReceipt:
    if mode not in ("exact_argmax", "final_global_closure", "proposal_separation"):
        raise ValueError("selective-separation search mode differs")
    node_map = {node.prefix: node for node in compiled.nodes}
    if len(node_map) != len(compiled.nodes) or () not in node_map:
        raise ValueError("selective-separation compiled node domain differs")
    sources, subsets = validate_instance(compiled.instance)
    root = node_map[()]
    frontier: list[tuple[int, int, tuple[int, ...]]] = [
        (-root.upper, root.first_colex_rank, root.prefix)
    ]
    maximum_frontier = 1
    popped = 0
    leaves = 0
    reads = 0
    pruned = 0
    maximum: int | None = None
    maximizers: list[int] = []
    positives: list[int] = []
    proposal_coordinate: int | None = None
    proposal_price: int | None = None
    stopped_early = False
    while frontier:
        _, _, prefix = heapq.heappop(frontier)
        popped += 1
        node = node_map[prefix]
        if allow_pruning:
            if mode == "exact_argmax" and maximum is not None and node.upper < maximum:
                pruned += node.descendant_count
                continue
            if mode in ("final_global_closure", "proposal_separation") and node.upper <= 0:
                pruned += node.descendant_count
                continue
        if not node.children:
            mask = _prefix_mask(prefix)
            price, row_reads = _selective_price_maps(mask, sources, subsets)
            leaves += 1
            reads += row_reads
            if maximum is None or price > maximum:
                maximum = price
                maximizers = [mask]
            elif price == maximum:
                maximizers.append(mask)
            if price > 0:
                positives.append(mask)
                if mode == "proposal_separation":
                    proposal_coordinate = mask
                    proposal_price = price
                    stopped_early = True
                    break
            continue
        for child_prefix in node.children:
            child = node_map[child_prefix]
            heapq.heappush(
                frontier,
                (-child.upper, child.first_colex_rank, child.prefix),
            )
        maximum_frontier = max(maximum_frontier, len(frontier))
    total_sources = comb(compiled.instance.available_cards, SOURCE_WIDTH)
    covered = not stopped_early and leaves + pruned == total_sources
    if mode != "proposal_separation" and not covered:
        raise AssertionError("selective-separation final search did not cover the domain")
    if mode == "proposal_separation" and proposal_coordinate is not None:
        if proposal_price is None or proposal_price <= 0:
            raise AssertionError("selective-separation proposal is not positive")
    ordered_maximizers = tuple(sorted(maximizers, key=colex_rank))
    ordered_positives = tuple(sorted(positives, key=colex_rank))
    return SearchReceipt(
        mode,
        allow_pruning,
        maximum,
        ordered_maximizers,
        ordered_positives,
        proposal_coordinate,
        proposal_price,
        popped,
        leaves,
        reads,
        pruned,
        leaves,
        maximum_frontier,
        covered,
    )


@dataclass(frozen=True, slots=True)
class ExhaustiveReceipt:
    maximum_price: int
    maximizers: tuple[int, ...]
    positive_coordinates: tuple[int, ...]
    exact_leaf_prices: int
    selective_subset_scalar_reads: int


def exhaustive_authority(instance: PriceInstance) -> ExhaustiveReceipt:
    sources, subsets = validate_instance(instance)
    rows = []
    reads = 0
    for mask in sources:
        price, count = _selective_price_maps(mask, sources, subsets)
        rows.append((mask, price))
        reads += count
    maximum = max(price for _, price in rows)
    return ExhaustiveReceipt(
        maximum,
        tuple(mask for mask, price in rows if price == maximum),
        tuple(mask for mask, price in rows if price > 0),
        len(rows),
        reads,
    )


def _integer_sequence_digest(values: Sequence[int]) -> str:
    digest = sha256()
    for value in values:
        encoded = str(value).encode("ascii")
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
    return digest.hexdigest()


def _instance_digest(instance: PriceInstance) -> str:
    return sha256(
        json.dumps(asdict(instance), sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def campaign_row(available_cards: int, family: str) -> dict[str, object]:
    instance = make_instance(available_cards, family)
    compiled = compile_separation(instance)
    exhaustive = exhaustive_authority(instance)
    argmax = search(compiled, "exact_argmax")
    closure = search(compiled, "final_global_closure")
    proposal = search(compiled, "proposal_separation")
    no_prune = search(compiled, "final_global_closure", allow_pruning=False)
    gates = {
        "selective_price_exact": exhaustive.selective_subset_scalar_reads
        == 57 * exhaustive.exact_leaf_prices,
        "node_bounds_conservative": compiled.ledger.descendant_domination_comparisons > 0,
        "leaf_bounds_exact": compiled.ledger.leaf_bound_equalities
        == exhaustive.exact_leaf_prices,
        "argmax_exact": (
            argmax.maximum_price == exhaustive.maximum_price
            and argmax.maximizers == exhaustive.maximizers
        ),
        "closure_exact": closure.positive_coordinates
        == exhaustive.positive_coordinates,
        "proposal_sound": (
            (not exhaustive.positive_coordinates and proposal.proposal_coordinate is None)
            or (
                proposal.proposal_coordinate in exhaustive.positive_coordinates
                and proposal.proposal_price is not None
                and proposal.proposal_price > 0
            )
        ),
        "domain_covered": argmax.complete_domain_covered
        and closure.complete_domain_covered,
        "no_prune_control_exact": (
            no_prune.exact_leaf_prices == exhaustive.exact_leaf_prices
            and no_prune.pruned_source_leaves == 0
            and no_prune.positive_coordinates == exhaustive.positive_coordinates
        ),
    }
    if not all(gates.values()):
        raise AssertionError("selective-separation campaign row rejected")
    return {
        "available_cards": available_cards,
        "family": family,
        "instance_sha256": _instance_digest(instance),
        "source_count": comb(available_cards, SOURCE_WIDTH),
        "subset_scalar_count": sum(
            comb(available_cards, level)
            for level in range(SUBSET_LEVEL_MAXIMUM + 1)
        ),
        "compiled_node_sha256": compiled.node_digest,
        "compile_ledger": asdict(compiled.ledger),
        "exhaustive": {
            "maximum_price": exhaustive.maximum_price,
            "maximizer_count": len(exhaustive.maximizers),
            "maximizers_sha256": _integer_sequence_digest(exhaustive.maximizers),
            "positive_count": len(exhaustive.positive_coordinates),
            "positive_coordinates_sha256": _integer_sequence_digest(
                exhaustive.positive_coordinates
            ),
            "exact_leaf_prices": exhaustive.exact_leaf_prices,
            "selective_subset_scalar_reads": exhaustive.selective_subset_scalar_reads,
        },
        "exact_argmax": asdict(argmax),
        "final_global_closure": asdict(closure),
        "proposal_separation": asdict(proposal),
        "unpruned_closure_control": asdict(no_prune),
        "gates": gates,
    }


def result_claims() -> dict[str, object]:
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


def build_result(*, source_commit: str, dependency_hashes: Mapping[str, str]) -> dict[str, object]:
    verify_preregistered_contract()
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("selective-separation source commit differs")
    if (
        not isinstance(dependency_hashes, Mapping)
        or not dependency_hashes
        or any(
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            for relative, digest in dependency_hashes.items()
        )
    ):
        raise ValueError("selective-separation dependency hashes differ")
    rows = [campaign_row(cards, family) for cards in DOMAINS for family in FAMILIES]
    some_pruning = any(
        int(row["final_global_closure"]["pruned_source_leaves"]) > 0
        for row in rows
    )
    return {
        "schema_version": "legal-river-quotient-selective-certified-separation-result-v1",
        "source_commit": source_commit,
        "config_sha256": CONFIG_SHA256,
        "dependency_hashes": dict(sorted(dependency_hashes.items())),
        "rows": rows,
        "row_count": len(rows),
        "all_gates_passed": all(all(row["gates"].values()) for row in rows),
        "terminal": (
            "completed_exact_separation_with_pruning"
            if some_pruning
            else "completed_exact_separation_no_material_pruning"
        ),
        "claims": result_claims(),
    }


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


__all__ = [
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "DOMAINS",
    "FAMILIES",
    "LEVEL_COEFFICIENTS",
    "PriceInstance",
    "RESULT_RELATIVE_PATH",
    "SearchReceipt",
    "build_result",
    "campaign_row",
    "canonical_json_bytes",
    "colex_rank",
    "compile_separation",
    "complete_masks",
    "exhaustive_authority",
    "load_preregistered_config",
    "make_instance",
    "mask_from_cards",
    "search",
    "selective_price",
    "source_subsets",
    "subset_masks",
    "validate_instance",
    "verify_preregistered_contract",
]
