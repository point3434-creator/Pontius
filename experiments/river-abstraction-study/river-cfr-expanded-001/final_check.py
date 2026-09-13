"""Verify new evidence and all earlier manifests; no solver execution."""
from pathlib import Path
import json
import hashlib

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


index = ROOT/'docs/research/README.md'
text = index.read_text(encoding='utf-8')
text = text.replace('\n\n| river-cfr-expanded-001 |','\n| river-cfr-expanded-001 |')
index.write_text(text,encoding='utf-8',newline='\n')
manifests = sorted(HISTORY.glob('*/milestone-manifest.json'))
members = 0
for manifest in manifests:
    for name,expected in read(manifest).items():
        assert digest(manifest.parent/name)==expected,(manifest,name)
        members += 1
target = HISTORY/HERE.name
assert digest(target/'report.md')==digest(ROOT/'docs/research/river-cfr-expanded-001.md')
pins = 0
for variant in ('checkback','raise'):
    for name,expected in read(target/variant/'plan.json')['pins'].items():
        assert digest(Path(name))==expected,name
        pins += 1
    assert read(target/variant/'run/receipt.json')['complete']
roadmap = (ROOT/'experiments/research-roadmap.md').read_text(encoding='utf-8')
assert '2609.11923v1' in roadmap and '2511.08174v1' in roadmap
for path in target.rglob('*.py'):
    compile(path.read_text(encoding='utf-8'),str(path),'exec')
result = dict(milestones=len(manifests),verified_members=members,cell_source_pins=pins,
              report_identical=True,queued_papers_preserved=True,retained_python_compiles=True)
with (HERE/'final-verification.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,indent=2,sort_keys=True)
    f.write('\n')
print(json.dumps(result))
