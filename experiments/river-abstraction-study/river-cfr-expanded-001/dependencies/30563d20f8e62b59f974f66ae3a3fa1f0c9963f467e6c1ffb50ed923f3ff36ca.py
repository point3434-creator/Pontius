"""One fixed-capacity split/merge using one retained opponent witness per seat."""
from fractions import Fraction as Q
from itertools import combinations
from environment import np, opt, core


def deltas(matrix, opponent, seat):
    """Own utility of action 1 minus action 0, weighted by original joint mass."""
    opt.require(type(seat) is int and seat in (0, 1), 'invalid seat')
    n, m = matrix.joint.shape
    exact = (np.arange(n), np.arange(m))
    opt.validate(matrix, exact)
    witness = opt.policy(opponent, exact[1-seat])
    result = [Q(0)]*(n if seat == 0 else m)
    for i in range(n):
        for j in range(m):
            c, f, a = [Q(float(t[i, j])) for t in
                       (matrix.check, matrix.fold, matrix.call)]
            if seat == 0:
                result[i] += (1-witness[j])*f+witness[j]*a-c
            else:
                result[j] += witness[i]*(f-a)
    return result


def exchange(groups, changes):
    labels = opt._labels(groups, len(changes)).tolist()
    opt.require(all(type(d) is Q for d in changes), 'exact rational changes required')
    k = max(labels)+1
    total = [sum((d for d, g in zip(changes, labels) if g == s), Q(0)) for s in range(k)]
    gains = []
    for s in range(k):
        values = [d for d, g in zip(changes, labels) if g == s]
        positive = sum((d for d in values if d > 0), Q(0))
        negative = -sum((d for d in values if d < 0), Q(0))
        gains.append(min(positive, negative))
    best, chosen, examined = Q(0), None, 0
    for split in range(k):
        if gains[split] <= 0:
            continue
        for a, b in combinations([s for s in range(k) if s != split], 2):
            cost = max(Q(0), total[a])+max(Q(0), total[b])-max(Q(0), total[a]+total[b])
            net = gains[split]-cost
            examined += 1
            # Iteration order resolves exact ties by (split, a, b), smallest first.
            if net > best:
                best, chosen = net, (split, a, b, cost)
    result = labels.copy()
    split_gain, merge_cost = Q(0), Q(0)
    operation = None
    if chosen is not None:
        split, a, b, merge_cost = chosen
        result = [k if g == split and changes[i] <= 0 else a if g == b else g
                  for i, g in enumerate(labels)]
        mapping = {value: index for index, value in enumerate(sorted(set(result)))}
        result = [mapping[g] for g in result]
        split_gain = gains[split]
        operation = dict(split=split, merge=[a, b])
    opt.require(len(set(result)) == k, 'group budget changed')
    old_value = sum((max(Q(0), v) for v in total), Q(0))
    new_value = sum((max(Q(0), sum((d for d, g in zip(changes, result) if g == s), Q(0)))
                     for s in range(k)), Q(0))
    opt.require(new_value-old_value == best, 'witness objective mismatch')
    return dict(groups=result, changed=chosen is not None, operation=operation,
                split_gain_exact=str(split_gain), merge_cost_exact=str(merge_cost),
                net_witness_gain_exact=str(best), examined_exchanges=examined)


def propose(matrix, groups, baseline):
    groups = opt.validate(matrix, groups)
    weights = [np.eye(max(g)+1)[g] for g in groups]
    core.verify(matrix, weights, baseline)
    seats = []
    for seat in (0, 1):
        opponent = baseline[f'seat{seat}']['coefficients'][1-seat]
        changes = deltas(matrix, opponent, seat)
        seats.append(dict(**exchange(groups[seat], changes),
                          weighted_advantages_exact=list(map(str, changes))))
    return dict(groups=[s['groups'] for s in seats], seats=seats)
