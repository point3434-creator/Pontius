"""Thin payoff/menu adapter over the retained transfer pilot; no new repair rule."""
from pathlib import Path
import sys
import importlib.util
from fractions import Fraction as Q
from hashlib import sha256

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PRIOR = HISTORY/'blueprint-range-transfer-001'
sys.path.insert(0, str(PRIOR/'verification-tools'))
spec = importlib.util.spec_from_file_location('frozen_transfer',
    PRIOR/'verification-tools/experiment.py')
e = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = e
spec.loader.exec_module(e)
np, m, r, c = e.np, e.m, e.r, e.c
read, write, digest = e.read, e.write, e.digest
original_build = e.inputs.build


def state(record):
    cfg = read(e.BASELINE/'checkpoint/meta.json')['config']
    from types import SimpleNamespace
    game = e.inputs.engine(SimpleNamespace(config=cfg))
    old = record['actual_state']
    game.reset(deck=old['deck'])
    for action in old['actions']:
        assert action in game.legal_actions()
        game.step(action)
    for name in ('pot', 'stacks', 'committed', 'board', 'current', 'history'):
        assert getattr(game, name) == old[name], name
    assert e.river_capture.eligible(game)
    assert game.active_players() == old['seats']
    assert game.current == record['role_seats'][0]
    assert all(v == 0 for v in game.street_commit)
    return game


def admission(record):
    game = state(record)
    hero, villain = record['role_seats']
    assert game.stacks[hero] == game.stacks[villain] > 0
    assert game.committed[hero] == game.committed[villain]
    sizes, ids = [], []
    for fraction in (.5, 1.):
        target = game._raise_to(hero, fraction)
        action = (2+list(game.menu.sizes(3, 0)).index(fraction)
                  if target < game.stacks[hero] else game.all_in_action_id())
        assert action in game.legal_actions()
        child = game.clone()
        child.step(action)
        sizes.append(game.stacks[hero]-child.stacks[hero])
        ids.append(action)
    return dict(pot=game.pot, effective_stack=game.stacks[hero],
        spr=game.stacks[hero]/game.pot, sizes=sizes, action_ids=ids,
        legal_actions=game.legal_actions(), distinct_sizes=sorted(set(sizes)),
        applicable=len(set(sizes)) == 2,
        reason='two distinct sizes' if len(set(sizes)) == 2 else 'one distinct all-in size')


def population(record):
    hands = np.array(record['hands'])
    assert len(hands) == 1081
    compatible = ((hands[:, None, 0] != hands[None, :, 0]) &
                  (hands[:, None, 0] != hands[None, :, 1]) &
                  (hands[:, None, 1] != hands[None, :, 0]) &
                  (hands[:, None, 1] != hands[None, :, 1]))
    joint = np.outer(*[v['effective'] for v in record['ranges']])*compatible
    joint /= joint.sum()
    ranks = np.array([e.evaluator.hand_rank(list(h)+record['board']) for h in hands])
    signs = np.sign(ranks[:, None]-ranks[None, :])
    return hands, joint, signs, compatible


def build(record):
    meta = admission(record)
    if not meta['applicable']:
        raise ValueError('one distinct all-in size: frozen size repair is not applicable')
    _, groups, old = original_build(record)
    hands, joint, signs, compatible = population(record)
    hero, villain = record['role_seats']
    pot, sizes = meta['pot'], meta['sizes']
    tie = (pot % 2)*(.5 if hero < villain else -.5)
    scale = 10/pot
    check = joint*(signs*(pot/2)+(signs == 0)*tie)*scale
    fold = joint*(pot/2)*scale
    calls = [joint*(signs*(pot/2+b)+(signs == 0)*tie)*scale for b in sizes]
    game = m.Game(check, [fold, fold], calls)
    joint_hash = sha256(np.ascontiguousarray(joint).tobytes()).hexdigest()
    assert joint_hash == old['matrix_hashes']['joint']
    details = dict(menu=meta, normalization='10/pot', tie_centered_chips=tie,
        joint_sha256=joint_hash, groups=groups, prior_inputs=old,
        payoff_hashes={k: sha256(np.ascontiguousarray(v).tobytes()).hexdigest()
                      for k, v in [('check', check), ('fold', game.fold), ('call', game.call)]})
    return game, groups, details


def engine_audit(record):
    game = state(record)
    meta = admission(record)
    hands, joint, signs, compatible = population(record)
    hero, villain = record['role_seats']
    tie = Q(meta['pot'] % 2, 2)*(1 if hero < villain else -1)
    evidence = []
    for sign in (-1, 0, 1):
        spots = np.argwhere(compatible & (signs == sign))
        assert len(spots) > 0, 'audit requires an explicit win, tie and loss'
        a, b = map(int, spots[0])
        for kind, size_index in [('check', 0), ('fold', 0), ('call', 0),
                                 ('fold', 1), ('call', 1)]:
            child = game.clone()
            child.holes = [list(h) for h in game.holes]
            child.holes[hero], child.holes[villain] = hands[a].tolist(), hands[b].tolist()
            used = set(record['board']) | set(hands[a]) | set(hands[b])
            spare = iter(v for v in range(52) if v not in used)
            for seat in range(6):
                if seat not in (hero, villain):
                    child.holes[seat] = [next(spare), next(spare)]
            if kind == 'check':
                child.step(1)
                child.step(1)
                expected = sign*Q(game.pot, 2) if sign else tie
            else:
                child.step(meta['action_ids'][size_index])
                child.step(0 if kind == 'fold' else 1)
                expected = (Q(game.pot, 2) if kind == 'fold' else
                    sign*(Q(game.pot, 2)+meta['sizes'][size_index]) if sign else tie)
            assert child.is_over() and sum(child.payoffs()) == 0
            centered = Q(child.payoffs()[hero]+game.committed[hero])-Q(game.pot, 2)
            assert centered == expected, (centered, expected)
            evidence.append(dict(sign=sign, kind=kind, size=meta['sizes'][size_index],
                hero_hand=hands[a].tolist(), villain_hand=hands[b].tolist(),
                centered_chips=str(centered)))
    return dict(checks=len(evidence), outcomes=[-1, 0, 1],
                tie_centered_chips=float(tie), records=evidence)
