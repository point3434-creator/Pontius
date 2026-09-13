"""Capture through the existing engine; retain public ranges and normalized games."""
from support import *
from collections import Counter
from hashlib import sha256
import json
import random

SEED = 2026091207
TARGET = 4
MAX_HANDS = 2000


class Policy(BlueprintPolicy):
    def __init__(self, assigner):
        super().__init__(str(BASELINE/'checkpoint'), assigner, threshold=.05, loader='full')
        self.statuses = Counter()
        assert self.config['num_players'] == 6 and self.config['stack'] == 200
        assert self.bucket_build_id == assigner.build_id

    def probabilities(self, game, *args, **kwargs):
        probabilities = super().probabilities(game, *args, **kwargs)
        _, status = self.probabilities_with_status(game, *args, **kwargs)
        self.statuses[f'{game.street}:{status}'] += 1
        return probabilities


def engine(policy):
    cfg = policy.config
    sizes, cap, late = cfg['menu']
    return NLHE(num_players=6, stack=cfg['stack'], sb=cfg['sb'], bb=cfg['bb'],
                menu=BetMenu(sizes, cap, late))


def capture(policy):
    game = engine(policy)
    rng, rows = random.Random(SEED), []
    counts = Counter()
    for index in range(MAX_HANDS):
        deck = rng.sample(range(52), 17)
        policy.rng = river_capture.hand_rng(SEED, index)
        game.reset(deck=deck)
        actions, hit = [], None
        start_seen = False
        while not game.is_over():
            if game.street == 3:
                counts['river_decisions'] += 1
                if game.history[-1] == '/':
                    start_seen = True
                    counts['river_start_nodes'] += 1
                if hit is None and river_capture.eligible(game):
                    hit = dict(hand_index=index, deck=deck, actions=list(actions),
                        seats=game.active_players(), current=game.current,
                        board=game.board, pot=game.pot, stacks=game.stacks[:],
                        committed=game.committed[:], history=game.history[:])
            action = policy.act(game)
            actions.append(action)
            game.step(action)
        counts['hands'] += 1
        counts['rivers_dealt'] += len(game.board) == 5
        counts['hands_with_river_start'] += start_seen
        assert sum(game.payoffs()) == 0
        if hit is not None:
            counts['eligible_hands'] += 1
            rows.append(hit)
        if len(rows) == TARGET:
            break
    return dict(complete=len(rows) == TARGET, rows=rows, census=dict(counts),
                policy_statuses=dict(policy.statuses), seed=SEED, max_hands=MAX_HANDS)


def reconstruct(policy, assigner, row):
    game, ranges = public_range.build_public_ranges(policy, assigner, engine(policy),
        row['deck'], row['actions'], row['seats'])
    assert river_capture.eligible(game) and game.board == row['board']
    assert game.current == row['current'] and game.pot == row['pot']
    assert game.stacks == row['stacks'] and game.committed == row['committed']
    assert game.history == row['history'] and game.active_players() == row['seats']
    cix = ComboIndex(game.board)
    order = [game.current, next(s for s in row['seats'] if s != game.current)]
    records = []
    ids = np.array([public_range.COMBO_ID[h] for h in cix.combos])
    for seat in order:
        effective, stats = ranges[seat].vector(cix, floor=1e-6)
        sensitivity, lower_stats = ranges[seat].vector(cix, floor=1e-9)
        records.append(dict(seat=seat, raw=ranges[seat].raw[ids].tolist(),
            effective=effective.tolist(), stats=stats, lower_floor_stats=lower_stats,
            provenance=ranges[seat].provenance(cix),
            lower_floor_l1=float(np.abs(effective-sensitivity).sum())))
    return dict(board=game.board, hands=[list(h) for h in cix.combos], ranges=records,
                role_seats=order, actual_state=row)


def build(record):
    board = record['board']
    hands = tuple(map(tuple, record['hands']))
    assert len(hands) == 1081 and hands == tuple(ComboIndex(board).combos)
    weights = [np.asarray(v['effective']) for v in record['ranges']]
    assert all(np.isfinite(w).all() and (w > 0).all() for w in weights)
    h = np.asarray(hands)
    compatible = ((h[:, None, 0] != h[None, :, 0]) &
                  (h[:, None, 0] != h[None, :, 1]) &
                  (h[:, None, 1] != h[None, :, 0]) &
                  (h[:, None, 1] != h[None, :, 1]))
    assert np.all(compatible.sum(axis=1) == 990)
    joint = np.outer(*weights)*compatible
    joint /= joint.sum()
    ranks = np.array([evaluator.hand_rank(list(h)+board) for h in hands])
    sign = np.sign(ranks[:, None]-ranks[None, :])
    provenance = sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    matrix = c.PayoffGame(joint, joint*sign*5, joint*5, joint*sign*10,
                         (hands, hands), provenance)
    equities = {hand: float(((sign[i] > 0)*compatible[i]).sum()+
                    .5*((sign[i] == 0)*compatible[i]).sum())/990
                for i, hand in enumerate(hands)}
    features = [c.design(c.raw_features(matrix, equities, seat)) for seat in (0, 1)]
    models = c.read(c.MODEL)['models']
    predicted = [np.column_stack([np.full(len(x), head['constant'])
        if head['constant'] is not None else c.expit(x @ np.asarray(head['coefficients']))
        for head in model]) for x, model in zip(features, models)]
    groups = [c.anchored_clusters(p, joint.sum(axis=1-seat), 16).tolist()
              for seat, p in enumerate(predicted)]
    game = m.Game(matrix.check, [matrix.fold, matrix.fold],
                  [matrix.call, joint*sign*15])
    hashes = {name: sha256(np.ascontiguousarray(value).tobytes()).hexdigest()
              for name, value in [('joint', joint), ('check', game.check),
                                  ('fold', game.fold), ('call', game.call)]}
    return game, groups, dict(matrix_hashes=hashes, source_digest=provenance,
        groups=groups, features=[x.tolist() for x in features],
        predictions=[p.tolist() for p in predicted], compatible_deals=int(compatible.sum()))
