"""Committed identities for ADR-0334's non-replay qualification result."""

from types import MappingProxyType


ADR0334_QUALIFICATION_RESULT_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "certified_reduced_sizing_consumer_v2_seal.py": (
        "c4257cc79f15de3192eea8920fecf18dbb77f2e3a06eb6ad237489717b1e701a"
    ),
    "certified_reduced_sizing_highs.py": (
        "4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f"
    ),
    "certified_reduced_sizing_highs_seal.py": (
        "25acaef5776044b56ad370d42616200cc39d3d662a7ab1bc45f3366a6ae1c0b0"
    ),
    "durable_evidence_journal.py": (
        "a9f815a41abc8d9977375e0c8e71f66f788dd8d811d016735cb08ffa06bf5c11"
    ),
    "fresh_action_width_nonreplay.py": (
        "b870feb17d6e344b130f7b30d8b776be5b40537e3e71b7a14b9b4d2bcbae3e92"
    ),
    "fresh_action_width_nonreplay_qualification.py": (
        "c4979aa8b84ca30c80a3a4a01f4d345bd312dfef044d57243d723c71ac39cf5d"
    ),
    "fresh_action_width_nonreplay_qualification_result.py": (
        "bb3e0838b7c6e1e08941c18f32fe5bbcfa66aad7657fd1edbcf1a908fa42b352"
    ),
    "fresh_action_width_nonreplay_qualification_seal.py": (
        "5d6505be203358ed30e107ddf60071eccf89a8d6366a2faf703146d912167b94"
    ),
    "fresh_action_width_nonreplay_seal.py": (
        "2dbe1314ae4922c87af127fb8f1c1d8b6473b7394a78384721ac9f883840a98c"
    ),
    "fresh_action_width_qualification.py": (
        "95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7"
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
    "linear_program_certificate.py": (
        "0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910"
    ),
    "no_limit_betting.py": (
        "9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396"
    ),
    "reduced_river_sizing_lp.py": (
        "3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346"
    ),
    "river.py": (
        "bc56fefc3c24d371a9dd57048aa8e644a3ca6a111b35fe3dc1d5168bdb9046cb"
    ),
})
ADR0334_QUALIFICATION_RESULT_PROTOCOL_SHA256 = (
    "8b6a07730d59afb081013f644d455b4a0756eee82a6f9364a902ff4e8695a3fc"
)


__all__ = [
    "ADR0334_QUALIFICATION_RESULT_PROTOCOL_SHA256",
    "ADR0334_QUALIFICATION_RESULT_SOURCE_MANIFEST",
]
