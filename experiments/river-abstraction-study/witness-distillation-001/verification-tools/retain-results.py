"""Archive the verified milestone, both evidence layers and report; no publication."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT/'docs/research/river-witness-distillation-r001'
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-distillation-001')
ARCHIVE = ROOT/'experiments/river-abstraction-study/witness-distillation-001'
EVIDENCE = PACKET/'invocation-001'
SCRATCH = Path(__file__).parent
REPORT = ROOT/'docs/research/river-witness-distillation-001.md'
digest = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

assert read(EVIDENCE/'verification.json')['passed'] is True
assert read(EVIDENCE/'receipt.json')['exit'] == 0
assert not ARCHIVE.exists() and not REPORT.exists()
preserved = read(PACKET/'delivery-manifest.json')
for name,h in preserved.items():
    assert digest(PACKET/name) == h,name
prior = {}
for name in ('development-001','holdout-001','group-optimality-001',
             'witness-groups-development-001','witness-pilot-001'):
    archive = ROOT/'experiments/river-abstraction-study'/name
    manifest = read(archive/'milestone-manifest.json')
    for member,h in manifest.items():
        assert digest(archive/member) == h,(name,member)
    prior[name] = dict(members=len(manifest),manifest_sha256=digest(archive/'milestone-manifest.json'))
original = {p.name:digest(p) for p in OUT.iterdir() if p.is_file()}
shutil.copytree(OUT,ARCHIVE)
shutil.copytree(EVIDENCE,ARCHIVE/'invocation')
shutil.copytree(PACKET/'accounting',ARCHIVE/'accounting')
shutil.copyfile(PACKET/'controller-authorization.json',ARCHIVE/'controller-authorization.json')
(ARCHIVE/'verification-tools').mkdir()
for name in ('verify-retained.py','retain-results.py'):
    shutil.copyfile(SCRATCH/name,ARCHIVE/'verification-tools'/name)
for name,h in original.items():
    assert digest(OUT/name) == digest(ARCHIVE/name) == h
for p in EVIDENCE.rglob('*'):
    if p.is_file():
        assert digest(p) == digest(ARCHIVE/'invocation'/p.relative_to(EVIDENCE))
members = {p.relative_to(ARCHIVE).as_posix():digest(p)
           for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():
    assert digest(ARCHIVE/name) == h,name
with REPORT.open('xb') as stream:
    stream.write((SCRATCH/'result-report.md').read_bytes())
overview = ROOT/'docs/research/README.md'
previous = overview.read_bytes()
with (EVIDENCE/'research-readme-before.md').open('xb') as stream:
    stream.write(previous)
with overview.open('ab') as stream:
    stream.write(b'\n## Reserved-board witness distillation result\n\n'
        b'[Witness-distillation-001](river-witness-distillation-001.md) records the fixed\n'
        b'models and all 48 reserved cases, with strategic comparisons, prediction errors\n'
        b'and separate worker/full-command timing. All outcomes are retained.\n')
assert overview.read_bytes().startswith(previous)
for name,h in preserved.items():
    assert digest(PACKET/name) == h,name
assert {p.name:digest(p) for p in OUT.iterdir() if p.is_file()} == original
receipt = dict(original_output_files=len(original),original_output_unchanged=True,
    milestone_directory=str(ARCHIVE),milestone_members=len(members),
    milestone_manifest_sha256=digest(ARCHIVE/'milestone-manifest.json'),
    total_files=len(members)+1,total_bytes=sum(p.stat().st_size for p in ARCHIVE.rglob('*') if p.is_file()),
    report_sha256=digest(REPORT),prior_packet_members_preserved=len(preserved),
    preserved_prior_milestones=prior,commit_performed=False,push_performed=False)
write(EVIDENCE/'retention.json',receipt)
write(EVIDENCE/'evidence-manifest.json',{p.relative_to(EVIDENCE).as_posix():digest(p)
    for p in sorted(EVIDENCE.rglob('*')) if p.is_file()})
print(json.dumps(receipt,indent=2))
