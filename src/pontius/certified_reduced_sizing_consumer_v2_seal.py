"""Committed source identities for ADR-0321's reduced-sizing consumer."""

from types import MappingProxyType


ADR0321_CONSUMER_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "certified_reduced_sizing_highs.py": (
        "4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f"
    ),
    "certified_reduced_sizing_highs_seal.py": (
        "25acaef5776044b56ad370d42616200cc39d3d662a7ab1bc45f3366a6ae1c0b0"
    ),
    "legal_decision_spine_v2.py": (
        "a480918d5c6e5d06e2076ef64f7cccf14b63f61162b7b9d24dd7cae35825fca9"
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
})

ADR0321_CONSUMER_PROTOCOL_SHA256 = (
    "688263741a95eaf8405f3b69fd2cf7361d54ec265593883f2a55d767fca32a3c"
)

__all__ = [
    "ADR0321_CONSUMER_PROTOCOL_SHA256",
    "ADR0321_CONSUMER_SOURCE_MANIFEST",
]
