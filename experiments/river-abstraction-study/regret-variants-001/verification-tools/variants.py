"""Regret-update comparison; unchanged full-hand best-response payoff schedule."""
from load_frozen import m

np = m.np
MODES = ('rm', 'rm_plus', 'discounted')


def update(regret, instantaneous, t, mode):
    if mode not in MODES:
        raise ValueError(mode)
    assert type(t) is int and t >= 1
    result = regret + instantaneous
    if mode == 'rm_plus':
        return np.maximum(result, 0)
    if mode == 'discounted':
        positive = t**1.5
        return result * np.where(result > 0, positive/(positive+1), .5)
    return result


class Trainer(m.Trainer):
    def __init__(self, game, groups, mode):
        if mode not in MODES:
            raise ValueError(mode)
        super().__init__(game, groups)
        self.mode = mode
        self.weight = 0.

    def step(self):
        x, y = [m.match(r) for r in self.regrets]
        first, second = self.games
        b = len(first.fold)
        bettor = [first.check.sum(axis=1)]
        for s in range(b):
            f, a = x[:, s+1] @ first.fold[s], x[:, s+1] @ first.call[s]
            response = np.where(a < f, 1., np.where(a > f, 0., .5))
            bettor.append(first.fold[s].sum(axis=1)+(first.call[s]-first.fold[s]) @ response)
        options = np.column_stack([second.check.sum(axis=1)]+[
            second.fold[s].sum(axis=1)+(second.call[s]-second.fold[s]) @ y[s, :, 1]
            for s in range(b)])
        best = options == options.max(axis=1, keepdims=True)
        response = best/best.sum(axis=1, keepdims=True)
        caller = np.array([np.column_stack((-response[:, s+1] @ second.fold[s],
                                            -response[:, s+1] @ second.call[s])) for s in range(b)])
        t = self.iteration+1
        weight = 1. if self.mode == 'rm' else float(t*t)
        for seat, (strategy, value) in enumerate(((x, np.column_stack(bettor)), (y, caller))):
            self.sums[seat] += weight*strategy
            self.regrets[seat] = update(self.regrets[seat],
                value-(strategy*value).sum(axis=-1, keepdims=True), t, self.mode)
        self.weight += weight
        self.iteration = t

    def average(self):
        assert self.iteration > 0
        return ((self.sums[0]/self.weight).tolist(),
                (self.sums[1][:, :, 1]/self.weight).tolist())
