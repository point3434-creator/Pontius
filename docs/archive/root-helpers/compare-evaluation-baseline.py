"""Compare retained baseline captures; never imports repository modules."""
import hashlib
import json
from pathlib import Path

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
rows = []
for population in ('test', 'production'):
    documents = []
    identities = []
    for slot in ('311', '314'):
        path = root / 'process-temp' / f'baseline-census-{population}-{slot}' / f'census-{population}.json'
        raw = path.read_bytes()
        doc = json.loads(raw)
        identities.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                               interpreter=doc.pop('interpreter')))
        documents.append(doc)
    assert documents[0] == documents[1], population
    encoded = json.dumps(documents[0], sort_keys=True, separators=(',', ':')).encode()
    rows.append(dict(population=population, equal_complete_documents_excluding_interpreter=True,
                     normalized_sha256=hashlib.sha256(encoded).hexdigest(), inputs=identities))
result = dict(version='pontius-evaluation-baseline-comparison-v1', comparisons=rows)
raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
out = root / 'baseline-census-comparison.json'
with out.open('xb') as stream:
    assert stream.write(raw) == len(raw)
assert out.read_bytes() == raw
print(raw.decode())
