"""Verify retained descriptive results and write reports; no game/reader invocation."""
from collections import Counter
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat

root=Path('D:/Pontius/tmp/v0a-paired-evaluation-run-001')
packet=Path('D:/Pontius-handoffs/v0a-paired-closure/r001')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(path,value):
    raw=value.encode() if isinstance(value,str) else (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)

report_raw=(root/'comparison-report.json').read_bytes()
report=json.loads(report_raw)
assert report['status']=='COMPLETED_DESCRIPTIVE_COMPARISON'
raw_result=(root/'descriptive-result.json').read_bytes()
assert sha(raw_result)==report['descriptive_result_sha256']
assert raw_result==(root/'reader-stdout.bin').read_bytes()
result=json.loads(raw_result)
assert result['source_commit']=='bd71f4b11dcc0177283431a4ec468fdc152e7686'
assert result['request_sha256']=='d772691d85a903b4ac6e734b9aa4eac4f75e6ae0096def7c3c0481807729017e'
assert sha((root/'request.json').read_bytes())==result['request_sha256']
for name in ('wrapper','reader'):
    assert json.loads((root/(name+'-receipt.json')).read_bytes())==report[name]
    assert not report[name]['errors']
    assert all(n<=65536 for n in report[name]['observed_capture_bytes'])
assert report['reader']['exit_code']==0 and report['reader']['parent_elapsed_ns']<=10000000000
assert not os.path.lexists(root/'output/.publication-pending')
inventory_raw=(root/'output-file-inventory.json').read_bytes()
assert sha(inventory_raw)==report['output_inventory_sha256']
inventory=json.loads(inventory_raw)
actual=set()
for parent,dirs,names in os.walk(root/'output',followlinks=False):
    for name in dirs+names:
        path=Path(parent)/name
        info=path.lstat()
        assert not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        if name in names:
            assert stat.S_ISREG(info.st_mode)
            actual.add(path.relative_to(root/'output').as_posix())
assert actual=={f['path'] for f in inventory}
for row in inventory:
    raw=(root/'output'/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
assert sum(f['bytes'] for f in inventory)==report['output_bytes']<=4194304
assert len(inventory)==report['output_files']
for row in report['units']:
    raw=(root/'output'/f"u{row['ordinal']:03d}"/'result.json').read_bytes()
    assert sha(raw)==row['result_sha256']
    value=json.loads(raw)
    assert value['cleanup_complete'] is True and value['state']=='completed'
    assert value['elapsed_ns']==row['elapsed_ns_prefix']
assert len(report['units'])==48
plan_raw=(root/'output/plan.json').read_bytes()
assert sha(plan_raw)==result['plan_sha256']
plan=json.loads(plan_raw)
assert result['completed_pairs']==result['planned_pairs']==24
assert result['completed_trials']==result['planned_trials']==48
assert len(result['trials'])==48 and len(result['pairs'])==24
assert result['comparison_complete'] is True and result['evidentiary'] is False
trials=result['trials']
for pair in result['pairs']:
    arms={t['strategy']:t for t in trials if t['pair_index']==pair['pair_index']}
    assert len(arms)==2 and pair['complete'] is True
    b=arms['baseline-rules-v1']['net_chips']
    p=arms['blueprint-v1']['net_chips']
    assert type(b) is int and type(p) is int
    assert (pair['baseline_net_chips'],pair['blueprint_net_chips'],pair['delta_chips'])==(b,p,b-p)

def arithmetic(rows):
    b=sum(r['baseline_net_chips'] for r in rows)
    p=sum(r['blueprint_net_chips'] for r in rows)
    return dict(baseline_net_chips=b,blueprint_net_chips=p,delta_chips=b-p,
        mean_delta_numerator=b-p,mean_delta_denominator=len(rows))

aggregate=result['aggregate']
assert all(aggregate[k]==v for k,v in arithmetic(result['pairs']).items())
for field,key,count in (('lineup_index','by_lineup',12),('controlled_seat','by_seat',4)):
    for row in aggregate[key]:
        members=[p for p in result['pairs'] if plan['pairs'][p['pair_index']][field]==row[field]]
        assert len(members)==count
        assert all(row[k]==v for k,v in arithmetic(members).items())
metrics={}
for strategy in ('baseline-rules-v1','blueprint-v1'):
    members=[t for t in trials if t['strategy']==strategy]
    assert len(members)==24 and all(t['state']=='completed' for t in members)
    m={}
    for field in ('applied_actions_by_kind','baseline_fallback_selections',
                  'baseline_fallback_applied','legacy_choices'):
        values=[t[field] for t in members]
        if all(v is not None for v in values):
            counter=Counter()
            for v in values:
                counter.update(v)
            m[field]=dict(sorted(counter.items()))
        else:
            m[field]=None
    for field in ('unattributed_applied_actions','work_cutoff_actions','action_deadline_actions'):
        values=[t[field] for t in members]
        m[field]=sum(values) if all(type(v) is int for v in values) else None
    for field in ('action_failures','hand_failure_codes','session_failure_codes','capture_deficiencies'):
        m[field]=[entry for t in members for entry in (t[field] or [])]
        m[field+'_coverage_complete']=all(t[field] is not None for t in members)
    metrics[strategy]=m
verified=dict(status='VERIFIED_DESCRIPTIVE_COMPARISON',aggregate=aggregate,metrics=metrics,
    pairs=24,trials=48,wrapper_seconds=report['wrapper']['parent_elapsed_ns']/1e9,
    reader_seconds=report['reader']['parent_elapsed_ns']/1e9,output_files=report['output_files'],
    output_bytes=report['output_bytes'],reader_stdout_bytes=len(raw_result),
    all_cleanup_records_complete=True,comparison_report_sha256=sha(report_raw),
    descriptive_result_sha256=sha(raw_result),output_inventory_sha256=sha(inventory_raw),
    adoption_commit=report['adoption_commit'],source_commit=result['source_commit'],
    one_opportunity_consumed=True,lane_budget_exhausted=True,successor_authorized=False,
    standing='Exact arithmetic for this fixed matrix only; no strength, tuning or policy selection')
save(root/'result-verification.json',verified)

def table_row(label,a):
    return f"| {label} | {a['mean_delta_denominator']} | {a['baseline_net_chips']} | {a['blueprint_net_chips']} | {a['delta_chips']} | {a['mean_delta_numerator']}/{a['mean_delta_denominator']} |\n"

table='| Scope | Pairs | Baseline net chips | Blueprint net chips | Difference | Mean difference |\n'
table+='| --- | ---: | ---: | ---: | ---: | ---: |\n'
table+=table_row('All pairs',aggregate)
for row in aggregate['by_lineup']:
    table+=table_row('Lineup '+str(row['lineup_index'])+(' (passive)' if row['lineup_index']==0 else ' (mixed)'),row)
for row in aggregate['by_seat']:
    table+=table_row('Seat '+str(row['controlled_seat']),row)
markdown=f'''# Retained descriptive paired comparison

ADR-0511 adopted at {report['adoption_commit']}.
Execution source: {result['source_commit']}.
Exactly one comparison ran. All 48 trials and 24 matched pairs completed, the
single public reader passed its resource/deadline gates, and all 48 unit cleanup
records report complete. Raw file hashes and all total/subgroup arithmetic were
independently checked after successful public consumption.

{table}

Difference means baseline minus blueprint. The whole-matrix rational mean is
{aggregate['mean_delta_numerator']}/24 = {Fraction(aggregate['delta_chips'],24)} chips per matched pair.
Lineup 0 is five passive opponents. Lineup 1 is the frozen clockwise combination
fold_to_bet/min_raise_once/passive/shove_once/passive. All six seats and both fresh
deals are included, with stacks reset before every trial. The empty blueprint is
an untrained control. These two deals do not provide 24 independent samples or
establish a win rate, significance, general superiority or playing strength.
No policy selection or tuning follows from these descriptive values.

Parent launch-through-exit: {verified['wrapper_seconds']:.3f} seconds.
Separate reader interval: {verified['reader_seconds']:.3f} seconds.
Retained output: {verified['output_files']} files, {verified['output_bytes']:,} bytes,
within the 4,194,304-byte acceptance cap. Reader stdout: {len(raw_result):,} bytes,
within 65,536 bytes. Parent timing includes supervisor scheduling/polling; unit
elapsed prefixes exclude their own result publication. Peak memory, peak disk
and action-latency distributions remain unmeasured.

## Observable counters

The complete strategy-separated counters and failure scopes are below. Null means
unavailable or inapplicable, never an inferred zero. Full pair/trial summaries are
retained in descriptive-result.json and the source artifacts.

```json
{json.dumps(metrics,sort_keys=True,indent=2)}
```

This opportunity and the lane's one-invocation budget are exhausted. No retry,
extra deal, source adjustment or successor is authorized. The accompanying
architecture-checkpoint.md records the required checkpoint for a controller ruling.
All raw artifacts remain local and unchanged; no off-machine backup is asserted.

Comparison report SHA256: {sha(report_raw)}.
Public descriptive result SHA256: {sha(raw_result)}.
Output inventory SHA256: {sha(inventory_raw)}.
'''
save(root/'comparison-report.md',markdown)
checkpoint=f'''# Architecture checkpoint: paired comparison lane

Required by ADR-0511 on exhaustion of its one-invocation lane budget.
Status: prepared checkpoint; controller park-or-continue ruling pending.

Verdict: the authorized finite comparison completed and its descriptive output is
consumable. This closes the execution opportunity, not the research roadmap.
Confidence: high in fixed-matrix identity, completion and arithmetic; limited in
generalization and resource adequacy beyond these two deals.

Supporting evidence: result-verification.json independently binds all 48 trials,
24 pairs, clean unit cleanup records, the one successful public reader, retained
file inventory and aggregate/subgroup arithmetic. The full operator report is
{sha(report_raw)}; the public result is {sha(raw_result)}.
Opposing evidence: only two new deals were used; repeated rotations are dependent;
the empty blueprint is an untrained control; resource maxima and action-latency
distributions are unmeasured. This is no strength or policy-selection result.

Largest unknown: whether any later distinct workload would satisfy its own
resource, opponent-coverage and research requirements. Current results cannot
answer that by extrapolation.
Cheapest falsifier now: read-only raw identity/arithmetic verification already
completed; any discovered mismatch invalidates that affected claim and is retained.
No new runtime probe or rerun is proposed under this consumed owner.
Kill criterion: source/request/artifact drift, any score-driven tuning, reuse of
the consumed root, or any successor without the explicit checkpoint ruling.

Recommendation: park this completed comparison lane. Its frozen descriptive
question has been executed once; repetition or expansion is not automatically
useful and would need a new independently justified brief. This recommendation
is based on exhausting the planned scope, not on the sign of a poker result.
The controller may adopt parking or explicitly authorize a separately scoped next
task. No park-or-continue ruling, new decision commit or successor authority is
inferred by this note. No production source changed during this run.
'''
save(root/'architecture-checkpoint.md',checkpoint)
save(packet/'comparison-verification.json',dict(retained_root=str(root),
    verification_sha256=sha((root/'result-verification.json').read_bytes()),
    checkpoint_sha256=sha((root/'architecture-checkpoint.md').read_bytes()),
    ruling_pending=True,raw_evidence_uploaded=False))
print(json.dumps(verified))
