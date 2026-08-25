"""Committed identities for ADR-0356's directional-face result owner."""

from types import MappingProxyType


ADR0356_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_responder_raise_h4_directional_face_result.py": (
            "2bef9c0130b45010d34729abfb31a2cf634ed46cfbee9eeba90b4b76be251765"
        ),
    }
)
ADR0356_RESULT_PROTOCOL_SHA256 = (
    "42d97ff763bed912393cc6a92f9167565637fa46288730ffab1e5f30582a340a"
)


__all__ = [
    "ADR0356_RESULT_PROTOCOL_SHA256",
    "ADR0356_RESULT_SOURCE_MANIFEST",
]
