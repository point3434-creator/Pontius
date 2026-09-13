from pathlib import Path
import json
from hashlib import sha256
from fractions import Fraction as Q

HERE=Path(__file__).parent
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
plan=read(HERE/'plan.json')
assert digest(HERE/'plan.json')=='1215eb9a264712154212cf5ba57cbf62d15afe3dd523ba1651d8a309951bb5ea'
for p,h in plan['pins'].items(): assert digest(Path(p))==h,p
assert read(HERE/'preflight.json')['passed']
manifests=list(HISTORY.glob('*/milestone-manifest.json'))
assert len(manifests)==38
members=0
for p in manifests:
    for name,h in read(p).items():
        assert digest(p.parent/name)==h,(p,name)
        members+=1
receipt=read(HERE/'run/receipt.json')
assert len(receipt['rows'])==6
events={}
table=[]
certificates=[]
engine=literal=0
for job,row in zip(plan['jobs'],receipt['rows']):
    assert job['label']==row['label']
    label=row['label']
    calls=[json.loads(line) for line in (HERE/'run'/(label+'-calls.jsonl')).read_text().splitlines()]
    assert all(v['memory']['pid']==row['worker']['observed_pid'] for v in calls)
    entries=[c for c in calls if c['event']=='enter']
    returns=[c for c in calls if c['event']=='return']
    assert all(c['options']==dict(time_limit=10,maxiter=20000,presolve=job['presolve'],
        primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9) for c in entries)
    assert all(c['method']=='highs-ds' for c in entries)
    events[label]=entries
    if row['variant']=='baseline':
        assert len(entries)==len(returns)==2
        assert row['worker']['exit']==row['verify']['exit']==0
        result=read(HERE/'run'/(label+'.json'))
        audit=read(HERE/'run'/(label+'-audit.json'))
        assert audit['passed'] and audit['baseline_interval_overlap'] and audit['new_lp_calls']==0
        assert result['executing_pid']==row['worker']['observed_pid']
        assert audit['executing_pid']==row['verify']['observed_pid']
        assert all(v['success'] for v in returns)
        assert Q(result['certificate']['gap'])<=Q('1e-8')
        assert row['strict_pass'] and row['solver_success']
        certificates.append(result['certificate'])
        engine+=audit['engine']['checks']
        literal+=len(audit['literal_subgames'])
        if job['presolve']:
            old=read(HISTORY/'river-tree-expansion-001/run/001-baseline.json')
            assert all(old[k]==result[k] for k in ('payoff_hashes','probabilities','certificate'))
            assert old['solution']['realizations']==result['solution']['realizations']
    else:
        assert len(entries)==1 and len(returns)==0
        assert row['worker']['stop_reason']=='sampled_private_memory_limit'
        assert not (HERE/'run'/(label+'.json')).exists()
    table.append(dict(label=label,compute_seconds=row.get('compute_seconds'),
        worker_seconds=row['worker']['seconds'],peak_mib=row['worker']['os_peak_commit_bytes']/1024**2,
        strict_pass=row.get('strict_pass',False),error=row.get('error'),
        outcome='certified' if row.get('strict_pass') else row['worker']['stop_reason']))
for variant in ('baseline','checkback','raise'):
    a,b=(events['001-'+variant+'-'+arm] for arm in ('on','off'))
    assert len(a)==len(b)
    assert all(x['matrix']==y['matrix'] for x,y in zip(a,b)),variant
assert max(Q(c['lower']) for c in certificates)<=min(Q(c['upper']) for c in certificates)
result=dict(passed=True,prior_milestones=38,prior_members=members,
    prior_manifests={p.parent.name:digest(p) for p in manifests},table=table,
    all_entered_paired_matrices_equal=True,baseline_on_exact_prior_identity=True,
    baseline_intervals_overlap=True,engine_terminal_checks=engine,literal_subgames=literal,
    completed_lp_calls=4,stopped_lp_calls=4,campaign_seconds=receipt['seconds'],
    capacity_improved=False,no_complete_peak_or_timing_comparison_for_stopped_cells=True)
(HERE/'assessment.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',
    encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='prior_manifests'},indent=2))
