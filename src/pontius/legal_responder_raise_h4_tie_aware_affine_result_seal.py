"""Committed identities for ADR-0353's tie-aware h4 result owner."""

from types import MappingProxyType


ADR0353_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_responder_raise_h4_tie_aware_affine_result.py": (
            "045fd30a6d383c5a89f686943f31bb2fa424334d602710288fc5e082eb7bfc2c"
        ),
    }
)
ADR0353_RESULT_PROTOCOL_SHA256 = (
    "cdff79741d944a8bd576273c9658edd3fab51c482e04275915f3e0dc2bd0661c"
)


__all__ = [
    "ADR0353_RESULT_PROTOCOL_SHA256",
    "ADR0353_RESULT_SOURCE_MANIFEST",
]
