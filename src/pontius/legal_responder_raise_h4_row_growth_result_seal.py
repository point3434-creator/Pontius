"""Committed identities for ADR-0349's legal h4 row-growth result owner."""

from types import MappingProxyType


ADR0349_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_responder_raise_h4_row_growth_result.py": (
            "b300b5b5a022a698c7bce2c77a99212da272ecaa50e1964eac76a21c392add53"
        ),
    }
)
ADR0349_RESULT_PROTOCOL_SHA256 = (
    "d7184b60f9fd3c46ae761864ed28d59cd9e91af0b03eab950aa74fb67aafbd89"
)


__all__ = [
    "ADR0349_RESULT_PROTOCOL_SHA256",
    "ADR0349_RESULT_SOURCE_MANIFEST",
]
