"""Focused opposing checks: synthetic models and first-two old boards only."""
import importlib.util
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np

from pontius import river_witness_distillation as distill
from pontius import river_witness_pilot as pilot
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS, anchored_clusters

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
SCRATCH = Path('D:/Pontius/tmp/witness-distill-review-01')


def test_all_quadratic_columns_in_exact_order():
    x = (np.arange(22).reshape(2, 11) + 1) / 23
    expected = []
    for row in x:
        expected.append([1., *row, *(row[i] * row[j] for i in range(11)
                                     for j in range(i, 11))])
    np.testing.assert_array_equal(distill.design(x), expected)
    assert distill.design(x).dtype == np.float64


def test_equal_case_weight_despite_unequal_rows_and_mass():
    # All predictors coincide, so an unpenalized intercept must equal the
    # average of the two case means, regardless of row count and total mass.
    first = (np.zeros((1, 11)), np.full((1, 4), 2.), np.array([1000.]))
    second = (np.zeros((3, 11)), np.full((3, 4), 10.), np.array([1., 2., 7.]))
    model = distill.fit_model([first, second])
    np.testing.assert_allclose(distill.predict(model, np.zeros((1, 11))), 6.,
                               rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.asarray(model['coefficients'])[1:], 0.,
                               rtol=0, atol=1e-12)


def test_ridge_against_augmented_least_squares():
    rng = np.random.default_rng(8932)
    x1, x2 = rng.random((13, 11)), rng.random((7, 11))
    y1, y2 = rng.normal(size=(13, 4)), rng.normal(size=(7, 4))
    w1, w2 = rng.random(13) + .1, rng.random(7) + .1
    model = distill.fit_model([(x1, y1, w1), (x2, y2, w2)])
    weights = np.r_[w1 / w1.sum() / 2, w2 / w2.sum() / 2]
    raw = np.vstack([x1, x2])
    # Separate solver route: augmented least squares, not normal equations.
    basis = np.array([[1., *row, *(row[i] * row[j] for i in range(11)
                                  for j in range(i, 11))] for row in raw])
    regularizer = np.diag([0.] + [np.sqrt(.001)] * 77)
    lhs = np.vstack([np.sqrt(weights)[:, None] * basis, regularizer])
    rhs = np.vstack([np.sqrt(weights)[:, None] * np.vstack([y1, y2]),
                     np.zeros((78, 4))])
    expected = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
    np.testing.assert_allclose(model['coefficients'], expected, rtol=0, atol=1e-10)


def test_tied_predictions_keep_exact_capacity():
    for k in range(1, 7):
        labels = anchored_clusters(np.zeros((6, 4)), np.arange(1, 7), k)
        assert set(labels) == set(range(k))


def test_worker_and_case_order_without_teacher_information():
    spec = importlib.util.spec_from_file_location('review_distill',
                                                ROOT / 'tools/river_witness_distillation.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    events = []
    plan = {'output_directory': str(SCRATCH / 'never-created-order-output'),
            'cases': [{'id': 'synthetic'}], 'hands': 2}
    with patch.object(tool, 'read_plan', return_value=(b'', plan)), \
         patch.object(tool, 'fitted_record', side_effect=lambda _: events.append('fit') or
                      {'models': 'synthetic'}), \
         patch.object(tool.base, 'write_json',
                      side_effect=lambda path, value: events.append(path.name)), \
         patch.object(tool.old, 'equities_for',
                      side_effect=lambda *args: events.append('evaluation-equity')), \
         patch.object(tool.student, 'solve_record',
                      side_effect=lambda *args: events.append('case')), \
         patch.object(tool, 'verify_bindings'):
        tool.worker(Path('unused'), 'unused')
    assert events.index('fit') < events.index('models.json') < events.index('evaluation-equity')
    assert not (SCRATCH / 'never-created-order-output').exists()
    events = []
    with patch.object(pilot, 'build_inputs', return_value=('matrix', 'groups', 'inputs')), \
         patch.object(distill, 'propose', side_effect=lambda *args:
                      events.append('student-groups') or {'groups': 'student-groups'}), \
         patch.object(pilot, 'solve_record', side_effect=lambda *args:
                      events.append('teacher') or 'teacher'), \
         patch.object(distill, 'solve_groups', return_value='solution'), \
         patch.object(distill, 'student_record', return_value='student'):
        distill.solve_record({'id': 'synthetic'}, 2, {}, 'models')
    assert events == ['student-groups', 'teacher']


def test_retain_two_hand_smoke_and_time_boundary():
    spec = importlib.util.spec_from_file_location('review_smoke',
                                                ROOT / 'tools/river_witness_distillation.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    training = SCRATCH / 'independent-smoke-training'
    training.mkdir()
    output = SCRATCH / 'independent-smoke-output'
    producer = tool.old.make_plan(SCRATCH / 'unused-producer-output', smoke=True)
    case = producer['cases'][0]
    assert tuple(case['board']) == DEVELOPMENT_BOARDS[0] and producer['hands'] == 2
    equities = tool.old.equities_for(case, {})
    teacher = pilot.solve_record(case, 2, equities)
    tool.base.write_json(training / 'plan.json', producer)
    tool.base.write_json(training / (case['id'] + '.json'), teacher)
    plan = tool.make_plan(output, smoke=True, training=training)
    assert len(plan['training_cases']) == len(plan['cases']) == 1 and plan['hands'] == 2
    assert tuple(plan['cases'][0]['board']) == DEVELOPMENT_BOARDS[1]
    plan_path = SCRATCH / 'independent-smoke-plan.json'
    tool.base.write_json(plan_path, plan)
    start = perf_counter()
    result = tool.execute_plan(plan_path, tool.digest(plan_path))
    outer_seconds = perf_counter() - start
    receipt = tool.base.read(output / 'receipt.json')
    assert result['complete'] is True
    assert set(receipt) == {'exit', 'seconds'}
    assert outer_seconds > receipt['seconds']
    # Retain factual evidence instead of inventing a production timing field.
    evidence = dict(outer_measured_seconds=outer_seconds,
                    production_receipt_seconds=receipt['seconds'],
                    omitted_from_production_receipt_seconds=outer_seconds-receipt['seconds'],
                    production_receipt_keys=list(receipt),
                    production_summary_keys=list(result),
                    production_manifest_keys=list(tool.base.read(output / 'manifest.json')),
                    scope='one training case on old board 0 and one test case on old board 1; '
                          'two holdings per seat; reviewer outer measurement is scratch only')
    (SCRATCH / 'timing-boundary.json').write_text(json.dumps(evidence, indent=2) + '\n')
