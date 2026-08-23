"""Failure-complete canonical validation for the ADR-0318 sizing adapter.

The 48 exact micro LPs exercise the same public HiGHS dual-simplex boundary
through ADR-0313's generic adapter and exact vertex oracle.  The 129 reduced
sizing LPs exercise ADR-0318 directly and are then reconstructed again through
ADR-0313's independently sealed sizing verifier.  Every canonical base leaves
one ordered observation and one counted public HiGHS invocation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import MappingProxyType
from typing import Any
from enum import StrEnum

from .certified_reduced_sizing_highs import (
    ADR0318_CERTIFIED_SIZING_ALLOWANCES,
    ADR0318_HIGHS_DS_OPTIONS,
    CertifiedReducedSizingSolution,
    solve_certified_reduced_sizing_highs,
    verify_adr0318_runtime_identity,
    verify_adr0318_source_and_dependencies,
)
from .native_simplex_audit_corpus import (
    ADR0311_COMPLETE_CORPUS_SHA256,
    ADR0311_VARIANTS_PER_BASE,
    AuditBaseFamily,
    AuditLinearProgramBase,
    AuditVariantDescriptor,
    AuditVariantKind,
    MaterializedAuditLinearProgram,
    build_adr0311_known_regression_context,
    build_adr0311_native_simplex_audit_corpus,
    materialize_audit_variant,
)
from .native_simplex_audit_runner import (
    ADR0311_HIGHS_DS_OPTIONS,
    ADR0311_MICRO_DUAL_ALLOWANCE,
    ADR0311_MICRO_OBJECTIVE_ALLOWANCE,
    ADR0311_MICRO_PRIMAL_ALLOWANCE,
    ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE,
    ADR0311_SIZING_OBJECTIVE_ALLOWANCE,
    ADR0313_EXPECTED_ENVIRONMENT,
    AuditBackend,
    AuditEnvironmentIdentity,
    AuditExceptionRecord,
    AuditFailureStage,
    BackendRawResult,
    BackendTermination,
    DualHintConvention,
    ExactMicroEnumeration,
    MicroAuditVerification,
    SizingAuditVerification,
    canonical_audit_bytes,
    capture_audit_environment_identity,
    enumerate_exact_micro_vertices,
    invoke_highs_backend,
    verify_micro_backend_result,
    verify_sizing_backend_result,
)
from .native_simplex_audit_structures import (
    AuditWidthFourContext,
    ExactMicroLinearProgram,
)
from .reduced_river_sizing_lp import compile_reduced_river_sizing_lp


ADR0319_RUNNER_VERSION = "certified-sizing-canonical-validation-runner-v1"
ADR0319_EXPECTED_OBSERVATION_COUNT = 177


class CanonicalValidationPath(StrEnum):
    EXACT_MICRO_HIGHS_DS = "exact-micro-highs-ds"
    CERTIFIED_SIZING_ADAPTER = "certified-sizing-adapter"


@dataclass(frozen=True, slots=True)
class CanonicalValidationProtocol:
    runner_version: str
    expected_observation_count: int
    public_backend: AuditBackend
    canonical_variant: AuditVariantKind
    micro_highs_options: object
    sizing_highs_options: object
    micro_primal_allowance: object
    micro_dual_allowance: object
    micro_objective_allowance: object
    independent_sizing_objective_allowance: object
    independent_sizing_certificate_width_allowance: object
    certified_sizing_allowances: object

    def __post_init__(self) -> None:
        if self.runner_version != ADR0319_RUNNER_VERSION:
            raise ValueError("canonical validation runner version drifted")
        if self.expected_observation_count != ADR0319_EXPECTED_OBSERVATION_COUNT:
            raise ValueError("canonical validation observation count drifted")
        if self.public_backend is not AuditBackend.HIGHS_DS:
            raise ValueError("canonical validation backend must remain HiGHS-DS")
        if self.canonical_variant is not AuditVariantKind.CANONICAL:
            raise ValueError("canonical validation cannot transform a base")


ADR0319_PROTOCOL = CanonicalValidationProtocol(
    runner_version=ADR0319_RUNNER_VERSION,
    expected_observation_count=ADR0319_EXPECTED_OBSERVATION_COUNT,
    public_backend=AuditBackend.HIGHS_DS,
    canonical_variant=AuditVariantKind.CANONICAL,
    micro_highs_options=ADR0311_HIGHS_DS_OPTIONS,
    sizing_highs_options=ADR0318_HIGHS_DS_OPTIONS,
    micro_primal_allowance=ADR0311_MICRO_PRIMAL_ALLOWANCE,
    micro_dual_allowance=ADR0311_MICRO_DUAL_ALLOWANCE,
    micro_objective_allowance=ADR0311_MICRO_OBJECTIVE_ALLOWANCE,
    independent_sizing_objective_allowance=ADR0311_SIZING_OBJECTIVE_ALLOWANCE,
    independent_sizing_certificate_width_allowance=(
        ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE
    ),
    certified_sizing_allowances=ADR0318_CERTIFIED_SIZING_ALLOWANCES,
)


@dataclass(frozen=True, slots=True)
class CanonicalValidationTask:
    ordinal: int
    base: AuditLinearProgramBase
    descriptor: AuditVariantDescriptor
    materialized: MaterializedAuditLinearProgram
    path: CanonicalValidationPath
    exact_micro_case: ExactMicroLinearProgram | None
    sizing_context: AuditWidthFourContext | None

    def __post_init__(self) -> None:
        if (
            isinstance(self.ordinal, bool)
            or not isinstance(self.ordinal, int)
            or self.ordinal < 0
        ):
            raise ValueError("canonical validation ordinal must be nonnegative")
        if not isinstance(self.base, AuditLinearProgramBase):
            raise TypeError("canonical validation task requires a semantic base")
        if not isinstance(self.descriptor, AuditVariantDescriptor):
            raise TypeError("canonical validation task requires a semantic descriptor")
        if self.descriptor.kind is not AuditVariantKind.CANONICAL:
            raise ValueError("canonical validation task contains a transformed LP")
        if (
            self.descriptor.base_id != self.base.base_id
            or self.descriptor.base_sha256 != self.base.digest
        ):
            raise ValueError("canonical validation base and descriptor disagree")
        if (
            not isinstance(self.materialized, MaterializedAuditLinearProgram)
            or self.materialized.digest != self.descriptor.linear_program_sha256
        ):
            raise ValueError("canonical validation materialization identity drifted")
        if self.path is CanonicalValidationPath.EXACT_MICRO_HIGHS_DS:
            if (
                self.base.family is not AuditBaseFamily.EXACT_MICRO
                or self.exact_micro_case is None
                or self.sizing_context is not None
                or self.exact_micro_case.case_id != self.base.base_id
            ):
                raise ValueError("micro validation task has the wrong semantic binding")
        elif self.path is CanonicalValidationPath.CERTIFIED_SIZING_ADAPTER:
            if (
                self.base.family is AuditBaseFamily.EXACT_MICRO
                or self.exact_micro_case is not None
                or self.sizing_context is None
                or self.base.context_id != self.sizing_context.context_id
            ):
                raise ValueError("sizing validation task has the wrong semantic binding")
        else:
            raise TypeError("canonical validation path must be semantic")

    @property
    def identity_payload(self) -> Mapping[str, object]:
        independent_input_sha256 = (
            self.exact_micro_case.digest
            if self.exact_micro_case is not None
            else self.sizing_context.digest
        )
        return MappingProxyType(
            {
                "base_id": self.base.base_id,
                "base_sha256": self.base.digest,
                "canonical_linear_program_sha256": self.materialized.digest,
                "canonical_variant_sha256": self.descriptor.digest,
                "family": self.base.family.value,
                "independent_input_sha256": independent_input_sha256,
                "ordinal": self.ordinal,
                "path": self.path.value,
                "source_input_sha256": self.base.source_input_sha256,
                "variant_id": self.descriptor.variant_id,
                "version": "adr0319-canonical-validation-task-v1",
            }
        )


@dataclass(frozen=True, slots=True)
class CanonicalValidationPlan:
    corpus_sha256: str
    tasks: tuple[CanonicalValidationTask, ...]
    sealed_adr0312: bool

    def __post_init__(self) -> None:
        if not isinstance(self.corpus_sha256, str) or len(self.corpus_sha256) != 64:
            raise ValueError("canonical validation corpus digest is malformed")
        if not isinstance(self.tasks, tuple) or not self.tasks:
            raise TypeError("canonical validation tasks must be nonempty and immutable")
        if any(not isinstance(task, CanonicalValidationTask) for task in self.tasks):
            raise TypeError("canonical validation plan contains a nonsemantic task")
        if tuple(task.ordinal for task in self.tasks) != tuple(range(len(self.tasks))):
            raise ValueError("canonical validation task ordinals are not contiguous")
        if not isinstance(self.sealed_adr0312, bool):
            raise TypeError("canonical validation sealed flag must be boolean")
        if self.sealed_adr0312 and (
            self.corpus_sha256 != ADR0311_COMPLETE_CORPUS_SHA256
            or len(self.tasks) != ADR0319_EXPECTED_OBSERVATION_COUNT
        ):
            raise ValueError("sealed canonical validation inventory drifted")

    @property
    def schedule_bytes(self) -> bytes:
        return canonical_audit_bytes(tuple(task.identity_payload for task in self.tasks))

    @property
    def schedule_digest(self) -> str:
        return sha256(self.schedule_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class CanonicalValidationFailure:
    stage: AuditFailureStage
    code: str
    detail: str
    exception: AuditExceptionRecord | None = None
    causes: tuple[AuditExceptionRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.stage, AuditFailureStage):
            raise TypeError("canonical validation failure stage must be semantic")
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("canonical validation failure code must be nonempty")
        if not isinstance(self.detail, str):
            raise TypeError("canonical validation failure detail must be text")
        if self.exception is not None and not isinstance(
            self.exception,
            AuditExceptionRecord,
        ):
            raise TypeError("canonical validation exception must be semantic")
        if not isinstance(self.causes, tuple) or any(
            not isinstance(cause, AuditExceptionRecord) for cause in self.causes
        ):
            raise TypeError("canonical validation exception causes must be semantic")

    @classmethod
    def from_exception(
        cls,
        error: Exception,
        *,
        stage: AuditFailureStage,
        code: str,
    ) -> CanonicalValidationFailure:
        causes: list[AuditExceptionRecord] = []
        seen = {id(error)}
        current = error.__cause__
        if current is None and not error.__suppress_context__:
            current = error.__context__
        while isinstance(current, Exception) and id(current) not in seen:
            seen.add(id(current))
            causes.append(AuditExceptionRecord.from_exception(current, stage=stage))
            successor = current.__cause__
            if successor is None and not current.__suppress_context__:
                successor = current.__context__
            current = successor
        return cls(
            stage=stage,
            code=code,
            detail=str(error),
            exception=AuditExceptionRecord.from_exception(error, stage=stage),
            causes=tuple(causes),
        )


@dataclass(slots=True)
class _CountedPublicHighsCall:
    function: Callable[..., Any]
    invocation_count: int = 0

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.invocation_count += 1
        return self.function(*args, **kwargs)


@dataclass(frozen=True, slots=True)
class CanonicalValidationObservation:
    ordinal: int
    base_id: str
    base_sha256: str
    family: AuditBaseFamily
    path: CanonicalValidationPath
    canonical_linear_program_sha256: str
    public_highs_ds_invocation_count: int
    micro_backend_result: BackendRawResult | None
    exact_micro_work: ExactMicroEnumeration | None
    micro_verification: MicroAuditVerification | None
    sizing_adapter_result: CertifiedReducedSizingSolution | None
    sizing_independent_verification: SizingAuditVerification | None
    failures: tuple[CanonicalValidationFailure, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.ordinal, bool)
            or not isinstance(self.ordinal, int)
            or self.ordinal < 0
        ):
            raise ValueError("canonical validation observation ordinal is invalid")
        if not isinstance(self.base_id, str) or not self.base_id:
            raise ValueError("canonical validation observation base id is empty")
        for digest in (self.base_sha256, self.canonical_linear_program_sha256):
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError("canonical validation observation digest is malformed")
        if not isinstance(self.family, AuditBaseFamily):
            raise TypeError("canonical validation observation family must be semantic")
        if not isinstance(self.path, CanonicalValidationPath):
            raise TypeError("canonical validation observation path must be semantic")
        if (
            isinstance(self.public_highs_ds_invocation_count, bool)
            or not isinstance(self.public_highs_ds_invocation_count, int)
            or self.public_highs_ds_invocation_count < 0
        ):
            raise ValueError("public HiGHS invocation count must be nonnegative")
        if not isinstance(self.failures, tuple) or any(
            not isinstance(failure, CanonicalValidationFailure)
            for failure in self.failures
        ):
            raise TypeError("canonical validation failures must be semantic and immutable")
        if self.path is CanonicalValidationPath.EXACT_MICRO_HIGHS_DS:
            if self.family is not AuditBaseFamily.EXACT_MICRO or any(
                value is not None
                for value in (
                    self.sizing_adapter_result,
                    self.sizing_independent_verification,
                )
            ):
                raise ValueError("micro observation carries sizing evidence")
        elif self.family is AuditBaseFamily.EXACT_MICRO or any(
            value is not None
            for value in (
                self.micro_backend_result,
                self.exact_micro_work,
                self.micro_verification,
            )
        ):
            raise ValueError("sizing observation carries micro evidence")

    @property
    def passed(self) -> bool:
        if self.failures or self.public_highs_ds_invocation_count != 1:
            return False
        if self.path is CanonicalValidationPath.EXACT_MICRO_HIGHS_DS:
            return bool(
                self.micro_backend_result is not None
                and self.micro_backend_result.termination is BackendTermination.OPTIMAL
                and self.exact_micro_work is not None
                and self.micro_verification is not None
                and self.micro_verification.passed
            )
        return bool(
            self.sizing_adapter_result is not None
            and self.sizing_independent_verification is not None
            and self.sizing_independent_verification.passed
        )


@dataclass(frozen=True, slots=True)
class CanonicalValidationCampaign:
    runner_version: str
    runner_source_sha256: str
    corpus_sha256: str
    schedule_sha256: str
    environment: AuditEnvironmentIdentity
    protocol: CanonicalValidationProtocol
    observations: tuple[CanonicalValidationObservation, ...]
    sealed_adr0319: bool

    def __post_init__(self) -> None:
        if self.runner_version != ADR0319_RUNNER_VERSION:
            raise ValueError("canonical validation campaign runner version drifted")
        for digest in (
            self.runner_source_sha256,
            self.corpus_sha256,
            self.schedule_sha256,
        ):
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError("canonical validation campaign digest is malformed")
        if not isinstance(self.environment, AuditEnvironmentIdentity):
            raise TypeError("canonical validation environment must be semantic")
        if self.protocol != ADR0319_PROTOCOL:
            raise ValueError("canonical validation protocol drifted")
        if not isinstance(self.observations, tuple) or any(
            not isinstance(observation, CanonicalValidationObservation)
            for observation in self.observations
        ):
            raise TypeError("canonical validation observations must be semantic and immutable")
        if tuple(observation.ordinal for observation in self.observations) != tuple(
            range(len(self.observations))
        ):
            raise ValueError("canonical validation observations are not in schedule order")
        if not isinstance(self.sealed_adr0319, bool):
            raise TypeError("canonical validation sealed flag must be boolean")
        if self.sealed_adr0319:
            from .certified_sizing_validation_seal import (
                ADR0319_SCHEDULE_SHA256,
                ADR0319_SOURCE_MANIFEST,
            )

            if (
                self.runner_source_sha256
                != ADR0319_SOURCE_MANIFEST["certified_sizing_validation_runner.py"]
                or self.corpus_sha256 != ADR0311_COMPLETE_CORPUS_SHA256
                or self.schedule_sha256 != ADR0319_SCHEDULE_SHA256
                or self.environment != ADR0313_EXPECTED_ENVIRONMENT
                or len(self.observations) != ADR0319_EXPECTED_OBSERVATION_COUNT
            ):
                raise ValueError("sealed canonical validation provenance is incomplete")

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_audit_bytes(self)

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class CanonicalValidationAssessment:
    complete_schedule: bool
    one_public_call_per_base: bool
    passed_observation_count: int
    failed_observation_count: int
    passed_micro_count: int
    passed_sizing_count: int
    maximum_absolute_micro_exact_error: float | None
    maximum_absolute_micro_certificate_gap: float | None
    maximum_absolute_sizing_certificate_gap_chips: float | None
    total_solver_wall_seconds: float
    total_verification_wall_seconds: float
    certified_v2_consumer_eligible: bool
    failed_base_ids: tuple[str, ...]


def build_adr0319_canonical_validation_plan() -> CanonicalValidationPlan:
    """Bind ADR-0312's 177 bases to only their canonical representations."""

    corpus = build_adr0311_native_simplex_audit_corpus()
    if corpus.digest != ADR0311_COMPLETE_CORPUS_SHA256:
        raise ValueError("ADR-0312 corpus identity drifted")
    canonical_descriptors = corpus.variants[::ADR0311_VARIANTS_PER_BASE]
    if (
        len(canonical_descriptors) != len(corpus.bases)
        or any(
            descriptor.kind is not AuditVariantKind.CANONICAL
            for descriptor in canonical_descriptors
        )
    ):
        raise ValueError("ADR-0312 canonical representation schedule drifted")
    micro_by_id = {case.case_id: case for case in corpus.micro_structure.cases}
    sizing_contexts = (
        build_adr0311_known_regression_context(),
        *corpus.width_four_structure.contexts,
    )
    context_by_id = {context.context_id: context for context in sizing_contexts}
    tasks: list[CanonicalValidationTask] = []
    for ordinal, (base, descriptor) in enumerate(
        zip(corpus.bases, canonical_descriptors, strict=True)
    ):
        is_micro = base.family is AuditBaseFamily.EXACT_MICRO
        tasks.append(
            CanonicalValidationTask(
                ordinal=ordinal,
                base=base,
                descriptor=descriptor,
                materialized=materialize_audit_variant(
                    base=base,
                    descriptor=descriptor,
                ),
                path=(
                    CanonicalValidationPath.EXACT_MICRO_HIGHS_DS
                    if is_micro
                    else CanonicalValidationPath.CERTIFIED_SIZING_ADAPTER
                ),
                exact_micro_case=micro_by_id[base.base_id] if is_micro else None,
                sizing_context=None if is_micro else context_by_id[base.context_id],
            )
        )
    return CanonicalValidationPlan(
        corpus_sha256=corpus.digest,
        tasks=tuple(tasks),
        sealed_adr0312=True,
    )


def _failure_from_raw(raw: BackendRawResult) -> CanonicalValidationFailure:
    return CanonicalValidationFailure(
        stage=AuditFailureStage.BACKEND_INVOCATION,
        code=f"highs-ds-{raw.termination.value}",
        detail=raw.message,
        exception=raw.exception,
    )


def _micro_observation(
    task: CanonicalValidationTask,
    *,
    public_highs_call: _CountedPublicHighsCall,
) -> CanonicalValidationObservation:
    failures: list[CanonicalValidationFailure] = []
    exact: ExactMicroEnumeration | None = None
    raw: BackendRawResult | None = None
    verification: MicroAuditVerification | None = None
    assert task.exact_micro_case is not None
    try:
        exact = enumerate_exact_micro_vertices(task.exact_micro_case)
    except Exception as error:  # noqa: BLE001 - one failure cannot truncate the schedule
        failures.append(
            CanonicalValidationFailure.from_exception(
                error,
                stage=AuditFailureStage.INDEPENDENT_EXACT_ENUMERATION,
                code="exact-micro-enumeration-exception",
            )
        )
    try:
        raw = invoke_highs_backend(
            AuditBackend.HIGHS_DS,
            task.materialized,
            linprog_function=public_highs_call,
        )
    except Exception as error:  # pragma: no cover - adapter is already exception-complete
        failures.append(
            CanonicalValidationFailure.from_exception(
                error,
                stage=AuditFailureStage.BACKEND_INVOCATION,
                code="micro-highs-adapter-exception",
            )
        )
    if raw is not None and raw.termination is not BackendTermination.OPTIMAL:
        failures.append(_failure_from_raw(raw))
    if raw is not None and raw.termination is BackendTermination.OPTIMAL and exact is not None:
        try:
            verification = verify_micro_backend_result(
                base=task.base,
                descriptor=task.descriptor,
                raw=raw,
                exact=exact,
            )
            if not verification.passed:
                failures.append(
                    CanonicalValidationFailure(
                        stage=AuditFailureStage.SEMANTIC_VERIFICATION,
                        code="micro-semantic-rejection",
                        detail=",".join(failure.value for failure in verification.failures),
                    )
                )
        except Exception as error:  # noqa: BLE001 - retain and continue
            failures.append(
                CanonicalValidationFailure.from_exception(
                    error,
                    stage=AuditFailureStage.SEMANTIC_VERIFICATION,
                    code="micro-verification-exception",
                )
            )
    if public_highs_call.invocation_count != 1:
        failures.append(
            CanonicalValidationFailure(
                stage=AuditFailureStage.BACKEND_INVOCATION,
                code="public-highs-call-count",
                detail=(
                    "expected one public HiGHS-DS call, observed "
                    f"{public_highs_call.invocation_count}"
                ),
            )
        )
    return CanonicalValidationObservation(
        ordinal=task.ordinal,
        base_id=task.base.base_id,
        base_sha256=task.base.digest,
        family=task.base.family,
        path=task.path,
        canonical_linear_program_sha256=task.materialized.digest,
        public_highs_ds_invocation_count=public_highs_call.invocation_count,
        micro_backend_result=raw,
        exact_micro_work=exact,
        micro_verification=verification,
        sizing_adapter_result=None,
        sizing_independent_verification=None,
        failures=tuple(failures),
    )


def _sizing_consistency_failures(
    task: CanonicalValidationTask,
    solution: CertifiedReducedSizingSolution,
    verification: SizingAuditVerification,
) -> tuple[str, ...]:
    assert task.sizing_context is not None
    assert task.base.bet_sizes is not None
    context = task.sizing_context
    compiled = compile_reduced_river_sizing_lp(
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        joint_probabilities=tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        ),
        showdown_signs=context.showdown_signs,
        bet_sizes=task.base.bet_sizes,
    )
    mismatches: list[str] = []
    if solution.linear_program_sha256 != compiled.digest:
        mismatches.append("compiled-linear-program")
    if solution.bet_sizes != task.base.bet_sizes:
        mismatches.append("bet-sizes")
    if solution.raw_primal_variables != verification.canonical_primal:
        mismatches.append("canonical-primal")
    if solution.raw_inequality_multipliers != verification.dual_hint.raw_variant_hint:
        mismatches.append("raw-multipliers")
    adapter_policy = solution.exact_opening_policy
    independent_policy = tuple(
        tuple(value.fraction for value in row)
        for row in verification.exact_normalized_policy
    )
    if adapter_policy != independent_policy:
        mismatches.append("exact-policy")
    if solution.responder_best_actions != verification.responder_best_actions:
        mismatches.append("responder-actions")
    adapter_clips = tuple(
        (clip.variable_index, clip.raw_value, clip.clipped_value)
        for clip in solution.policy_clips
    )
    independent_clips = tuple(
        (clip.variable_index, clip.raw_value, clip.clipped_value)
        for clip in verification.policy_clips
    )
    if adapter_clips != independent_clips:
        mismatches.append("policy-clips")
    scalar_pairs = (
        (
            "reported-value",
            solution.reported_value_chips,
            verification.reported_value_chips,
        ),
        (
            "canonical-value",
            solution.canonical_raw_value_chips,
            verification.canonical_lp_value_chips,
        ),
        (
            "behavioral-lower-bound",
            solution.feasible_behavioral_lower_bound_chips,
            verification.behavioral_lower_bound_chips,
        ),
        (
            "certified-upper-bound",
            solution.certified_upper_bound_chips,
            verification.certified_upper_bound_chips,
        ),
        (
            "signed-certificate-gap",
            solution.signed_certificate_gap_chips,
            verification.certified_optimality_gap_chips,
        ),
    )
    mismatches.extend(label for label, left, right in scalar_pairs if left != right)
    if solution.certificate != verification.certificate:
        mismatches.append("outward-certificate")
    return tuple(mismatches)


def _sizing_observation(
    task: CanonicalValidationTask,
    *,
    public_highs_call: _CountedPublicHighsCall,
) -> CanonicalValidationObservation:
    failures: list[CanonicalValidationFailure] = []
    solution: CertifiedReducedSizingSolution | None = None
    verification: SizingAuditVerification | None = None
    assert task.sizing_context is not None
    assert task.base.bet_sizes is not None
    context = task.sizing_context
    try:
        solution = solve_certified_reduced_sizing_highs(
            pot=context.pot,
            stack=context.stack,
            minimum_bet=context.minimum_bet,
            joint_probabilities=tuple(
                tuple(probability.fraction for probability in row)
                for row in context.joint_probabilities
            ),
            showdown_signs=context.showdown_signs,
            bet_sizes=task.base.bet_sizes,
            linprog_function=public_highs_call,
        )
    except Exception as error:  # noqa: BLE001 - one rejection cannot truncate the schedule
        failures.append(
            CanonicalValidationFailure.from_exception(
                error,
                stage=AuditFailureStage.BACKEND_INVOCATION,
                code="certified-sizing-adapter-rejection",
            )
        )
    if solution is not None:
        raw = BackendRawResult(
            backend=AuditBackend.HIGHS_DS,
            termination=BackendTermination.OPTIMAL,
            status_code=solution.highs_status_code,
            status_text="optimal",
            message=solution.highs_message,
            iterations=solution.highs_iterations,
            crossover_iterations=None,
            primal_variant_coordinates=solution.raw_primal_variables,
            reported_maximization_objective=(
                solution.reported_value_chips - task.base.objective_offset
            ),
            dual_hint_variant_rows=solution.raw_inequality_multipliers,
            dual_hint_convention=DualHintConvention.MINIMIZATION_NONPOSITIVE,
            elapsed_seconds=solution.solver_wall_seconds,
        )
        try:
            verification = verify_sizing_backend_result(
                base=task.base,
                descriptor=task.descriptor,
                raw=raw,
                context=context,
            )
            if not verification.passed:
                failures.append(
                    CanonicalValidationFailure(
                        stage=AuditFailureStage.SEMANTIC_VERIFICATION,
                        code="independent-sizing-rejection",
                        detail=",".join(failure.value for failure in verification.failures),
                    )
                )
            mismatches = _sizing_consistency_failures(task, solution, verification)
            if mismatches:
                failures.append(
                    CanonicalValidationFailure(
                        stage=AuditFailureStage.SEMANTIC_VERIFICATION,
                        code="adapter-independent-mismatch",
                        detail=",".join(mismatches),
                    )
                )
        except Exception as error:  # noqa: BLE001 - retain and continue
            failures.append(
                CanonicalValidationFailure.from_exception(
                    error,
                    stage=AuditFailureStage.SEMANTIC_VERIFICATION,
                    code="independent-sizing-verification-exception",
                )
            )
    if public_highs_call.invocation_count != 1:
        failures.append(
            CanonicalValidationFailure(
                stage=AuditFailureStage.BACKEND_INVOCATION,
                code="public-highs-call-count",
                detail=(
                    "expected one public HiGHS-DS call, observed "
                    f"{public_highs_call.invocation_count}"
                ),
            )
        )
    return CanonicalValidationObservation(
        ordinal=task.ordinal,
        base_id=task.base.base_id,
        base_sha256=task.base.digest,
        family=task.base.family,
        path=task.path,
        canonical_linear_program_sha256=task.materialized.digest,
        public_highs_ds_invocation_count=public_highs_call.invocation_count,
        micro_backend_result=None,
        exact_micro_work=None,
        micro_verification=None,
        sizing_adapter_result=solution,
        sizing_independent_verification=verification,
        failures=tuple(failures),
    )


def _execute_canonical_validation_plan(
    plan: CanonicalValidationPlan,
    *,
    linprog_function: Callable[..., Any] | None = None,
    environment: AuditEnvironmentIdentity | None = None,
    runner_source_sha256: str = "0" * 64,
    sealed_adr0319: bool,
) -> CanonicalValidationCampaign:
    """Internal common loop after the caller establishes toy or sealed authority."""

    if not isinstance(plan, CanonicalValidationPlan):
        raise TypeError("canonical validation execution requires a semantic plan")
    if linprog_function is None:
        linprog_function = import_module("scipy.optimize").linprog
    if environment is None:
        environment = capture_audit_environment_identity()
    observations: list[CanonicalValidationObservation] = []
    for task in plan.tasks:
        public_highs_call = _CountedPublicHighsCall(linprog_function)
        try:
            observation = (
                _micro_observation(task, public_highs_call=public_highs_call)
                if task.path is CanonicalValidationPath.EXACT_MICRO_HIGHS_DS
                else _sizing_observation(task, public_highs_call=public_highs_call)
            )
        except Exception as error:  # pragma: no cover - last-resort completeness guard
            failure = CanonicalValidationFailure.from_exception(
                error,
                stage=AuditFailureStage.SEMANTIC_VERIFICATION,
                code="runner-task-exception",
            )
            observation = CanonicalValidationObservation(
                ordinal=task.ordinal,
                base_id=task.base.base_id,
                base_sha256=task.base.digest,
                family=task.base.family,
                path=task.path,
                canonical_linear_program_sha256=task.materialized.digest,
                public_highs_ds_invocation_count=(
                    public_highs_call.invocation_count
                ),
                micro_backend_result=None,
                exact_micro_work=None,
                micro_verification=None,
                sizing_adapter_result=None,
                sizing_independent_verification=None,
                failures=(failure,),
            )
        observations.append(observation)
    return CanonicalValidationCampaign(
        runner_version=ADR0319_RUNNER_VERSION,
        runner_source_sha256=runner_source_sha256,
        corpus_sha256=plan.corpus_sha256,
        schedule_sha256=plan.schedule_digest,
        environment=environment,
        protocol=ADR0319_PROTOCOL,
        observations=tuple(observations),
        sealed_adr0319=sealed_adr0319,
    )


def execute_canonical_validation_plan(
    plan: CanonicalValidationPlan,
    *,
    linprog_function: Callable[..., Any] | None = None,
    environment: AuditEnvironmentIdentity | None = None,
    runner_source_sha256: str = "0" * 64,
) -> CanonicalValidationCampaign:
    """Execute an explicitly unsealed toy plan; sealed plans require the sealed entry point."""

    if not isinstance(plan, CanonicalValidationPlan):
        raise TypeError("canonical validation execution requires a semantic plan")
    if plan.sealed_adr0312:
        raise RuntimeError(
            "sealed canonical plans require execute_sealed_adr0319_canonical_validation"
        )
    return _execute_canonical_validation_plan(
        plan,
        linprog_function=linprog_function,
        environment=environment,
        runner_source_sha256=runner_source_sha256,
        sealed_adr0319=False,
    )


def assess_adr0319_canonical_validation(
    campaign: CanonicalValidationCampaign,
) -> CanonicalValidationAssessment:
    """Apply the correctness-only all-bases gate; wall times remain diagnostics."""

    from .certified_sizing_validation_seal import (
        ADR0319_SCHEDULE_SHA256,
        ADR0319_SOURCE_MANIFEST,
    )

    complete = bool(
        campaign.sealed_adr0319
        and campaign.runner_source_sha256
        == ADR0319_SOURCE_MANIFEST["certified_sizing_validation_runner.py"]
        and campaign.corpus_sha256 == ADR0311_COMPLETE_CORPUS_SHA256
        and campaign.schedule_sha256 == ADR0319_SCHEDULE_SHA256
        and campaign.environment == ADR0313_EXPECTED_ENVIRONMENT
        and len(campaign.observations) == ADR0319_EXPECTED_OBSERVATION_COUNT
        and tuple(observation.ordinal for observation in campaign.observations)
        == tuple(range(ADR0319_EXPECTED_OBSERVATION_COUNT))
    )
    one_call = all(
        observation.public_highs_ds_invocation_count == 1
        for observation in campaign.observations
    )
    passed = tuple(observation for observation in campaign.observations if observation.passed)
    failed = tuple(observation for observation in campaign.observations if not observation.passed)
    micro = tuple(
        observation
        for observation in passed
        if observation.path is CanonicalValidationPath.EXACT_MICRO_HIGHS_DS
    )
    sizing = tuple(
        observation
        for observation in passed
        if observation.path is CanonicalValidationPath.CERTIFIED_SIZING_ADAPTER
    )
    micro_exact_errors = tuple(
        abs(observation.micro_verification.exact_objective_error)
        for observation in micro
        if observation.micro_verification is not None
    )
    micro_certificate_gaps = tuple(
        abs(observation.micro_verification.certified_gap_above_exact)
        for observation in micro
        if observation.micro_verification is not None
    )
    sizing_certificate_gaps = tuple(
        abs(
            observation.sizing_independent_verification.certified_optimality_gap_chips
        )
        for observation in sizing
        if observation.sizing_independent_verification is not None
    )
    solver_wall = 0.0
    verification_wall = 0.0
    for observation in campaign.observations:
        if observation.micro_backend_result is not None:
            solver_wall += observation.micro_backend_result.elapsed_seconds
        if observation.sizing_adapter_result is not None:
            solver_wall += observation.sizing_adapter_result.solver_wall_seconds
            verification_wall += observation.sizing_adapter_result.verification_wall_seconds
    eligible = bool(
        complete
        and one_call
        and len(passed) == ADR0319_EXPECTED_OBSERVATION_COUNT
        and len(micro) == 48
        and len(sizing) == 129
    )
    return CanonicalValidationAssessment(
        complete_schedule=complete,
        one_public_call_per_base=one_call,
        passed_observation_count=len(passed),
        failed_observation_count=len(failed),
        passed_micro_count=len(micro),
        passed_sizing_count=len(sizing),
        maximum_absolute_micro_exact_error=(
            max(micro_exact_errors) if micro_exact_errors else None
        ),
        maximum_absolute_micro_certificate_gap=(
            max(micro_certificate_gaps) if micro_certificate_gaps else None
        ),
        maximum_absolute_sizing_certificate_gap_chips=(
            max(sizing_certificate_gaps) if sizing_certificate_gaps else None
        ),
        total_solver_wall_seconds=solver_wall,
        total_verification_wall_seconds=verification_wall,
        certified_v2_consumer_eligible=eligible,
        failed_base_ids=tuple(observation.base_id for observation in failed),
    )


def verify_adr0319_source_and_dependencies() -> str:
    """Verify the committed runner and all direct semantic authorities."""

    from .certified_reduced_sizing_highs import canonical_lf_source_sha256
    from .certified_sizing_validation_seal import ADR0319_SOURCE_MANIFEST

    source_root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(source_root / name)
        for name in ADR0319_SOURCE_MANIFEST
    }
    if actual != ADR0319_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0319 source or dependency differs from its committed seal")
    return actual["certified_sizing_validation_runner.py"]


def verify_adr0319_plan_identity(plan: CanonicalValidationPlan) -> None:
    """Fail before the first proposal if the exact canonical schedule drifts."""

    from .certified_reduced_sizing_highs_seal import (
        ADR0318_CANONICAL_VALIDATION_COUNTS,
    )
    from .certified_sizing_validation_seal import (
        ADR0319_PROTOCOL_SHA256,
        ADR0319_SCHEDULE_SHA256,
    )

    family_counts = {
        "known_regression_bases": sum(
            task.base.family is AuditBaseFamily.KNOWN_REGRESSION for task in plan.tasks
        ),
        "exact_micro_bases": sum(
            task.base.family is AuditBaseFamily.EXACT_MICRO for task in plan.tasks
        ),
        "fresh_sizing_bases": sum(
            task.base.family is AuditBaseFamily.FRESH_REDUCED_SIZING
            for task in plan.tasks
        ),
        "total_bases": len(plan.tasks),
    }
    if family_counts != ADR0318_CANONICAL_VALIDATION_COUNTS:
        raise RuntimeError("ADR-0319 validation family counts drifted")
    if plan.schedule_digest != ADR0319_SCHEDULE_SHA256:
        raise RuntimeError("ADR-0319 canonical schedule differs from its committed seal")
    if sha256(canonical_audit_bytes(ADR0319_PROTOCOL)).hexdigest() != ADR0319_PROTOCOL_SHA256:
        raise RuntimeError("ADR-0319 validation protocol differs from its committed seal")


def execute_sealed_adr0319_canonical_validation() -> CanonicalValidationCampaign:
    """Run the sealed 177-base campaign only after every preflight passes."""

    runner_source_sha256 = verify_adr0319_source_and_dependencies()
    verify_adr0318_source_and_dependencies()
    verify_adr0318_runtime_identity()
    environment = capture_audit_environment_identity()
    if environment != ADR0313_EXPECTED_ENVIRONMENT:
        raise RuntimeError("ADR-0319 audit runtime differs from its committed identity")
    plan = build_adr0319_canonical_validation_plan()
    verify_adr0319_plan_identity(plan)
    return _execute_canonical_validation_plan(
        plan,
        environment=environment,
        runner_source_sha256=runner_source_sha256,
        sealed_adr0319=True,
    )


__all__ = [
    "ADR0319_EXPECTED_OBSERVATION_COUNT",
    "ADR0319_PROTOCOL",
    "ADR0319_RUNNER_VERSION",
    "CanonicalValidationAssessment",
    "CanonicalValidationCampaign",
    "CanonicalValidationFailure",
    "CanonicalValidationObservation",
    "CanonicalValidationPath",
    "CanonicalValidationPlan",
    "CanonicalValidationProtocol",
    "CanonicalValidationTask",
    "assess_adr0319_canonical_validation",
    "build_adr0319_canonical_validation_plan",
    "execute_canonical_validation_plan",
    "execute_sealed_adr0319_canonical_validation",
    "verify_adr0319_plan_identity",
    "verify_adr0319_source_and_dependencies",
]
