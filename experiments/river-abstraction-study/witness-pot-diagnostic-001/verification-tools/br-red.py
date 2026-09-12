"""RED scaffold: records uniform strategies without regret updates."""
from context import np,opt,_regret_match


class RegretBR:
    def __init__(self,matrix,groups):
        self.groups=opt.validate(matrix,groups)
        self.regrets=[np.zeros((len(set(g)),2)) for g in self.groups]
        self.sums=[np.zeros_like(r) for r in self.regrets]
        self.iteration=0

    def current(self):
        return tuple(_regret_match(r)[:,1] for r in self.regrets)

    def step(self):
        for seat in (0,1):self.sums[seat]+=_regret_match(self.regrets[seat])
        self.iteration+=1

    def average(self):
        if not self.iteration:raise ValueError('empty average')
        return tuple(s[:,1]/self.iteration for s in self.sums)
