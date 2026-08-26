"""Standard-library independent reader for the ADR-0439/0440 journal."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import base64
import json
import math
from pathlib import Path
import re
from typing import Mapping

from .durable_evidence_journal import (
    JournalRecordKind,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)


_ROOT = Path(__file__).parents[2]
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0439-0440-fixed-width-device-preflight-owner-v1"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0439-0440-fixed-width-device-preflight-campaign-v1"
).hexdigest()
CONFIG_SHA256 = "84da7e82ef07620b0d7869a1e52da6a80f5f3815c0e4dc7007068ce6664ed6af"
CORRECTION_CONFIG_SHA256 = (
    "6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41"
)
MAXIMUM_JOURNAL_BYTES = 67_108_864
MAXIMUM_CUBIN_BYTES = 8_388_608
PUBLIC_WALL_NS = 270_000_000_000
LABORATORY_WALL_NS = 240_000_000_000
OUTSIDE_LABORATORY_WALL_NS = 30_000_000_000
COMPILE_RESOURCE_WALL_NS = 60_000_000_000
PER_POPULATION_ARM_WALL_NS = 30_000_000_000
DEVICE_TOTAL_BYTES = 17_094_475_776
DEVICE_RESERVE_BYTES = 2_000_000_000
REGISTER_CEILING = 255
BACKING_CEILING_BYTES = 4096
BLOCK_THREADS = 128

POSITIONAL = "positional"
RESIDENT_RRNS = "resident_nine_RRNS"
BATCHED_RRNS = "batched_five_then_four_RRNS"
ARMS = (POSITIONAL, RESIDENT_RRNS, BATCHED_RRNS)
POPULATIONS = ("complete_10", "signed_12")
KERNEL_NAMES = (
    "positional_encode_aggregate",
    "positional_forward_level",
    "positional_forward_selective",
    "positional_forward_stream",
    "positional_adjoint_level",
    "positional_adjoint_selective",
    "positional_adjoint_stream",
    "positional_contract",
    "rrns_encode_aggregate",
    "rrns_forward_level",
    "rrns_forward_selective",
    "rrns_forward_stream",
    "rrns_adjoint_level",
    "rrns_adjoint_selective",
    "rrns_adjoint_stream",
    "rrns_contract",
)
SINGLE_PASS_PHASES = (
    "candidate_state_validation_and_input_digest",
    "device_allocation_and_input_transfer",
    "family_admission_pair_encoding_and_label_aggregation",
    "forward_recurrence",
    "forward_selective_queries",
    "forward_streamed_global_scan_and_scalar_contract",
    "adjoint_recurrence",
    "adjoint_selective_queries",
    "adjoint_streamed_global_scan_and_scalar_contract",
    "scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding",
    "verification_output_transfer_and_exact_differential",
    "candidate_cleanup",
)
BATCHED_PHASES = (
    "candidate_state_validation_and_input_digest",
    "device_allocation_and_input_transfer",
    "first_batch_family_admission_pair_encoding_and_label_aggregation",
    "first_batch_forward_recurrence",
    "first_batch_forward_selective_queries",
    "first_batch_forward_streamed_global_scan_and_scalar_contract",
    "first_batch_adjoint_recurrence",
    "first_batch_adjoint_selective_queries",
    "first_batch_adjoint_streamed_global_scan_and_scalar_contract",
    "first_batch_output_drain_and_workspace_reuse_boundary",
    "second_batch_family_admission_pair_encoding_and_label_aggregation",
    "second_batch_forward_recurrence",
    "second_batch_forward_selective_queries",
    "second_batch_forward_streamed_global_scan_and_scalar_contract",
    "second_batch_adjoint_recurrence",
    "second_batch_adjoint_selective_queries",
    "second_batch_adjoint_streamed_global_scan_and_scalar_contract",
    "scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding",
    "verification_output_transfer_and_exact_differential",
    "candidate_cleanup",
)
GLOBAL_PHASES = (
    "bootstrap_handshake",
    "tool_identity_and_cuda_source_materialization",
    "compile",
    "durable_cubin_capture",
    "external_resource_inspection",
    "module_load_and_driver_attributes",
    "complete_10_host_authority_and_fixture",
    "complete_12_host_authority_and_fixture",
    "final_device_and_temporary_cleanup",
)
OUTPUT_NAMES = (
    "source_encoding",
    "aggregated_covectors",
    "aggregated_weights",
    "forward_levels",
    "forward_selected",
    "forward_stream",
    "adjoint_levels",
    "adjoint_selected",
    "adjoint_stream",
)
EXPECTED_GEOMETRY = {
    "complete_10": {
        "available_cards": 10,
        "feature_width": 176,
        "source_occupancies": 210,
        "query_occupancies": 210,
        "labeled_query_records": 1260,
    },
    "signed_12": {
        "available_cards": 12,
        "feature_width": 5,
        "source_occupancies": 924,
        "query_occupancies": 495,
        "labeled_query_records": 2970,
    },
}
TABLE_WORKING_MODULI = (
    4611686018427387701,
    4611686018427387709,
    4611686018427387733,
    4611686018427387737,
)
SCALAR_WORKING_MODULI = TABLE_WORKING_MODULI + (
    4611686018427387751,
    4611686018427387761,
    4611686018427387787,
    4611686018427387817,
)
REDUNDANT_MODULUS = 4611686018427387847
TABLE_ABSOLUTE_BOUND = (
    1241736265294193050841576639532444637352249557295785522558402560
)
SCALAR_ABSOLUTE_BOUND = int(
    "25343000991712832203818620656858029851242844262588928043335390731684288131505326860132036232212990202232374539530220339200"
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
HEADER_CLAIMS = {
    "device_preflight_result": None,
    "candidate_selected": None,
    "population_25_numeric_value": None,
    "actual_45_card_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "action_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}
SCIENTIFIC_CLAIMS = {
    key: value
    for key, value in HEADER_CLAIMS.items()
    if key not in {"device_preflight_result", "candidate_selected"}
}
DEPENDENCY_RELATIVE_PATHS = (
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v2-topology.json",
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md",
    "docs/decisions/ADR-0441-source-seal-the-corrected-fixed-width-compiled-device-preflight.md",
    "run_legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)


@dataclass(frozen=True, slots=True)
class AssessedDevicePreflight:
    terminal: str
    passed: bool
    source_commit: str
    event_count: int
    eligible_arms: tuple[str, ...]
    candidate_selected: None
    laboratory_elapsed_ns: int | None
    public_elapsed_ns: int


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("reader canonical input must be bytes")
    output = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] == 13 and index + 1 < len(raw) and raw[index + 1] == 10:
            output.append(10)
            index += 2
        else:
            output.append(raw[index])
            index += 1
    return bytes(output)


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer at least {minimum}")
    return value


def _decimal_integer(value: object, *, label: str) -> int:
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise ValueError(f"{label} must be a canonical decimal string")
    return int(value)


def _digest_rows(value: object, *, label: str) -> dict[str, str]:
    rows = _mapping(value, label=label)
    if set(rows) != set(OUTPUT_NAMES):
        raise ValueError(f"{label} output domain differs")
    output: dict[str, str] = {}
    for name in OUTPUT_NAMES:
        digest = rows[name]
        if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
            raise ValueError(f"{label} digest differs")
        output[name] = digest
    return output


def _parse_authority_manifest(value: object, *, population: str) -> dict[str, object]:
    row = _mapping(value, label="reduced authority manifest")
    expected_fields = {
        "schema_version",
        "population",
        "input_sha256",
        "geometry",
        "representation_digests",
        "scalar_values_decimal",
        "conditional_value_bits",
    }
    if (
        set(row) != expected_fields
        or row.get("schema_version")
        != "fixed-width-device-reduced-authority-manifest-v1"
        or row.get("population") != population
        or not isinstance(row.get("input_sha256"), str)
        or _DIGEST.fullmatch(str(row.get("input_sha256"))) is None
        or row.get("geometry") != EXPECTED_GEOMETRY[population]
    ):
        raise ValueError("reduced authority manifest differs")
    representations = _mapping(
        row.get("representation_digests"), label="authority representations"
    )
    if set(representations) != set(ARMS):
        raise ValueError("authority representation arm domain differs")
    positional = _digest_rows(representations[POSITIONAL], label="positional authority")
    resident = _mapping(representations[RESIDENT_RRNS], label="resident authority")
    batched = _mapping(representations[BATCHED_RRNS], label="batched authority")
    resident_key = str(tuple(range(9)))
    batched_keys = (str((0, 1, 2, 3, 8)), str((4, 5, 6, 7)))
    if set(resident) != {resident_key} or set(batched) != set(batched_keys):
        raise ValueError("authority RRNS batch domain differs")
    normalized_representations = {
        POSITIONAL: positional,
        RESIDENT_RRNS: {
            resident_key: _digest_rows(
                resident[resident_key], label="resident authority batch"
            )
        },
        BATCHED_RRNS: {
            key: _digest_rows(batched[key], label="batched authority batch")
            for key in batched_keys
        },
    }
    scalars = _mapping(row.get("scalar_values_decimal"), label="authority scalars")
    scalar_names = {"forward_numerator", "adjoint_numerator", "reach"}
    if set(scalars) != scalar_names:
        raise ValueError("authority scalar domain differs")
    normalized_scalars = {
        name: str(_decimal_integer(scalars[name], label=f"authority {name}"))
        for name in scalar_names
    }
    if any(int(value) % 720 for value in normalized_scalars.values()):
        raise ValueError("authority scalar is not divisible by 720")
    bits = _integer(
        row.get("conditional_value_bits"), label="authority binary64 bits"
    )
    if bits >= 1 << 64:
        raise ValueError("authority binary64 bits exceed uint64")
    return {
        "population": population,
        "input_sha256": row["input_sha256"],
        "representation_digests": normalized_representations,
        "scalar_values_decimal": normalized_scalars,
        "conditional_value_bits": bits,
    }


class _RRNSFaultDetected(ArithmeticError):
    pass


def _is_prime_u64(candidate: int) -> bool:
    if candidate < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small:
        if candidate == prime:
            return True
        if candidate % prime == 0:
            return False
    odd = candidate - 1
    shifts = 0
    while odd % 2 == 0:
        odd //= 2
        shifts += 1
    for base in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        witness = base % candidate
        if witness in (0, 1):
            continue
        result = pow(witness, odd, candidate)
        if result in (1, candidate - 1):
            continue
        for _ in range(shifts - 1):
            result = result * result % candidate
            if result == candidate - 1:
                break
        else:
            return False
    return True


def _signed_crt(residues: tuple[int, ...], moduli: tuple[int, ...]) -> int:
    if len(residues) != len(moduli) or not residues:
        raise ValueError("RRNS residue and modulus domains differ")
    product = math.prod(moduli)
    total = 0
    for residue, modulus in zip(residues, moduli, strict=True):
        if residue < 0 or residue >= modulus:
            raise ValueError("RRNS residue is outside its canonical interval")
        partial = product // modulus
        total += residue * partial * pow(partial, -1, modulus)
    unsigned = total % product
    return unsigned - product if unsigned > (product - 1) // 2 else unsigned


def _rrns_full(
    residues: tuple[int, ...], working: tuple[int, ...], redundant: int, bound: int
) -> int:
    decoded = _signed_crt(residues, working + (redundant,))
    if abs(decoded) > bound:
        raise _RRNSFaultDetected("rrns_channel_fault_detected")
    return decoded


def _rrns_base_extension(
    residues: tuple[int, ...], working: tuple[int, ...], redundant: int, bound: int
) -> int:
    decoded = _signed_crt(residues[:-1], working)
    if abs(decoded) > bound or decoded % redundant != residues[-1]:
        raise _RRNSFaultDetected("rrns_channel_fault_detected")
    return decoded


def _assess_rrns_fault_evidence(
    value: object, *, scalar_authority: Mapping[str, str]
) -> int:
    root = _mapping(value, label="RRNS fault evidence")
    if set(root) != {
        "schema_version",
        "changed_residue_delta",
        "table_code",
        "scalar_code",
        "correlated_control",
    } or (
        root.get("schema_version")
        != "fixed-width-device-rrns-fault-evidence-v1"
        or root.get("changed_residue_delta") != 1
    ):
        raise ValueError("RRNS fault evidence fields differ")

    for modulus in TABLE_WORKING_MODULI + SCALAR_WORKING_MODULI[4:] + (
        REDUNDANT_MODULUS,
    ):
        if modulus >= 1 << 63 or not _is_prime_u64(modulus):
            raise ValueError("RRNS frozen modulus is not prime below two-to-63")
    if (
        len(set(SCALAR_WORKING_MODULI + (REDUNDANT_MODULUS,))) != 9
        or REDUNDANT_MODULUS <= SCALAR_WORKING_MODULI[-1]
        or math.prod(TABLE_WORKING_MODULI) < 2 * TABLE_ABSOLUTE_BOUND + 1
        or math.prod(SCALAR_WORKING_MODULI) < 2 * SCALAR_ABSOLUTE_BOUND + 1
    ):
        raise ValueError("RRNS frozen theorem obligations differ")

    def parameters(
        raw: object,
        *,
        expected_working: tuple[int, ...],
        expected_bound: int,
        expected_labels: tuple[str, ...],
    ) -> list[tuple[str, int, tuple[int, ...]]]:
        row = _mapping(raw, label="RRNS parameter row")
        if set(row) != {
            "working_moduli",
            "redundant_modulus",
            "absolute_bound_decimal",
            "codewords",
        } or (
            row.get("working_moduli") != list(expected_working)
            or row.get("redundant_modulus") != REDUNDANT_MODULUS
            or _decimal_integer(
                row.get("absolute_bound_decimal"), label="RRNS absolute bound"
            )
            != expected_bound
        ):
            raise ValueError("RRNS parameter evidence differs")
        codewords = row.get("codewords")
        if not isinstance(codewords, list) or len(codewords) != len(expected_labels):
            raise ValueError("RRNS codeword domain differs")
        parsed = []
        for expected_label, raw_codeword in zip(
            expected_labels, codewords, strict=True
        ):
            codeword = _mapping(raw_codeword, label="RRNS codeword")
            if set(codeword) != {"label", "decoded_decimal", "residues"} or (
                codeword.get("label") != expected_label
            ):
                raise ValueError("RRNS codeword fields differ")
            decoded = _decimal_integer(
                codeword.get("decoded_decimal"), label="RRNS decoded value"
            )
            raw_residues = codeword.get("residues")
            if not isinstance(raw_residues, list) or len(raw_residues) != (
                len(expected_working) + 1
            ):
                raise ValueError("RRNS codeword residue count differs")
            residues = tuple(
                _integer(item, label="RRNS residue") for item in raw_residues
            )
            try:
                full = _rrns_full(
                    residues, expected_working, REDUNDANT_MODULUS, expected_bound
                )
                extended = _rrns_base_extension(
                    residues, expected_working, REDUNDANT_MODULUS, expected_bound
                )
            except _RRNSFaultDetected as error:
                raise ValueError(
                    "RRNS original codeword was rejected as a fault"
                ) from error
            if full != decoded or extended != decoded:
                raise ValueError("RRNS original codeword reconstruction differs")
            parsed.append((expected_label, decoded, residues))
        return parsed

    table = parameters(
        root["table_code"],
        expected_working=TABLE_WORKING_MODULI,
        expected_bound=TABLE_ABSOLUTE_BOUND,
        expected_labels=("source_encoding_first",),
    )
    scalar = parameters(
        root["scalar_code"],
        expected_working=SCALAR_WORKING_MODULI,
        expected_bound=SCALAR_ABSOLUTE_BOUND,
        expected_labels=("forward_numerator", "adjoint_numerator", "reach"),
    )
    for label, decoded, _ in scalar:
        if str(decoded) != scalar_authority[label] or decoded % 720:
            raise ValueError("RRNS scalar codeword differs from host authority")

    changed_controls = 0
    for working, bound, codewords in (
        (TABLE_WORKING_MODULI, TABLE_ABSOLUTE_BOUND, table),
        (SCALAR_WORKING_MODULI, SCALAR_ABSOLUTE_BOUND, scalar),
    ):
        moduli = working + (REDUNDANT_MODULUS,)
        for _, _, residues in codewords:
            for channel, modulus in enumerate(moduli):
                mutated = list(residues)
                mutated[channel] = (mutated[channel] + 1) % modulus
                detected = []
                for check in (_rrns_full, _rrns_base_extension):
                    try:
                        check(tuple(mutated), working, REDUNDANT_MODULUS, bound)
                    except _RRNSFaultDetected:
                        detected.append(True)
                    else:
                        detected.append(False)
                if detected != [True, True]:
                    raise ValueError("RRNS one-channel mutation escaped detection")
                changed_controls += 1
    if changed_controls != 32:
        raise ValueError("RRNS changed-channel control count differs")

    correlated = _mapping(root["correlated_control"], label="correlated control")
    if set(correlated) != {
        "label",
        "decoded_decimal",
        "unbounded_authority_decimal",
        "residues",
    } or correlated.get("label") != "forward_numerator_plus_720":
        raise ValueError("RRNS correlated-control fields differ")
    decoded = _decimal_integer(
        correlated.get("decoded_decimal"), label="correlated decoded value"
    )
    authority = _decimal_integer(
        correlated.get("unbounded_authority_decimal"),
        label="correlated unbounded authority",
    )
    raw_residues = correlated.get("residues")
    if not isinstance(raw_residues, list) or len(raw_residues) != 9:
        raise ValueError("correlated-control residue count differs")
    residues = tuple(_integer(item, label="correlated residue") for item in raw_residues)
    if (
        authority != int(scalar_authority["forward_numerator"])
        or decoded != authority + 720
        or _rrns_full(
            residues,
            SCALAR_WORKING_MODULI,
            REDUNDANT_MODULUS,
            SCALAR_ABSOLUTE_BOUND,
        )
        != decoded
        or _rrns_base_extension(
            residues,
            SCALAR_WORKING_MODULI,
            REDUNDANT_MODULUS,
            SCALAR_ABSOLUTE_BOUND,
        )
        != decoded
        or decoded == authority
    ):
        raise ValueError("RRNS correlated-fault boundary differs")
    return changed_controls


def _decode_command(value: object) -> tuple[Mapping[str, object], bytes, bytes]:
    row = _mapping(value, label="bounded command")
    expected = {
        "argv", "return_code", "status", "elapsed_ns",
        "stdout_base64", "stdout_bytes", "stdout_sha256",
        "stderr_base64", "stderr_bytes", "stderr_sha256",
    }
    if set(row) != expected or row.get("status") != "completed" or row.get("return_code") != 0:
        raise ValueError("bounded command fields or terminal differ")
    argv = row.get("argv")
    if not isinstance(argv, list) or any(not isinstance(item, str) for item in argv):
        raise TypeError("bounded command argv differs")
    _integer(row.get("elapsed_ns"), label="bounded command elapsed")

    def stream(prefix: str) -> bytes:
        encoded = row.get(f"{prefix}_base64")
        if not isinstance(encoded, str):
            raise TypeError("bounded command stream encoding differs")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except ValueError as error:
            raise ValueError("bounded command stream base64 differs") from error
        if (
            len(raw) != _integer(row.get(f"{prefix}_bytes"), label="stream bytes")
            or sha256(raw).hexdigest() != row.get(f"{prefix}_sha256")
        ):
            raise ValueError("bounded command stream identity differs")
        return raw

    return row, stream("stdout"), stream("stderr")


_PTXAS_FUNCTION = re.compile(
    r"(?:Compiling entry function|Function properties for)\s+'?([^'\s]+)'?"
)
_PTXAS_STACK = re.compile(
    r"(?P<stack>\d+) bytes stack frame,\s*"
    r"(?P<stores>\d+) bytes spill stores,\s*"
    r"(?P<loads>\d+) bytes spill loads"
)
_PTXAS_REGISTERS = re.compile(r"Used\s+(?P<registers>\d+)\s+registers\b")


def _parse_ptxas(raw: bytes) -> dict[str, dict[str, object]]:
    text = raw.decode("ascii")
    current: str | None = None
    rows: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        found = _PTXAS_FUNCTION.search(line)
        if found is not None:
            name = found.group(1)
            current = name if name in KERNEL_NAMES else None
            if current is not None:
                rows.setdefault(current, {})
            continue
        if current is None:
            continue
        stack = _PTXAS_STACK.search(line)
        if stack is not None:
            for key, group in (
                ("stack_frame_bytes", "stack"),
                ("spill_store_bytes", "stores"),
                ("spill_load_bytes", "loads"),
            ):
                if key in rows[current]:
                    raise ValueError("ptxas resource field repeats")
                rows[current][key] = int(stack.group(group))
        registers = _PTXAS_REGISTERS.search(line)
        if registers is not None:
            if "registers" in rows[current]:
                raise ValueError("ptxas register field repeats")
            rows[current]["registers"] = int(registers.group("registers"))
    fields = {"registers", "stack_frame_bytes", "spill_store_bytes", "spill_load_bytes"}
    if set(rows) != set(KERNEL_NAMES) or any(set(row) != fields for row in rows.values()):
        raise ValueError("ptxas kernel domain or fields differ")
    return {name: {"kernel": name, **rows[name]} for name in KERNEL_NAMES}


_CUBIN_FUNCTION = re.compile(r"^\s*Function\s+([^:]+):\s*$")
_CUBIN_FIELD = re.compile(r"\b(REG|STACK|LOCAL|SHARED):(\d+)\b")


def _parse_cuobjdump(raw: bytes) -> dict[str, dict[str, object]]:
    text = raw.decode("ascii")
    current: str | None = None
    rows: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        found = _CUBIN_FUNCTION.match(line)
        if found is not None:
            name = found.group(1).strip()
            current = name if name in KERNEL_NAMES else None
            if current is not None:
                if current in rows:
                    raise ValueError("cuobjdump kernel repeats")
                rows[current] = {}
            continue
        if current is not None:
            for key, raw_value in _CUBIN_FIELD.findall(line):
                if key in rows[current]:
                    raise ValueError("cuobjdump field repeats")
                rows[current][key] = int(raw_value)
    if set(rows) != set(KERNEL_NAMES) or any(
        set(row) != {"REG", "STACK", "LOCAL", "SHARED"} for row in rows.values()
    ):
        raise ValueError("cuobjdump kernel domain or fields differ")
    return {
        name: {
            "kernel": name,
            "registers": rows[name]["REG"],
            "stack_bytes": rows[name]["STACK"],
            "local_bytes": rows[name]["LOCAL"],
            "shared_bytes": rows[name]["SHARED"],
        }
        for name in KERNEL_NAMES
    }


_SASS_FUNCTION = re.compile(r"^\s*\.global\s+([^\s]+)\s*$")
_SASS_OPCODE = re.compile(r"\b(LDL|STL)(?:\.[A-Z0-9.]+)?\b")


def _parse_sass(raw: bytes) -> dict[str, dict[str, object]]:
    text = raw.decode("ascii")
    current: str | None = None
    seen: set[str] = set()
    counts = {name: [0, 0] for name in KERNEL_NAMES}
    for line in text.splitlines():
        found = _SASS_FUNCTION.match(line)
        if found is not None:
            name = found.group(1).rstrip(":")
            current = name if name in counts else None
            if current is not None:
                if current in seen:
                    raise ValueError("SASS kernel repeats")
                seen.add(current)
            continue
        if current is not None:
            for opcode in _SASS_OPCODE.findall(line):
                counts[current][0 if opcode == "LDL" else 1] += 1
    if seen != set(KERNEL_NAMES):
        raise ValueError("SASS kernel domain differs")
    return {
        name: {
            "kernel": name,
            "local_load_sites": counts[name][0],
            "local_store_sites": counts[name][1],
        }
        for name in KERNEL_NAMES
    }


def _binary(value: object, *, maximum: int) -> bytes:
    row = _mapping(value, label="binary evidence")
    if set(row) != {"base64", "byte_count", "sha256"}:
        raise ValueError("binary evidence fields differ")
    encoded = row.get("base64")
    if not isinstance(encoded, str):
        raise TypeError("binary evidence base64 differs")
    raw = base64.b64decode(encoded, validate=True)
    if (
        len(raw) != _integer(row.get("byte_count"), label="binary byte count")
        or len(raw) > maximum
        or sha256(raw).hexdigest() != row.get("sha256")
    ):
        raise ValueError("binary evidence identity differs")
    return raw


def _phase_rows(value: object, phases: tuple[str, ...]) -> list[dict[str, object]]:
    partition = _mapping(value, label="phase partition")
    if set(partition) != {"rows", "total_ns"}:
        raise ValueError("candidate phase partition fields differ")
    raw_rows = partition.get("rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != len(phases):
        raise ValueError("candidate phase row count differs")
    rows: list[dict[str, object]] = []
    for expected_name, raw in zip(phases, raw_rows, strict=True):
        row = _mapping(raw, label="candidate phase row")
        if set(row) != {"name", "start_ns", "end_ns", "elapsed_ns"} or row.get("name") != expected_name:
            raise ValueError("candidate phase row fields differ")
        start = _integer(row.get("start_ns"), label="phase start")
        end = _integer(row.get("end_ns"), label="phase end")
        elapsed = _integer(row.get("elapsed_ns"), label="phase elapsed")
        if end - start != elapsed:
            raise ValueError("candidate phase elapsed differs")
        rows.append(dict(row))
    total = _integer(partition.get("total_ns"), label="phase total")
    if sum(int(row["elapsed_ns"]) for row in rows) != total:
        raise ValueError("candidate phase sum differs")
    if any(left["end_ns"] != right["start_ns"] for left, right in zip(rows, rows[1:])):
        raise ValueError("candidate phase partition has a gap or overlap")
    return rows


def _schedule() -> list[tuple[str, str, int, str]]:
    rows = [("warmup", arm, 0, "ascending_colex") for arm in ARMS]
    rotations = (
        ARMS,
        (RESIDENT_RRNS, BATCHED_RRNS, POSITIONAL),
        (BATCHED_RRNS, POSITIONAL, RESIDENT_RRNS),
    )
    for order in ("ascending_colex", "descending_colex"):
        for repeat, rotation in enumerate(rotations):
            rows.extend(("timed", arm, repeat, order) for arm in rotation)
    return rows


def _assess_memory(value: object) -> dict[str, bool]:
    root = _mapping(value, label="symbolic memory")
    if set(root) != set(ARMS):
        raise ValueError("symbolic memory arm domain differs")
    output = {}
    for arm in ARMS:
        arm_row = _mapping(root[arm], label="symbolic arm memory")
        if arm_row.get("fixed_width_level_six_materialized") is not False:
            raise ValueError("fixed-width level six was materialized")
        buffers = arm_row.get("buffers")
        liveness = _mapping(arm_row.get("liveness"), label="memory liveness")
        if not isinstance(buffers, list) or not buffers:
            raise ValueError("symbolic memory buffers are absent")
        boundary_count = len(BATCHED_PHASES if arm == BATCHED_RRNS else SINGLE_PASS_PHASES) + 1
        live = []
        logical: set[str] = set()
        for boundary in range(boundary_count):
            active: dict[str, int] = {}
            for raw_buffer in buffers:
                row = _mapping(raw_buffer, label="memory buffer")
                if set(row) != {"logical_name", "storage_identity", "byte_count", "birth_boundary", "death_boundary"}:
                    raise ValueError("memory buffer fields differ")
                name = row.get("logical_name")
                storage = row.get("storage_identity")
                if not isinstance(name, str) or not isinstance(storage, str):
                    raise TypeError("memory buffer identity differs")
                if boundary == 0:
                    if name in logical:
                        raise ValueError("memory logical name repeats")
                    logical.add(name)
                count = _integer(row.get("byte_count"), label="buffer bytes", minimum=1)
                birth = _integer(row.get("birth_boundary"), label="buffer birth")
                death = _integer(row.get("death_boundary"), label="buffer death")
                if birth >= death or death > boundary_count:
                    raise ValueError("memory buffer lifetime differs")
                if birth <= boundary < death:
                    if storage in active:
                        raise ValueError("memory aliases overlap")
                    active[storage] = count
            live.append(sum(active.values()))
        peak = max(live)
        eligible = peak + DEVICE_RESERVE_BYTES <= DEVICE_TOTAL_BYTES
        if (
            liveness.get("boundary_live_bytes") != live
            or liveness.get("peak_live_bytes") != peak
            or liveness.get("peak_boundary") != live.index(peak)
            or liveness.get("device_reserve_bytes") != DEVICE_RESERVE_BYTES
            or liveness.get("device_total_bytes") != DEVICE_TOTAL_BYTES
            or liveness.get("eligible") is not eligible
        ):
            raise ValueError("symbolic memory liveness differs")
        output[arm] = eligible
    return output


def assess_device_preflight_bytes(raw: bytes) -> AssessedDevicePreflight:
    if not isinstance(raw, bytes) or len(raw) > MAXIMUM_JOURNAL_BYTES:
        raise ValueError("device-preflight journal byte envelope differs")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or recovery.invalid_suffix_bytes or len(recovery.records) < 2:
        raise ValueError("device-preflight journal is torn, invalid, or incomplete")
    if recovery.records[0].body.kind is not JournalRecordKind.HEADER or recovery.records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("device-preflight journal lifecycle differs")
    header = recovery.records[0].body.payload
    if (
        header.get("schema_version") != "legal-river-fixed-width-device-owner-header-v1"
        or header.get("protocol_sha256") != PROTOCOL_SHA256
        or header.get("campaign_sha256") != CAMPAIGN_SHA256
        or header.get("config_sha256") != CONFIG_SHA256
        or header.get("correction_config_sha256") != CORRECTION_CONFIG_SHA256
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("reserved_actual_result_relative_path")
        != "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
        or header.get("literal_worker_module")
        != "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
        or header.get("scientific_module")
        != "pontius.legal_river_quotient_fixed_width_device_preflight"
        or header.get("claims") != HEADER_CLAIMS
    ):
        raise ValueError("device-preflight header differs")
    git = _mapping(header.get("source_seal_git"), label="source seal Git")
    source_commit = git.get("commit")
    if (
        not isinstance(source_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
        or git.get("dirty") is not False
        or git.get("strict_status") is not True
    ):
        raise ValueError("device-preflight source seal differs")
    dependencies = _mapping(header.get("dependency_hashes"), label="dependency hashes")
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("device-preflight dependency domain differs")
    for relative, expected in dependencies.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise TypeError("dependency hash row differs")
        path = _ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"device-preflight dependency is absent: {relative}")
        if sha256(_canonical_lf(path.read_bytes())).hexdigest() != expected:
            raise ValueError(f"device-preflight dependency drifted: {relative}")

    observations = []
    for expected_index, envelope in enumerate(recovery.records[1:-1]):
        if envelope.body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("device-preflight nonterminal record kind differs")
        row = envelope.body.payload
        if (
            row.get("schema_version") != "legal-river-fixed-width-device-owner-observation-v1"
            or row.get("event_index") != expected_index
            or row.get("source_commit") != source_commit
            or not isinstance(row.get("kind"), str)
        ):
            raise ValueError("device-preflight observation envelope differs")
        observations.append((row["kind"], _mapping(row.get("event"), label="event")))
    if observations and observations[0][0] != "bootstrap_handshake":
        raise ValueError("device-preflight observation start differs")
    if not observations or observations[-1][0] != "terminal_evidence":
        terminal = recovery.records[-1].body.payload
        terminal_name = terminal.get("terminal")
        if (
            terminal.get("schema_version")
            != "legal-river-fixed-width-device-owner-terminal-v1"
            or terminal_name
            not in {
                "infrastructure_failure",
                "laboratory_wall_rejection",
                "public_wall_rejection",
                "outside_laboratory_wall_rejection",
            }
            or terminal.get("passed") is not False
            or terminal.get("event_count") != len(observations)
        ):
            raise ValueError("device-preflight incomplete owner terminal differs")
        public_elapsed = _integer(
            terminal.get("public_elapsed_ns"), label="public elapsed"
        )
        laboratory_raw = terminal.get("laboratory_elapsed_ns")
        laboratory_elapsed = (
            None
            if laboratory_raw is None
            else _integer(laboratory_raw, label="laboratory elapsed")
        )
        return AssessedDevicePreflight(
            terminal=str(terminal_name),
            passed=False,
            source_commit=source_commit,
            event_count=len(observations),
            eligible_arms=(),
            candidate_selected=None,
            laboratory_elapsed_ns=laboratory_elapsed,
            public_elapsed_ns=public_elapsed,
        )

    by_kind: dict[str, list[Mapping[str, object]]] = {}
    for kind, event in observations:
        by_kind.setdefault(kind, []).append(event)
    if len(by_kind.get("terminal_evidence", ())) != 1:
        raise ValueError("device-preflight terminal-evidence count differs")
    scientific_terminal = by_kind["terminal_evidence"][0]
    scientific_name = scientific_terminal.get("terminal")
    if not isinstance(scientific_name, str) or not scientific_name:
        raise ValueError("device-preflight scientific terminal name differs")
    normal_terminals = {
        "completed_device_preflight",
        "completed_no_device_candidate",
    }
    if scientific_name not in normal_terminals:
        if (
            scientific_terminal.get("passed") is not False
            or scientific_terminal.get("candidate_selected") is not None
        ):
            raise ValueError("device-preflight rejecting scientific terminal differs")
        terminal = recovery.records[-1].body.payload
        public_elapsed = _integer(
            terminal.get("public_elapsed_ns"), label="public elapsed"
        )
        laboratory_raw = terminal.get("laboratory_elapsed_ns")
        laboratory_elapsed = (
            None
            if laboratory_raw is None
            else _integer(laboratory_raw, label="laboratory elapsed")
        )
        outside = (
            None
            if laboratory_elapsed is None
            else public_elapsed - laboratory_elapsed
        )
        if (
            terminal.get("schema_version")
            != "legal-river-fixed-width-device-owner-terminal-v1"
            or terminal.get("terminal") != scientific_name
            or terminal.get("passed") is not False
            or terminal.get("event_count") != len(observations)
            or terminal.get("outside_laboratory_elapsed_ns") != outside
        ):
            raise ValueError("device-preflight rejecting owner terminal differs")
        return AssessedDevicePreflight(
            terminal=scientific_name,
            passed=False,
            source_commit=source_commit,
            event_count=len(observations),
            eligible_arms=(),
            candidate_selected=None,
            laboratory_elapsed_ns=laboratory_elapsed,
            public_elapsed_ns=public_elapsed,
        )
    required_single = {
        "bootstrap_handshake",
        "tool_identity_and_cuda_source_materialization",
        "tool_versions",
        "compile",
        "durable_cubin_capture",
        "live_hardware_identity",
        "module_load_and_resource_evidence",
        "symbolic_literal_45_memory_liveness",
        "laboratory_partition",
        "candidate_eligibility",
        "terminal_evidence",
    }
    if any(len(by_kind.get(kind, ())) != 1 for kind in required_single):
        raise ValueError("device-preflight singleton event count differs")
    if (
        len(by_kind.get("external_resource_command", ())) != 2
        or len(by_kind.get("reduced_population_authority", ())) != 2
        or len(by_kind.get("candidate_observation", ())) != 42
    ):
        raise ValueError("device-preflight repeated event count differs")
    event_kinds = [kind for kind, _ in observations]
    authority_positions = [
        index
        for index, kind in enumerate(event_kinds)
        if kind == "reduced_population_authority"
    ]
    candidate_positions = [
        index
        for index, kind in enumerate(event_kinds)
        if kind == "candidate_observation"
    ]
    if not candidate_positions or max(authority_positions) >= min(candidate_positions):
        raise ValueError("reduced authority was not durable before candidate evidence")

    bootstrap = by_kind["bootstrap_handshake"][0]
    if (
        bootstrap.get("cupy_loaded") is not False
        or bootstrap.get("scientific_source_loaded") is not False
        or bootstrap.get("parent_journal_present") is not True
        or bootstrap.get("python_no_bytecode") is not True
    ):
        raise ValueError("device-preflight bootstrap semantics differ")
    source_event = by_kind["tool_identity_and_cuda_source_materialization"][0]
    source_sha = source_event.get("cuda_source_sha256")
    if not isinstance(source_sha, str) or source_event.get("compiler_options") != [
        "--cubin", "--gpu-architecture=sm_120", "--std=c++17",
        "--ftz=false", "--prec-div=true", "--prec-sqrt=true",
        "--fmad=false", "--ptxas-options=-v",
    ]:
        raise ValueError("device-preflight source/compiler contract differs")

    tool_versions = _mapping(
        by_kind["tool_versions"][0].get("commands"), label="tool versions"
    )
    expected_tools = {
        "nvcc": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe",
        "cuobjdump": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe",
        "nvdisasm": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvdisasm.exe",
    }
    if set(tool_versions) != set(expected_tools):
        raise ValueError("device-preflight tool-version domain differs")
    for label, path in expected_tools.items():
        command, stdout, stderr = _decode_command(tool_versions[label])
        if command["argv"] != [path, "--version"] or not (
            b"release 13.3" in stdout + stderr or b"V13.3" in stdout + stderr
        ):
            raise ValueError("device-preflight tool version differs")

    compile_event = by_kind["compile"][0]
    compile_command, compile_stdout, compile_stderr = _decode_command(compile_event.get("command"))
    argv = compile_command["argv"]
    if (
        len(argv) != 12
        or argv[0] != r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe"
        or argv[1:9] != source_event["compiler_options"]
        or argv[9] != "--output-file"
    ):
        raise ValueError("device-preflight compiler argv differs")
    ptxas = _parse_ptxas(compile_stdout + compile_stderr)
    cubin_event = by_kind["durable_cubin_capture"][0]
    cubin = _binary(cubin_event.get("cubin"), maximum=MAXIMUM_CUBIN_BYTES)
    if not cubin.startswith(bytes((0x7F, 0x45, 0x4C, 0x46))) or cubin_event.get("zero_suffix_or_repair_applied") is not False:
        raise ValueError("device-preflight direct cubin differs")
    cubin_sha = sha256(cubin).hexdigest()

    external_rows = {}
    for event in by_kind["external_resource_command"]:
        command_id = event.get("command_id")
        if command_id in external_rows or command_id not in {"cuobjdump_resource_usage", "nvdisasm"}:
            raise ValueError("device-preflight external command id differs")
        if event.get("inspected_cubin_sha256") != cubin_sha:
            raise ValueError("device-preflight inspected cubin identity differs")
        external_rows[command_id] = _decode_command(event.get("command"))
    cuobjdump = _parse_cuobjdump(external_rows["cuobjdump_resource_usage"][1])
    sass = _parse_sass(external_rows["nvdisasm"][1])
    resource_event = by_kind["module_load_and_resource_evidence"][0]
    if resource_event.get("cubin_sha256") != cubin_sha:
        raise ValueError("device-preflight loaded cubin identity differs")
    if resource_event.get("ptxas") != ptxas or resource_event.get("cuobjdump") != cuobjdump or resource_event.get("sass") != sass:
        raise ValueError("device-preflight stored resource parse differs")
    streams = _mapping(resource_event.get("arm_streams"), label="arm streams")
    if streams != {
        "count": 3,
        "arms": list(ARMS),
        "one_persistent_nonblocking_stream_per_arm": True,
    }:
        raise ValueError("device-preflight persistent arm-stream contract differs")
    driver = _mapping(resource_event.get("driver"), label="driver resources")
    effective = _mapping(resource_event.get("effective"), label="effective resources")
    runtime = _mapping(resource_event.get("runtime"), label="runtime")
    live_runtime = _mapping(
        by_kind["live_hardware_identity"][0].get("runtime"),
        label="live hardware runtime",
    )
    if live_runtime != runtime:
        raise ValueError("device-preflight live and loaded runtime identities differ")
    if (
        runtime.get("device_name") != "NVIDIA GeForce RTX 5080"
        or runtime.get("compute_capability") != "120"
        or runtime.get("device_total_bytes") != DEVICE_TOTAL_BYTES
        or runtime.get("multiprocessor_count") != 84
        or runtime.get("maximum_threads_per_multiprocessor") != 1536
        or _integer(runtime.get("cuda_driver_version"), label="driver version") < 13030
        or _integer(runtime.get("cuda_runtime_version"), label="runtime version") < 13020
    ):
        raise ValueError("device-preflight runtime identity differs")
    shared_limit = _integer(runtime.get("maximum_shared_bytes_per_block"), label="shared limit")
    resource_arm_pass = {}
    for name in KERNEL_NAMES:
        d = _mapping(driver.get(name), label="driver row")
        e = _mapping(effective.get(name), label="effective row")
        if d.get("kernel") != name or e.get("kernel") != name:
            raise ValueError("device-preflight resource row label differs")
        registers = max(ptxas[name]["registers"], cuobjdump[name]["registers"], _integer(d.get("registers"), label="driver registers"))
        backing = max(ptxas[name]["stack_frame_bytes"], cuobjdump[name]["stack_bytes"] + cuobjdump[name]["local_bytes"], _integer(d.get("local_bytes"), label="driver local"))
        shared = max(cuobjdump[name]["shared_bytes"], _integer(d.get("shared_bytes"), label="driver shared"))
        eligible = (
            registers <= REGISTER_CEILING
            and backing <= BACKING_CEILING_BYTES
            and ptxas[name]["spill_store_bytes"] == 0
            and ptxas[name]["spill_load_bytes"] == 0
            and BLOCK_THREADS <= _integer(d.get("maximum_threads_per_block"), label="driver block")
            and shared <= shared_limit
        )
        expected_effective = {
            "kernel": name,
            "registers": registers,
            "backing_bytes": backing,
            "spill_store_bytes": ptxas[name]["spill_store_bytes"],
            "spill_load_bytes": ptxas[name]["spill_load_bytes"],
            "static_local_load_sites": sass[name]["local_load_sites"],
            "static_local_store_sites": sass[name]["local_store_sites"],
            "shared_bytes": shared,
            "maximum_threads_per_block": d["maximum_threads_per_block"],
            "eligible": eligible,
        }
        if dict(e) != expected_effective:
            raise ValueError("device-preflight effective resource row differs")
    for arm, prefix in ((POSITIONAL, "positional_"), (RESIDENT_RRNS, "rrns_"), (BATCHED_RRNS, "rrns_")):
        resource_arm_pass[arm] = all(bool(effective[name]["eligible"]) for name in KERNEL_NAMES if name.startswith(prefix))

    memory_event = by_kind["symbolic_literal_45_memory_liveness"][0]
    memory_pass = _assess_memory(memory_event)
    authority_rows = by_kind["reduced_population_authority"]
    authority_manifests = {
        population: _parse_authority_manifest(
            authority_rows[index], population=population
        )
        for index, population in enumerate(POPULATIONS)
    }
    candidate_events = by_kind["candidate_observation"]
    schedule = _schedule()
    candidate_rows: list[dict[str, object]] = []
    flat_candidate_phases: list[dict[str, object]] = []
    timed = {population: {arm: 0 for arm in ARMS} for population in POPULATIONS}
    fault_pass = {arm: arm == POSITIONAL for arm in ARMS}
    for population_index, population in enumerate(POPULATIONS):
        authority_manifest = authority_manifests[population]
        for schedule_index, expected_schedule in enumerate(schedule):
            event = candidate_events[population_index * len(schedule) + schedule_index]
            kind, arm, repeat, order = expected_schedule
            if (
                event.get("schema_version") != "fixed-width-device-candidate-run-v1"
                or event.get("population") != population
                or event.get("arm") != arm
                or event.get("schedule_kind") != kind
                or event.get("repeat_index") != repeat
                or event.get("traversal_order") != order
                or event.get("arm_order_index") != schedule_index
                or event.get("exact_verified") is not True
                or event.get("input_sha256")
                != authority_manifest["input_sha256"]
            ):
                raise ValueError("device-preflight candidate schedule differs")
            phases = BATCHED_PHASES if arm == BATCHED_RRNS else SINGLE_PASS_PHASES
            parsed_phases = _phase_rows(event.get("phase_partition"), phases)
            flat_candidate_phases.extend(parsed_phases)
            total = sum(int(row["elapsed_ns"]) for row in parsed_phases)
            if kind == "timed":
                timed[population][arm] += total
            expected_digests = authority_manifest["representation_digests"][arm]
            if arm == POSITIONAL:
                digest_value = _digest_rows(
                    event.get("output_digests"), label="positional candidate output"
                )
                if digest_value != expected_digests:
                    raise ValueError("positional output differs from host authority")
            else:
                controls = _assess_rrns_fault_evidence(
                    event.get("rrns_fault_evidence"),
                    scalar_authority=authority_manifest["scalar_values_decimal"],
                )
                if (
                    event.get("single_changed_channel_controls") != controls
                    or event.get("correlated_fault_boundary")
                    != "rrns_passed_unbounded_differential_rejected"
                ):
                    raise ValueError("device-preflight RRNS fault contract differs")
                digests = _mapping(event.get("batch_output_digests"), label="RRNS batch digests")
                if set(digests) != set(expected_digests):
                    raise ValueError("device-preflight RRNS pass count differs")
                digest_value = {
                    batch: _digest_rows(
                        digests[batch], label="RRNS candidate output batch"
                    )
                    for batch in expected_digests
                }
                if digest_value != expected_digests:
                    raise ValueError("RRNS output differs from host authority")
                fault_pass[arm] = True
            scalars = _mapping(event.get("scalar_values_decimal"), label="candidate scalars")
            if dict(scalars) != authority_manifest["scalar_values_decimal"] or (
                event.get("conditional_value_bits")
                != authority_manifest["conditional_value_bits"]
            ):
                raise ValueError("candidate scalar output differs from host authority")
            candidate_rows.append(dict(event))

    laboratory_event = by_kind["laboratory_partition"][0]
    lab_rows = laboratory_event.get("rows")
    if not isinstance(lab_rows, list) or laboratory_event.get("exact_sum") is not True:
        raise ValueError("device-preflight laboratory rows differ")
    expected_lab_rows: list[dict[str, object]] = []
    candidate_cursor = 0
    expected_lab_rows.extend(lab_rows[:6])
    if [row.get("name") for row in expected_lab_rows] != list(GLOBAL_PHASES[:6]):
        raise ValueError("device-preflight initial global phases differ")
    index = 6
    for fixture_name in GLOBAL_PHASES[6:8]:
        fixture = _mapping(lab_rows[index], label="fixture phase")
        if fixture.get("name") != fixture_name:
            raise ValueError("device-preflight fixture phase differs")
        expected_lab_rows.append(dict(fixture))
        index += 1
        for _ in range(len(schedule)):
            candidate = candidate_rows[candidate_cursor]
            phases = BATCHED_PHASES if candidate["arm"] == BATCHED_RRNS else SINGLE_PASS_PHASES
            parsed = _phase_rows(candidate["phase_partition"], phases)
            for expected in parsed:
                if index >= len(lab_rows) or lab_rows[index] != expected:
                    raise ValueError("candidate phase differs from laboratory ledger")
                expected_lab_rows.append(expected)
                index += 1
            candidate_cursor += 1
    if index != len(lab_rows) - 1 or lab_rows[index].get("name") != GLOBAL_PHASES[-1]:
        raise ValueError("device-preflight final global phase differs")
    expected_lab_rows.append(dict(lab_rows[index]))
    if any(left["end_ns"] != right["start_ns"] for left, right in zip(expected_lab_rows, expected_lab_rows[1:])):
        raise ValueError("device-preflight laboratory has a gap or overlap")
    laboratory_elapsed = _integer(laboratory_event.get("total_ns"), label="laboratory elapsed")
    if sum(int(row["elapsed_ns"]) for row in expected_lab_rows) != laboratory_elapsed:
        raise ValueError("device-preflight laboratory sum differs")

    eligibility_event = by_kind["candidate_eligibility"][0]
    eligibility = _mapping(eligibility_event, label="candidate eligibility")
    if set(eligibility) != set(ARMS):
        raise ValueError("device-preflight eligibility arm domain differs")
    eligible_arms = []
    compile_elapsed = sum(int(row["elapsed_ns"]) for row in expected_lab_rows[1:6])
    compile_pass = compile_elapsed <= COMPILE_RESOURCE_WALL_NS
    lab_pass = laboratory_elapsed <= LABORATORY_WALL_NS
    for arm in ARMS:
        row = _mapping(eligibility[arm], label="arm eligibility")
        walls = _mapping(row.get("timed_population_walls"), label="timed walls")
        wall_pass = True
        for population in POPULATIONS:
            wall = _mapping(walls.get(population), label="population wall")
            passed = timed[population][arm] <= PER_POPULATION_ARM_WALL_NS
            if wall.get("elapsed_ns") != timed[population][arm] or wall.get("ceiling_ns") != PER_POPULATION_ARM_WALL_NS or wall.get("passed") is not passed:
                raise ValueError("device-preflight timed wall differs")
            wall_pass &= passed
        expected_eligible = (
            resource_arm_pass[arm]
            and memory_pass[arm]
            and compile_pass
            and lab_pass
            and wall_pass
            and fault_pass[arm]
        )
        if (
            row.get("resource_eligible") is not resource_arm_pass[arm]
            or row.get("symbolic_literal_45_memory_eligible") is not memory_pass[arm]
            or row.get("complete_reduced_exactness") is not True
            or row.get("RRNS_fault_contract") is not fault_pass[arm]
            or row.get("compile_and_resource_wall") is not compile_pass
            or row.get("laboratory_wall") is not lab_pass
            or row.get("eligible") is not expected_eligible
        ):
            raise ValueError("device-preflight eligibility recomputation differs")
        if expected_eligible:
            eligible_arms.append(arm)

    evidence = by_kind["terminal_evidence"][0]
    expected_terminal = "completed_device_preflight" if eligible_arms else "completed_no_device_candidate"
    expected_counts = {
        population: {
            arm: {
                "warmup": 1,
                "timed_ascending": 3,
                "timed_descending": 3,
            }
            for arm in ARMS
        }
        for population in POPULATIONS
    }
    if (
        evidence.get("terminal") != expected_terminal
        or evidence.get("passed") is not bool(eligible_arms)
        or evidence.get("candidate_selected") is not None
        or evidence.get("cuda_source_sha256") != source_sha
        or evidence.get("cubin_sha256") != cubin_sha
        or evidence.get("runtime") != runtime
        or evidence.get("compile_and_resource_elapsed_ns") != compile_elapsed
        or evidence.get("resource_rows") != effective
        or evidence.get("symbolic_literal_45_memory_liveness") != memory_event
        or evidence.get("authority_manifests") != authority_rows
        or evidence.get("candidate_observations") != candidate_rows
        or evidence.get("observed_counts") != expected_counts
        or evidence.get("laboratory_partition") != laboratory_event
        or evidence.get("eligibility") != eligibility_event
        or evidence.get("claims") != SCIENTIFIC_CLAIMS
    ):
        raise ValueError("device-preflight scientific terminal differs")

    terminal = recovery.records[-1].body.payload
    public_elapsed = _integer(terminal.get("public_elapsed_ns"), label="public elapsed")
    outside = public_elapsed - laboratory_elapsed
    owner_terminal = expected_terminal
    if public_elapsed > PUBLIC_WALL_NS:
        owner_terminal = "public_wall_rejection"
    elif outside > OUTSIDE_LABORATORY_WALL_NS:
        owner_terminal = "outside_laboratory_wall_rejection"
    if (
        terminal.get("schema_version") != "legal-river-fixed-width-device-owner-terminal-v1"
        or terminal.get("event_count") != len(observations)
        or terminal.get("laboratory_elapsed_ns") != laboratory_elapsed
        or terminal.get("outside_laboratory_elapsed_ns") != outside
        or terminal.get("terminal") != owner_terminal
        or terminal.get("passed") is not (owner_terminal == "completed_device_preflight")
        or terminal.get("claims")
        != {
            **HEADER_CLAIMS,
            "device_preflight_result": (
                True if owner_terminal in normal_terminals else None
            ),
        }
    ):
        raise ValueError("device-preflight owner terminal differs")
    return AssessedDevicePreflight(
        terminal=owner_terminal,
        passed=owner_terminal == "completed_device_preflight",
        source_commit=source_commit,
        event_count=len(observations),
        eligible_arms=tuple(eligible_arms),
        candidate_selected=None,
        laboratory_elapsed_ns=laboratory_elapsed,
        public_elapsed_ns=public_elapsed,
    )


def assess_device_preflight_file(path: Path = RESULT_PATH) -> AssessedDevicePreflight:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("device-preflight result is absent")
    return assess_device_preflight_bytes(path.read_bytes())


__all__ = [
    "AssessedDevicePreflight",
    "CAMPAIGN_SHA256",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_device_preflight_bytes",
    "assess_device_preflight_file",
]
