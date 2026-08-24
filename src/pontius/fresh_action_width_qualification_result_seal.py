"""Committed identities for ADR-0326's qualification-result owner."""

from types import MappingProxyType


ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "fresh_action_width_qualification.py": (
        "95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7"
    ),
    "fresh_action_width_qualification_result.py": (
        "9348231f46f83a8a3072f6e5ea7f33f76d446cbabdbd5feef4a3d800c3a16c6f"
    ),
    "fresh_action_width_qualification_seal.py": (
        "7ebd5e9b234b9c28339f2a49214889c3acfdb879c8cb529dd4c7b57c56d5aa76"
    ),
    "fresh_action_width_structures.py": (
        "429f72fff02de515536db36a4754708e71cf93653ad6574026c1fe3c4de82acf"
    ),
    "fresh_action_width_structures_seal.py": (
        "7c810d4bdd1eae509c50ae8ddd44fc221837241eeb186e5a67a86d79bb61ed29"
    ),
})
ADR0326_QUALIFICATION_RESULT_PROTOCOL_SHA256 = (
    "2dee4847e4eb4ba209b6ae300f9214890204ce25a02144f2e7237a401db906db"
)


__all__ = [
    "ADR0326_QUALIFICATION_RESULT_PROTOCOL_SHA256",
    "ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST",
]
