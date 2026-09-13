"""Fixed quadratic ridge distillation of four strategic hand features per seat."""
from __future__ import annotations

from fractions import Fraction as Q
from hashlib import sha256
from time import perf_counter

import numpy as np

from .river_abstraction_study import (DEVELOPMENT_BOARDS, HOLDOUT_BOARDS,
                                      anchored_clusters, range_features)
from .river_group_optimality import require, solve_groups, verify_solution
from .river_witness_groups import difference
from . import river_witness_pilot as pilot

SEED = 'river-witness-distillation-001'
ALPHA = .001
FEATURES = [f'{band}_{field}' for band in ('low','middle','high')
            for field in ('mass','win','tie')]+['range_equity','uniform_equity']
TIMINGS = ('game_and_control_preparation','prediction_and_clustering',
           'oracle_rebuild_and_solve','student_solve_and_verification')


def select_boards():
    excluded = {pilot.canonical_board(b) for b in (
        *DEVELOPMENT_BOARDS,*HOLDOUT_BOARDS,*pilot.select_boards())}
    selected = {name:[] for name in pilot.TEXTURES}
    for attempt in range(10000):
        def order(card):
            return sha256(f'{SEED}|board|{attempt}|{card}'.encode()).digest(),card
        board = tuple(sorted(sorted(range(52),key=order)[:5]))
        key,name = pilot.canonical_board(board),pilot.texture(board)
        if key not in excluded and len(selected[name]) < 2:
            selected[name].append(board)
            excluded.add(key)
        if all(len(rows) == 2 for rows in selected.values()):
            return tuple(b for name in pilot.TEXTURES for b in selected[name])
    raise ValueError('reserved board selection exhausted')


def raw_features(matrix, equities, player):
    response,equity = range_features(matrix,equities,player)
    uniform = [equities[h] for h in matrix.hands[player]]
    return np.column_stack((response,equity,uniform))


def design(raw):
    x = np.asarray(raw,dtype=float)
    require(x.ndim == 2 and x.shape[1] == 11 and len(x) > 0 and
            np.isfinite(x).all() and (x >= -1e-12).all() and (x <= 1+1e-12).all(),
            'eleven finite probability features required')
    return np.column_stack([np.ones(len(x)),x,*[x[:,i]*x[:,j]
                                               for i in range(11) for j in range(i,11)]])


def fit_model(samples):
    require(len(samples) > 0, 'training cases required')
    designs,targets,weights = [],[],[]
    for x,y,w in samples:
        d = design(x)
        y,w = np.asarray(y,dtype=float),np.asarray(w,dtype=float)
        require(y.shape == (len(d),4) and np.isfinite(y).all() and
                w.shape == (len(d),) and np.isfinite(w).all() and (w > 0).all(),
                'invalid training targets or weights')
        designs.append(d)
        targets.append(y)
        weights.append(w/w.sum()/len(samples))
    d,y,w = np.vstack(designs),np.vstack(targets),np.concatenate(weights)
    penalty = np.diag([0.]+[ALPHA]*77)
    coefficients = np.linalg.solve(d.T@(w[:,None]*d)+penalty,d.T@(w[:,None]*y))
    require(np.isfinite(coefficients).all(), 'nonfinite fitted coefficients')
    return dict(schema='quadratic-ridge-witness-v1',alpha=ALPHA,features=FEATURES,
                coefficients=coefficients.tolist())


def predict(model, raw):
    require(type(model) is dict and set(model) == {'schema','alpha','features','coefficients'}
            and model['schema'] == 'quadratic-ridge-witness-v1' and
            type(model['alpha']) is float and model['alpha'] == ALPHA and
            model['features'] == FEATURES, 'model recipe changed')
    b = np.asarray(model['coefficients'],dtype=float)
    require(b.shape == (78,4) and np.isfinite(b).all(), 'invalid coefficients')
    prediction = design(raw)@b
    require(np.isfinite(prediction).all(), 'nonfinite prediction')
    return prediction


def fit_models(training):
    """Caller verifies retained training rows before supplying these triples."""
    return [fit_model([(raw_features(matrix,equities,p),
                       row['candidate']['proposal']['features'][p],
                       matrix.joint.sum(axis=1-p)) for matrix,equities,row in training])
            for p in (0,1)]


def propose(matrix, groups, equities, models):
    require(type(models) is list and len(models) == 2, 'one model per seat required')
    features,labels = [],[]
    for p in (0,1):
        f = predict(models[p],raw_features(matrix,equities,p))
        k = len(set(groups['uniform_equity_200'][p]))
        labels.append(anchored_clusters(f,matrix.joint.sum(axis=1-p),k).tolist())
        features.append(f.tolist())
    return dict(method='predicted_witness',features=features,groups=labels)


def student_record(matrix, groups, equities, models, teacher, solution):
    proposal = propose(matrix,groups,equities,models)
    floor = verify_solution(matrix,proposal['groups'],solution)
    comparisons = {r['method']:difference(floor,r['solution']['minimum_exploitability'])
                   for r in teacher['bank']['methods']}
    comparisons['oracle_witness'] = difference(
        floor,teacher['candidate']['solution']['minimum_exploitability'])
    errors = []
    for p in (0,1):
        delta = np.asarray(proposal['features'][p])-teacher['candidate']['proposal']['features'][p]
        w = matrix.joint.sum(axis=1-p)
        errors.append(dict(mse_by_column=(w@np.square(delta)).tolist(),
                           max_absolute_by_column=np.abs(delta).max(axis=0).tolist()))
    return dict(proposal=proposal,solution=solution,comparisons=comparisons,
                prediction_error=errors)


def solve_record(case, count, equities, models):
    started = perf_counter()
    matrix,groups,_ = pilot.build_inputs(case,count,equities)
    prepared = perf_counter()
    proposal = propose(matrix,groups,equities,models)
    predicted = perf_counter()
    # No test-case witness or target enters the prediction above.
    teacher = pilot.solve_record(case,count,equities)
    taught = perf_counter()
    student = student_record(matrix,groups,equities,models,teacher,
                             solve_groups(matrix,proposal['groups']))
    ended = perf_counter()
    return dict(case=case,teacher=teacher,student=student,
                seconds=dict(zip(TIMINGS,(prepared-started,predicted-prepared,
                                         taught-predicted,ended-taught),strict=True)))


def verify_record(case, count, equities, models, row):
    require(type(row) is dict and set(row) == {'case','teacher','student','seconds'} and
            pilot.canonical_json(row['case']) == pilot.canonical_json(case), 'case mismatch')
    require(set(row['seconds']) == set(TIMINGS) and all(type(v) in (int,float) and
            np.isfinite(v) and v >= 0 for v in row['seconds'].values()), 'invalid timing record')
    pilot.verify_record(case,count,equities,row['teacher'])
    matrix,groups,_ = pilot.build_inputs(case,count,equities)
    expected = student_record(matrix,groups,equities,models,row['teacher'],
                              row['student']['solution'])
    require(pilot.canonical_json(expected) == pilot.canonical_json(row['student']),
            'student reconstruction mismatch')
    return row


def rename_student(value):
    if isinstance(value,dict):
        return {('predicted_witness' if k == 'witness_advantage' else k):rename_student(v)
                for k,v in value.items()}
    if isinstance(value,list):
        return [rename_student(v) for v in value]
    return value


def summarize(cases, rows):
    require(pilot.canonical_json([r['case'] for r in rows]) == pilot.canonical_json(cases),
            'missing or reordered cases')
    oracle = pilot.summarize(cases,[r['teacher'] for r in rows])
    projected = [dict(case=r['case'],inputs=r['teacher']['inputs'],bank=r['teacher']['bank'],
                      candidate=r['student']) for r in rows]
    student = rename_student(pilot.summarize(cases,projected))
    student['lp_calls_planned'] = 2*len(rows)
    student['interpretation'] = 'Predicted features from frozen training-only ridge models; '
    student['interpretation'] += 'board/pool summaries are descriptive, not confidence intervals.'
    comparisons = [r['student']['comparisons']['oracle_witness'] for r in rows]
    return dict(complete=True,case_count=len(rows),board_units=student['board_units'],
        lp_calls_planned=12*len(rows),student=student,oracle=oracle,
        oracle_gap=dict(**pilot.mean_interval(comparisons),case_counts={
            label:sum(c['classification'] == label for c in comparisons)
            for label in ('lower','higher','overlapping')},
            by_board=[dict(board_index=b,**pilot.mean_interval([
                r['student']['comparisons']['oracle_witness'] for r in rows
                if r['case']['board_index'] == b])) for b in sorted(
                    {c['board_index'] for c in cases})]),
        prediction_errors=[dict(case=r['case']['id'],seats=r['student']['prediction_error'])
                           for r in rows],
        seconds={k:sum(r['seconds'][k] for r in rows) for k in TIMINGS},
        meaning='Primary endpoint is predicted-group floor minus range_equity floor; '
        'oracle gap and prediction errors are secondary. No tuning, winner selection, '
        'population confidence or six-max strength claim. A negative oracle gap is possible '
        'because neither clustering procedure globally optimizes partitions.',
        nonimprovement_cases=[r['case']['id'] for r in rows if
            Q(r['student']['comparisons']['range_equity']['upper_exact']) >= 0])
