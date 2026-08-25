"""Explicitly typed Windows physical/process-memory telemetry."""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
from ctypes import wintypes
from pathlib import Path
from typing import Any


class MemoryStatusEx(ctypes.Structure):
    _fields_ = (
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    )


class ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = (
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    )


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("typed process-memory telemetry requires Windows")


def _raise_last_error(function: str) -> None:
    code = ctypes.get_last_error()
    message = ctypes.FormatError(code) if code else "function returned false"
    raise OSError(code, f"{function} failed: {message}")


def _libraries() -> tuple[Any, Any]:
    _require_windows()
    return (
        ctypes.WinDLL("kernel32", use_last_error=True),
        ctypes.WinDLL("psapi", use_last_error=True),
    )


def _current_process(kernel32: Any) -> int:
    function = kernel32.GetCurrentProcess
    function.argtypes = []
    function.restype = wintypes.HANDLE
    process = function()
    if process is None:
        _raise_last_error("GetCurrentProcess")
    return int(process)


def _global_memory(kernel32: Any) -> dict[str, int]:
    function = kernel32.GlobalMemoryStatusEx
    function.argtypes = [ctypes.POINTER(MemoryStatusEx)]
    function.restype = wintypes.BOOL
    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    ctypes.set_last_error(0)
    if not function(ctypes.byref(status)):
        _raise_last_error("GlobalMemoryStatusEx")
    return {
        "host_total_physical_bytes": int(status.ullTotalPhys),
        "host_available_physical_bytes": int(status.ullAvailPhys),
    }


def _process_counters(
    *,
    library: Any,
    function_name: str,
    process: int,
) -> dict[str, int]:
    function = getattr(library, function_name)
    function.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCountersEx),
        wintypes.DWORD,
    ]
    function.restype = wintypes.BOOL
    counters = ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    ctypes.set_last_error(0)
    if not function(process, ctypes.byref(counters), counters.cb):
        _raise_last_error(function_name)
    return {
        "process_working_set_bytes": int(counters.WorkingSetSize),
        "process_peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "process_private_bytes": int(counters.PrivateUsage),
        "process_pagefile_bytes": int(counters.PagefileUsage),
        "process_peak_pagefile_bytes": int(counters.PeakPagefileUsage),
    }


def typed_windows_memory_snapshot() -> dict[str, object]:
    """Read one process through two fully declared Win32 ABI entry points."""

    kernel32, psapi = _libraries()
    process = _current_process(kernel32)
    psapi_counters = _process_counters(
        library=psapi,
        function_name="GetProcessMemoryInfo",
        process=process,
    )
    kernel32_counters = _process_counters(
        library=kernel32,
        function_name="K32GetProcessMemoryInfo",
        process=process,
    )
    return {
        **_global_memory(kernel32),
        **kernel32_counters,
        "process_id": os.getpid(),
        "process_counter_struct_bytes": ctypes.sizeof(ProcessMemoryCountersEx),
        "psapi": psapi_counters,
        "kernel32": kernel32_counters,
    }


def powershell_process_memory_snapshot(process_id: int | None = None) -> dict[str, int]:
    """Read the same Python process through PowerShell's managed process view."""

    _require_windows()
    pid = os.getpid() if process_id is None else process_id
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError("process id must be a positive integer")
    system_root = os.environ.get("SystemRoot")
    if not system_root:
        raise RuntimeError("SystemRoot is unavailable")
    executable = (
        Path(system_root)
        / "System32"
        / "WindowsPowerShell"
        / "v1.0"
        / "powershell.exe"
    )
    if not executable.is_file():
        raise RuntimeError("the frozen PowerShell executable is unavailable")
    command = (
        f"$p=Get-Process -Id {pid};"
        "$o=[ordered]@{"
        "process_id=[int]$p.Id;"
        "process_working_set_bytes=[int64]$p.WorkingSet64;"
        "process_peak_working_set_bytes=[int64]$p.PeakWorkingSet64;"
        "process_private_bytes=[int64]$p.PrivateMemorySize64};"
        "[Console]::Out.Write(($o|ConvertTo-Json -Compress))"
    )
    completed = subprocess.run(
        [
            str(executable),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10.0,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"PowerShell process-memory control failed: {message}")
    payload = json.loads(completed.stdout)
    expected = {
        "process_id",
        "process_working_set_bytes",
        "process_peak_working_set_bytes",
        "process_private_bytes",
    }
    if set(payload) != expected:
        raise ValueError("PowerShell process-memory fields differ from v2")
    record = {key: int(value) for key, value in payload.items()}
    if record["process_id"] != pid:
        raise ValueError("PowerShell process-memory control rebound to another process")
    return record


def typed_memory_telemetry_control(*, maximum_delta_bytes: int) -> dict[str, object]:
    """Cross-check typed Win32 counters against PowerShell without exact-value gates."""

    if (
        isinstance(maximum_delta_bytes, bool)
        or not isinstance(maximum_delta_bytes, int)
        or maximum_delta_bytes < 0
    ):
        raise ValueError("maximum telemetry delta must be a nonnegative integer")
    snapshot = typed_windows_memory_snapshot()
    powershell = powershell_process_memory_snapshot(int(snapshot["process_id"]))
    fields = (
        "process_working_set_bytes",
        "process_peak_working_set_bytes",
        "process_private_bytes",
    )
    alias_deltas = {
        field: abs(int(snapshot["psapi"][field]) - int(snapshot["kernel32"][field]))
        for field in fields
    }
    powershell_deltas = {
        field: abs(int(snapshot[field]) - int(powershell[field])) for field in fields
    }
    nonnegative = all(
        int(record[field]) >= 0
        for record in (snapshot["psapi"], snapshot["kernel32"], powershell)
        for field in fields
    )
    ordered = all(
        int(record["process_peak_working_set_bytes"])
        >= int(record["process_working_set_bytes"])
        for record in (snapshot["psapi"], snapshot["kernel32"], powershell)
    )
    gates = {
        "process_identity": int(snapshot["process_id"]) == powershell["process_id"],
        "counter_structure_is_80_bytes": (
            int(snapshot["process_counter_struct_bytes"]) == 80
        ),
        "nonnegative_counters": nonnegative,
        "peak_working_set_not_below_working_set": ordered,
        "psapi_kernel32_within_sampling_allowance": (
            max(alias_deltas.values()) <= maximum_delta_bytes
        ),
        "win32_powershell_within_sampling_allowance": (
            max(powershell_deltas.values()) <= maximum_delta_bytes
        ),
    }
    return {
        "maximum_delta_bytes": maximum_delta_bytes,
        "snapshot": snapshot,
        "powershell": powershell,
        "psapi_kernel32_absolute_deltas": alias_deltas,
        "win32_powershell_absolute_deltas": powershell_deltas,
        "gates": gates,
        "passed": all(gates.values()),
    }


__all__ = [
    "MemoryStatusEx",
    "ProcessMemoryCountersEx",
    "powershell_process_memory_snapshot",
    "typed_memory_telemetry_control",
    "typed_windows_memory_snapshot",
]
