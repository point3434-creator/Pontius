"""Audit a frozen metadata candidate and prepare its local light-review handoff."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('D:/Pontius/tmp/v0a-evaluation-seal-r001')
source_root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
work = source_root / 'authoring'
packet = root / 'packets/r001'
source_packet = source_root / 'packets/r001'
git_exe = 'C:/Program Files/Git/cmd/git.exe'


def git(*args):
    return subprocess.run([git_exe, '--no-replace-objects', '-c',
        f'safe.directory={work.as_posix()}', '-C', str(work), *args],
        check=True, capture_output=True).stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        assert stream.write(raw) == len(raw)
    assert path.read_bytes() == raw


identity = json.loads((packet / 'candidate.json').read_bytes())
source = json.loads((source_packet / 'candidate.json').read_bytes())
summary_path = source_packet / 'checks/final-acceptance-summary.json'
summary = json.loads(summary_path.read_bytes())
assert summary['candidate'] == source
assert source['commit'] == 'bca326c6bfedd71324a19c809f617e267cc9e0a2'
assert identity['base'] == source['base']
assert git('rev-parse', identity['ref']).decode().strip() == identity['commit']
assert git('rev-parse', identity['commit'] + '^').decode().strip() == source['base']
assert git('rev-parse', identity['commit'] + '^{tree}').decode().strip() == identity['tree']
source_rows = (source_packet / 'manifest.sha256').read_bytes().decode().splitlines()
source_paths = [row.split('  ', 1)[1] for row in source_rows]
assert len(source_paths) == 12
metadata_paths = ['STATUS.md',
    'docs/decisions/ADR-0509-source-seal-the-paired-local-evaluation-loop.md']
all_paths = sorted(source_paths + metadata_paths)
changed = git('diff', '--name-only', '--no-renames', identity['base'],
              identity['commit']).decode().splitlines()
assert sorted(changed) == all_paths
assert sorted(git('diff', '--name-only', '--no-renames', source['commit'],
                 identity['commit']).decode().splitlines()) == sorted(metadata_paths)
rows = []
incorporation = []
for path in all_paths:
    raw = git('cat-file', 'blob', identity['commit'] + ':' + path)
    assert raw == (packet / 'files' / path).read_bytes()
    assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
    assert all(line.rstrip() == line for line in raw.decode().splitlines())
    rows.append(sha(raw) + '  ' + path + '\n')
    if path in source_paths:
        source_raw = git('cat-file', 'blob', source['commit'] + ':' + path)
        assert raw == source_raw == (source_packet / 'files' / path).read_bytes()
        incorporation.append(dict(path=path, sha256=sha(raw), bytes=len(raw)))
    elif path != 'STATUS.md':
        assert all(len(line) <= 100 for line in raw.decode().splitlines())
manifest = ''.join(sorted(rows)).encode()
assert manifest == (packet / 'manifest.sha256').read_bytes()
assert sha(manifest) == identity['manifest_sha256']
assert b'@ACCEPTANCE_SHA@' not in (packet / 'files' / metadata_paths[1]).read_bytes()
git('diff', '--check', identity['base'], identity['commit'])
review_hashes = {'review-a.md':
    '034bc3a780b0e83c34519707183dff5dc33fedab6289efa4a0407f554b4e09cc',
    'review-b.md': '255af51e120b379e371083724f011c5edc314a577a1b4a3655ed7b34d4786346'}
for name, digest in review_hashes.items():
    assert sha((source_packet / 'reviews' / name).read_bytes()) == digest
assert all(t['commands'] == 16 and t['skips'] == 0 for t in summary['totals'].values())
for row in summary['acceptance_receipts']:
    receipt = Path(row['receipt'])
    assert sha(receipt.read_bytes()) == row['sha256']
    probe, payload = json.loads(receipt.read_bytes())
    assert all(r['snapshot_head'] == source['commit'] and r['exit_code'] == 0
               for r in (probe, payload))
generation = json.loads((root / 'status-generation-copy.json').read_bytes())
generation_receipt = Path(generation['receipt'])
assert sha(generation_receipt.read_bytes()) == generation['receipt_sha256']
generation_records = json.loads(generation_receipt.read_bytes())
assert len(generation_records) == 2
assert all(r['exit_code'] == 0 and r['snapshot_head'] == generation['snapshot_head']
           for r in generation_records)
assert generation_records[0]['stdout'].startswith('3.11.15 ')
assert 'pontius.status_generation as m' in generation_records[0]['argv'][3]
assert generation_records[-1]['argv'] == ['-B', '-P', '-m', 'pontius.status_generation']
generated_raw = Path(generation['source']).read_bytes()
assert sha(generated_raw) == generation['generated_raw_sha256']
status_raw = (packet / 'files/STATUS.md').read_bytes()
assert generated_raw.replace(b'\r\n', b'\n') == status_raw
assert sha(status_raw) == generation['copied_sha256']
assert git('diff', '--name-only', generation['snapshot_head'],
           identity['commit']).decode().splitlines() == ['STATUS.md']
audit = dict(verdict='PASS', candidate=identity, incorporated_source=source,
    incorporated_paths=incorporation, metadata_paths=metadata_paths,
    full_change_paths=all_paths, source_acceptance_summary=str(summary_path),
    source_acceptance_summary_sha256=sha(summary_path.read_bytes()),
    source_acceptance_totals=summary['totals'], source_reviews=review_hashes,
    status_generation=generation,
    standing='Exact source incorporation and metadata scope only; light review and four gates pending')
audit_raw = (json.dumps(audit, sort_keys=True, indent=2) + '\n').encode()
write(packet / 'incorporation-audit.json', audit_raw)
write(packet / 'metadata.diff', git('diff', '--no-ext-diff', '--no-renames', '-U10',
                                  source['commit'], identity['commit']))
handoff = f'''# Paired evaluation source-seal metadata light review

Task v0a-evaluation-seal/r001. Tier A: verified mechanical incorporation and
decision metadata; the underlying whole source has two fresh CLEAN Tier C reviews
and all 32 prescribed exact-candidate acceptance commands passed. Finalizer: Codex
coordinator. This is a frozen local review snapshot, not an adopted decision.

Read this handoff first, then candidate.json, manifest.sha256, metadata.diff,
the two metadata files, incorporation-audit.json and its raw named evidence.
Read D:/Pontius/CLAUDE.md, docs/workflow.md and adopted ADR-0508/source-contract;
ADR-0506 provides the prior metadata integration procedure. Use only immutable
candidate blobs and exact retained evidence. Do not read a current other review,
implementation transcripts or coordinator conversation.

## Exact identities

Candidate: {identity['commit']}
Tree: {identity['tree']}
Base: {identity['base']}
Ref: {identity['ref']}
Manifest SHA256: {identity['manifest_sha256']}

Accepted source candidate: {source['commit']}
Source manifest SHA256: {source['manifest_sha256']}
Source packet: D:/Pontius-handoffs/v0a-evaluation-source/r001/
Original source packet: {source_packet.as_posix()}/
Source acceptance summary: {summary_path.as_posix()}
Summary SHA256: {sha(summary_path.read_bytes())}
Source acceptance totals: {json.dumps(summary['totals'], sort_keys=True)}
Incorporation audit SHA256: {sha(audit_raw)}
Native Git: C:/Program Files/Git/cmd/git.exe
Object repository: {work.as_posix()}

## Bounded review

Independently verify ref/parent/tree/manifest and all fourteen frozen raw files.
Verify all twelve incorporated source blobs equal the named fully accepted source,
the entire remaining diff is exactly ADR-0509 and generated STATUS, and all other
tracked blobs equal base. Inspect the actual source review reports and raw receipt
index, including prior retained failures, against the ADR's factual claims. Verify
the status-generation receipt and copied output, new decision headers, front-door
standing and no new evaluation or invocation authority. Distinguish a reviewed
draft from an adopted source seal. Check exact source and comparison hashes and
budgets, including the explicit 1200-to-1250 controller ruling. The source code need
not undergo a redundant substantive Tier C review; escalate a real incorporation
or metadata claim defect if found. Read-only native Git, raw hash/JSON/AST inspection
is permitted. No test, generator, analyzer, poker/evaluation payload, mutation,
source edit, new agent, commit, push or upload may be run by this reviewer.

One fresh independent Tier A CLEAN review precedes four final metadata checks:
status --check then all twelve status tests on actual 3.11.15, then those same two
commands on actual 3.14.6. Each uses a fresh exact metadata candidate D-local
snapshot, -B -P, scrubbed env, snapshot cwd/src, actual-version/flags/cwd and
status-module-origin preflight, absolute native Git. These checks are pending.

Remote handoff upload is blocked by automatic approval review and pending explicit
user permission; the local canonical packet is complete. Do not attempt publication
or treat local preservation as evidence of remote upload. This administrative block
is not source or metadata acceptance. The ceremonial decision also remains pending
separate exact user authorization under CLAUDE rule 4; do not claim adoption.

Write only reviews/review-light.md under the canonical local packet
D:/Pontius-handoffs/v0a-evaluation-seal/r001/, using create-new LF bytes. Return
CLEAN/NOT CLEAN, specification PASS/FAIL, engineering PASS/FAIL, mandatory design
SOUND/STRAINED/WRONG SHAPE, required findings, evidence/limits and report SHA256.
The verdict must bind the exact metadata candidate and manifest above.
'''
write(packet / 'handoff.md', handoff.encode())
print(json.dumps(dict(candidate=identity, audit_sha256=sha(audit_raw), paths=len(all_paths))))
