"""Committed identities for ADR-0362's confirmation-result owner."""

from types import MappingProxyType


ADR0362_RESULT_SOURCE_MANIFEST = MappingProxyType(
    {
        "legal_h4_factorized_affine_confirmation_result.py": (
            "505b01eecfcd15c402bdd1a895d7e9ad5308f263690cc2e91f7b307b290044ad"
        ),
    }
)
ADR0362_RESULT_PROTOCOL_SHA256 = (
    "f4e2dc05ad8e8337f6c05853302af90866fdd0324c40d593a977434656f6c703"
)


__all__ = [
    "ADR0362_RESULT_PROTOCOL_SHA256",
    "ADR0362_RESULT_SOURCE_MANIFEST",
]
