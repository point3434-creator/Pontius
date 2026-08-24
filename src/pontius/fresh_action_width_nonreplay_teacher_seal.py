"""Committed source identities for ADR-0335's non-replay exhaustive teacher."""

from types import MappingProxyType


ADR0335_TEACHER_SOURCE_MANIFEST = MappingProxyType({
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
    "fresh_action_width_nonreplay_qualification_result_seal.py": (
        "605b7d7ae3fab3efa0a81c4753b70215b310ce7e930952d8c79e99ce223199bd"
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
    "fresh_action_width_nonreplay_teacher.py": (
        "62598e606be983b9fef60a32933bcbbb113ab75aca5aa326bb05d1b2d8b7071f"
    ),
})
ADR0335_TEACHER_PROTOCOL_SHA256 = (
    "475866512b9c0d7c12cab51e32fa36efdc7be6922c09ea7d8b2a069f521f2a11"
)
ADR0335_TEACHER_SCHEDULE_SHA256 = (
    "94da8f2fbcef3f16e74e729442c8c65bdd0c75be0cb400c4ebee66336b4dcb2d"
)
ADR0335_TEACHER_SUBSET_COUNTS = (
    (2, 16),
    (3, 114),
    (4, 367),
    (5, 705),
    (6, 895),
)
ADR0335_TEACHER_TASK_COUNT = 2_113
ADR0335_SYNTHETIC_COMPLETED_CONTROL = MappingProxyType({
    "context_count": 16,
    "journal_byte_count": 6_616_076,
    "journal_sha256": (
        "b9f6bde14df55fa90534ed874c683063df5adcee3e56b10311d04d5aaf9f034f"
    ),
    "public_call_count": 2_113,
    "record_count": 2_115,
    "terminal_sha256": (
        "c8ecbe9960ec89aef6a1705dc10f8b8aa846e20485444f65bc31598c833c29ef"
    ),
})


__all__ = [
    "ADR0335_SYNTHETIC_COMPLETED_CONTROL",
    "ADR0335_TEACHER_PROTOCOL_SHA256",
    "ADR0335_TEACHER_SCHEDULE_SHA256",
    "ADR0335_TEACHER_SOURCE_MANIFEST",
    "ADR0335_TEACHER_SUBSET_COUNTS",
    "ADR0335_TEACHER_TASK_COUNT",
]
