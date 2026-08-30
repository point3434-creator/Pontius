"""CI diagnostics probe: native identity, status chains, and writer behavior.

Classified stabilization origin (controller-authorized instrumentation).
The probe is assertive: exit 0 requires every ancestor identity comparison
to MATCH, the lock discipline to behave (held unlink denied with sharing
violation 32, post-close unlink clean), and one real standalone
``write_atomic_lf`` to publish successfully. Any observed deviation exits 1
with the deviations listed; probe-internal failures exit 3. It gates the
identity contract, never mere process survival.
"""

import ctypes
import importlib.util
import os
import sys
import tempfile
import traceback
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PROBLEMS: list[str] = []


def section(title: str) -> None:
    print(f"\n=== {title} ===", flush=True)


def problem(text: str) -> None:
    PROBLEMS.append(text)
    print(f"PROBLEM: {text}")


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "pontius_ci_native_diagnostics_generator",
        ROOT / "tools" / "generate_test_inventory.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def volume_info(root: str) -> str:
    name = ctypes.create_unicode_buffer(261)
    filesystem = ctypes.create_unicode_buffer(261)
    serial = wintypes.DWORD()
    ok = ctypes.windll.kernel32.GetVolumeInformationW(
        root, name, 261, ctypes.byref(serial), None, None, filesystem, 261
    )
    if not ok:
        return f"{root}: GetVolumeInformationW failed ({ctypes.get_last_error()})"
    return f"{root}: filesystem={filesystem.value} serial={serial.value:#010x} label={name.value!r}"


def describe_chain(error: BaseException, depth: int = 0) -> None:
    while error is not None and depth < 10:
        extras = []
        for attribute in ("winerror", "errno", "args"):
            value = getattr(error, attribute, None)
            if value not in (None, ()):
                extras.append(f"{attribute}={value!r}")
        print(f"  chain[{depth}] {type(error).__name__}: {error} {' '.join(extras)}")
        for attribute in ("primary", "participant"):
            value = getattr(error, attribute, None)
            if isinstance(value, BaseException):
                print(f"  chain[{depth}].{attribute} ->")
                describe_chain(value, depth + 1)
            elif value is not None:
                print(f"  chain[{depth}].{attribute} = {value!r}")
        error = error.__cause__ or error.__context__
        depth += 1


def main() -> int:
    section("environment")
    print(f"python={sys.version.split()[0]} cwd={os.getcwd()}")
    print(f"TEMP={os.environ.get('TEMP')!r} PONTIUS_GIT={os.environ.get('PONTIUS_GIT')!r}")
    for root in {"C:\\", str(Path(os.environ.get("TEMP", "C:\\")).anchor), str(ROOT.anchor)}:
        print(volume_info(root))
    try:
        print(f"is_admin={bool(ctypes.windll.shell32.IsUserAnAdmin())}")
    except Exception as error:  # noqa: BLE001 - diagnostic best effort
        print(f"is_admin=unknown ({error})")

    generator = load_generator()
    fs = generator.secure_filesystem

    section("git ancestor identities (both sides, two passes)")
    git_path = Path(os.environ["PONTIUS_GIT"])
    for attempt in (1, 2):
        chain = generator._git_ancestor_chain(git_path)
        print(f"pass {attempt}: chain of {len(chain)} ancestors")
        create = fs._windows_directory_api()[0]
        for ancestor, expected in chain:
            stat_ino = os.stat(ancestor).st_ino
            handle = create(
                str(ancestor),
                0x00000001 | 0x00000080 | 0x00100000,
                0x00000001 | 0x00000002,
                None,
                3,
                0x02000000 | 0x00200000,
                None,
            )
            invalid = ctypes.c_void_p(-1).value
            if not handle or int(handle) == invalid:
                problem(f"ancestor open failed gle={ctypes.get_last_error()}: {ancestor}")
                continue
            try:
                volume, file_id = fs._windows_directory_handle_identity(int(handle), ancestor)
            finally:
                ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(int(handle)))
            live = (volume, int.from_bytes(file_id, "little"))
            if live == tuple(expected[:2]):
                verdict = "MATCH"
            else:
                verdict = "MISMATCH"
                problem(f"ancestor identity mismatch: {ancestor}")
            print(
                f"  {verdict} {ancestor}\n"
                f"    expected[:2]={tuple(expected[:2])!r} expected_rest={tuple(expected[2:])!r}\n"
                f"    live=(volume={volume:#x}, id_le={live[1]:#x}) raw_id={file_id.hex()} st_ino={stat_ino:#x}"
            )

    section("native governance create sequence with raw status")
    with tempfile.TemporaryDirectory(prefix="pontius-native-diag-") as directory:
        parent = Path(directory).resolve()
        directory_handle, identity = generator._windows_open_governance_directory(
            parent, owner=None
        )
        print(f"directory open OK handle={directory_handle:#x} identity={identity!r}")
        try:
            for label, share_delete in (("lock", False), ("staging", True)):
                name = f".probe.{label}"
                created = None
                try:
                    created = generator._windows_create_relative_governance_file(
                        directory_handle,
                        name,
                        owner=SimpleNamespace(handle=None, state=None),
                        share_delete=share_delete,
                    )
                    print(f"{label} create OK handle={created:#x}")
                except BaseException as error:  # noqa: BLE001
                    problem(f"{label} create failed")
                    describe_chain(error)
                if label == "lock" and created is not None:
                    lock_path = parent / name
                    try:
                        os.unlink(lock_path)
                        problem("unlink-while-held unexpectedly succeeded")
                    except OSError as error:
                        print(
                            "unlink-while-held: "
                            f"{type(error).__name__} winerror={error.winerror} errno={error.errno}"
                        )
                        if error.winerror != 32:
                            problem(
                                "unlink-while-held expected sharing violation 32, "
                                f"observed winerror={error.winerror}"
                            )
                    ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(created))
                    created = None
                    try:
                        os.unlink(lock_path)
                        print("unlink-after-close: OK")
                    except OSError as error:
                        problem(
                            "unlink-after-close failed: "
                            f"winerror={error.winerror} errno={error.errno}"
                        )
                elif created is not None:
                    ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(created))
        finally:
            ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(directory_handle))

    section("real standalone write_atomic_lf")
    with tempfile.TemporaryDirectory(prefix="pontius-native-diag-write-") as directory:
        destination = Path(directory).resolve() / "probe-out.toml"
        try:
            generator.write_atomic_lf(destination, b"probe = 1\n")
            published = destination.read_bytes()
            if published == b"probe = 1\n":
                print(f"write_atomic_lf OK bytes={published!r}")
            else:
                problem(f"write_atomic_lf published unexpected bytes: {published!r}")
        except BaseException as error:  # noqa: BLE001
            problem("write_atomic_lf failed")
            describe_chain(error)

    if PROBLEMS:
        section("verdict")
        for entry in PROBLEMS:
            print(f"FAILED-EXPECTATION: {entry}")
        print(f"DIAGNOSTICS-FAILED ({len(PROBLEMS)} expectation(s) unmet)")
        return 1
    print("\nDIAGNOSTICS-COMPLETE: identity matches and writer behavior verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001 - probe-internal failures are nonzero
        traceback.print_exc()
        print("PROBE-INTERNAL-ERROR")
        raise SystemExit(3)
