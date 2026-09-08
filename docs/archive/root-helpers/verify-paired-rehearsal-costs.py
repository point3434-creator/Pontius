"""Read-only cost checks and append-only report; no public payload invocation."""
import hashlib
import json
import os
from pathlib import Path
import stat

root = Path('D:/Pontius/tmp/v0a-paired-rehearsal-run-001')
packet = Path('D:/Pontius-handoffs/v0a-paired-prereg/r001')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    raw = value.encode() if isinstance(value, str) else (json.dumps(value,
        indent=2, sort_keys=True)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)


raw_report = (root/'cost-report.json').read_bytes()
report = json.loads(raw_report)
inventory = json.loads((root/'output-file-inventory.json').read_bytes())
actual = set()
for parent, directories, files in os.walk(root/'output', followlinks=False):
    for name in directories + files:
        path = Path(parent)/name
        info = path.lstat()
        assert not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        if name in files:
            assert stat.S_ISREG(info.st_mode)
            actual.add(path.relative_to(root/'output').as_posix())
assert actual == {row['path'] for row in inventory}
for row in inventory:
    raw = (root/'output'/row['path']).read_bytes()
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
assert sum(row['bytes'] for row in inventory) == report['output_retained_bytes']
assert len(inventory) == report['output_regular_files']
for name in ('wrapper', 'reader'):
    receipt = json.loads((root/(name+'-receipt.json')).read_bytes())
    assert receipt == report[name]
    assert receipt['parent_elapsed_ns'] == receipt['finished_monotonic_ns']-receipt['started_monotonic_ns']
    assert receipt['exit_code'] == 0 and not receipt['errors']
assert report['source']['commit'] == 'bd71f4b11dcc0177283431a4ec468fdc152e7686'
assert sha((root/'request.json').read_bytes()) == report['request_sha256']
completion = json.loads((root/'reader-stdout.bin').read_bytes())
assert completion == report['completion']
assert completion['planned_trials'] == completion['completed_trials'] == 24
assert completion['planned_pairs'] == completion['completed_pairs'] == 12
assert not os.path.lexists(root/'output/.publication-pending')
prefixes = []
for unit in report['units']:
    raw = (root/'output'/f"u{unit['ordinal']:03d}"/'result.json').read_bytes()
    assert sha(raw) == unit['result_sha256']
    value = json.loads(raw)
    assert unit['state'] == value['state'] == 'completed'
    assert unit['cleanup_complete'] is value['cleanup_complete'] is True
    assert unit['elapsed_ns_prefix'] == value['elapsed_ns']
    prefixes.append(unit['elapsed_ns_prefix'])
assert len(prefixes) == 24
summary = dict(status='COMPLETED_COST_REHEARSAL', source_commit=report['source']['commit'],
    adoption_commit=report['adoption_commit'], completed_pairs=12, completed_trials=24,
    wrapper_seconds=report['wrapper']['parent_elapsed_ns']/1e9,
    reader_seconds=report['reader']['parent_elapsed_ns']/1e9,
    unit_prefix_min_seconds=min(prefixes)/1e9, unit_prefix_max_seconds=max(prefixes)/1e9,
    output_files=len(inventory), output_bytes=report['output_retained_bytes'],
    max_unit_stdout_bytes=report['max_unit_stdout_bytes'],
    max_unit_stderr_bytes=report['max_unit_stderr_bytes'],
    source_tracked_bytes=report['source_checkout_tracked_bytes'],
    report_sha256=sha(raw_report), inventory_sha256=sha((root/'output-file-inventory.json').read_bytes()),
    checks='Exact file inventory/hashes, cost receipts and all 24 completed unit cleanup records verified',
    no_new_payload_invocations=True, operating_closure_admitted=False)
save(root/'cost-verification.json', summary)
markdown = f'''# Retained paired cost rehearsal

ADR-0510 adopted at {summary['adoption_commit']}.
Execution source: {summary['source_commit']}.
Exactly one wrapper launch; 24/24 trials and 12/12 pairs completed. The one
approved public reader succeeded. All 24 unit cleanup records report complete.

| Measurement | Observed value |
| --- | ---: |
| Parent launch-through-exit interval | {summary['wrapper_seconds']:.3f} seconds |
| Separate public-reader interval | {summary['reader_seconds']:.3f} seconds |
| Unit elapsed prefixes, minimum to maximum | {summary['unit_prefix_min_seconds']:.3f}–{summary['unit_prefix_max_seconds']:.3f} seconds |
| Retained output regular files | {summary['output_files']} |
| Retained output bytes | {summary['output_bytes']:,} |
| Maximum unit stdout bytes | {summary['max_unit_stdout_bytes']:,} |
| Maximum unit stderr bytes | {summary['max_unit_stderr_bytes']:,} |
| Source checkout tracked bytes, separate | {summary['source_tracked_bytes']:,} |

Parent intervals include supervisor scheduling and up to one second of polling delay.
Unit times end before unit result publication and are not complete per-trial walls.
Output storage is the post-run retained total, not peak disk. Source checkout and
external supervisor diagnostics are separate. Peak memory, peak disk and action p95
remain unmeasured; new-deal scaling remains unsupported by this single synthetic deal.

This is non-evidentiary cost provenance only. No poker scores or rankings are reported
or used. It does not establish playing strength or authorize an evaluation. The
single opportunity is consumed and all artifacts remain retained without retry.
Next: prepare a separate measured operating closure, addressing resource gaps and
scaling assumptions before any actual paired evaluation is admitted.

Raw cost report SHA256: {summary['report_sha256']}.
File inventory SHA256: {summary['inventory_sha256']}.
'''
save(root/'cost-report.md', markdown)
save(packet/'rehearsal-disposition.json', dict(summary=summary, retained_root=str(root),
    raw_evidence_uploaded=False, standing='One approved rehearsal completed and retained; measured closure pending'))
print(json.dumps(summary))
