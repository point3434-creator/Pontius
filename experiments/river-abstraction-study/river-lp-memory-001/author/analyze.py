from pathlib import Path
from hashlib import sha256
import json

HERE=Path(__file__).parent
RUN=HERE/'trace-correction/run'
read=lambda p:json.loads(p.read_bytes())
MIB=1024**2
result={}
for record in read(RUN/'receipt.json')['records']:
    label=record['label']
    events=[json.loads(s) for s in (RUN/(label+'-trace.jsonl')).read_text().splitlines()]
    points=[]
    for i,v in enumerate(events):
        if v.get('role')!=0: continue
        f=v['function']; s=v['source_line']; k=v['event']
        choose=(f=='solve' and s.startswith('result=linprog('))
        choose|=(f in ('_clean_inputs','_format_A_constraints') and k in ('call','return'))
        choose|=(f=='_linprog_highs' and (s.startswith(('A =','res = _highs_wrapper'))))
        choose|=(f=='_highs_wrapper' and (s.startswith(('lp =','lp.a_matrix_.', 'lp.col_cost_', 'lp.col_lower_', 'lp.col_upper_', 'lp.row_lower_', 'lp.row_upper_', 'if integrality.size', 'highs =','init_status =','run_status ='))))
        if choose:
            points.append(dict(index=i,event=k,function=f,line=v['line'],source=s,
                private_mib=v['memory']['private_bytes']/MIB,
                peak_mib=v['memory']['peak_commit_bytes']/MIB,
                buffers=v['buffers']))
    jumps=sorted([(b['memory']['private_bytes']-a['memory']['private_bytes'],i,a,b)
                  for i,(a,b) in enumerate(zip(events,events[1:])) if b.get('role')==0],reverse=True,key=lambda x:x[0])[:8]
    result[label]=dict(receipt=record,points=points,largest_jumps=[dict(delta_mib=d/MIB,
        previous_index=i,previous_function=a['function'],previous_source=a['source_line'],
        next_function=b['function'],next_source=b['source_line']) for d,i,a,b in jumps],
        trace_sha256=sha256((RUN/(label+'-trace.jsonl')).read_bytes()).hexdigest(),
        last_event=events[-1])
    print(label,'peak',round(record['os_peak_commit_bytes']/MIB,1))
    for v in points:
        print(v['index'],v['event'],v['function'],v['line'],round(v['private_mib'],2),v['source'])
    print('JUMPS',json.dumps(result[label]['largest_jumps']))
(HERE/'analysis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
