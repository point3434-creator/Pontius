"""Committed identities for ADR-0319's canonical validation runner."""

from types import MappingProxyType


ADR0319_SOURCE_MANIFEST = MappingProxyType({
    "certified_reduced_sizing_highs.py": (
        "4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f"
    ),
    "certified_reduced_sizing_highs_seal.py": (
        "25acaef5776044b56ad370d42616200cc39d3d662a7ab1bc45f3366a6ae1c0b0"
    ),
    "certified_sizing_validation_runner.py": (
        "5116c1d4b2632da76cf83e6d7d015b190e061330094d27b3c9719631a89252e1"
    ),
    "linear_program_certificate.py": (
        "0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910"
    ),
    "native_simplex_audit_corpus.py": (
        "b65c301b9f0443b9f25da4da22fa7f8c15017cd63b4abe2670c5d98c32085918"
    ),
    "native_simplex_audit_runner.py": (
        "cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16"
    ),
    "native_simplex_audit_seal.py": (
        "a0305de4af43366f6e2ed2a1d5bcd4fafba01f94d5e7103201bcaa9385ff05e3"
    ),
    "native_simplex_audit_structures.py": (
        "ea945d3ce76b38c893029884bcbda2280fc22ce66fdac30fdb09508929d39801"
    ),
    "reduced_river_sizing_lp.py": (
        "3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346"
    ),
})

ADR0319_SCHEDULE_SHA256 = "36f34eb820bfaa4b58747201c9b27779553d0f8e250c73786da34542b5d8cba4"
ADR0319_PROTOCOL_SHA256 = "51d4f188fbf2e5b78b38fca7712294b2001d0d0959a00c575d17a0b0adc0a5df"

__all__ = [
    "ADR0319_PROTOCOL_SHA256",
    "ADR0319_SCHEDULE_SHA256",
    "ADR0319_SOURCE_MANIFEST",
]
