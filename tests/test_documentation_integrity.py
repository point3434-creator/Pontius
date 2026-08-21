from __future__ import annotations

from pathlib import Path
import re
import unittest
from urllib.parse import unquote


_ROOT = Path(__file__).parents[1]
_MAINTAINED = (
    _ROOT / "README.md",
    _ROOT / "PROJECT.md",
    _ROOT / "STATUS.md",
    _ROOT / "ROADMAP.md",
    _ROOT / "RUNBOOK.md",
    _ROOT / "ARCHITECTURE.md",
    _ROOT / "RISK_REGISTER.md",
    _ROOT / "experiments/RESULTS.md",
    _ROOT / "docs/reviews/C1-exact-game-laboratory.md",
)
_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


class DocumentationIntegrityTests(unittest.TestCase):
    def test_maintained_local_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for source in _MAINTAINED:
            self.assertTrue(source.is_file(), source)
            for raw_target in _LINK.findall(source.read_text(encoding="utf-8")):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith(("mailto:", "#")):
                    continue
                destination = (source.parent / unquote(target)).resolve()
                if not destination.exists():
                    failures.append(f"{source.relative_to(_ROOT)} -> {raw_target}")
        self.assertEqual([], failures)

    def test_current_contract_is_visible_in_every_front_door(self) -> None:
        expected = {
            "README.md": ("six-player river control", "15-second"),
            "PROJECT.md": ("15,000 ms", "immutable blueprint"),
            "ROADMAP.md": ("ADR-0178", "deep-horizon"),
            "RUNBOOK.md": ("PONTIUS_CUDA_DLL_DIRECTORY", "status_generation --check"),
            "ARCHITECTURE.md": ("Current h32 execution spine", "deadline-admitted exact certificate"),
            "RISK_REGISTER.md": ("R35", "Documentation drift"),
        }
        for relative, phrases in expected.items():
            text = (_ROOT / relative).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")


if __name__ == "__main__":
    unittest.main()
