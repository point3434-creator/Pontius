"""ADR-0427 shared sample-plan binding for the shared-direct device lane.

Import is device-free. The module reuses the sealed ADR-0419 device science and
changes only the sample-plan namespace/evidence seam that ADR-0426 rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sys
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from . import legal_river_quotient_cuda_compensated_tiles as _paired
from . import legal_river_quotient_cuda_compensated_work_preflight as _v4
from . import legal_river_quotient_cuda_shared_direct_device as _parent


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v3.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v3.jsonl"
)
V2_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v2.jsonl"
)
V1_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
CONFIG_SHA256 = (
    "e9265c9626fa8ba568922fb6297db75f68ca65fcaeb138cf1431aa7867d8ec5f"
)
PREREGISTRATION_COMMIT = "4be8b0316e115f3cb1548ddce43b211dcbf84101"
V2_RESULT_SHA256 = (
    "10a74f09c1a2e079c2c57459a58c6bb92362261a82a3b003378455ce61589686"
)
V2_RESULT_BYTES = 4_005_853


@dataclass(frozen=True, slots=True)
class CalibrationSamplePlan:
    available_cards: int
    source_ranks: tuple[int, ...]
    query_records: tuple[int, ...]
    boundary_features: tuple[int, ...]
    source_pair_shape: tuple[int, int, int]
    query_pair_shape: tuple[int, int, int]
    fold_pair_shape: tuple[int, int, int]
    adjoint_pair_shape: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class SamplePlanResolver:
    plans: Mapping[int, CalibrationSamplePlan]

    def plan(self, available_cards: int) -> CalibrationSamplePlan:
        try:
            plan = self.plans[available_cards]
        except KeyError as error:
            raise ValueError(
                "shared sample plan population differs"
            ) from error
        if plan.available_cards != available_cards:
            raise ValueError("shared sample plan key differs")
        return plan

    def __call__(
        self, available_cards: int
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        plan = self.plan(available_cards)
        return plan.source_ranks, plan.query_records


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared sample-plan path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"shared sample-plan {label} mapping differs")
    return value


def load_preregistered_config() -> Mapping[str, object]:
    path = _ROOT / CONFIG_RELATIVE_PATH
    if canonical_lf_sha256(path) != CONFIG_SHA256:
        raise ValueError("shared sample-plan config hash differs")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("shared sample-plan config root differs")
    return value


def _integer_tuple(value: object, *, label: str) -> tuple[int, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise ValueError(f"shared sample-plan {label} differs")
    result = tuple(value)
    if tuple(sorted(set(result))) != result:
        raise ValueError(f"shared sample-plan {label} is not unique sorted")
    return result


def _shape(value: object, *, label: str) -> tuple[int, int, int]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise ValueError(f"shared sample-plan {label} shape differs")
    result = tuple(value)
    if any(item <= 0 for item in result):
        raise ValueError(f"shared sample-plan {label} shape is nonpositive")
    return result  # type: ignore[return-value]


def compile_sample_plans(
    config: Mapping[str, object],
) -> Mapping[int, CalibrationSamplePlan]:
    frozen = _mapping(config.get("immutable_sample_plans"), label="plans")
    boundary = _integer_tuple(
        frozen.get("boundary_features"), label="boundary features"
    )
    if boundary != tuple(_v4.BOUNDARY_FEATURES):
        raise ValueError("shared sample-plan boundary features differ")
    plans: dict[int, CalibrationSamplePlan] = {}
    for cards in (10, 22):
        entry = _mapping(frozen.get(str(cards)), label=f"population {cards}")
        source = _integer_tuple(
            entry.get("source_ranks"), label=f"population {cards} source ranks"
        )
        query = _integer_tuple(
            entry.get("labeled_query_records"),
            label=f"population {cards} query records",
        )
        geometry = _v4.population_geometry(cards)
        if (
            len(source) != 16
            or len(query) != 16
            or source[-1] >= geometry.source_occupancies
            or query[-1] >= geometry.labeled_query_records
            or (source, query) != _v4.sample_rows(cards)
        ):
            raise ValueError(
                f"shared sample-plan population {cards} ranks differ"
            )
        plan = CalibrationSamplePlan(
            available_cards=cards,
            source_ranks=source,
            query_records=query,
            boundary_features=boundary,
            source_pair_shape=_shape(
                entry.get("source_pair_shape"),
                label=f"population {cards} source",
            ),
            query_pair_shape=_shape(
                entry.get("query_pair_shape"),
                label=f"population {cards} query",
            ),
            fold_pair_shape=_shape(
                entry.get("fold_pair_shape"),
                label=f"population {cards} fold",
            ),
            adjoint_pair_shape=_shape(
                entry.get("adjoint_pair_shape"),
                label=f"population {cards} adjoint",
            ),
        )
        expected = {
            "source": (len(source), len(boundary), 2),
            "query": (len(query), len(boundary), 2),
            "fold": (len(query), 2, 2),
            "adjoint": (len(source), len(boundary), 2),
        }
        if (
            plan.source_pair_shape != expected["source"]
            or plan.query_pair_shape != expected["query"]
            or plan.fold_pair_shape != expected["fold"]
            or plan.adjoint_pair_shape != expected["adjoint"]
        ):
            raise ValueError(
                f"shared sample-plan population {cards} expected shapes differ"
            )
        plans[cards] = plan
    return MappingProxyType(plans)


_CONFIG = load_preregistered_config()
CALIBRATION_SAMPLE_PLANS = compile_sample_plans(_CONFIG)
SAMPLE_PLAN_RESOLVER = SamplePlanResolver(CALIBRATION_SAMPLE_PLANS)


def verify_preregistered_contract(*, allow_live_result: bool = False) -> None:
    config = load_preregistered_config()
    retained = _mapping(
        config.get("retained_v2_contract"), label="retained V2"
    )
    fresh = _mapping(config.get("fresh_identity"), label="fresh identity")
    shared = _mapping(config.get("shared_plan_contract"), label="shared contract")
    if (
        config.get("schema_version")
        != "legal-river-quotient-cuda-shared-direct-sample-plan-v3"
        or retained.get("outcome_commit")
        != "118546c99b7c6ffd79addeab543e54ca9a20aa06"
        or retained.get("result_raw_sha256") != V2_RESULT_SHA256
        or retained.get("result_bytes") != V2_RESULT_BYTES
        or retained.get("v2_identity_permanently_consumed") is not True
        or fresh.get("sample_plan_adapter_relative_path")
        != "src/pontius/legal_river_quotient_cuda_shared_direct_sample_plan.py"
        or fresh.get("result_relative_path") != RESULT_RELATIVE_PATH
        or shared.get(
            "execution_sample_resolver_and_evidence_receive_"
            "the_same_mapping_and_same_plan_identity"
        )
        is not True
        or shared.get(
            "plan_contract_is_verified_before_cupy_import_"
            "compilation_allocation_or_launch"
        )
        is not True
    ):
        raise ValueError("shared sample-plan preregistered contract differs")
    for prefix in (
        "source_seal_adr",
        "outcome_adr",
        "config",
        "root_launcher",
        "science_adapter",
        "runner",
        "reader",
        "controls",
    ):
        relative = retained.get(f"{prefix}_relative_path")
        expected = retained.get(f"{prefix}_canonical_lf_sha256")
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or canonical_lf_sha256(_ROOT / relative) != expected
        ):
            raise ValueError(
                f"shared sample-plan retained V2 {prefix} differs"
            )
    v2 = _ROOT / V2_RESULT_RELATIVE_PATH
    if (
        not v2.is_file()
        or v2.stat().st_size != V2_RESULT_BYTES
        or sha256(v2.read_bytes()).hexdigest() != V2_RESULT_SHA256
    ):
        raise ValueError("shared sample-plan retained V2 artifact differs")
    if (
        (_ROOT / V1_RESULT_RELATIVE_PATH).exists()
        or (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists()
        or ((not allow_live_result) and (_ROOT / RESULT_RELATIVE_PATH).exists())
    ):
        raise ValueError("shared sample-plan result lifecycle differs")
    rebuilt = compile_sample_plans(config)
    if rebuilt != CALIBRATION_SAMPLE_PLANS:
        raise ValueError("shared sample-plan module plans differ")


def _compile_population_builder() -> Callable[..., object]:
    source = inspect.getsource(_parent.build_generated_population_runner)
    old = "    namespace = dict(vars(_paired))"
    new = (
        old
        + "\n"
        + '    namespace["_sample_rows"] = SAMPLE_PLAN_RESOLVER'
    )
    if source.count(old) != 1 or "SAMPLE_PLAN_RESOLVER" in source:
        raise ValueError("shared sample-plan population builder seam differs")
    namespace = dict(vars(_parent))
    namespace["SAMPLE_PLAN_RESOLVER"] = SAMPLE_PLAN_RESOLVER
    return _parent._compile_generated_function(
        source.replace(old, new, 1),
        "build_generated_population_runner",
        namespace,
    )


build_generated_population_runner = _compile_population_builder()


def _compile_plan_error_evidence() -> Callable[..., object]:
    source = inspect.getsource(_v4._pair_error_evidence)
    namespace = dict(vars(_v4))
    namespace["sample_rows"] = SAMPLE_PLAN_RESOLVER
    return _parent._compile_generated_function(
        source, "_pair_error_evidence", namespace
    )


_PLAN_ERROR_EVIDENCE = _compile_plan_error_evidence()


def _require_shape(label: str, value: object, expected: tuple[int, ...]) -> None:
    actual_value = getattr(value, "shape", None)
    actual = tuple(actual_value) if actual_value is not None else None
    if actual != expected:
        raise ValueError(
            "shared sample-plan "
            f"{label} shape differs: actual={actual!r} expected={expected!r}"
        )


def validate_execution_shapes(
    plan: CalibrationSamplePlan,
    execution: _paired.PairedPopulationExecution,
    *,
    family: str,
) -> None:
    if execution.available_cards != plan.available_cards:
        raise ValueError(
            "shared sample-plan "
            f"{family} population differs: actual={execution.available_cards!r} "
            f"expected={plan.available_cards!r}"
        )
    checks = (
        ("source", execution.source_samples, plan.source_pair_shape),
        ("query", execution.query_samples, plan.query_pair_shape),
        ("fold", execution.fold_samples, plan.fold_pair_shape),
        ("adjoint", execution.adjoint_samples, plan.adjoint_pair_shape),
        (
            "direct_query",
            execution.direct_query_samples,
            plan.query_pair_shape,
        ),
        (
            "direct_fold",
            execution.direct_fold_samples,
            plan.fold_pair_shape,
        ),
        (
            "direct_adjoint",
            execution.direct_adjoint_samples,
            plan.adjoint_pair_shape,
        ),
    )
    for label, value, expected in checks:
        _require_shape(f"{family}.{label}", value, expected)


def _plan_error_evidence(
    cards: int,
    normal: _paired.PairedPopulationExecution,
    alternate: _paired.PairedPopulationExecution,
    fixture: object,
) -> dict[str, object]:
    plan = SAMPLE_PLAN_RESOLVER.plan(cards)
    validate_execution_shapes(plan, normal, family="default")
    validate_execution_shapes(plan, alternate, family="alternate")
    return _PLAN_ERROR_EVIDENCE(  # type: ignore[return-value]
        cards, normal, alternate, fixture
    )


def _compile_population_evidence() -> Callable[..., object]:
    source = inspect.getsource(_parent._population_evidence)
    old = "_v4._pair_error_evidence("
    if source.count(old) != 1:
        raise ValueError("shared sample-plan evidence seam differs")
    namespace = dict(vars(_parent))
    namespace["_plan_error_evidence"] = _plan_error_evidence
    return _parent._compile_generated_function(
        source.replace(old, "_plan_error_evidence(", 1),
        "_population_evidence",
        namespace,
    )


_POPULATION_EVIDENCE = _compile_population_evidence()


def _population_evidence(*args: object, **kwargs: object) -> dict[str, object]:
    return _POPULATION_EVIDENCE(*args, **kwargs)  # type: ignore[return-value]


def _compile_family_runner() -> Callable[..., object]:
    source = inspect.getsource(_parent.run_shared_family)
    namespace = dict(vars(_parent))
    namespace[
        "build_generated_population_runner"
    ] = build_generated_population_runner
    return _parent._compile_generated_function(
        source, "run_shared_family", namespace
    )


_RUN_SHARED_FAMILY = _compile_family_runner()


def run_shared_family(*args: object, **kwargs: object) -> object:
    return _RUN_SHARED_FAMILY(*args, **kwargs)


def _compile_validation() -> Callable[..., object]:
    source = inspect.getsource(_parent.run_shared_direct_device_validation)
    namespace = dict(vars(_parent))
    namespace["run_shared_family"] = run_shared_family
    namespace["_population_evidence"] = _population_evidence
    return _parent._compile_generated_function(
        source, "run_shared_direct_device_validation", namespace
    )


_VALIDATION = _compile_validation()


def generated_binding_report() -> Mapping[str, object]:
    runner = build_generated_population_runner(object())
    execution_resolver = runner.__globals__.get("_sample_rows")
    evidence_resolver = _PLAN_ERROR_EVIDENCE.__globals__.get("sample_rows")
    gates = {
        "execution_resolver_identity": (
            execution_resolver is SAMPLE_PLAN_RESOLVER
        ),
        "evidence_resolver_identity": (
            evidence_resolver is SAMPLE_PLAN_RESOLVER
        ),
        "same_resolver_identity": execution_resolver is evidence_resolver,
        "same_plan_mapping_identity": (
            SAMPLE_PLAN_RESOLVER.plans is CALIBRATION_SAMPLE_PLANS
        ),
        "population_ten_plan_identity": (
            SAMPLE_PLAN_RESOLVER.plan(10) is CALIBRATION_SAMPLE_PLANS[10]
        ),
        "population_twenty_two_plan_identity": (
            SAMPLE_PLAN_RESOLVER.plan(22) is CALIBRATION_SAMPLE_PLANS[22]
        ),
        "parent_helper_not_bound": execution_resolver is not _paired._sample_rows,
        "population_evidence_helper_identity": (
            _POPULATION_EVIDENCE.__globals__.get("_plan_error_evidence")
            is _plan_error_evidence
        ),
        "family_builder_identity": (
            _RUN_SHARED_FAMILY.__globals__.get(
                "build_generated_population_runner"
            )
            is build_generated_population_runner
        ),
        "validation_family_identity": (
            _VALIDATION.__globals__.get("run_shared_family")
            is run_shared_family
        ),
        "validation_evidence_identity": (
            _VALIDATION.__globals__.get("_population_evidence")
            is _population_evidence
        ),
    }
    return MappingProxyType(
        {
            "schema_version": "shared-sample-plan-binding-report-v1",
            "gates": MappingProxyType(gates),
            "all_gates_pass": all(gates.values()),
        }
    )


def source_seal_report() -> Mapping[str, object]:
    verify_preregistered_contract(allow_live_result=False)
    parent = _parent.source_seal_report()
    binding = generated_binding_report()
    gates = {
        "parent_source_seal_passed": parent["all_gates_pass"] is True,
        "generated_binding_passed": binding["all_gates_pass"] is True,
        "config_plans_are_read_only": isinstance(
            CALIBRATION_SAMPLE_PLANS, MappingProxyType
        ),
        "cupy_not_imported": (
            "cupy" not in sys.modules and _parent._CUPY_IMPORT_CALLS == 0
        ),
        "v3_result_absent": not (_ROOT / RESULT_RELATIVE_PATH).exists(),
        "v1_result_absent": not (_ROOT / V1_RESULT_RELATIVE_PATH).exists(),
        "reserved_actual_result_absent": not (
            _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        ).exists(),
    }
    return MappingProxyType(
        {
            "schema_version": "shared-sample-plan-source-seal-v1",
            "binding": binding,
            "gates": MappingProxyType(gates),
            "all_gates_pass": all(gates.values()),
        }
    )


def run_shared_direct_device_validation(
    emit: Callable[[str, Mapping[str, object]], None] | None = None,
) -> dict[str, object]:
    verify_preregistered_contract(allow_live_result=emit is not None)
    binding = generated_binding_report()
    if binding["all_gates_pass"] is not True:
        raise ValueError("shared sample-plan generated binding differs")
    return _VALIDATION(emit)  # type: ignore[return-value]


__all__ = [
    "CALIBRATION_SAMPLE_PLANS",
    "CONFIG_SHA256",
    "CalibrationSamplePlan",
    "RESULT_RELATIVE_PATH",
    "SAMPLE_PLAN_RESOLVER",
    "SamplePlanResolver",
    "compile_sample_plans",
    "generated_binding_report",
    "run_shared_direct_device_validation",
    "source_seal_report",
    "validate_execution_shapes",
    "verify_preregistered_contract",
]
