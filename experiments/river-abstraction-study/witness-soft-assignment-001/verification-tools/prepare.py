"""Freeze the prepared experiment; this does not invoke the retained worker."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import experiment as e

here = Path(__file__).parent
plan_path = here/'plan.json'
if plan_path.exists():
    raise FileExistsError('frozen plan already exists')
result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
                         '-m', 'unittest', 'test_soft', 'test_runner', '-v'],
                        cwd=here, capture_output=True, timeout=60)
(here/'checks-stdout.txt').write_bytes(result.stdout)
(here/'checks-stderr.txt').write_bytes(result.stderr)
if result.returncode:
    raise RuntimeError('author checks failed')
result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning', 'preflight.py'],
                        cwd=here, capture_output=True, timeout=60)
(here/'preflight-stdout.txt').write_bytes(result.stdout)
(here/'preflight-stderr.txt').write_bytes(result.stderr)
if result.returncode:
    raise RuntimeError('synthetic preflight failed')

output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
if output.exists():
    raise FileExistsError('retained output already exists')
plan = e.make_plan(output)
plan['request_verbatim'] = (
    "Ok let's tackle the next research then if you are ready. "
    "Unless you can brainstorm something brilliant :)")
plan['frozen_at_utc'] = datetime.now(timezone.utc).isoformat()
plan['run_authorization'] = 'Separate approval of this frozen retained plan is pending.'
for path in here.iterdir():
    if path.is_file() and path.name not in ('plan.json', 'freeze.json'):
        plan['pins'][str(path.resolve())] = e.digest(path)
e.bindings(plan)
e.write(plan_path, plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(plan_path),
    pinned_files=len(plan['pins']), cells=32, capacities=[8, 16, 32],
    paired_method_cells=96, lp_calls=384, fixed_trajectories=192, timed_trajectories=576,
    synthetic_preflight=e.read(here/'preflight.json'),
    retained_output_exists=output.exists(), retained_invoked=False,
    run_command=[sys.executable, '-B', '-W', 'error::ResourceWarning',
                 str(here/'experiment.py'), 'run', str(plan_path), e.digest(plan_path)]))
print(e.read(here/'freeze.json'))
