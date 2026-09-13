"""Research-only alternating full-tree CFR over chance-weighted payoff products."""
import numpy as np


def normalize(values):
    total = values.sum(axis=1, keepdims=True)
    return np.divide(values, total, out=np.full_like(values, 1 / values.shape[1]),
                     where=total > 0)


def update(old, regret, iteration, alpha, denominator, predict):
    def discount(t):
        return 1. if alpha is None else t**alpha / (t**alpha + denominator)
    cumulative = np.maximum(old * discount(iteration - 1) + regret, 0.)
    decision = (np.maximum(cumulative * discount(iteration) + regret, 0.)
                if predict else cumulative)
    return cumulative, normalize(decision)


class Solver:
    def __init__(self, nodes, arrays, config):
        self.nodes, self.arrays, self.config = nodes, arrays, config
        self.n = next(iter(arrays.values())).shape[0]
        assert all(a.shape == (self.n, self.n) for a in arrays.values())
        self.policy = {i: np.full((self.n, len(v['children'])), 1/len(v['children']))
                       for i, v in enumerate(nodes) if v['player'] != -1}
        self.regret = {i: np.zeros_like(v) for i, v in self.policy.items()}
        self.accumulator = {i: np.zeros_like(v) for i, v in self.policy.items()}
        self.iteration = 0

    def reaches(self, policy, role):
        reach = [None] * len(self.nodes)
        reach[0] = np.ones(self.n)
        for i, node in enumerate(self.nodes):
            for a, child in enumerate(node.get('children', [])):
                reach[child] = (reach[i]*policy[i][:, a]
                                if node['player'] == role else reach[i])
        return reach

    def values_for(self, role, policy, best=False):
        other = self.reaches(policy, 1-role)
        values, regrets = {}, {}
        for i in reversed(range(len(self.nodes))):
            node = self.nodes[i]
            if node['player'] == -1:
                a = self.arrays[tuple(node['payoff'])]
                values[i] = a @ other[i] if role == 0 else -(other[i] @ a)
            else:
                children = np.stack([values[c] for c in node['children']], axis=1)
                if node['player'] == role:
                    current = np.sum(children*policy[i], axis=1)
                    regrets[i] = children-current[:, None]
                    values[i] = children.max(axis=1) if best else current
                else:
                    values[i] = children.sum(axis=1)
        return values[0], regrets

    def regrets_for(self, role):
        return self.values_for(role, self.policy)[1]

    def step(self):
        self.iteration += 1
        t, c = self.iteration, self.config
        for role in (0, 1):
            regrets = self.regrets_for(role)
            own = self.reaches(self.policy, role)
            for i, regret in regrets.items():
                self.accumulator[i] *= ((t-1)/t)**c['gamma']
                self.accumulator[i] += own[i][:, None]*self.policy[i]
                self.regret[i], self.policy[i] = update(
                    self.regret[i], regret, t, c['alpha'], c['denominator'], c['predict'])

    def average(self):
        return {i: normalize(v) for i, v in self.accumulator.items()}

    def score(self, policy):
        value = float(self.values_for(0, policy)[0].sum())
        high = float(self.values_for(0, policy, best=True)[0].sum())
        low = -float(self.values_for(1, policy, best=True)[0].sum())
        assert low-1e-11 <= value <= high+1e-11
        return dict(value=value, lower=low, upper=high, gap=high-low,
                    exploitability=(high-low)/2)
