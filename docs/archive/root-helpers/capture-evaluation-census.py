"""Read-only capture of complete unchanged analyzer returns for ADR-0508 registration."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

root = Path.cwd()
path = root / 'tools/generate_test_inventory.py'
spec = importlib.util.spec_from_file_location('pontius_evaluation_census_observer', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert Path(module.__file__).resolve() == path.resolve()
population = sys.argv[1]
assert population in ('test', 'production')
raw = (root / 'tests/test-inventory.json').read_bytes()
inventory = json.loads(raw)
profiles = tomllib.loads((root / 'tests/test-profiles.toml').read_text(encoding='utf-8'))
capture = None
if population == 'test':
    sources = module._working_sources(root)
else:
    capture = module._capture_working_sources(root, include_support_modules=True)
    sources = capture.sources
direct = {p: value for p, value in sources.items()
          if p.startswith('tests/') and Path(p).name.startswith('test')}
discovery = module.discover_test_sources(direct)
assert set(discovery.stable_ids) == {row['stable_id'] for row in inventory['entries']}
profile_by_id = {row['stable_id']: row['assignment']['profile_name']
                 for row in inventory['entries']}
design_profiles = {'core', 'current', 'gpu'}
universe = {('stable_id', item) for item, profile in profile_by_id.items()
            if profile in design_profiles}
for fixture in discovery.lifecycle_fixtures:
    members = {profile_by_id[item] for item in fixture.member_ids}
    if members <= design_profiles:
        universe.add(('fixture', fixture.fixture_id))
    else:
        assert members == {'historical'}
for payload in profiles['payload']:
    if payload['profile_name'] in design_profiles:
        universe.update(('probe', str(item)) for item in payload['probe_ids'])
observed = {}
process_code = module._process_review_rows.__code__
decoy_code = module._string_decoy_census.__code__


def observe(frame, event, result):
    if event == 'return' and frame.f_code is process_code:
        assert 'process_rows' not in observed
        observed['process_rows'] = copy.deepcopy(result)
    elif event == 'return' and frame.f_code is decoy_code:
        assert 'decoy_rows_with_provenance' not in observed
        observed['decoy_rows_with_provenance'] = copy.deepcopy(frame.f_locals['rows_with_provenance'])


sys.setprofile(observe)
try:
    review = module.derive_design_review(
        baseline_commit=module.BASELINE_COMMIT,
        baseline_root_tree_oid=module.BASELINE_ROOT_TREE_OID,
        inventory_document=inventory, inventory_document_bytes=raw,
        sources=sources, item_universe=tuple(sorted(universe)))
finally:
    sys.setprofile(None)
assert len(observed) == 2
if capture is not None:
    capture.revalidate()
head = subprocess.run([os.environ['PONTIUS_GIT'], '--no-replace-objects',
                       '--no-optional-locks', '-C', str(root), 'rev-parse', 'HEAD'],
                      capture_output=True, check=True).stdout.decode().strip()
document = dict(version='pontius-evaluation-census-capture-v1', population=population,
                source_commit=head, interpreter=sys.version,
                analyzer_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                inventory_sha256=hashlib.sha256(raw).hexdigest(),
                profiles_sha256=hashlib.sha256((root / 'tests/test-profiles.toml').read_bytes()).hexdigest(),
                item_universe=sorted(universe), review=review, observed=observed)
out = Path(os.environ['TEMP']) / ('census-' + population + '.json')
encoded = (json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
with out.open('xb') as stream:
    assert stream.write(encoded) == len(encoded)
    stream.flush()
    os.fsync(stream.fileno())
assert out.read_bytes() == encoded
print(json.dumps(dict(path=str(out), sha256=hashlib.sha256(encoded).hexdigest(),
                      source_commit=head, population=population,
                      expanded_rows=len(review['receipt']['expanded_rows']),
                      blockers=len(review['unresolved_dynamic_blockers']),
                      analysis_census=review['analysis_census']), sort_keys=True))
