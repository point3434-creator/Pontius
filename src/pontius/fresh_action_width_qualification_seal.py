"""Committed source identities for ADR-0323's qualification owner."""

from types import MappingProxyType


ADR0323_QUALIFICATION_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "certified_reduced_sizing_consumer_v2_seal.py": (
        "c4257cc79f15de3192eea8920fecf18dbb77f2e3a06eb6ad237489717b1e701a"
    ),
    "fresh_action_width_qualification.py": (
        "95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7"
    ),
    "fresh_action_width_structures.py": (
        "429f72fff02de515536db36a4754708e71cf93653ad6574026c1fe3c4de82acf"
    ),
    "fresh_action_width_structures_seal.py": (
        "7c810d4bdd1eae509c50ae8ddd44fc221837241eeb186e5a67a86d79bb61ed29"
    ),
})
ADR0323_QUALIFICATION_PROTOCOL_SHA256 = (
    "154e7dad5a95165b064deda4a550bd61483e4ffe572f1203c8792d3c45baa70a"
)
ADR0323_QUALIFICATION_SCHEDULE_SHA256 = (
    "de4b5c39cb973673d51dd9b80be5e47193d6b0ace77c77cd56471dca7eeeb6cc"
)
ADR0323_QUALIFICATION_TASK_COUNT = 192


__all__ = [
    "ADR0323_QUALIFICATION_PROTOCOL_SHA256",
    "ADR0323_QUALIFICATION_SCHEDULE_SHA256",
    "ADR0323_QUALIFICATION_SOURCE_MANIFEST",
    "ADR0323_QUALIFICATION_TASK_COUNT",
]
