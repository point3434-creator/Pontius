from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).parents[1]
_RESULT = (
    _ROOT / "experiments/results/full-width-river-capacity-preflight-v1.json"
)
_EXPECTED_BYTES = 798
_EXPECTED_SHA256 = "ff1c757fb1c388c239ca3c7fdacad15bffa6ee62e00b882827ffb5626f40a906"


class FullWidthRiverCapacityPreflightResultTests(unittest.TestCase):
    def payload(self) -> dict[str, object]:
        raw = _RESULT.read_bytes()
        self.assertEqual(len(raw), _EXPECTED_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        return json.loads(raw)

    def test_exact_first_terminal_is_immutable_and_source_bound(self) -> None:
        payload = self.payload()

        self.assertEqual(
            payload["source_commit"],
            "c7d96241e8642aa85964865a0c90e591a6788f9c",
        )
        self.assertIs(payload["source_dirty"], False)
        self.assertEqual(
            payload["config_sha256"],
            "76d4314b9e509effec1608995d88490a0ad71685b27de2297c3c5d2b4e855fa5",
        )
        self.assertEqual(
            payload["implementation_sha256"],
            "37580cfd6042b12dc0a864b515d5f4e79e0e1733ca5471fa29d41b3d7ad46c90",
        )

    def test_terminal_is_a_pre_capacity_telemetry_failure(self) -> None:
        payload = self.payload()

        self.assertIs(payload["passed"], False)
        self.assertEqual(payload["terminal"], "typed_failure")
        self.assertEqual(
            payload["failure"],
            {"message": "GetProcessMemoryInfo failed", "type": "OSError"},
        )
        self.assertNotIn("control", payload)
        self.assertNotIn("target", payload)
        self.assertNotIn("runtime_at_target_admission", payload)
        self.assertNotIn("campaign_wall_seconds", payload)

    def test_terminal_emits_no_action_or_quality_claim(self) -> None:
        payload = self.payload()

        self.assertEqual(
            payload["emissions"],
            {
                "actions": 0,
                "quality_claim": None,
                "strategy_labels": 0,
                "strategy_quality_rows": 0,
            },
        )
        attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/experiments/results/full-width-river-capacity-preflight-v1.json -text",
            attributes,
        )


if __name__ == "__main__":
    unittest.main()
