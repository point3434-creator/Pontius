"""Audit and locally preserve the exact documentation-only cold-review packet."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('D:/Pontius/tmp/v0a-paired-prereg-r001')
work = root / 'authoring'
packet = root / 'packets/r001'
home = Path('D:/Pontius-handoffs/v0a-paired-prereg/r001')
facts = json.loads((root / 'preparation-facts.json').read_bytes())
identity = json.loads((packet / 'candidate.json').read_bytes())
git_exe = 'C:/Program Files/Git/cmd/git.exe'


def git(*args):
    return subprocess.run([git_exe, '--no-replace-objects', '-c',
        f'safe.directory={work.as_posix()}', '-C', str(work), *args],
        check=True, capture_output=True).stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        assert stream.write(raw) == len(raw)


assert identity['base'] == facts['base']
assert git('rev-parse', identity['ref']).decode().strip() == identity['commit']
assert git('rev-parse', identity['commit']+'^{tree}').decode().strip() == identity['tree']
assert git('rev-parse', identity['commit']+'^').decode().strip() == identity['base']
assert sorted(git('diff', '--name-only', identity['base'], identity['commit']).decode().splitlines()) == sorted(facts['paths'])
rows = []
for path in facts['paths']:
    raw = git('cat-file', 'blob', identity['commit']+':'+path)
    assert raw == (packet/'files'/path).read_bytes()
    assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
    assert all(line.rstrip() == line for line in raw.decode().splitlines())
    rows.append(sha(raw)+'  '+path+'\n')
manifest = ''.join(sorted(rows)).encode()
assert manifest == (packet/'manifest.sha256').read_bytes()
assert sha(manifest) == identity['manifest_sha256']
for path, digest in facts['pins'].items():
    assert sha(git('cat-file','blob',identity['base']+':'+path)) == digest
    assert git('cat-file','blob',identity['base']+':'+path) == git('cat-file','blob',identity['commit']+':'+path)
request_raw = (packet/'files'/facts['paths'][2]).read_bytes()
request = json.loads(request_raw)
assert len(request_raw) == facts['request_bytes'] == 352
assert sha(request_raw) == facts['request_sha256']
assert (json.dumps(request, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode() == request_raw
assert set(request) == set('version seed deal_count lineups seat_start initial_button total_budget_ms trial_budget_ms'.split())
assert request['version'] == 'pontius-v0a-evaluation-request-v1' and request['seed'] == '0'*64
assert request['deal_count'] == 1 and request['seat_start'] == request['initial_button'] == 0
assert request['lineups'] == [['passive']*5,['fold_to_bet','min_raise_once','passive','shove_once','passive']]
assert request['trial_budget_ms'] == 360000 and request['total_budget_ms'] == 9000000
assert facts['safety_arithmetic_ms'] == 24*(360000+5000)+240000 == 9000000
contract = ast.parse(git('cat-file','blob',identity['base']+':tools/v0a_evaluation_contract.py'))
policies = next(ast.literal_eval(node.value) for node in contract.body if isinstance(node,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='POLICIES' for t in node.targets))
assert all(p in policies for lineup in request['lineups'] for p in lineup)
copy = json.loads((root/'status-copy.json').read_bytes())
assert sha(Path(copy['receipt']).read_bytes()) == copy['receipt_sha256']
generation = json.loads(Path(copy['receipt']).read_bytes())
assert len(generation) == 2 and all(r['exit_code']==0 for r in generation)
assert generation[0]['stdout'].startswith('3.11.15 ')
assert 'pontius.status_generation as m' in generation[0]['argv'][3]
assert Path(copy['source']).read_bytes().replace(b'\r\n',b'\n') == (packet/'files/STATUS.md').read_bytes()
assert git('diff','--name-only',copy['snapshot_head'],identity['commit']).decode().splitlines()==['STATUS.md']
run_root = Path('D:/Pontius/tmp/v0a-paired-rehearsal-run-001')
assert not run_root.exists()
audit = dict(verdict='PASS', candidate=identity, facts=facts, planned_pairs=12, planned_trials=24,
    zero_dealer_or_poker_payloads=True, reserved_root=str(run_root), reserved_root_absent=True,
    status_generation=copy, standing='Static proposal audit and status generation only; reviews/gates pending')
raw = (json.dumps(audit,sort_keys=True,indent=2)+'\n').encode()
save(packet/'proposal-audit.json',raw)
handoff = f'''# First paired rehearsal preregistration: cold review

Task v0a-paired-prereg/r001. Tier C: external rehearsal authority, identity,
measurement provenance and evidence meaning. Finalizer: Codex coordinator.
Read this handoff FIRST, then candidate.json/manifest.sha256 and all four frozen
files. Read applicable CLAUDE.md, PROJECT.md evidence/dissent protocol, workflow.md,
ADR-0482 rehearsal rules, ADR-0485 bootstrap sequencing, ADR-0509 source seal and
the immutable public wrapper/contract needed to assess the proposed commands.

Candidate: {identity['commit']}
Tree: {identity['tree']}
Base: {identity['base']}
Ref: {identity['ref']}
Manifest SHA256: {identity['manifest_sha256']}
Object repository: {work.as_posix()}
Native Git: C:/Program Files/Git/cmd/git.exe
Original packet: {packet.as_posix()}
Canonical local packet: {home.as_posix()}
Proposal audit SHA256: {sha(raw)}

Review the entire four-path candidate, including source/read-only reader command
bindings, literal request and arithmetic, bootstrap safety-versus-operating-budget
distinction, one opportunity/no-retry ownership, supervision and failure standing,
cost interval limitations, prohibition on outcome use, future population boundary,
and metadata front door. Independently verify raw Git blobs and all pinned identities,
canonical request shape/size/hash, complete changed-path scope and reserved-root
absence. Check the exact public CLI/reader against raw sealed source without running
it. Consider any real circular or weakened authority/measurement condition; do not
accept a label as a substitute for the governing semantics. Verify the scaled-cost
and missing-resource limits are honest. The source is unchanged and needs no new
substantive implementation review; these are normative documents and an inert JSON.

No transcript, coordinator rationale, other current review or implementation report
may be read. The frozen audit and its raw sources are permitted evidence; independently
establish your expectations before treating its PASS as a conclusion. Read-only native
Git and standalone stdlib hash/JSON/AST inspection are allowed. No test, status generator,
request decoder import, dealer, poker, wrapper/reader invocation, rehearsal, mutation,
source edit, subagent, commit, push or upload may be performed. Write only your own
create-new LF review report in this packet's reviews directory. Both reviewers are blind.

After two independent CLEAN verdicts, the coordinator runs four exact candidate gates:
status --check and twelve status tests on actual3.11.15 first, then the same on3.14.6,
fresh D-local snapshots, -B -P, scrubbed env, snapshot cwd/src, actual version/flags/cwd
and status module-origin preflight, absolute native Git. No run root or cards are created.
The decision commit and the exact single rehearsal launch remain separate user actions.
The local packet is preserved; no remote upload is part of this review.

Return CLEAN/NOT CLEAN, specification PASS/FAIL, engineering PASS/FAIL, mandatory design
SOUND/STRAINED/WRONG SHAPE, severity/locations for required corrections, confidence,
supporting/opposing evidence, largest unknown, cheapest falsifying check, kill criterion,
recommendation, limits and report SHA256. Bind the exact candidate plus manifest above.
Do not infer adoption, an authorized launch or completed future measurements.
'''
save(packet/'handoff.md',handoff.encode())
for path in sorted(packet.rglob('*')):
    if path.is_file():
        save(home/path.relative_to(packet),path.read_bytes())
for path in (root/'preparation-facts.json',root/'status-copy.json',root/'run-records/gen1-311.json'):
    save(home/'checks'/path.name,path.read_bytes())
save(root/'progress.md', f'''# Paired rehearsal preregistration progress

- Prepared the requested next step after ADR-0509 adoption. ADR-0482/0485 require
  authorized rehearsal cost provenance before measured evaluation closure. No old
  source correctness record was relabelled as that measurement.
- Four documentation/request paths frozen at {identity['commit']}, manifest
  {identity['manifest_sha256']}. Static audit PASS; no runtime payload or run root.
- Two fresh Tier C reviews and four exact metadata gates pending. No adoption,
  remote publication, rehearsal launch or actual evaluation.
'''.encode())
print(json.dumps(dict(candidate=identity, audit_sha256=sha(raw),canonical_packet=str(home))))
