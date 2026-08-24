"""Committed source identities for ADR-0328's solver-free result owner."""

from types import MappingProxyType


ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST = MappingProxyType({
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
})
ADR0328_EXHAUSTIVE_TEACHER_RESULT_PROTOCOL_SHA256 = (
    "7326881f68cc159e8b702f87f7d08f5eb8782a5a79117e80574d75a2367ae7b1"
)


__all__ = [
    "ADR0328_EXHAUSTIVE_TEACHER_RESULT_PROTOCOL_SHA256",
    "ADR0328_EXHAUSTIVE_TEACHER_RESULT_SOURCE_MANIFEST",
]
