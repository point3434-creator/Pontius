"""One bounded, exclusively claimed diagnostic invocation."""
from pathlib import Path
from time import perf_counter
import subprocess
import sys
import diagnostic as d

path, expected = sys.argv[1:]
assert d.digest(path) == expected
plan = d.read(path)
d.bindings(plan)
assert plan['timeout_seconds'] == 600
out = Path(plan['output'])
out.mkdir(parents=True, exist_ok=False)
started = perf_counter()
try:
    d.write(out/'plan.json', plan)
    d.write(out/'started.json', dict(plan_sha256=expected))
    command = [sys.executable, '-B', '-W', 'error::ResourceWarning',
               str(d.HERE/'diagnostic.py'), path, expected]
    with (out/'stdout.txt').open('xb') as stdout, (out/'stderr.txt').open('xb') as stderr:
        child = subprocess.run(command, stdout=stdout, stderr=stderr,
                               cwd=d.HERE, timeout=plan['timeout_seconds'])
    d.write(out/'worker-receipt.json', dict(exit=child.returncode, command=command,
                                          seconds=perf_counter()-started))
    assert child.returncode == 0, 'diagnostic failed'
    d.bindings(plan)
    d.write(out/'results-manifest.json', {p.name: d.digest(p) for p in sorted(out.iterdir())
                                        if p.is_file()})
    d.write(out/'receipt.json', dict(exit=0, seconds=perf_counter()-started,
        result_manifest_sha256=d.digest(out/'results-manifest.json')))
except BaseException as error:
    d.write(out/'failed.json', dict(error=type(error).__name__, message=str(error)))
    raise
