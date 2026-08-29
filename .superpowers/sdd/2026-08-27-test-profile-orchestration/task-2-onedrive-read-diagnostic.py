from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys


task_root = Path(r"C:\Users\point\AppData\Local\Temp\pontius-orch-task2")
primary_root = Path(r"C:\Users\point\OneDrive\Documents\ChatGPT\Pontius").resolve()
candidate = primary_root / "tests" / "test_cfr.py"

support_path = task_root / "tests" / "orchestration_test_support.py"
support_spec = importlib.util.spec_from_file_location("onedrive_read_support", support_path)
if support_spec is None or support_spec.loader is None:
    raise RuntimeError("orchestration support unavailable")
support = importlib.util.module_from_spec(support_spec)
support_spec.loader.exec_module(support)
_, _, configuration = support.load_orchestration_modules(task_root)

generator_path = task_root / "tools" / "generate_test_inventory.py"
generator_spec = importlib.util.spec_from_file_location("onedrive_read_generator", generator_path)
if generator_spec is None or generator_spec.loader is None:
    raise RuntimeError("inventory generator unavailable")
generator = importlib.util.module_from_spec(generator_spec)
sys.modules[generator_spec.name] = generator
generator_spec.loader.exec_module(generator)

expected = generator.secure_filesystem.read_regular_snapshot(
    candidate,
    maximum_bytes=configuration.MAX_CONFIGURATION_BYTES,
    root=primary_root,
)
actual = configuration._read_bounded(
    candidate,
    root=primary_root,
    label="OneDrive diagnostic",
)
if actual != expected.raw:
    raise RuntimeError("candidate read differs from independently bound snapshot")
expected.revalidate()
again = configuration._read_bounded(
    candidate,
    root=primary_root,
    label="OneDrive diagnostic revalidation",
)
if again != actual:
    raise RuntimeError("candidate read changed across revalidation")
print(f"bytes={len(actual)} sha256={sha256(actual).hexdigest()} revalidated=true")
