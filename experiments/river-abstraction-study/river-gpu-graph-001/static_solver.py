"""Fixed-horizon research DCFR+: stable buffers, one alternating iteration per replay."""
import cupy as cp
from blas import Blas

NORMALIZE=cp.ElementwiseKernel('float64 v, float64 total, float64 uniform',
    'float64 out', 'out = total > 0.0 ? v / total : uniform;', 'graph_normalize')
DISCOUNTS=cp.ElementwiseKernel('raw float64 ds, raw float64 ws, int64 t',
    'float64 d, float64 w', 'd=ds[t]; w=ws[t];', 'graph_discounts')


class StaticSolver:
    def __init__(self,nodes,arrays,horizon=2048):
        self.nodes,self.arrays,self.horizon=nodes,arrays,horizon
        self.n=next(iter(arrays.values())).shape[0]
        assert horizon>0 and all(a.dtype==cp.float64 for a in arrays.values())
        cp.cuda.Stream.null.synchronize()
        self.stream=cp.cuda.Stream(non_blocking=True)
        self.blas=Blas(self.stream)
        self.graph=None
        with self.stream:
            self.policy={i:cp.empty((self.n,len(n['children'])),dtype=cp.float64)
                         for i,n in enumerate(nodes) if n['player']!=-1}
            self.regret={i:cp.empty_like(a) for i,a in self.policy.items()}
            self.accumulator={i:cp.empty_like(a) for i,a in self.policy.items()}
            self.children={i:cp.empty_like(a) for i,a in self.policy.items()}
            self.scratch={i:cp.empty_like(a) for i,a in self.policy.items()}
            self.instant={i:cp.empty_like(a) for i,a in self.policy.items()}
            self.total={i:cp.empty((self.n,1),dtype=cp.float64) for i in self.policy}
            self.values=[cp.empty(self.n,dtype=cp.float64) for _ in nodes]
            self.reach=[cp.empty(self.n,dtype=cp.float64) for _ in nodes]
            self.counter=cp.zeros((),dtype=cp.int64)
            self.d,self.w=cp.empty((),dtype=cp.float64),cp.empty((),dtype=cp.float64)
            self.discounts=cp.asarray([t**1.5/(t**1.5+1.5) for t in range(horizon)])
            self.weights=cp.asarray([(t/(t+1))**4 for t in range(horizon)])
            self.reset()
        self.stream.synchronize()

    def reset(self):
        self.iteration=0
        self.counter.fill(0)
        for i,a in self.policy.items():
            a.fill(1/a.shape[1])
            self.regret[i].fill(0)
            self.accumulator[i].fill(0)

    def reaches(self,role):
        self.reach[0].fill(1)
        for i,n in enumerate(self.nodes):
            for action,child in enumerate(n.get('children',[])):
                if n['player']==role:
                    cp.multiply(self.reach[i],self.policy[i][:,action],out=self.reach[child])
                else:
                    cp.copyto(self.reach[child],self.reach[i])

    def operations(self):
        DISCOUNTS(self.discounts,self.weights,self.counter,self.d,self.w)
        for role in (0,1):
            self.reaches(1-role)
            for i in reversed(range(len(self.nodes))):
                n=self.nodes[i]
                if n['player']==-1:
                    a=self.arrays[tuple(n['payoff'])]
                    if role==0:
                        self.blas.product(a,self.reach[i],self.values[i],True)
                    else:
                        self.blas.product(a,self.reach[i],self.values[i],False)
                        cp.negative(self.values[i],out=self.values[i])
                else:
                    child=self.children[i]
                    for action,c in enumerate(n['children']):
                        cp.copyto(child[:,action],self.values[c])
                    if n['player']==role:
                        cp.multiply(child,self.policy[i],out=self.scratch[i])
                        cp.sum(self.scratch[i],axis=1,out=self.values[i])
                        cp.subtract(child,self.values[i][:,None],out=self.instant[i])
                    else:
                        cp.sum(child,axis=1,out=self.values[i])
            self.reaches(role)
            for i in self.policy:
                if self.nodes[i]['player']!=role: continue
                cp.multiply(self.accumulator[i],self.w,out=self.accumulator[i])
                cp.multiply(self.reach[i][:,None],self.policy[i],out=self.scratch[i])
                cp.add(self.accumulator[i],self.scratch[i],out=self.accumulator[i])
                cp.multiply(self.regret[i],self.d,out=self.regret[i])
                cp.add(self.regret[i],self.instant[i],out=self.regret[i])
                cp.maximum(self.regret[i],0.,out=self.regret[i])
                cp.sum(self.regret[i],axis=1,keepdims=True,out=self.total[i])
                NORMALIZE(self.regret[i],self.total[i],1/self.policy[i].shape[1],self.policy[i])
        cp.add(self.counter,1,out=self.counter)

    def step(self,replay=False):
        if self.iteration>=self.horizon: raise ValueError('fixed horizon exhausted')
        if replay:
            if self.graph is None: raise ValueError('graph not captured')
            self.graph.launch(stream=self.stream)
        else:
            self.operations()
        self.iteration+=1

    def capture(self):
        self.stream.synchronize()
        with self.stream:
            self.stream.begin_capture()
            self.operations()
            self.graph=self.stream.end_capture()

    def average(self):
        self.stream.synchronize()
        result={}
        for i,a in self.accumulator.items():
            total=a.sum(axis=1,keepdims=True)
            result[i]=NORMALIZE(a,total,1/a.shape[1])
        return result

    def close(self):
        self.stream.synchronize()
        self.graph=None
        self.blas.close()
