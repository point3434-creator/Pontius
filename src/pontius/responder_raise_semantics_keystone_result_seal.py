"""Committed identities for ADR-0345's responder-raise result owner."""

from types import MappingProxyType


ADR0345_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "responder_raise_semantics_keystone_result.py": (
            "757c593081d78e7823cfa680b782385ddbb33badfe70d8ef907478c1ce8791b7"
        ),
    }
)
ADR0345_RESULT_PROTOCOL_SHA256 = (
    "e459d7ea2d2e9ea6f63918fa1fac7985f7411a3d4f07e3935d897a11a45e0793"
)


__all__ = [
    "ADR0345_RESULT_PROTOCOL_SHA256",
    "ADR0345_RESULT_SOURCE_MANIFEST",
]
