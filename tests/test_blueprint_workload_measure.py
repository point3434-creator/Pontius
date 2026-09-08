"""Finite real-provider controls; controlled clocks are not performance evidence."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / 'tools' / (name + '.py')
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Clock:
    def __init__(self):
        self.value = -10

    def __call__(self):
        self.value += 10
        return self.value


class BlueprintWorkloadMeasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load('v0a_blueprint_workload_measure')
        cls.p = load('v0a_blueprint_workload_population')
        fixture = json.loads((ROOT / 'tests/fixtures/blueprint_workload/control.json').read_bytes())
        # Four legal trajectories total per invocation; no future recipe seeds.
        cls.traces = [cls.p.trajectory(cls.p.factors('table', i), seed=fixture['seed'])
                      for i in (0, 6, 12, 18)]
        cls.members = cls.p.interleave([t['contexts'] for t in cls.traces])

    def setUp(self):
        self.assertIsNotNone(self.m, 'direct measurement contract implementation is absent')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def inputs(self, size=1):
        raw, meta = self.p.artifact(self.members[:size])
        path = Path(self.temp.name) / f'{size}.json'
        path.write_bytes(raw)
        meta['file'] = dict(sha256=self.p.sha(raw))
        return dict(artifact_path=path, artifact_metadata=meta,
                    selections=dict(first_context=self.members[0]), population=self.p,
                    clock=Clock(), stage=lambda name: None)

    def test_five_operations_real_outputs_and_independent_wrong_result_refusal(self):
        source = self.m.decode_blueprint(self.inputs()['artifact_path'].read_bytes())
        provider = self.m.PreparedBlueprintProvider(source)
        for hit, record in ((True, self.members[0]), (False, self.members[-1])):
            query = self.m.prepare_queries([record], source, self.p, hit)[0]
            for name in ('key', 'hash', 'lookup', 'identity', 'provider'):
                result = self.m.operation(name, query, provider)
                self.m.validate_result(name, result, query)
                with self.assertRaises(self.m.Refusal):
                    self.m.validate_result(name, object(), query)

    def test_construction_separate_intervals_and_exact_bytes(self):
        for size in (0, 1, 16, 128):
            inputs = self.inputs(size)
            result = self.m.construction_observation(inputs)
            self.assertEqual([result[k] for k in
                ('read_ns', 'decode_ns', 'prepare_ns', 'first_ns', 'canonical_ns', 'sha_ns')],
                [10] * 6)
            self.assertEqual(result['outer_total_ns'], 90)
            self.assertEqual(result['source_sha256'], inputs['artifact_metadata']['source_sha256'])
            self.assertEqual(result['memory_samples'], [])
            for field in ('wire_bytes', 'key_bytes', 'canonical_bytes'):
                self.assertEqual(result[field], inputs['artifact_metadata'][field])

    def test_artifact_drift_and_exact_input_refusals(self):
        inputs = self.inputs()
        inputs['artifact_path'].write_bytes(b'{}')
        with self.assertRaises(self.m.Refusal): self.m.construction_observation(inputs)
        inputs['artifact_metadata']['wire_bytes'] = 2
        inputs['artifact_metadata']['file']['sha256'] = self.p.sha(b'{}')
        with self.assertRaises(self.m.Refusal): self.m.construction_observation(inputs)
        inputs = self.inputs()
        inputs['artifact_metadata']['source_sha256'] = '0' * 64
        with self.assertRaises(self.m.Refusal): self.m.construction_observation(inputs)
        for field in ('size', 'wire_bytes', 'key_bytes', 'canonical_bytes'):
            inputs = self.inputs()
            inputs['artifact_metadata'][field] = True
            with self.assertRaises(self.m.Refusal): self.m.construction_observation(inputs)

    def test_reuse_charges_initial_preparation_and_each_retained_hash(self):
        source = self.m.decode_blueprint(self.inputs()['artifact_path'].read_bytes())
        sequences = [[self.members[0], self.members[-1]], [self.members[0]]]
        results = {}
        for arm, outer, prepare, hashes in [('fresh', 50, [10, 10], []),
                                           ('retained', 70, [10], [10, 10])]:
            results[arm] = self.m.reuse_group(source, sequences, self.p, arm,
                                            source.digest, Clock())
            self.assertEqual(results[arm]['group_ns'], outer)
            self.assertEqual(results[arm]['prepare_ns'], prepare)
            self.assertEqual(results[arm]['hash_ns'], hashes)
            self.assertEqual(results[arm]['query_count'], 3)
            self.assertEqual(results[arm]['distinct_keys'], 2)
        self.assertEqual(results['fresh']['context_ids'], results['retained']['context_ids'])

    def test_cached_byte_mismatch_refuses_against_frozen_source(self):
        source = self.m.decode_blueprint(self.inputs()['artifact_path'].read_bytes())
        provider = self.m.PreparedBlueprintProvider(source)
        object.__setattr__(provider._blueprint, '_canonical', b'changed owned bytes')
        with self.assertRaises(self.m.Refusal) as caught:
            self.m.verify_cached(provider, source.digest, Clock())
        self.assertEqual(caught.exception.code, 'parity_failed')

    def test_caller_and_result_isolation(self):
        source = self.m.decode_blueprint(self.inputs()['artifact_path'].read_bytes())
        provider = self.m.PreparedBlueprintProvider(source)
        observation = self.p.replay_context(self.members[0])
        initial = provider.propose(observation)
        object.__setattr__(source.entries[0].action, 'raise_to', 999)
        object.__setattr__(initial.action, 'raise_to', 888)
        again = provider.propose(self.p.replay_context(self.members[0]))
        self.assertEqual(self.p.action_payload(again.action), dict(kind='call', raise_to=None))
        self.assertIsNot(initial.action, again.action)
        first_key = self.p.context_key(observation)
        indexed = next(iter(provider._blueprint._actions))
        self.assertEqual(first_key, indexed)
        self.assertIsNot(first_key, indexed)

    def test_finite_phase_retention_and_validation_outside_clock(self):
        source = self.m.decode_blueprint(self.inputs()['artifact_path'].read_bytes())
        provider = self.m.PreparedBlueprintProvider(source)
        queries = self.m.prepare_queries(self.members[:1], source, self.p, True)
        for individual, expected in ((False, [10, 10]), (True, [10, 10])):
            clock = Clock()
            samples, position = self.m.operation_phase('provider', queries, provider,
                clock, count=2, batch_calls=3, individual=individual, offset=0)
            self.assertEqual(samples, expected)
            self.assertEqual(position, 2 if individual else 6)
            self.assertEqual(clock.value, 30)
        self.assertTrue(hasattr(self.m, 'history_block'), 'finite ABBA control seam is absent')
        block, offsets = self.m.history_block('lookup', dict(hit=queries, miss=[]), provider,
            Clock(), dict(hit=0, miss=0), warmups=1, batches=1, batch_calls=2, individual_calls=2)
        self.assertEqual(block['hit']['batch_ns'], [10, 10])
        self.assertEqual(block['hit']['individual_ns'], [10] * 4)
        self.assertEqual(block['miss'], dict(context_ids=[], batch_ns=[], individual_ns=[]))
        self.assertEqual(offsets, dict(hit=10, miss=0))
        controls = self.m.clock_controls(Clock(), brackets=3, batches=2, calls=2)
        self.assertEqual(controls['empty_brackets_ns'], [10] * 3)
        self.assertEqual(controls['empty_batches_ns'], [10] * 2)
        self.assertEqual(controls['loop_batches_ns'], [10] * 2)

    def test_comparison_continuous_context_cycle_and_provider_parity(self):
        source = self.m.decode_blueprint(self.inputs(16)['artifact_path'].read_bytes())
        selected = dict(hit=self.members[:3], miss=self.members[-3:])
        result = self.m.comparison_blocks(source, selected, self.p, Clock(),
                                         blocks=3, warmups=2, calls_per_class=2)
        for block_index, block in enumerate(result):
            self.assertEqual(block['legacy'], block['prepared'])
            for label in ('hit', 'miss'):
                self.assertEqual(block['legacy'][label]['context_ids'],
                    [selected[label][(block_index * 2 + i) % 3]['id'] for i in range(2)])
                self.assertEqual(block['legacy'][label]['call_ns'], [10, 10])

    def test_memory_real_trace_and_owned_stage_order(self):
        inputs = self.inputs()
        stages = []
        def stage(name):
            stages.append(name)
            if name == 'final':
                import sys
                # The final native sample must see all named owners simultaneously alive.
                owners = sys._getframe(1).f_locals
                self.assertTrue({'raw', 'source', 'provider', 'observation'} <= set(owners))
                self.assertEqual(len(owners['raw']), inputs['artifact_metadata']['wire_bytes'])
                if owners['traced']:
                    self.assertFalse(self.m.tracemalloc.is_tracing())
                    self.assertGreater(owners['retained'], 0)
                else:
                    self.assertIsNotNone(owners['proposal'].action)
        inputs['stage'] = stage
        untraced = self.m.memory_observation(inputs, traced=False)
        self.assertEqual(stages, ['idle', 'read', 'decode', 'prepare', 'first', 'final'])
        self.assertEqual(untraced['memory_samples'], [])
        stages.clear()
        traced = self.m.memory_observation(inputs, traced=True)
        self.assertEqual(stages, ['final'])
        self.assertGreater(traced['retained_bytes'], 0)
        self.assertGreaterEqual(traced['peak_bytes'], traced['retained_bytes'])
        self.assertEqual(traced['excluded_observation'], self.members[0]['id'])

    def test_profile_and_cell_shape_refusals(self):
        inputs = self.inputs()
        with self.assertRaises(self.m.Refusal): self.m.measure_cell({}, inputs)
        import gc
        gc.disable()
        try:
            with self.assertRaises(self.m.Refusal): self.m.construction_observation(inputs)
        finally:
            gc.enable()


if __name__ == '__main__':
    unittest.main()
