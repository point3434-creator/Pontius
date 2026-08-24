"""Committed identities for ADR-0341's transfer qualification result."""

from types import MappingProxyType


ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_consumer_v2.py": (
        "931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a"
    ),
    "certified_reduced_sizing_consumer_v2_seal.py": (
        "c4257cc79f15de3192eea8920fecf18dbb77f2e3a06eb6ad237489717b1e701a"
    ),
    "durable_evidence_journal.py": (
        "a9f815a41abc8d9977375e0c8e71f66f788dd8d811d016735cb08ffa06bf5c11"
    ),
    "fresh_action_width_nonreplay_qualification.py": (
        "c4979aa8b84ca30c80a3a4a01f4d345bd312dfef044d57243d723c71ac39cf5d"
    ),
    "fresh_action_width_nonreplay_qualification_seal.py": (
        "5d6505be203358ed30e107ddf60071eccf89a8d6366a2faf703146d912167b94"
    ),
    "fresh_action_width_qualification.py": (
        "95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7"
    ),
    "fresh_action_width_qualification_seal.py": (
        "7ebd5e9b234b9c28339f2a49214889c3acfdb879c8cb529dd4c7b57c56d5aa76"
    ),
    "fresh_action_width_transfer_qualification.py": (
        "6233c8161084c0bab07f902c8d6033e8aa555d51ace552017ca97f53fe402bd5"
    ),
    "fresh_action_width_transfer_qualification_result.py": (
        "ed54b5676073ec019f3b544515f5a89c07b68eff5a7158b771a2d7914d83da55"
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
ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256 = (
    "45b8e3ae8cadd93afa9ab60c8b4f18bd977ff35e38130ac0e35def81352fedc7"
)


__all__ = [
    "ADR0341_TRANSFER_QUALIFICATION_RESULT_PROTOCOL_SHA256",
    "ADR0341_TRANSFER_QUALIFICATION_RESULT_SOURCE_MANIFEST",
]
