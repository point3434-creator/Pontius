"""Committed identities for the factorized tie-aware affine source boundary."""

from __future__ import annotations

from hashlib import sha256
import json
from types import MappingProxyType


ADR0357_PARENT_DECISION_SHA256 = (
    "c0e144389158baaa26698bf93537b73e0c5f5ddfad637e75e02c2f01831b46bf"
)
ADR0357_SOURCE_MANIFEST = MappingProxyType(
    {
        "factorized_tie_aware_affine.py": (
            "cb9d1cbf7cef390a7b8c2adfee0ef0fed416c77e781902e07a53fc912b378276"
        ),
        "tie_semantics_conformance_v2.py": (
            "9740d26d1cca4cd6ff926115ff315ad6bd367848669cb6ee213e917250dd957e"
        ),
    }
)
ADR0357_CONTROL_MANIFEST = MappingProxyType(
    {
        "test_factorized_tie_aware_affine.py": (
            "d8aabc5248be0adba1d161999f65193f132c55f2db1208ed54f4051c12f9fc2b"
        ),
        "test_tie_semantics_conformance_v2.py": (
            "3e0ad57835617a0676c83671b8450a7b4c0d8acf847c7ab2398ab3f54e4f2bec"
        ),
    }
)
_PROTOCOL_PAYLOAD = {
    "boundary_slope_semantics": (
        "full_face_at_point_inward_one_sided_fan_owner_at_ray_endpoints"
    ),
    "cardinality_columns": ("total_function", "reachable_support"),
    "certificate_identity_authority": "total_function_only",
    "control_manifest": tuple(sorted(ADR0357_CONTROL_MANIFEST.items())),
    "epigraph_orientation": "z_greater_than_or_equal_to_every_row",
    "exact_envelope_domain": ("0/1", "1/1"),
    "exact_source_tie_dispatch": "factorized_tie_aware_maximum_envelope",
    "face_materialization_bound": None,
    "historical_tie_registry_mutated": False,
    "maximum_fan_pieces_default": 256,
    "maximum_tree_nodes_default": 100000,
    "parent_decision_sha256": ADR0357_PARENT_DECISION_SHA256,
    "point_authority": "two_pass_factorized_directional_face",
    "ray_authority": "exact_selector_normal_fan",
    "reachable_identity_role": "reporting_only",
    "singleton_dispatch": "selector_window_v2",
    "source_manifest": tuple(sorted(ADR0357_SOURCE_MANIFEST.items())),
    "tape_cartesian_product": "forbidden",
    "version": "adr0357-factorized-tie-aware-affine-source-protocol-v1",
}
ADR0357_PROTOCOL = MappingProxyType(_PROTOCOL_PAYLOAD)
ADR0357_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _PROTOCOL_PAYLOAD,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()


__all__ = [
    "ADR0357_CONTROL_MANIFEST",
    "ADR0357_PARENT_DECISION_SHA256",
    "ADR0357_PROTOCOL",
    "ADR0357_PROTOCOL_SHA256",
    "ADR0357_SOURCE_MANIFEST",
]
