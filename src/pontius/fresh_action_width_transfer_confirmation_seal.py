"""Committed source identities for ADR-0342 transfer confirmation."""

from types import MappingProxyType


ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST = MappingProxyType({
    "fresh_action_width_greedy.py": (
        "050bad76fd5fac2d3151d7500140acddcaffcf133979a0493733666413e1b26e"
    ),
    "fresh_action_width_greedy_seal.py": (
        "44c9b5045eec6124919547acc13a15b920e7c57983e7105c3b4417c06a2c78ca"
    ),
    "fresh_action_width_nonreplay_greedy_result.py": (
        "d35fcdd3bf3173bf478619662da12d780ea0343b675946211107904a9f040b56"
    ),
    "fresh_action_width_nonreplay_greedy_result_seal.py": (
        "13bfafbb27fa26ec58784ff1744e66e75f6f5e3dc92228d8b04bf3d77768b807"
    ),
    "fresh_action_width_nonreplay_qualification.py": (
        "c4979aa8b84ca30c80a3a4a01f4d345bd312dfef044d57243d723c71ac39cf5d"
    ),
    "fresh_action_width_nonreplay_qualification_seal.py": (
        "5d6505be203358ed30e107ddf60071eccf89a8d6366a2faf703146d912167b94"
    ),
    "fresh_action_width_teacher.py": (
        "14250c3dbe504318640fc0ca35098c5c014e03eca23d3ea8fee4ec470705b8fd"
    ),
    "fresh_action_width_teacher_seal.py": (
        "918ead2998871744b08b318bc9b4d65e414124bdf0ff0d921ca7e9dbf56a268a"
    ),
    "fresh_action_width_transfer_confirmation.py": (
        "ec24d1710598003e7e76ff9b1062829107e28ba1766e680bec2a1411b736e202"
    ),
    "fresh_action_width_transfer_qualification.py": (
        "6233c8161084c0bab07f902c8d6033e8aa555d51ace552017ca97f53fe402bd5"
    ),
    "fresh_action_width_transfer_qualification_result.py": (
        "ed54b5676073ec019f3b544515f5a89c07b68eff5a7158b771a2d7914d83da55"
    ),
    "fresh_action_width_transfer_qualification_result_seal.py": (
        "a23559fb20e8e3ea6ff23ebfa20618022f3f7072cdc5e53f30b33eaaa0b08653"
    ),
    "fresh_action_width_transfer_qualification_seal.py": (
        "0fd8a115705772b9a11fc5d3a77f0e0c613bbd966f94dc01cfa6066d22727711"
    ),
    "fresh_action_width_transfer_structures.py": (
        "6704084f2bddfac2d58e3066b9844bc0fc633346bf3b00a7034ccc9b154e622f"
    ),
    "fresh_action_width_transfer_structures_seal.py": (
        "592287bb426ac17e16bb2bf7666016d8e4fafb616c12d6c283094abc4b8e0f69"
    ),
})
ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH = (
    "experiments/results/fresh-action-width-transfer-confirmation-v1.jsonl"
)
ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256 = (
    "0f1cc9b42a4d4c4a394acca073dee64dcd245f6496d89a3bf708dbdfecad4fa9"
)
ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256 = (
    "53389f770aa3fa0773d003df11a48858a1cb42ee166cb44bba74dda42805d7fe"
)
ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT = 126
ADR0342_SYNTHETIC_CONTROL_IDENTITIES = MappingProxyType({
    "confirmed": (
        "6c16411c7d596da7969bd92d7fa281fd7977f6250ccc30cc5fd250b96556e77c",
        "57750a9d49b2403a30b5f09ab7079a2846941a8ba6e588f111cb4c795af4ff2c",
        392_603,
        128,
    ),
    "rejected": (
        "4fbd19a5a44e0e92327c193cb4634a02cc725f61ece8767e1b0c3a6733412c71",
        "d55463f610e289185d787f874c6c95a9f0bb3b26505e03bf45c0d482b4ad1427",
        392_615,
        128,
    ),
})


__all__ = [
    "ADR0342_SYNTHETIC_CONTROL_IDENTITIES",
    "ADR0342_TRANSFER_CONFIRMATION_ARTIFACT_RELATIVE_PATH",
    "ADR0342_TRANSFER_CONFIRMATION_CANDIDATE_CALL_COUNT",
    "ADR0342_TRANSFER_CONFIRMATION_PROTOCOL_SHA256",
    "ADR0342_TRANSFER_CONFIRMATION_SCHEDULE_SHA256",
    "ADR0342_TRANSFER_CONFIRMATION_SOURCE_MANIFEST",
]
