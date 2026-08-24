"""Committed source identities for ADR-0329's finite-block greedy owner."""

from types import MappingProxyType


ADR0329_GREEDY_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "certified_reduced_sizing_consumer_v2_seal.py": (
        "c4257cc79f15de3192eea8920fecf18dbb77f2e3a06eb6ad237489717b1e701a"
    ),
    "fresh_action_width_qualification.py": (
        "95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7"
    ),
    "fresh_action_width_qualification_result.py": (
        "9348231f46f83a8a3072f6e5ea7f33f76d446cbabdbd5feef4a3d800c3a16c6f"
    ),
    "fresh_action_width_qualification_result_seal.py": (
        "08dcb80b6ae5cc84bd492226c2d7038d71f73d8a236e95338ddf5762e51ffd05"
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
    "fresh_action_width_teacher.py": (
        "14250c3dbe504318640fc0ca35098c5c014e03eca23d3ea8fee4ec470705b8fd"
    ),
    "fresh_action_width_teacher_seal.py": (
        "918ead2998871744b08b318bc9b4d65e414124bdf0ff0d921ca7e9dbf56a268a"
    ),
    "fresh_action_width_teacher_result.py": (
        "c845e3308211f6e454ac6a10188897fa9f318b8ba2c89fc95e9c7b9f0931f9c1"
    ),
    "fresh_action_width_teacher_result_seal.py": (
        "1f985c587c6f446526374c0d6d45403bb689a1dd80f7aa6572a3281e17d23be5"
    ),
    "fresh_action_width_greedy.py": (
        "6e824b83c8789ae64f1859aa5536769a815aca5dd0480500268e335a3a6244f5"
    ),
})
ADR0329_GREEDY_PROTOCOL_SHA256 = (
    "dc703d044b35d4820d4a1742b4295b35cb09af720f66a5e9a21e127edbb226b2"
)
ADR0329_GREEDY_SCHEDULE_SHA256 = (
    "a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a"
)
ADR0329_GREEDY_ARM_COUNT = 2_479
ADR0329_GREEDY_TRANSITION_COUNT = 7_848
ADR0329_GREEDY_EXECUTED_CALL_COUNT = 400
ADR0330_GREEDY_REPAIRED_SOURCE_MANIFEST = MappingProxyType({
    **ADR0329_GREEDY_SOURCE_MANIFEST,
    "fresh_action_width_greedy.py": (
        "050bad76fd5fac2d3151d7500140acddcaffcf133979a0493733666413e1b26e"
    ),
})
ADR0330_GREEDY_REPAIR_PROTOCOL_SHA256 = (
    "d26ae591ec30983342607b431579b449419d51fcacf992edf27b384f69ed1d06"
)


__all__ = [
    "ADR0329_GREEDY_ARM_COUNT",
    "ADR0329_GREEDY_EXECUTED_CALL_COUNT",
    "ADR0329_GREEDY_PROTOCOL_SHA256",
    "ADR0329_GREEDY_SCHEDULE_SHA256",
    "ADR0329_GREEDY_SOURCE_MANIFEST",
    "ADR0329_GREEDY_TRANSITION_COUNT",
    "ADR0330_GREEDY_REPAIRED_SOURCE_MANIFEST",
    "ADR0330_GREEDY_REPAIR_PROTOCOL_SHA256",
]
