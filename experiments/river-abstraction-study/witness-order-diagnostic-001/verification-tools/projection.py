"""Euclidean projection onto p(-.25) >= p(0) >= p(.25), no fitted parameters."""
from math import fsum, isfinite

def triplet(values):
    if len(values)!=3 or any(not isfinite(v) or not 0<=v<=1 for v in values):
        raise ValueError('expected three finite probabilities')
    blocks=[]
    for v in values:
        blocks.append([v])
        while len(blocks)>1 and fsum(blocks[-2])/len(blocks[-2])<fsum(blocks[-1])/len(blocks[-1]):
            last=blocks.pop();blocks[-1].extend(last)
    return sum(([fsum(b)/len(b)]*len(b) for b in blocks),[])

def project(rows):
    if any(len(row)!=9 for row in rows):raise ValueError('expected three witness triplets')
    return [sum((triplet(row[i:i+3]) for i in (0,3,6)),[]) for row in rows]
