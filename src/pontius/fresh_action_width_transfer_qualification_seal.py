"""Committed source identities for ADR-0340 transfer qualification."""

from types import MappingProxyType


ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST = MappingProxyType({
    "fresh_action_width_nonreplay_qualification.py": (
        "c4979aa8b84ca30c80a3a4a01f4d345bd312dfef044d57243d723c71ac39cf5d"
    ),
    "fresh_action_width_nonreplay_qualification_seal.py": (
        "5d6505be203358ed30e107ddf60071eccf89a8d6366a2faf703146d912167b94"
    ),
    "fresh_action_width_transfer_qualification.py": (
        "6233c8161084c0bab07f902c8d6033e8aa555d51ace552017ca97f53fe402bd5"
    ),
    "fresh_action_width_transfer_structures.py": (
        "6704084f2bddfac2d58e3066b9844bc0fc633346bf3b00a7034ccc9b154e622f"
    ),
    "fresh_action_width_transfer_structures_seal.py": (
        "592287bb426ac17e16bb2bf7666016d8e4fafb616c12d6c283094abc4b8e0f69"
    ),
})
ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-transfer-qualification-v1.jsonl"
)
ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256 = (
    "d3b39c8cb99825844bbe4210fc235eee12e8f525e69bbd55187007d6361154f8"
)
ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256 = (
    "d54267fc71c165637fbf1ea73c7e29be7a6d0471a01396ca788099625087b680"
)
ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT = 192
ADR0340_SYNTHETIC_CONTROL_IDENTITIES = MappingProxyType({
    "ambiguous": (
        "26e61f485762f943202c57c0480fc6822a515391e3d1f3171c0849812e81a379",
        "bdb1a720af252d716932006d4d6528aa01f95606302ea60d4ad0ca1ab0ac3e1b",
        9_554,
        4,
    ),
    "exhausted": (
        "344f005e908374d1b3d9daaa3fdb14d8988f8eae758274bd89563a8b2697b64d",
        "0069d323b77368199c3ca1ec959545850afc0506c4568c6d03b746a1b2c488f5",
        648_106,
        194,
    ),
    "rejected": (
        "eb6d3f69892fb17f8d677d7fe6d8e3e3ba9bd304d17b09728ae87e0f99f998b4",
        "8fd911d4eb1ca979db512f44f4c0f27eb7b9df6961e55174659fec615dad433d",
        8_416,
        4,
    ),
    "reversal": (
        "64ff1bf966795c38c98f3fdd31138efd24a707a5c573a93ac70867dc95f27065",
        "a174199da87b5ae828fe374c22c7313907f990b4796fd5e152252e9a456baba6",
        9_083,
        4,
    ),
    "target": (
        "81f704a48c0a6c7879ed1a0c53a1786f6779ccc2590ffe4314edd580a26e85ca",
        "4586c50af5b290782d2ba818fedb90337a4b7c200bef0b18920d8367997f9b29",
        111_357,
        34,
    ),
    "unexpected": (
        "4d1255f9e1e8acfd06fac79043fdc052d55f85482f381a685bda0505e0b714f4",
        "b164cb1d5d63958577f877df3f4443502aa334200dd7a2c7a0cb55a9e3b9b508",
        7_782,
        4,
    ),
})
ADR0340_SYNTHETIC_TARGET_PANEL_SHA256 = (
    "80ddf860fe6914fef190c17e236b5b5bcc106bcebe95cb97dd032b4b133d6d85"
)


__all__ = [
    "ADR0340_SYNTHETIC_CONTROL_IDENTITIES",
    "ADR0340_SYNTHETIC_TARGET_PANEL_SHA256",
    "ADR0340_TRANSFER_QUALIFICATION_ARTIFACT_RELATIVE_PATH",
    "ADR0340_TRANSFER_QUALIFICATION_PROTOCOL_SHA256",
    "ADR0340_TRANSFER_QUALIFICATION_SCHEDULE_SHA256",
    "ADR0340_TRANSFER_QUALIFICATION_SOURCE_MANIFEST",
    "ADR0340_TRANSFER_QUALIFICATION_TASK_COUNT",
]
