"""Committed identities for ADR-0347's legal h4 result owner."""

from types import MappingProxyType


ADR0347_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_responder_raise_h4_coefficient_result.py": (
            "4c67ce1e724e6196a1fff6d7d6312c7a117fd9ff5ea47c8e82d7a1f21e8e1547"
        ),
    }
)
ADR0347_RESULT_PROTOCOL_SHA256 = (
    "88ff8d65f25d34cd99225d23c5cb3689b72a414e79863e8eb0fccd40565acdd6"
)


__all__ = [
    "ADR0347_RESULT_PROTOCOL_SHA256",
    "ADR0347_RESULT_SOURCE_MANIFEST",
]
