"""Derive the small experiment delta from the sealed predecessor, before freeze."""
from pathlib import Path

HERE=Path(__file__).parent
OLD=Path('D:/Pontius-worktrees/eval-runner-consolidation/experiments/river-abstraction-study/witness-bet-conditioned-001/verification-tools')
s=(OLD/'experiment.py').read_text()
def replace_function(name,body):
    global s
    begin=s.index('def '+name+'(')
    end=s.find('\ndef ',begin+1)
    assert end>begin
    s=s[:begin]+body.strip()+'\n'+s[end:]
s=s.replace('from bridge import','from loader import').replace('import model\n','from loader import model,parent\nimport ordinal\n')
s=s.replace("SEED='witness-bet-conditioned-001'","SEED='witness-ordinal-001'")
s=s.replace("'conditioned'","'ordinal'").replace("'blind'","'sign_conditioned'")
s=s.replace("METHODS=(*SOLVERS,'oracle_sign','oracle_clipped')","METHODS=(*SOLVERS,'oracle_ordinal','oracle_sign','oracle_clipped')")
replace_function('fit_models','''
def fit_models(rows):return ordinal.fit_models(rows)
''')
replace_function('proposal','''
def proposal(core,witnesses,models):
    groups={m:core['bank_groups'][m] for m in SOLVERS if m in BANK}
    features={}
    for m in ('ordinal','sign_conditioned','oracle_ordinal','oracle_sign','oracle_clipped'):
        groups[m]=[];features[m]=[]
        for seat in (0,1):
            if m in models:
                x=model.design(core['raw_features'][seat],core['bet'],True)
                f=model.predict(models[m][seat],x)
            elif m=='oracle_ordinal':f=ordinal.targets(witnesses[seat]['advantages'])
            else:f=np.asarray(witnesses[seat]['target' if m=='oracle_sign' else 'clipped'])
            k=len(set(core['bank_groups'][BANK[0]][seat]))
            g=anchored_clusters(f,np.asarray(witnesses[seat]['weights']),k).tolist()
            assert len(set(g))==k
            groups[m].append(g);features[m].append(f.tolist())
        if m=='ordinal':
            for seat in (0,1):
                baseline=model.predict(models['sign_conditioned'][seat],
                    model.design(core['raw_features'][seat],core['bet'],True))
                assert np.array_equal(np.asarray(features[m][seat])[:,[1,4,7]],baseline)
    crossings=[ordinal.crossing(features['ordinal'][seat],witnesses[seat]['weights']) for seat in (0,1)]
    return dict(groups=groups,features=features,ordinal_crossings=crossings)
''')
begin=s.index('    training=[]\n',s.index('def worker('))
end=s.index('    models=fit_models(training)',begin)
s=s[:begin]+'''    training=[]
    for case in plan['training_cases']:
        for bet in BETS:
            path=PRIOR/filename('train',case,bet)
            row=read(path)
            training.append(row);write(out/path.name,row)
    assert calls==0
'''+s[end:]
s=s.replace('assert calls<=1280','assert calls<=1024').replace('assert calls==1280','assert calls==1024')
s=s.replace("fit_tasks=12,\n        schema='two-bet-preference-v1',outputs_per_seat=3,quadratic_columns=91)",
"fit_tasks=18,\n        schema='ordinal-preference-v1',outputs_per_seat=dict(ordinal=9,sign_conditioned=3),\n        thresholds=list(ordinal.THRESHOLDS),baseline_sha256=digest(PRIOR/'candidate.json'),quadratic_columns=91)")
s=s.replace('lp_calls=1280,fit_tasks=12','lp_calls=1024,fit_tasks=18')
s=s.replace('conditioning_actual_gain','ordinal_actual_gain').replace('conditioning_floor_gain','ordinal_floor_gain')
s=s.replace("return dict(actual=actual,floors=floors,comparisons=comparisons)",
"return dict(actual=actual,floors=floors,comparisons=comparisons,\n        crossing_mass=[avg([r['proposal']['ordinal_crossings'][seat]['mean'] for r in rows]) for seat in (0,1)])")
old="""        assert pair[0]['proposal']['features']['sign_conditioned']==pair[1]['proposal']['features']['sign_conditioned']
        assert pair[0]['proposal']['groups']['sign_conditioned']==pair[1]['proposal']['groups']['sign_conditioned']
"""
assert old in s;s=s.replace(old,'')
s=s.replace('assert (certs,policies)==(1280,768)','assert (certs,policies)==(1408,768)')
s=s.replace('fit_tasks_reproduced=12','fit_tasks_reproduced=18')
old="""            row=read(out/filename('train',case,bet));matrix,core=setup(case,bet,tool,cache)
"""
new=old+"            assert row==read(PRIOR/filename('train',case,bet))\n"
assert old in s;s=s.replace(old,new)
old="    candidate=read(out/'candidate.json')\n"
new=old+"    assert candidate['baseline_sha256']==digest(PRIOR/'candidate.json')\n    assert candidate['thresholds']==list(ordinal.THRESHOLDS)\n"
assert old in s;s=s.replace(old,new)
(HERE/'experiment.py').write_text(s,encoding='utf-8',newline='\n')

s=(OLD/'audit.py').read_text()
s=s.replace("'conditioned'","'ordinal'").replace("'blind'","'sign_conditioned'")
s=s.replace("'range_response','oracle_sign'","'range_response','oracle_ordinal','oracle_sign'")
s=s.replace('conditioning_actual_gain','ordinal_actual_gain').replace('conditioning_floor_gain','ordinal_floor_gain')
old="        elif isinstance(b,str):assert a==b;checks+=1"
new="        elif isinstance(b,list):\n            assert len(a)==len(b)\n            for x,y in zip(a,b,strict=True):compare(x,y)\n"+old
assert old in s;s=s.replace(old,new)
old="        return dict(actual={m:avg(v) for m,v in vals.items()},floors=floors,comparisons=comparisons)"
new="""        crossing=[]
        for seat in (0,1):
            masses=[]
            for r in rs:
                fs=r['proposal']['features']['ordinal'][seat]
                ws=list(map(Q,r['witness'][seat]['weights']))
                mass=sum(w*sum(any(Q(f[j+k+1])-Q(f[j+k])>Q(1e-12) for k in (0,1))
                    for j in (0,3,6)) for w,f in zip(ws,fs,strict=True))/sum(ws)/3
                masses.append(mass)
            crossing.append(avg(masses))
        return dict(actual={m:avg(v) for m,v in vals.items()},floors=floors,
                    comparisons=comparisons,crossing_mass=crossing)"""
assert old in s;s=s.replace(old,new)
(HERE/'audit.py').write_text(s,encoding='utf-8',newline='\n')
print('Derived experiment and independent audit from the frozen predecessor.')
