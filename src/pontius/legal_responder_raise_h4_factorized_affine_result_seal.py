"""Committed identities for ADR-0359's factorized-affine result owner."""

from types import MappingProxyType


ADR0359_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_responder_raise_h4_factorized_affine_result.py": (
            "5c7d906ac6cfaa821a49dd5362367b0ea15813260cb6747c4b8a4cbb9c295984"
        ),
    }
)
ADR0359_RESULT_PROTOCOL_SHA256 = (
    "8d78d45a45e9988950747e40d4ee04c3e71176bdde32ef39c275d54aecb7ebda"
)


__all__ = [
    "ADR0359_RESULT_PROTOCOL_SHA256",
    "ADR0359_RESULT_SOURCE_MANIFEST",
]
