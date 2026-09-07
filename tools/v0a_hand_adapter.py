"""Run one declared file-backed correctness hand; never operating authority."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

BASE = 'e205cd8cd6f46a50db8b2d0cb1f39366da0f2767'
ADDITIONS = tuple('src/pontius/decision_provider/' + name + '.py'
                  for name in ('__init__', 'model', 'providers', 'selection', 'codec'))
EXCEPTIONS = ('src/pontius/v0a/runtime.py', 'tools/v0a_hand_adapter.py')
TOOLS = ('tools/v0a_hand_adapter.py', 'tools/v0a_rehearsal_driver.py')
PREFIX = 'pontius-v0a-hand-replay-v1-correctness-adapter-'


class AdapterRefusal(ValueError):
    """A failed admission or acceptance boundary; retained bytes are never repaired."""


def require(condition, reason):
    if not condition:
        raise AdapterRefusal(reason)


def regular(path, directory=False):
    info = path.lstat()
    require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)),
            f'PATH: not regular/non-reparse: {path}')


def checked_path(path, *, directory=False, d_local=True):
    require(path.is_absolute() and len(path.drive) == 2 and '..' not in path.parts
            and (not d_local or path.drive.upper() == 'D:'), 'PATH: absolute local path required')
    for parent in path.parents:
        regular(parent, directory=True)
    regular(path, directory)
    return path


class Source:
    """Raw commit/blob identity, not an archive/filter or a source-adoption claim."""
    def __init__(self, repo):
        require(os.name == 'nt' and sys.flags.dont_write_bytecode and sys.flags.safe_path,
                'SOURCE: require Windows Python -B -P')
        require(not any(n == 'pontius' or n.startswith('pontius.') for n in sys.modules),
                'SOURCE: pontius must not be preloaded')
        self.repo = checked_path(repo, directory=True)
        require(Path(__file__).absolute() == self.repo / TOOLS[0],
                'SOURCE: executed adapter must be the declared tool origin')
        self.git = checked_path(Path(os.environ.get('PONTIUS_GIT', '')), d_local=False)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.upper().startswith(('GIT_', 'PYTHON', 'PONTIUS_'))}
        self.commit = self.head()
        current, inherited = self.inventory(self.commit), self.inventory(BASE)
        require(set(current) == set(inherited) | set(ADDITIONS) | {TOOLS[0]},
                'SOURCE: unexpected committed source population')
        require(all(current[p] == oid for p, oid in inherited.items() if p not in EXCEPTIONS),
                'SOURCE: inherited source differs from pinned base')
        stream = io.BytesIO(self.command('cat-file', '--batch',
                             content=('\n'.join(current.values()) + '\n').encode('ascii')))
        self.expected = {}
        for path, oid in current.items():
            header = stream.readline().split()
            require(len(header) == 3 and header[:2] == [oid.encode(), b'blob'],
                    'SOURCE: raw object is not the requested blob')
            content = stream.read(int(header[2]))
            require(len(content) == int(header[2]) and stream.read(1) == b'\n',
                    'SOURCE: truncated raw blob')
            self.expected[path] = content
        require(stream.read() == b'', 'SOURCE: extra raw object output')
        rows = sorted(hashlib.sha256(raw).hexdigest().encode() + b'  ' + path.encode() + b'\n'
                      for path, raw in self.expected.items())
        self.manifest = hashlib.sha256(b''.join(rows)).hexdigest()
        self.check()

    def command(self, *args, content=None):
        result = subprocess.run([str(self.git), '--no-replace-objects', '--no-optional-locks',
                                 '-C', str(self.repo), *args], input=content, env=self.env,
                                capture_output=True, timeout=30)
        require(result.returncode == 0, 'SOURCE: raw Git operation failed')
        return result.stdout

    def head(self):
        commit = self.command('rev-parse', '--verify', 'HEAD^{commit}').decode('ascii').strip()
        require(re.fullmatch('[0-9a-f]{40}', commit), 'SOURCE: invalid commit identity')
        return commit

    def inventory(self, commit):
        entries = self.command('ls-tree', '-r', '-z', commit, '--', 'src/pontius', *TOOLS)
        result = {}
        for row in entries.split(b'\0'):
            if not row:
                continue
            metadata, name = row.split(b'\t', 1)
            mode, kind, oid = metadata.split()
            require(mode in (b'100644', b'100755') and kind == b'blob',
                    'SOURCE: committed source must be regular blobs')
            result[name.decode('utf-8')] = oid.decode('ascii')
        require(result, 'SOURCE: empty raw source inventory')
        return result

    def check(self):
        require(self.head() == self.commit, 'SOURCE: HEAD changed during invocation')
        package = self.repo / 'src/pontius'
        checked_path(package, directory=True)
        actual, directories = {}, set()
        for parent, dirs, files in os.walk(package, followlinks=False):
            for name in dirs:
                path = Path(parent) / name
                regular(path, directory=True)
                directories.add(path.relative_to(self.repo).as_posix())
            for name in files:
                path = Path(parent) / name
                regular(path)
                actual[path.relative_to(self.repo).as_posix()] = path.read_bytes()
        expected_dirs = {p.as_posix() for name in self.expected
                         if name.startswith('src/pontius/') for p in Path(name).parents
                         if p.as_posix().startswith('src/pontius/')}
        require(directories == expected_dirs, 'SOURCE: extra or missing package directory')
        for name in TOOLS:
            path = checked_path(self.repo / name)
            actual[name] = path.read_bytes()
        require(actual == self.expected, 'SOURCE: missing, modified, extra or cached source bytes')

    def load(self):
        sys.path.insert(0, str(self.repo / 'src'))
        import pontius.hand_scenario.codec as scenario_codec
        import pontius.blueprint_artifact.codec as blueprint_codec
        import pontius.v0a.replay as replay
        import pontius.v0a.trace as trace
        for module in (scenario_codec, blueprint_codec, replay, trace):
            expected = self.repo / 'src' / (module.__name__.replace('.', '/') + '.py')
            require(Path(module.__file__).absolute() == expected,
                    'SOURCE: delayed import origin disagrees with checked source')
        return scenario_codec, blueprint_codec, replay, trace


def accept(outcome, destination, scenario, policy, run_id, source, replay, trace):
    require(outcome.receipt.passed is True and outcome.receipt.accounting_complete is True,
            'HOST: replay, publication or accounting did not complete')
    content = checked_path(destination).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    require(content == outcome.trace and digest == outcome.receipt.trace_sha256,
            'READBACK: persisted trace differs from completed publication')
    verified = replay.verify_successful_trace(content, fixture=scenario.fixture, blueprint=policy,
        source_commit=source.commit, source_manifest_sha256=source.manifest,
        expected_mode='correctness', expected_clock_kind='monotonic_ns')
    require(verified.run_id == run_id and outcome.receipt.run_id == run_id,
            'VERIFY: completed run differs from requested identity')
    actions = tuple((row['street'], row['selected_action']['kind'],
                     row['selected_action']['raise_to'], row['selection_reason'])
                    for row in trace.parse_trace(content).records
                    if row['record_type'] == 'decision')
    require(actions == scenario.expected_actions, 'EXPECTATION: controlled actions differ')
    source.check()
    return dict(passed=True, evidentiary=False, mode='correctness', run_id=run_id,
        case_id=scenario.fixture.name, source_commit=source.commit,
        source_manifest_sha256=source.manifest, blueprint_sha256=policy.digest,
        trace_sha256=digest, semantic_sha256=verified.semantic_sha256, trace_path=str(destination),
        actions=[dict(zip(('street', 'kind', 'raise_to', 'selection_reason'), row))
                 for row in actions],
        table_hits=sum(row[3] == 'table_hit' for row in actions),
        passive_fallbacks=sum(row[3] == 'passive_default' for row in actions),
        payouts=verified.payouts, final_stacks=verified.final_stacks)


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise AdapterRefusal('ARGUMENT: ' + message)


def main(argv=None):
    try:
        parser = Arguments(description=__doc__)
        for field in ('scenario', 'blueprint', 'run-root'):
            parser.add_argument('--' + field, required=True, type=Path)
        parser.add_argument('--run-id', required=True)
        args = parser.parse_args(argv)
        require(re.fullmatch(re.escape(PREFIX) + '[A-Za-z0-9_-]+', args.run_id),
                'IDENTITY: correctness adapter namespace required')
        root = checked_path(args.run_root, directory=True)
        require(root.name == args.run_id and not any(root.iterdir()),
                'ROOT: existing empty directory named exactly as run ID required')
        scenario_path, policy_path = checked_path(args.scenario), checked_path(args.blueprint)
        source = Source(Path(__file__).absolute().parents[1])
        scenario_codec, blueprint_codec, replay, trace = source.load()
        raw_scenario, raw_policy = scenario_path.read_bytes(), policy_path.read_bytes()
        scenario_hash = hashlib.sha256(raw_scenario).hexdigest()
        policy_hash = hashlib.sha256(raw_policy).hexdigest()
        scenario = scenario_codec.decode_scenario(raw_scenario)
        policy = blueprint_codec.decode_blueprint(raw_policy)
        outcome = replay.ReplayHost(scenario.fixture, run_id=args.run_id, blueprint=policy,
            mode='correctness', source_commit=source.commit, source_manifest_sha256=source.manifest,
            clock_kind='monotonic_ns').run(destination='trace.jsonl', run_root=root)
        summary = accept(outcome, root / 'trace.jsonl', scenario, policy, args.run_id,
                         source, replay, trace)
        summary.update(scenario_sha256=scenario_hash, blueprint_artifact_sha256=policy_hash)
        line = json.dumps(summary, sort_keys=True, separators=(',', ':'), allow_nan=False)
        payload = (line + '\n').encode('utf-8')
        require(os.write(sys.stdout.fileno(), payload) == len(payload),
                'OUTPUT: incomplete summary write')
        return 0
    except Exception as error:  # The CLI is the typed refusal boundary for every failed phase.
        print(f'REFUSED {type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
