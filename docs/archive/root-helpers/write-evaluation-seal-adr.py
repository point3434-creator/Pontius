"""Instantiate the proposed ADR only from completed, exact source acceptance."""
import hashlib
import json
from pathlib import Path

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
summary_path = root / 'packets/r001/checks/final-acceptance-summary.json'
summary = json.loads(summary_path.read_bytes())
assert summary['candidate']['commit'] == 'bca326c6bfedd71324a19c809f617e267cc9e0a2'
assert all(t['commands'] == 16 and t['skips'] == 0 for t in summary['totals'].values())
assert summary['totals']['311']['tests'] == summary['totals']['314']['tests']
template = Path(__file__).with_name('evaluation-seal-adr-template.md').read_text(encoding='utf-8')
text = template.replace('@TESTS_PER_SLOT@', str(summary['totals']['311']['tests']))
text = text.replace('@TOTAL_TESTS@', str(sum(t['tests'] for t in summary['totals'].values())))
text = text.replace('@ACCEPTANCE_SHA@', hashlib.sha256(summary_path.read_bytes()).hexdigest())
assert '@' not in text
raw = text.replace('\r\n', '\n').encode()
assert all(len(line) <= 100 and line.rstrip() == line for line in raw.decode().splitlines())
destination = root / 'authoring/docs/decisions/ADR-0509-source-seal-the-paired-local-evaluation-loop.md'
with destination.open('xb') as stream:
    assert stream.write(raw) == len(raw)
print(json.dumps(dict(path=str(destination), sha256=hashlib.sha256(raw).hexdigest())))
