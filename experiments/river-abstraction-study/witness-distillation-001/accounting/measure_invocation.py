"""Retain elapsed time around the approved, unchanged distillation run command."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT/'docs/research/river-witness-distillation-r001'
PLAN_SHA = '47b26fc64aa3b2ddb36ebe11a02d16253b240a61672cff162c51af689728e524'


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def validate_approval(approval,plan_hash,recorder_hash):
    if (type(approval) is not dict or
        type(approval.get('user_words_verbatim')) is not str or
        not approval['user_words_verbatim'].strip() or
        approval.get('plan_sha256') != plan_hash or
        approval.get('recorder_sha256') != recorder_hash):
        raise ValueError('controller record must bind the plan and timing recorder')


def measure(command,evidence,binding,cwd):
    evidence.mkdir(exist_ok=False)
    write(evidence/'launch.json',dict(command=command,binding=binding,cwd=str(cwd),
        recorded_at_utc=datetime.now(timezone.utc).isoformat()))
    try:
        environment = os.environ.copy()
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        environment.pop('PYTHONTRACEMALLOC',None)
        with (evidence/'stdout.txt').open('xb') as stdout:
            with (evidence/'stderr.txt').open('xb') as stderr:
                start = perf_counter()
                result = subprocess.run(command,cwd=cwd,env=environment,stdout=stdout,stderr=stderr)
                elapsed = perf_counter()-start
        write(evidence/'receipt.json',dict(command=command,binding=binding,exit=result.returncode,
            whole_command_seconds=elapsed,ended_at_utc=datetime.now(timezone.utc).isoformat(),
            boundary='Immediately before subprocess.run through its return: includes command '
            'startup, worker, parent refit/verification, summary and manifest writes, and exit; '
            'excludes recorder preflight and writing this outer receipt.'))
        return result.returncode
    except BaseException as error:
        write(evidence/'failed.json',dict(error=type(error).__name__,message=str(error)))
        raise


def main():
    # The controller creates this record only after the user's separate approval.
    approval = json.loads((PACKET/'controller-authorization.json').read_bytes())
    recorder_hash = sha256(Path(__file__).read_bytes()).hexdigest()
    validate_approval(approval,PLAN_SHA,recorder_hash)
    spec = importlib.util.spec_from_file_location('bound_distillation',
                                                ROOT/'tools/river_witness_distillation.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    _,plan = tool.read_plan(PACKET/'plan.json',PLAN_SHA)
    if Path(plan['output_directory']).exists():
        raise FileExistsError('bound output already exists; no retry')
    identity = json.loads((PACKET/'identity.json').read_bytes())
    for name,expected in identity['sha256'].items():
        if sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError('candidate identity drift: '+name)
    command = [sys.executable,'-B',str(ROOT/'tools/river_witness_distillation.py'),
               'run','--plan',str(PACKET/'plan.json'),'--sha256',PLAN_SHA]
    return measure(command,PACKET/'invocation-001',
                   dict(plan_sha256=PLAN_SHA,recorder_sha256=recorder_hash,approval=approval),ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
