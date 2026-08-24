"""Committed value-free structure identities for ADR-0323."""

from types import MappingProxyType


ADR0323_STRUCTURE_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "certified_reduced_sizing_consumer_v2_seal.py": (
        "c4257cc79f15de3192eea8920fecf18dbb77f2e3a06eb6ad237489717b1e701a"
    ),
    "fresh_action_width_structures.py": (
        "429f72fff02de515536db36a4754708e71cf93653ad6574026c1fe3c4de82acf"
    ),
    "no_limit_betting.py": (
        "9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396"
    ),
    "river.py": (
        "bc56fefc3c24d371a9dd57048aa8e644a3ca6a111b35fe3dc1d5168bdb9046cb"
    ),
})
ADR0323_STRUCTURE_PROTOCOL_SHA256 = (
    "938ab634acdb993341229878407529cf80117ae6dab154dcc789d2814a097671"
)
ADR0323_DEVELOPMENT_POOL_SHA256 = (
    "48e084db53941615f3b1e2d13814718a2c833369b0b5e827f3adc7ee1fc799ed"
)
ADR0323_DEVELOPMENT_CANDIDATE_ATTEMPTS = 440
ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH = (
    (2, 96),
    (3, 678),
    (4, 2_177),
    (5, 4_203),
    (6, 5_402),
)
ADR0323_TOTAL_SUBSET_COUNT = 12_556


__all__ = [
    "ADR0323_DEVELOPMENT_CANDIDATE_ATTEMPTS",
    "ADR0323_DEVELOPMENT_POOL_SHA256",
    "ADR0323_STRUCTURE_PROTOCOL_SHA256",
    "ADR0323_STRUCTURE_SOURCE_MANIFEST",
    "ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH",
    "ADR0323_TOTAL_SUBSET_COUNT",
]
