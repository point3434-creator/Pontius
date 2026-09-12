from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
source=ROOT/'experiments/river-abstraction-study/witness-hybrid-001/verification-tools/audit.py'
old=source.read_text(encoding='utf-8')
new=old.replace('combined-feature experiment','boundary-resolution experiment')
new=new.replace('witness-hybrid-001','witness-boundary-001')
new=new.replace('from math import fsum,sqrt,isclose','from math import isfinite')
start=new.index('scale_data='); end=new.index('rows=[',start)
new=new[:start]+"assert read(OUT/'transform.json')==dict(clip_magnitude=.5)\n\n"+new[end:]
new=new.replace('maxgap=Q(0)','maxgap=Q(0)\nclipped_values=0\ntransform_diagnostics=[]')
needle="    for name,value in old.items(): assert row['floors'][name]==value\n"
extra='''    for method,original in (
        ('clipped_oracle',saved['teacher']['candidate']['proposal']['features']),
        ('clipped_prediction',saved['student']['proposal']['features'])):
        for seat in (0,1):
            transformed=row['features'][method][seat]
            assert len(original[seat])==len(transformed)==96
            saturated=0
            for before,after in zip(original[seat],transformed,strict=True):
                assert len(before)==len(after)==4
                for value,actual in zip(before,after,strict=True):
                    assert isfinite(value) and actual==min(.5,max(-.5,value))
                    assert (value>0)-(value<0)==(actual>0)-(actual<0)
                    saturated+=int(abs(value)>.5)
                    clipped_values+=1
            transform_diagnostics.append(dict(case=row['case']['id'],method=method,seat=seat,
                saturated_entries=saturated,total_entries=384,
                original_distinct_vectors=len({tuple(v) for v in original[seat]}),
                clipped_distinct_vectors=len({tuple(v) for v in transformed})))
'''
assert new.count(needle)==1
new=new.replace(needle,needle+extra)
new=new.replace("('raw11','hybrid')","('clipped_oracle','clipped_prediction')")
new=new.replace('scales_independently_verified=4','clipped_values_independently_verified=clipped_values')
start=new.index('analysis=dict(')
new=new[:start]+'''analysis=dict(mean_floors={m:mid(v) for m,v in summary['overall']['mean_floors'].items()},
    comparisons={m:{other:dict(delta=mid(c),counts=c['counts']) for other,c in cols.items()}
                 for m,cols in summary['overall']['comparisons'].items()},
    boards={b:dict(floors={m:mid(v) for m,v in s['mean_floors'].items()},
                   deltas={method:{m:mid(v) for m,v in cols.items()}
                           for method,cols in s['comparisons'].items()})
            for b,s in summary['boards'].items()},
    regimes={name:dict(floors={m:mid(v) for m,v in s['mean_floors'].items()},
        counts={method:{m:c['counts'] for m,c in cols.items()}
                for method,cols in s['comparisons'].items()})
        for name,s in summary['regimes'].items()},
    lobo={method:{other:[mid(s['comparisons'][method][other])
                        for s in summary['leave_one_board_out'].values()]
                  for other in summary['overall']['comparisons'][method]}
          for method in ('clipped_oracle','clipped_prediction')},
    worker_seconds=read(OUT/'worker-receipt.json')['seconds'],
    worker_plus_parent_seconds=read(OUT/'receipt.json')['seconds'],
    transform_diagnostics=transform_diagnostics)
write(OUT/'analysis.json',analysis)
print(json.dumps(verification,indent=2))
print(json.dumps({k:v for k,v in analysis.items() if k!='transform_diagnostics'},indent=2))
'''
compile(new,'audit.py','exec')
with (HERE/'audit.py').open('x',encoding='utf-8',newline='\n') as f:f.write(new)
print('Scalar/rational audit prepared without executing the experiment.')
