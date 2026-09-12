"""Two independent constrained regret learners against unrestricted best responses.

One-bet specialization of the CFR-BR principle, with full enumeration and no
sampling. Pair the learners' average policies for full-hand profile evaluation.
"""
from context import np,opt,_regret_match


class RegretBR:
    def __init__(self,matrix,groups):
        self.groups=opt.validate(matrix,groups)
        self.regrets=[np.zeros((len(set(g)),2)) for g in self.groups]
        self.sums=[np.zeros_like(r) for r in self.regrets]
        self.iteration=0
        n0,n1=matrix.joint.shape
        self.games=(matrix.aggregate((self.groups[0],np.arange(n1))),
                    matrix.aggregate((np.arange(n0),self.groups[1])))
        self.check=[g.check.sum(axis=1) for g in self.games]
        self.fold=[g.fold.sum(axis=1) for g in self.games]
        self.difference=[g.call-g.fold for g in self.games]

    def current(self):
        return tuple(_regret_match(r)[:,1] for r in self.regrets)

    def step(self):
        s0,s1=(_regret_match(r) for r in self.regrets)
        first,second=self.games
        # Opponent actions are independent across their exact private hands.
        f,a=s0[:,1] @ first.fold,s0[:,1] @ first.call
        y=np.where(a<f,1.,np.where(a>f,0.,.5))
        betting=self.fold[1]+self.difference[1] @ s1[:,1]
        x=np.where(betting>self.check[1],1.,np.where(betting<self.check[1],0.,.5))
        values=(np.column_stack((self.check[0],self.fold[0]+self.difference[0] @ y)),
                np.column_stack((-x @ second.fold,-x @ second.call)))
        for seat,strategy in enumerate((s0,s1)):
            self.sums[seat]+=strategy
            self.regrets[seat]+=values[seat]-(strategy*values[seat]).sum(axis=1,keepdims=True)
        self.iteration+=1

    def average(self):
        if not self.iteration:raise ValueError('empty average')
        return tuple(s[:,1]/self.iteration for s in self.sums)
