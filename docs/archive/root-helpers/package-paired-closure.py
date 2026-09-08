import hashlib
import json
import os
from pathlib import Path
import subprocess

root=Path('D:/Pontius/tmp/v0a-paired-closure-r001')
packet=root/'packets/r001'
home=Path('D:/Pontius-handoffs/v0a-paired-closure/r001')
work=root/'authoring'
identity=json.loads((packet/'candidate.json').read_bytes())
facts=json.loads((root/'preparation-facts.json').read_bytes())

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        f.write(raw.encode() if isinstance(raw,str) else raw)

def git(*args):
    return subprocess.run(['C:/Program Files/Git/cmd/git.exe','--no-replace-objects',
        '-c',f'safe.directory={work.as_posix()}','-C',str(work),*args],
        capture_output=True,check=True).stdout

assert identity['base']==facts['base']
assert git('rev-parse',identity['ref']).decode().strip()==identity['commit']
assert git('rev-parse',identity['commit']+'^{tree}').decode().strip()==identity['tree']
assert sorted(git('diff','--name-only',identity['base'],identity['commit']).decode().splitlines())==sorted(facts['paths'])
rows=[]
for path in facts['paths']:
    raw=git('cat-file','blob',identity['commit']+':'+path)
    assert raw==(packet/'files'/path).read_bytes()
    assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
    assert all(line.rstrip()==line for line in raw.splitlines())
    rows.append(sha(raw)+'  '+path+'\n')
manifest=''.join(sorted(rows)).encode()
assert manifest==(packet/'manifest.sha256').read_bytes()
assert sha(manifest)==identity['manifest_sha256']
generated=(root/'snapshots/gen2-311/STATUS.md').read_bytes()
assert generated.replace(b'\r\n',b'\n')==(packet/'files/STATUS.md').read_bytes()
assert not os.path.lexists('D:/Pontius/tmp/v0a-paired-evaluation-run-001')
generation=[]
for name in ('gen1-311.json','gen2-311.json'):
    raw=(root/'run-records'/name).read_bytes()
    generation.append(dict(receipt=name,sha256=sha(raw),exit_code=json.loads(raw)[-1]['exit_code']))
    save(packet/'checks'/name,raw)
audit=dict(candidate=identity,verdict='PASS',paths=facts['paths'],basis=facts['basis'],
    reserved_root_absent=True,zero_poker_or_reader_invocations=True,generation=generation,
    generation_correction='First draft used Decision and exact boundary; exact Decision heading required. '
        'Only unsealed heading corrected; failed snapshot/receipt retained. gen2 PASS.',
    status_transformation='CRLF to LF only',status_sha256=sha(generated.replace(b'\r\n',b'\n')))
raw=(json.dumps(audit,indent=2,sort_keys=True)+'\n').encode()
save(packet/'proposal-audit.json',raw)
handoff=f'''# Measured paired comparison: cold review

Task v0a-paired-closure/r001, NEW-SURFACE, Tier C. Finalizer Codex coordinator.
Read this handoff FIRST, then candidate.json/manifest.sha256 and the five raw frozen
files. Candidate {identity['commit']}; tree {identity['tree']};
base {identity['base']}; ref {identity['ref']}.
Manifest SHA256 {identity['manifest_sha256']}.
Object repository: {work.as_posix()}.
Canonical local packet: {home.as_posix()}.
Native Git: C:/Program Files/Git/cmd/git.exe.
Proposal audit SHA256 {sha(raw)}.

Read applicable complete CLAUDE.md, PROJECT.md evidence/dissent protocol and current
docs/workflow.md, ADR-0482/0485/0489/0508/0509/0510, and the sealed paired source
contract/public wrapper/contract as necessary. Establish your own invariant inventory
before reading proposal-audit.json. No transcript, coordinator rationale, other
current review or implementation report may be read. Reviewers are independent/blind.

Review the entire five-path prospective contract. Independently recompute complete
raw Git delta, source/base/tree/ref identities, manifest under whole-row-byte sorting,
literal request/seed derivation/counts/types/arithmetic, every cost-basis record hash,
raw output inventory hashes and cost projections. Rehearsal records stay at their
original paths under D:/Pontius/tmp/v0a-paired-rehearsal-run-001. The cost report,
identity/intent/receipt records and read-only raw file hashing are allowed inputs.
Do not display or use any rehearsal poker score/card/ranking; inspect only needed
cost/identity/completion/cleanup fields. No private values supply design decisions.

Challenge authority and resource necessity under ADR-0489; explicit scoped versus
missing resource limits; honesty of margin four and finite sample; unit prefix versus
full interval; shared deadline versus source admission/visibility; single-lifecycle
budget and checkpoint; actual CLI/reader binding and invocation standing; reader
deadline/output/capture gates before descriptive consumption; complete denominators;
all failure/retention paths; future population uniqueness claims; source immutability.
Labels cannot replace real semantics. Assess concrete unsafe or circular conditions.
No prior source seal re-review is required; its exact execution tree and preservation
must be verified. Unavailable historical review objects may be reported as limits.

No test, status generator, repository import, request decoder, dealer, poker,
wrapper/reader invocation, rehearsal, source change, commit/push/upload or subagent.
Read-only native Git and standalone stdlib JSON/hash/AST/header calculation allowed.
Write only your assigned create-new LF review report and own one-line attributed
ledger in reviews/. That directory is provided. No candidate byte changes permitted.

Return CLEAN/NOT CLEAN, specification/engineering PASS/FAIL, mandatory design
SOUND/STRAINED/WRONG SHAPE, severity/location/concrete scenario for required findings,
confidence, supporting/opposing evidence, largest unknown, cheapest falsifier,
kill criterion, recommendation, limits and report SHA256. Verdict binds exact
candidate plus manifest. No adoption, launch or measured worst-case claim.

After both CLEAN, four exact metadata gates only: status --check and twelve status
tests on actual 3.11.15 first then 3.14.6, fresh D-local exact snapshots, scrubbed
-B -P, cwd/src, version/module-origin probe and absolute native Git. No run root,
cards or poker payload is created. Decision commit/push and exact single launch
need final user authority. Local packet publication is not a remote upload.
'''
save(packet/'handoff.md',handoff)
for path in packet.rglob('*'):
    if path.is_file():
        save(home/path.relative_to(packet),path.read_bytes())
(home/'reviews').mkdir()
save(root/'progress.md',f'''# Measured paired closure progress

- Five-path proposal frozen at {identity['commit']}, manifest
  {identity['manifest_sha256']}. Static audit PASS; gen1 metadata heading failure
  retained and gen2 generated status PASS. Two fresh Tier C reviews pending.
- No adoption, remote packet upload, new card generation, public reader or comparison.
''')
print(json.dumps(dict(candidate=identity,audit_sha256=sha(raw),home=str(home))))
