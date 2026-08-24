"""Committed identities for ADR-0351's corrected selector-fan result owner."""

from types import MappingProxyType


ADR0351_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_responder_raise_h4_selector_fan_result.py": (
            "9ed770a532cb2a665dbe6b01c2385f66b763ab02d86750e9b44642a5df894d9a"
        ),
    }
)
ADR0351_RESULT_PROTOCOL_SHA256 = (
    "12e95e2ca5adfd14dc5557101a099dbefbffa20062e079bf18d3db14d59c6f0f"
)


__all__ = [
    "ADR0351_RESULT_PROTOCOL_SHA256",
    "ADR0351_RESULT_SOURCE_MANIFEST",
]
