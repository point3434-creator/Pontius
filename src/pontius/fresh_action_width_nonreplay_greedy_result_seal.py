"""Committed identities for ADR-0338's solver-free greedy result owner."""

from types import MappingProxyType

from .fresh_action_width_nonreplay_greedy_seal import (
    ADR0337_GREEDY_SOURCE_MANIFEST,
)


ADR0338_GREEDY_RESULT_SOURCE_MANIFEST = MappingProxyType({
    **dict(ADR0337_GREEDY_SOURCE_MANIFEST),
    "fresh_action_width_nonreplay_greedy_seal.py": (
        "91f950d6b1c0133e1735fcc2996ec75ccd3c3ec980fa3e56dfaa5fe35042393a"
    ),
    "fresh_action_width_nonreplay_greedy_result.py": (
        "d35fcdd3bf3173bf478619662da12d780ea0343b675946211107904a9f040b56"
    ),
})
ADR0338_GREEDY_RESULT_PROTOCOL_SHA256 = (
    "97dcfec73dd209a534d0eecabd602dcf0ec5d87d99fe167db8293855f49b853e"
)


__all__ = [
    "ADR0338_GREEDY_RESULT_PROTOCOL_SHA256",
    "ADR0338_GREEDY_RESULT_SOURCE_MANIFEST",
]
