"""Post-run verification only, with an explicit all-zero payoff case."""
from pathlib import Path
import importlib.util
import json
import sys
import shutil
import itertools
import os
from fractions import Fraction as Q
from time import perf_counter

HERE=Path(__file__).resolve().parent
POST=HERE/'post-verification'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m


e=load('frozen_expansion',HERE/'experiment.py')
fixed=load('zero_safe_tree',POST/'tree.py')
e.t=fixed
e.OUT=POST/'results'
t=fixed
plan=e.d.read(HERE/'plan.json')


def zero_control():
    record=t.d.read(t.d.b.PRIOR/'input-000.json')
    nodes=t.public_tree(record,'checkback')
    sizes,_=t.sequence_layout(nodes)
    arrays={tuple(n['payoff']):t.np.zeros((2,2)) for n in nodes if n['player']==-1}
    probs={str(i):t.quantize(t.np.ones((2,len(n['children']))))
           for i,n in enumerate(nodes) if n['player']!=-1}
    old=load('original_zero_control',HERE/'tree.py')
    try:
        old.certificate(nodes,sizes,arrays,probs)
    except ValueError as error:
        failure=str(error)
        assert 'empty' in failure
    else:
        raise AssertionError('original must expose the zero-payoff edge case')
    result=t.certificate(nodes,sizes,arrays,probs)
    assert all(Q(result[k])==0 for k in ('lower','upper','value','gap'))
    e.write(POST/'zero-control.json',dict(original_failure=failure,corrected=result,new_lp_calls=0))


def verify(index):
    e.bindings(plan)
    def forbidden(*args,**kwargs): raise AssertionError('post-run verification cannot optimize')
    t.linprog=forbidden
    e.verify(plan,index)
    job=plan['jobs'][index]
    row=e.d.read(e.OUT/(job['label']+'.json'))
    record,nodes,sizes,flows,arrays,hashes=e.game(job)
    probs=row['probabilities']
    any_nonzero=next(a for k,a in arrays.items() if k[0]=='fold')
    coordinates=t.np.argwhere(any_nonzero!=0)
    counts=0
    for position in (0,10000,500000):
        i,j=map(int,coordinates[position%len(coordinates)])
        assert i!=j
        ix=[i,j]
        sub={k:a[t.np.ix_(ix,ix)] for k,a in arrays.items()}
        sp={n:[p[k] for k in ix] for n,p in probs.items()}
        cert=t.certificate(nodes,sizes,sub,sp)
        assert t.literal_value(nodes,sizes,sub,sp)==Q(cert['value'])
        for role in (0,1):
            owned=[(n,node) for n,node in enumerate(nodes) if node['player']==role]
            choices=[range(len(node['children'])) for n,node in owned for _ in ix]
            values=[]
            for combo in itertools.product(*choices):
                candidate=dict(sp)
                for k,(n,node) in enumerate(owned):
                    candidate[str(n)]=[[t.GRID if a==combo[2*k+h] else 0
                        for a in range(len(node['children']))] for h in range(2)]
                values.append(t.literal_value(nodes,sizes,sub,candidate))
            assert (max(values) if role==0 else min(values))==Q(cert['upper' if role==0 else 'lower'])
            counts+=len(values)
    e.write(e.OUT/(job['label']+'-independent.json'),dict(passed=True,executing_pid=os.getpid(),
        nonzero_subgames=3,exhaustive_pure_responses=counts,new_lp_calls=0))


def run():
    zero_control()
    e.OUT.mkdir(exist_ok=False)
    receipts=[]
    start=perf_counter()
    for index,job in enumerate(plan['jobs']):
        source=HERE/'run'/(job['label']+'.json')
        if not source.exists():
            receipts.append(dict(label=job['label'],status='no saved policy; original resource refusal retained'))
            continue
        shutil.copyfile(source,e.OUT/source.name)
        code=('import sys,runpy;sys.path[:0]='+repr([e.monitor.SITE,str(HERE)])+
              ';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")')
        cmd=[e.monitor.BASE_PYTHON,'-I','-S','-B','-W','error::ResourceWarning','-c',code,
             str(HERE/'verify_saved.py'),'verify',str(index)]
        receipt=e.monitor.monitor(cmd,plan,e.OUT,job['label']+'-post')
        assert receipt['exit']==0 and receipt['stop_reason'] is None
        audit=e.d.read(e.OUT/(job['label']+'-independent.json'))
        assert audit['executing_pid']==receipt['observed_pid']
        receipts.append(dict(label=job['label'],status='verified',receipt=receipt))
        print(job['label']+' verified without new LP calls',flush=True)
    e.bindings(plan)
    e.write(POST/'receipt.json',dict(seconds=perf_counter()-start,records=receipts,
        new_lp_calls=0,verified=sum(r['status']=='verified' for r in receipts)))


if __name__=='__main__':
    if sys.argv[1]=='run': run()
    else: verify(int(sys.argv[2]))
