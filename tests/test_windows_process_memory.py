from __future__ import annotations

import ctypes
import os
import unittest

from pontius.windows_process_memory import (
    MemoryStatusEx,
    ProcessMemoryCountersEx,
    powershell_process_memory_snapshot,
    typed_memory_telemetry_control,
    typed_windows_memory_snapshot,
)


@unittest.skipUnless(os.name == "nt", "typed memory telemetry is Windows-only")
class WindowsProcessMemoryTests(unittest.TestCase):
    def test_frozen_structures_have_the_win64_layout(self) -> None:
        self.assertEqual(ctypes.sizeof(MemoryStatusEx), 64)
        self.assertEqual(ctypes.sizeof(ProcessMemoryCountersEx), 80)
        self.assertEqual(ProcessMemoryCountersEx.WorkingSetSize.offset, 16)
        self.assertEqual(ProcessMemoryCountersEx.PrivateUsage.offset, 72)

    def test_both_typed_win32_entry_points_return_ordered_counters(self) -> None:
        snapshot = typed_windows_memory_snapshot()

        self.assertEqual(snapshot["process_id"], os.getpid())
        self.assertGreater(snapshot["host_total_physical_bytes"], 0)
        self.assertGreater(snapshot["host_available_physical_bytes"], 0)
        self.assertLessEqual(
            snapshot["host_available_physical_bytes"],
            snapshot["host_total_physical_bytes"],
        )
        for source in ("psapi", "kernel32"):
            record = snapshot[source]
            self.assertGreater(record["process_working_set_bytes"], 0)
            self.assertGreaterEqual(
                record["process_peak_working_set_bytes"],
                record["process_working_set_bytes"],
            )
            self.assertGreaterEqual(record["process_private_bytes"], 0)

    def test_powershell_rebinds_the_same_process(self) -> None:
        snapshot = powershell_process_memory_snapshot()

        self.assertEqual(snapshot["process_id"], os.getpid())
        self.assertGreater(snapshot["process_working_set_bytes"], 0)
        self.assertGreaterEqual(
            snapshot["process_peak_working_set_bytes"],
            snapshot["process_working_set_bytes"],
        )

    def test_cross_source_control_passes_without_exact_value_authority(self) -> None:
        control = typed_memory_telemetry_control(maximum_delta_bytes=536_870_912)

        self.assertTrue(control["passed"])
        self.assertTrue(all(control["gates"].values()))
        self.assertEqual(control["snapshot"]["process_counter_struct_bytes"], 80)

    def test_boolean_or_negative_allowance_fails_closed(self) -> None:
        for value in (True, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                typed_memory_telemetry_control(maximum_delta_bytes=value)


if __name__ == "__main__":
    unittest.main()
