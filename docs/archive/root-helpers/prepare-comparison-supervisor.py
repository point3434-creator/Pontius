"""Adapt external operator plumbing to the exact approved comparison contract."""
from pathlib import Path

old = Path('launch-paired-rehearsal-once.py').read_text()
prefix = old.split('last_progress = [time.monotonic_ns()]',1)[0]
prefix = prefix.replace('ADR-0510 single cost rehearsal','ADR-0511 single comparison')
prefix = prefix.replace('v0a-paired-prereg','v0a-paired-closure')
prefix = prefix.replace('v0a-paired-rehearsal-run-001','v0a-paired-evaluation-run-001')
prefix = prefix.replace('67af9c6fb677af40937c7640e391bdabcf7f0c27a0a261ac9efdbbf98ddf8359',
    'd772691d85a903b4ac6e734b9aa4eac4f75e6ae0096def7c3c0481807729017e')
prefix = prefix.replace('def run_capture(name, argv, show_progress=False):',
    'def run_capture(name, argv, show_progress=False, budget_ns=None):')
prefix = prefix.replace('            if failed.wait(1):',
    "            if budget_ns is not None and time.monotonic_ns()-started > budget_ns:\n"
    "                raise TimeoutError('reader_observed_exit_deadline')\n"
    '            if failed.wait(.05 if budget_ns is not None else 1):')
prefix = prefix.replace('        ended = time.monotonic_ns()\n    except BaseException',
    "        ended = time.monotonic_ns()\n"
    "        if budget_ns is not None and ended-started > budget_ns:\n"
    "            errors.append('reader_observed_exit_deadline')\n"
    '    except BaseException')
prefix = prefix.replace("range(1,25)","range(1,49)").replace('planned_units=24','planned_units=48')
prefix = prefix.replace("progress='rehearsal'","progress='comparison'")
tail = r'''
last_progress = [time.monotonic_ns()]
adoption = json.loads((packet/'adoption-result.json').read_bytes())
assert adoption['status'] == 'COMMITTED_AND_PUSHED'
assert adoption['candidate'] == 'e80b794050a466a3f8115b640b53dca3b51816a7'
save(packet/'comparison-opportunity.json', dict(user_message='lets do it', decision='ADR-0511',
    adoption_commit=adoption['commit'], root=str(root), utc=utc(), opportunities=1))
launched = reader = None
try:
    assert not os.path.lexists(root), 'reserved_root_collision'
    root.mkdir()
    save(root/'approval.json', (packet/'adoption-authorization.json').read_bytes())
    save(root/'supervisor.py', Path(__file__).read_bytes())
    (root/'process-temp').mkdir()
    for path in (python, git_exe, taskkill):
        regular(path)
    request = (packet/'files/docs/architecture/v0a-paired-closure-r001/evaluation-request.json').read_bytes()
    assert len(request) == 351 and sha(request) == request_hash
    save(root/'request.json', request)
    git(Path('D:/Pontius'), 'clone', '--quiet', '--no-hardlinks', '--no-checkout',
        'D:/Pontius', str(source))
    git(source, '-c', 'core.autocrlf=false', 'checkout', '--quiet', '--detach', base)
    identity = verify_source()
    identity['executables'] = {str(p): dict(sha256=sha(p.read_bytes()), bytes=p.stat().st_size)
        for p in (python, git_exe, taskkill)}
    save(root/'source-identity.json', identity)
    probe_code = "import sys,pathlib; assert sys.implementation.name=='cpython'; assert sys.version_info[:3]==(3,11,15); assert sys.flags.safe_path and sys.dont_write_bytecode; assert pathlib.Path.cwd()==pathlib.Path(sys.argv[1]); print(sys.version); print(sys.executable); print(pathlib.Path.cwd())"
    probe = run_capture('preflight', [str(python), '-B', '-P', '-c', probe_code, str(source)])
    assert probe['exit_code'] == 0 and not probe['errors'], 'preflight_failed'
    assert not os.path.lexists(output)
    assert (root/'request.json').read_bytes() == request
    argv = [str(python), '-B', '-P', 'tools/v0a_evaluation.py', '--request',
        'D:/Pontius/tmp/v0a-paired-evaluation-run-001/request.json', '--output-root',
        'D:/Pontius/tmp/v0a-paired-evaluation-run-001/output', '--evaluation-id',
        'pontius-v0a-evaluation-v1-correctness-comparison-001']
    launched = run_capture('wrapper', argv, True)
    assert not launched['errors'], 'wrapper_capture_or_cleanup_failed'
    assert verify_source() == {k:v for k,v in identity.items() if k != 'executables'}
    assert (root/'request.json').read_bytes() == request
    for path in (python, git_exe, taskkill):
        regular(path)
        assert sha(path.read_bytes()) == identity['executables'][str(path)]['sha256']
    files = []
    if output.is_dir():
        for parent, directories, names in os.walk(output, followlinks=False):
            regular(Path(parent), True)
            for name in directories:
                regular(Path(parent)/name, True)
            for name in names:
                path = Path(parent)/name
                regular(path)
                raw = path.read_bytes()
                files.append(dict(path=path.relative_to(output).as_posix(), bytes=len(raw), sha256=sha(raw)))
    save(root/'output-file-inventory.json', files)
    output_bytes = sum(f['bytes'] for f in files)
    assert output_bytes <= 4194304, 'retained_output_cap_exceeded'
    save(root/'output-cap-check.json', dict(bytes=output_bytes, cap=4194304,
        files=len(files), passed=True, scope='post-termination retained output only'))
    companion = (packet/'files/docs/architecture/v0a-paired-closure-r001/operating-contract.md').read_bytes()
    assert sha(companion) == 'ea7aeda249f4e7a3d0dfbd38475c8d8a55d724850ae42332bb9e57fe552f5f8d'
    reader_program = companion.decode().split('```python\n',1)[1].split('```',1)[0]
    reader = run_capture('reader', [str(python), '-B', '-P', '-c', reader_program],
        budget_ns=10000000000)
    assert reader['exit_code'] == 0 and not reader['errors'], 'reader_refused_or_cleanup_unknown'
    assert reader['parent_elapsed_ns'] <= 10000000000, 'reader_late'
    assert all(n <= 65536 for n in reader['observed_capture_bytes']), 'reader_capture_overflow'
    raw_result = (root/'reader-stdout.bin').read_bytes()
    result = json.loads(raw_result)
    assert result['planned_pairs'] == result['completed_pairs'] == 24
    assert result['planned_trials'] == result['completed_trials'] == 48
    assert result['source_commit'] == base and result['request_sha256'] == request_hash
    assert result['comparison_complete'] is True and result['evidentiary'] is False
    save(root/'descriptive-result.json', raw_result)
    units = []
    for i in range(1,49):
        path = output/f'u{i:03d}'/'result.json'
        regular(path)
        raw = path.read_bytes()
        value = json.loads(raw)
        unit = {k:value.get(k) for k in ('ordinal','strategy','state','cleanup_complete',
            'exit_code','failure_reason','secondary_failures','capture_complete')}
        unit.update(result_sha256=sha(raw),elapsed_ns_prefix=value.get('elapsed_ns'))
        assert unit['state'] == 'completed' and unit['cleanup_complete'] is True
        units.append(unit)
    report = dict(status='COMPLETED_DESCRIPTIVE_COMPARISON', source=identity,
        adoption_commit=adoption['commit'], request_sha256=request_hash,
        wrapper=launched, reader=reader, units=units,
        planned_trials=48, completed_trials=48, planned_pairs=24, completed_pairs=24,
        descriptive_result_sha256=sha(raw_result), output_files=len(files), output_bytes=output_bytes,
        output_inventory_sha256=sha((root/'output-file-inventory.json').read_bytes()),
        opportunity_consumed=True, lane_budget_exhausted=True, successor_authorized=False,
        standing='Finite descriptive arithmetic only; no strength, selection or tuning claim',
        unknown=['peak process-tree memory','peak disk','action latency distribution'],
        next_required='Written architecture checkpoint and explicit park-or-continue ruling')
    save(root/'comparison-report.json', report)
    save(packet/'comparison-disposition.json', dict(status=report['status'], retained_root=str(root),
        report_sha256=sha((root/'comparison-report.json').read_bytes()),
        opportunity_consumed=True,lane_budget_exhausted=True,raw_evidence_uploaded=False))
    print(json.dumps(dict(status=report['status'],completed_trials=48,completed_pairs=24,
        wrapper_exit=launched['exit_code'],wrapper_seconds=launched['parent_elapsed_ns']/1e9,
        reader_exit=reader['exit_code'],reader_seconds=reader['parent_elapsed_ns']/1e9,
        output_files=len(files),output_bytes=output_bytes,
        report=str(root/'comparison-report.json'))),flush=True)
except BaseException as error:
    record = dict(status='INCOMPLETE', error_type=type(error).__name__, reason=str(error),
        opportunity_consumed=True,lane_budget_exhausted=True,successor_authorized=False,
        utc=utc(),root=str(root),wrapper=launched,reader=reader,
        next_required='Written architecture checkpoint and explicit park-or-continue ruling')
    save(packet/'comparison-incomplete.json', record)
    if root.is_dir() and not os.path.lexists(root/'comparison-incomplete.json'):
        save(root/'comparison-incomplete.json',record)
    print(json.dumps(dict(status='INCOMPLETE',error_type=type(error).__name__,reason=str(error),
        retained_root=str(root),opportunity_consumed=True)),flush=True)
    raise
'''
# Raw literal tail needs actual source quoting, not escaped transport newlines.
tail = tail.replace('\\"','"').replace("'```python\\\\n'", "'```python\\n'")
with Path('launch-paired-comparison-once.py').open('x',encoding='utf-8',newline='\n') as f:
    f.write(prefix+tail)
print('Prepared external comparison supervisor; no launch occurred')
