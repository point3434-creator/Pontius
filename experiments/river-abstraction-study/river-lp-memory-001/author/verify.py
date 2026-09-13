from pathlib import Path
from hashlib import sha256
from fractions import Fraction
import json
import sys
import numpy
import scipy

HERE=Path(__file__).parent
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
assert sys.version_info[:3]==(3,14,6)
assert numpy.__version__=='2.5.2' and scipy.__version__=='1.18.0'
manifests=list(HISTORY.glob('*/milestone-manifest.json'))
assert len(manifests)==37
members=0
for manifest in manifests:
    for name,h in read(manifest).items():
        assert digest(manifest.parent/name)==h,(manifest,name)
        members+=1
for directory,expected in [(HERE,'9952e44850e5a88a414a3b716929129528cfed54cc0711be87c584164fb89076'),
    (HERE/'trace-correction','1917df22d83f10350e862a5f8e4bf73b1793f7a35bea23a2214ff6ea560e6fbb')]:
    plan=read(directory/'plan.json')
    assert digest(directory/'plan.json')==expected
    assert plan['prior_plan']==read(HISTORY/'river-tree-expansion-001/author/plan.json')
    for p,h in plan['pins'].items(): assert digest(Path(p))==h,p
    assert plan['jobs']==[2,3,4] and plan['private_limit_mib']==3072
    assert plan['case_timeout_seconds']==180
    assert read(directory/'monitor-check.json')['passed']

analysis=read(HERE/'analysis.json')
table=[]
for label,summary in analysis.items():
    path=HERE/'trace-correction/run'/(label+'-trace.jsonl')
    events=[json.loads(s) for s in path.read_text().splitlines()]
    assert digest(path)==summary['trace_sha256']
    assert len(events)==summary['receipt']['events']
    assert all(v['memory']['pid']==summary['receipt']['observed_pid'] for v in events)
    before_lp=next(v for v in events if v['function']=='_clean_inputs' and v['event']=='call')
    before_native=next(v for v in events if v['function']=='_highs_wrapper' and v['event']=='call')
    load=[i for i,v in enumerate(events) if v['source_line']=='init_status = highs.passModel(lp)']
    start=[i for i,v in enumerate(events) if v['source_line']=='run_status = highs.run()']
    assert load and start and load[0]<start[0]
    marker=events[start[0]]
    assert marker.get('role')==0
    first_role=events[:start[0]+1]
    assert max(v['memory']['peak_commit_bytes'] for v in first_role)<3072*1024**2
    for point in summary['points']:
        v=events[point['index']]
        assert point['private_mib']==v['memory']['private_bytes']/1024**2
        assert point['source']==v['source_line']
    if label=='001-baseline':
        original=read(HISTORY/'river-tree-expansion-001/run/001-baseline.json')
        for directory in (HERE,HERE/'trace-correction'):
            observed=read(directory/'run/001-baseline.json')
            for key in ('payoff_hashes','probabilities','certificate'):
                assert observed[key]==original[key],key
            assert observed['solution']['realizations']==original['solution']['realizations']
            assert Fraction(observed['certificate']['gap'])<=Fraction('1e-8')
        assert len(start)==2 and events[start[0]+1]['source_line']=='if run_status == _h.HighsStatus.kError:'
    else:
        assert len(start)==1 and start[0]==len(events)-1
        assert summary['receipt']['stop_reason']=='sampled_private_memory_limit'
        assert not (HERE/'trace-correction/run'/(label+'.json')).exists()
    table.append(dict(label=label,before_linprog_mib=before_lp['memory']['private_bytes']/1024**2,
        after_scipy_conversion_mib=before_native['memory']['private_bytes']/1024**2,
        before_native_run_mib=marker['memory']['private_bytes']/1024**2,
        whole_worker_peak_mib=summary['receipt']['os_peak_commit_bytes']/1024**2))

control=read(HERE/'trace-correction/monitor-check.json')['trace_boundary_control']
assert len(control)==4 and not any(v['original_filter_matches'] for v in control.values())
receipt=dict(passed=True,prior_milestones=37,prior_members=members,
    prior_manifests={p.parent.name:digest(p) for p in manifests},
    python=sys.version,numpy=numpy.__version__,scipy=scipy.__version__,
    table=table,baseline_identity_verified_in_both_attempts=True,
    original_trace_incomplete=True,corrected_boundary_control_passed=True,
    original_seconds=read(HERE/'run/receipt.json')['seconds'],
    corrected_seconds=read(HERE/'trace-correction/run/receipt.json')['seconds'])
(HERE/'verification.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',
    encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='prior_manifests'},indent=2))
