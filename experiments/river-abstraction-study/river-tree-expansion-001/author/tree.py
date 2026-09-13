"""Finite public river tree, sparse realization-plan LP, and exact response checks."""
from pathlib import Path
import importlib.util
import sys
from fractions import Fraction as Q
from time import perf_counter
import gc
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
OLD=ROOT/'experiments/river-abstraction-study/full-combo-direct-002'
spec=importlib.util.spec_from_file_location('expanded_direct',OLD/'verification-tools/direct.py')
d=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=d
spec.loader.exec_module(d)
VARIANTS=('baseline','checkback','raise')
GRID=2**48
SCALE=2**20


def public_tree(record,variant):
    assert variant in VARIANTS
    root=d.b.state(record)
    hero,villain=record['role_seats']
    seats=(hero,villain)
    initial=root.street_commit.copy()
    nodes=[]
    def visit(game,path):
        index=len(nodes)
        node=dict(path=path,children=[])
        nodes.append(node)
        if game.is_over():
            live=game.active_players()
            contribution=[game.street_commit[p]-initial[p] for p in seats]
            if len(live)==1:
                winner=seats.index(live[0])
                payoff=['fold',winner,contribution[1-winner]]
            else:
                assert contribution[0]==contribution[1]
                payoff=['showdown',0,contribution[0]]
            node.update(player=-1,payoff=payoff)
            return index
        node['player']=seats.index(game.current)
        if game.to_call(game.current):
            actions=[0,1]
            if variant=='raise' and game.raises_this_street==1:
                action=game.all_in_action_id()
                if action in game.legal_actions(): actions.append(action)
        else:
            actions=[1]
            if path!=[1] or variant!='baseline':
                seen=set()
                for fraction in (.5,1.):
                    target=min(game._raise_to(game.current,fraction),
                               game.street_commit[game.current]+game.stacks[game.current])
                    action=(game.all_in_action_id() if target==game.street_commit[game.current]+game.stacks[game.current]
                        else 2+list(game.menu.sizes(3,game.raises_this_street)).index(fraction))
                    if target not in seen:
                        actions.append(action)
                        seen.add(target)
        # Once two players check the engine settles; every action here is engine-admitted.
        node['actions']=actions
        for action in actions:
            assert action in game.legal_actions()
            child=game.clone()
            child.step(action)
            node['children'].append(visit(child,path+[action]))
        return index
    visit(root,[])
    return nodes


def terminal_chips(key,pot,sign,tie):
    kind,winner,amount=key
    return ((Q(pot,2)+amount)*(1 if winner==0 else -1) if kind=='fold'
            else sign*(Q(pot,2)+amount) if sign else tie)


def engine_audit(record,nodes):
    root=d.b.state(record)
    hands,joint,signs,compatible=d.b.population(record)
    hero,villain=record['role_seats']
    tie=Q(root.pot%2,2)*(1 if hero<villain else -1)
    count=0
    for sign in (-1,0,1):
        i,j=map(int,np.argwhere(compatible & (signs==sign))[0])
        for node in nodes:
            if node['player']!=-1: continue
            child=root.clone()
            child.holes=[list(h) for h in root.holes]
            child.holes[hero],child.holes[villain]=hands[i].tolist(),hands[j].tolist()
            used=set(record['board'])|set(hands[i])|set(hands[j])
            spare=iter(c for c in range(52) if c not in used)
            for seat in range(6):
                if seat not in (hero,villain): child.holes[seat]=[next(spare),next(spare)]
            for action in node['path']:
                assert action in child.legal_actions()
                child.step(action)
            assert child.is_over() and sum(child.payoffs())==0
            actual=Q(child.payoffs()[hero]+root.committed[hero])-Q(root.pot,2)
            assert actual==terminal_chips(node['payoff'],root.pot,sign,tie),(node,actual)
            count+=1
    return dict(checks=count,all_terminal_paths=True,win_tie_loss=True)


def payoff_arrays(record,nodes):
    hands,joint,signs,compatible=d.b.population(record)
    pot=record['actual_state']['pot']
    hero,villain=record['role_seats']
    tie=(pot%2)*(.5 if hero<villain else -.5)
    arrays={}
    for node in nodes:
        if node['player']!=-1: continue
        key=tuple(node['payoff'])
        if key in arrays: continue
        kind,winner,amount=key
        utility=((pot/2+amount)*(1 if winner==0 else -1) if kind=='fold'
                 else signs*(pot/2+amount)+(signs==0)*tie)
        arrays[key]=joint*utility*(10/pot)
    return arrays


def sequence_layout(nodes):
    sizes=[1,1]
    rows=[[],[]]
    def walk(i,last):
        node=nodes[i]
        node['last']=last.copy()
        role=node['player']
        if role==-1: return
        children=list(range(sizes[role],sizes[role]+len(node['children'])))
        sizes[role]+=len(children)
        node['sequences']=children
        rows[role].append((last[role],children))
        for child,seq in zip(node['children'],children):
            new=last.copy()
            new[role]=seq
            walk(child,new)
    walk(0,[0,0])
    flows=[]
    for role in (0,1):
        a=np.zeros((len(rows[role])+1,sizes[role]))
        a[0,0]=1
        for r,(parent,children) in enumerate(rows[role],1):
            a[r,parent]=-1
            a[r,children]=1
        flows.append(a)
    return sizes,flows


def solve(nodes,sizes,flows,arrays):
    n=next(iter(arrays.values())).shape[0]
    start=perf_counter()
    blocks=[[None]*sizes[1] for _ in range(sizes[0])]
    for node in nodes:
        if node['player']!=-1: continue
        i,j=node['last']
        block=sparse.csr_matrix(arrays[tuple(node['payoff'])]*SCALE)
        blocks[i][j]=block if blocks[i][j] is None else blocks[i][j]+block
    # Keep empty sequences present even if no terminal ends on them.
    for i in range(sizes[0]):
        for j in range(sizes[1]):
            if blocks[i][j] is None: blocks[i][j]=sparse.csr_matrix((n,n))
    a=sparse.bmat(blocks,format='csr')
    del blocks
    assert not len(a.data) or np.min(np.abs(a.data[a.data!=0]))>1e-9
    e,f=[sparse.kron(sparse.csr_matrix(v),sparse.eye(n),format='csr') for v in flows]
    rhs=[np.r_[np.ones(n),np.zeros(v.shape[0]-n)] for v in (e,f)]
    assembly=perf_counter()-start
    calls=[]
    policies=[]
    for role in (0,1):
        own,other=(e,f) if role==0 else (f,e)
        payoff=-a.T if role==0 else a
        other_sign=1 if role==0 else -1
        inequalities=sparse.hstack([payoff,other_sign*other.T],format='csc')
        equalities=sparse.hstack([own,sparse.csr_matrix((own.shape[0],other.shape[0]))],format='csc')
        objective=np.r_[np.zeros(own.shape[1]),rhs[1-role]*(-1 if role==0 else 1)]
        start=perf_counter()
        result=linprog(objective,A_ub=inequalities,b_ub=np.zeros(inequalities.shape[0]),
            A_eq=equalities,b_eq=rhs[role],bounds=[(0,1)]*own.shape[1]+[(None,None)]*other.shape[0],
            method='highs-ds',options=dict(time_limit=10,maxiter=20000,
                primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
        calls.append(dict(status=int(result.status),success=bool(result.success),
            message=str(result.message),iterations=int(result.nit),seconds=perf_counter()-start,
            objective=None if result.fun is None else float(result.fun)/SCALE,
            variables=len(objective),inequalities=inequalities.shape[0],nonzeros=inequalities.nnz,
            raw_x=None if result.x is None else result.x.tolist()))
        policies.append(None if result.x is None else result.x[:own.shape[1]].reshape(sizes[role],n).tolist())
        del result,inequalities,equalities,payoff
        gc.collect()
    return dict(calls=calls,realizations=policies,assembly_seconds=assembly,
        solver_success=all(r['success'] for r in calls),payoff_nonzeros=a.nnz,sequences=sizes)


def quantize(raw):
    rows=[]
    for row in np.maximum(np.asarray(raw),0):
        p=row/row.sum() if row.sum()>0 else np.full(len(row),1/len(row))
        scaled=p*GRID
        count=np.floor(scaled).astype(np.int64)
        remaining=GRID-int(count.sum())
        assert 0<=remaining<=len(row)
        order=np.argsort(-(scaled-count),kind='stable')
        count[order[:remaining]]+=1
        rows.append(count.tolist())
    return rows


def behavior(nodes,realizations,n):
    result={}
    for i,node in enumerate(nodes):
        if node['player']==-1: continue
        x=np.asarray(realizations[node['player']])
        result[str(i)]=quantize(x[node['sequences']].T)
    return result


def realization_integers(nodes,sizes,probs,n):
    result=[np.zeros((k,n),dtype=object) for k in sizes]
    for r in result: r[0]=GRID**2
    for i,node in enumerate(nodes):
        role=node['player']
        if role==-1: continue
        p=np.array(probs[str(i)],dtype=object)
        assert p.shape==(n,len(node['children']))
        assert all(sum(row)==GRID and min(row)>=0 for row in p)
        for a,seq in enumerate(node['sequences']):
            numerator=result[role][node['last'][role]]*p[:,a]
            assert all(v%GRID==0 for v in numerator),'more than two own decisions'
            result[role][seq]=numerator//GRID
    return result


def certificate(nodes,sizes,arrays,probs):
    n=next(iter(arrays.values())).shape[0]
    realization=realization_integers(nodes,sizes,probs,n)
    power=max(0,53-min(int(np.frexp(np.abs(a[a!=0]))[1].min()) for a in arrays.values() if np.any(a)))
    denominator=1<<power
    cast=np.frompyfunc(int,1,1)
    ints={k:cast(a*float(denominator)) for k,a in arrays.items()}
    assert all(np.array_equal(np.asarray(ints[k],dtype=float)/float(denominator),a) for k,a in arrays.items())
    value=0
    leaves={}
    for i,node in enumerate(nodes):
        if node['player']!=-1: continue
        a=ints[tuple(node['payoff'])]
        x,y=[realization[r][node['last'][r]] for r in (0,1)]
        hi=a@y
        lo=x@a
        value+=sum(x*hi)
        leaves[i]=(hi,lo)
    def backup(i,role):
        node=nodes[i]
        if node['player']==-1: return leaves[i][role]
        values=[backup(child,role) for child in node['children']]
        if node['player']!=role: return sum(values)
        choose=max if role==0 else min
        return np.array([choose(v) for v in zip(*values)],dtype=object)
    high=Q(int(sum(backup(0,0))),denominator*GRID**2)
    low=Q(int(sum(backup(0,1))),denominator*GRID**2)
    actual=Q(int(value),denominator*GRID**4)
    assert low<=actual<=high
    return dict(lower=str(low),upper=str(high),value=str(actual),gap=str(high-low),
        exploitability=float((high-low)/2),strict_pass=high-low<=Q('1e-8'),
        coefficient_roundtrips=sum(a.size for a in arrays.values()))


def literal_value(nodes,sizes,arrays,probs):
    n=next(iter(arrays.values())).shape[0]
    def visit(i,h0,h1):
        node=nodes[i]
        if node['player']==-1: return Q(float(arrays[tuple(node['payoff'])][h0,h1]))
        hand=h0 if node['player']==0 else h1
        return sum(Q(probs[str(i)][hand][a],GRID)*visit(child,h0,h1)
                   for a,child in enumerate(node['children']))
    return sum(visit(0,i,j) for i in range(n) for j in range(n))
