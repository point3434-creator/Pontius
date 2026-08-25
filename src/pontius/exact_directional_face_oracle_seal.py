"""Committed source identities for ADR-0354's directional face oracle."""

from __future__ import annotations

from hashlib import sha256
import json
from types import MappingProxyType


ADR0354_PARENT_DECISION_SHA256 = (
    "c36566d1e4928a88ee67a77d8bd4c5086a08439f149a9be810e30f9325983bad"
)
ADR0354_SOURCE_MANIFEST = MappingProxyType(
    {
        "exact_directional_face_oracle.py": (
            "eb2c2e06cfaa7794570819ccbdb4558c80c62a91bf40b7a56a9c8424bb5c6ccb"
        ),
        "tie_semantics_conformance.py": (
            "036f9e5928f94bf36e5ae88108d96ca1a7127eb3f7ac860c2abc88693e4eec49"
        ),
    }
)
ADR0354_CONTROL_MANIFEST = MappingProxyType(
    {
        "test_exact_directional_face_oracle.py": (
            "e40e9f1c3c662cea1c01ed71e2034ba9f1650492a2aaff5394b2657016e37a92"
        ),
        "test_tie_semantics_conformance.py": (
            "19faad907b572787600bbb245f575090363f7d2b57bce418f6239dc66111f84b"
        ),
    }
)
_PROTOCOL_PAYLOAD = {
    "active_face": "factorized_exact_local_maximizer_sets",
    "cardinality_columns": ("total_function", "reachable_support"),
    "face_instrument": "two_independent_lexicographic_backward_passes",
    "face_tape_bound": None,
    "fan_instrument": "exact_sequence_form_normal_fan",
    "future_crossing_control": "dominated_source_row_crosses_inside_section",
    "materialized_response_tapes": 0,
    "maximum_fan_pieces_default": 256,
    "maximum_tree_nodes_default": 100000,
    "parent_decision_sha256": ADR0354_PARENT_DECISION_SHA256,
    "source_manifest": tuple(sorted(ADR0354_SOURCE_MANIFEST.items())),
    "control_manifest": tuple(sorted(ADR0354_CONTROL_MANIFEST.items())),
    "work_ledger": "linear_logical_operations_plus_exact_bigint_bit_lengths",
    "version": "adr0354-exact-directional-face-source-protocol-v1",
}
ADR0354_PROTOCOL = MappingProxyType(_PROTOCOL_PAYLOAD)
ADR0354_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


__all__ = [
    "ADR0354_CONTROL_MANIFEST",
    "ADR0354_PARENT_DECISION_SHA256",
    "ADR0354_PROTOCOL",
    "ADR0354_PROTOCOL_SHA256",
    "ADR0354_SOURCE_MANIFEST",
]
