from __future__ import annotations

from pathlib import Path
import unittest

from pontius.status_generation import read_decision_headers, render_status


_ROOT = Path(__file__).parents[1]


class StatusGenerationTests(unittest.TestCase):
    def test_status_is_exact_generated_output_from_current_adrs(self) -> None:
        self.assertEqual(
            (_ROOT / "STATUS.md").read_text(encoding="utf-8"),
            render_status(_ROOT),
        )

    def test_decision_numbers_are_unique_and_latest_decision_is_visible(self) -> None:
        rows = read_decision_headers(_ROOT / "docs/decisions")
        self.assertEqual(len({row.number for row in rows}), len(rows))
        rendered = render_status(_ROOT)
        self.assertIn(f"ADR-{rows[-1].number:04d}", rendered)
        self.assertIn(rows[-1].title, rendered)


if __name__ == "__main__":
    unittest.main()
