"""Bind unchanged logical source lines for a retained census candidate."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('capture')
p.add_argument('outdir')
a = p.parse_args()
capture = json.loads(Path(a.capture).read_bytes())
candidate = capture['source_commit']
base = '34616938c708b1ca306b9d8a17b9d98e2f9e451f'
repo = Path('D:/Pontius/tmp/v0a-evaluation-source-r001/authoring')
git = 'C:/Program Files/Git/cmd/git.exe'
path = 'tests/test_inventory_and_profiles.py'

def blob(commit):
    return subprocess.run([git, '--no-replace-objects', '-c',
        'safe.directory=' + repo.as_posix(), '-C', str(repo),
        'cat-file', 'blob', commit + ':' + path], capture_output=True, check=True).stdout

before, after = blob(base), blob(candidate)
old, new = [raw.decode().replace('\r\n', '\n').splitlines() for raw in (before, after)]
ranges = [[i + 1, i + n, j + 1]
          for i, j, n in difflib.SequenceMatcher(None, old, new, autojunk=False).get_matching_blocks()
          if n]
out = Path(a.outdir)
out.mkdir(exist_ok=False)
doc = dict(baseline_sha256=hashlib.sha256(before).hexdigest(),
           candidate_sha256=hashlib.sha256(after).hexdigest(), ranges=ranges,
           method='Exact equal logical-line blocks; increasing and injective; no heuristic fallback')
(out / 'line-map.json').write_bytes((json.dumps(doc, indent=2) + '\n').encode())
(out / 'empty-explanations.json').write_bytes(b'{}\n')
print(json.dumps(dict(candidate=candidate, output=str(out), equal_blocks=len(ranges))))
