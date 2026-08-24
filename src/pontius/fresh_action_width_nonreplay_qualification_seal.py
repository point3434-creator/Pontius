"""Committed source identities for ADR-0331 non-replay qualification."""

from types import MappingProxyType


ADR0331_QUALIFICATION_SOURCE_MANIFEST = MappingProxyType({
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
    "river.py": (
        "bc56fefc3c24d371a9dd57048aa8e644a3ca6a111b35fe3dc1d5168bdb9046cb"
    ),
    "reduced_river_sizing_lp.py": (
        "3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346"
    ),
})
ADR0331_QUALIFICATION_PROTOCOL_SHA256 = (
    "3506b0a33aec61b85b1a0a9ade7e1d86c8a944ad79cecbb1253b611d46c69c61"
)
ADR0331_QUALIFICATION_SCHEDULE_SHA256 = (
    "132513efa7cdf32298e5d19cb60afa69fda2580a8e98c9b3e4724781d07a50b2"
)
ADR0331_QUALIFICATION_TASK_COUNT = 192
ADR0333_SYNTHETIC_CONTROL_IDENTITIES = MappingProxyType({
    "ambiguous": (
        "49541d168708cdb305311b8549f4cb850fd1cdf8bda476fc0ec50c90a5774864",
        "9239404d6fbfe34324f120b3a2e3b310696fba024d490516f676944360a94e3d",
        9798,
        4,
    ),
    "exhausted": (
        "13dc7916bcd5e8942d8dee5b7a2c352274f3a0d2cd13fdf86ab10ed1093af25c",
        "4224ad6f3c406e20c46bd8a89945399ef2612f1deb43fcb55f1639bb4692589a",
        645537,
        194,
    ),
    "rejected": (
        "b178e18ab81b076fef88425c282bf9c997bc43a6f35a70e6e4437abac43f34f7",
        "32308496ebab95ff148b3c44ee996392d7ee51c3c74a4da4cb69d7fbcd558512",
        8721,
        4,
    ),
    "reversal": (
        "3551a5fbaff22196428bd2ebf557daffce608787e6d4115e334a0e668df47e8d",
        "01f121d981f13f6b43c2112d676dd9b0315ff2f5d78724c4b1359dfc13eca790",
        9388,
        4,
    ),
    "target": (
        "678ec8ab4e981b0a70eea56cd01ed312824f4a1ae8d5638942704bcbaaf639af",
        "244f501d2c74e673300dcb78d6e7df6bbd8cc6bbb8943311477397954559d8d8",
        111424,
        34,
    ),
    "unexpected": (
        "98ab541a5cbf9502603d33d14e4dba7f8412e250189794371dfa93abcf1d3c57",
        "e75a1d7d114b3de5c1af6053300467e51982574a934bb1eae1ead2e9b9368d0a",
        8077,
        4,
    ),
})


__all__ = [
    "ADR0331_QUALIFICATION_PROTOCOL_SHA256",
    "ADR0331_QUALIFICATION_SCHEDULE_SHA256",
    "ADR0331_QUALIFICATION_SOURCE_MANIFEST",
    "ADR0331_QUALIFICATION_TASK_COUNT",
    "ADR0333_SYNTHETIC_CONTROL_IDENTITIES",
]
