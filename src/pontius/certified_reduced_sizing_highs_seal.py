"""Committed ADR-0318 identities for the certified reduced-sizing adapter."""

from types import MappingProxyType


ADR0318_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_highs.py": (
        "4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f"
    ),
    "linear_program_certificate.py": (
        "0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910"
    ),
    "reduced_river_sizing_lp.py": (
        "3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346"
    ),
})

ADR0318_EXPECTED_RUNTIME = MappingProxyType({
    "python": "3.14.6",
    "numpy": "2.5.2",
    "scipy": "1.18.0",
    "highs": "1.12.0",
})

ADR0318_CANONICAL_VALIDATION_COUNTS = MappingProxyType({
    "known_regression_bases": 1,
    "exact_micro_bases": 48,
    "fresh_sizing_bases": 128,
    "total_bases": 177,
})

__all__ = [
    "ADR0318_CANONICAL_VALIDATION_COUNTS",
    "ADR0318_EXPECTED_RUNTIME",
    "ADR0318_SOURCE_MANIFEST",
]
