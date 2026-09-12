"""Domain-gated reuse of the frozen repair comparison on actual pot/stack payoffs."""
import stack_bridge as b
from pathlib import Path
import os
import sys
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'river-stack-transfer-001'
ROOT, HISTORY, PRIOR = b.ROOT, b.HISTORY, b.PRIOR
read, write, digest = b.read, b.write, b.digest


def bindings(plan):
    assert plan['name'] == NAME and sys.version_info[:3] == (3, 14, 6)
    assert not tracemalloc.is_tracing()
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, b.np.__version__, b.c.scipy.__version__)
    assert b.e.evaluator.BACKEND == plan['evaluator'] == 'phevaluator-c'
    assert plan['phase_timeout_seconds'] == 1800
    assert plan['cases'] == list(range(4)) and plan['expected_applicable'] == [1]
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        assert os.environ[name] == '1'
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path


def worker(plan, out):
    bindings(plan)
    applicable = []
    for j in plan['cases']:
        record = read(PRIOR/f'input-{j:03d}.json')
        meta = b.admission(record)
        audit = b.engine_audit(record)
        row = dict(source=str(PRIOR/f'input-{j:03d}.json'),
            source_sha256=digest(PRIOR/f'input-{j:03d}.json'), menu=meta, engine_audit=audit)
        if meta['applicable']:
            applicable.append(j)
            b.e.inputs.build = b.build
            try:
                row['result'] = b.e.solve_case(record)
            finally:
                b.e.inputs.build = b.original_build
            assert row['result']['groups'] == read(PRIOR/f'case-{j:03d}.json')['groups']
            row['status'] = 'evaluated'
        else:
            row['status'] = 'not_applicable_single_size'
        write(out/f'case-{j:03d}.json', row)
        print(f"case {j}: {row['status']}", flush=True)
    assert applicable == plan['expected_applicable']
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, census=4, evaluated=1,
                                          not_applicable=3, lp_calls=6, gates=2))


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    b.c.opt.linprog = forbidden
    coefficients, updates = 0, 0
    for j in plan['cases']:
        record = read(PRIOR/f'input-{j:03d}.json')
        row = read(out/f'case-{j:03d}.json')
        assert row['source'] == str(PRIOR/f'input-{j:03d}.json')
        assert row['source_sha256'] == digest(row['source'])
        assert row['menu'] == b.admission(record)
        assert row['engine_audit'] == b.engine_audit(record)
        if row['menu']['applicable']:
            assert row['status'] == 'evaluated'
            b.e.inputs.build = b.build
            try:
                checked, replayed = b.e.verify_case(record, row['result'])
                coefficients += checked
                updates += replayed
            finally:
                b.e.inputs.build = b.original_build
        else:
            assert row['status'] == 'not_applicable_single_size' and 'result' not in row
            try:
                b.build(record)
            except ValueError as error:
                assert 'one distinct' in str(error)
            else:
                raise AssertionError('inapplicable solver entry admitted')
        print(f'verified {j+1}/4', flush=True)
    assert read(out/'worker-complete.json') == dict(complete=True, census=4, evaluated=1,
                                                 not_applicable=3, lp_calls=6, gates=2)
    bindings(plan)
    write(out/'audit.json', dict(passed=True, census=4, evaluated=1, not_applicable=3,
        literal_settlement_checks=60, exact_coefficients=coefficients,
        replayed_updates=updates, certificate_pairs=3, gates=2, new_lp_calls=0))


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        b.e.d.runner.HERE, b.e.d.runner.bindings = HERE, bindings
        b.e.d.runner.run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
