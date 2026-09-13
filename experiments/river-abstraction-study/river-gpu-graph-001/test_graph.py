"""Pre-timing gates: reference semantics, exact graph/eager parity, reset and counter."""
from pathlib import Path
import json
import numpy as np
import cupy as cp
import experiment as old
from gpu_adapter import Solver as Eager
from static_solver import StaticSolver

cp.get_default_memory_pool().set_limit(size=1024*2**20)
rows=[]
for case in ('checkback','raise'):
    spec,host=old.game(case)
    arrays={k:cp.asarray(a) for k,a in host.items()}
    reference=Eager(spec['nodes'],arrays,old.CONFIG)
    static=StaticSolver(spec['nodes'],arrays,64)
    graph=StaticSolver(spec['nodes'],arrays,64)
    with graph.stream:
        for _ in range(2): graph.step()
    graph.stream.synchronize()
    graph.capture()
    with graph.stream: graph.reset()
    graph.stream.synchronize()
    maxima=[]
    for t in range(1,33):
        reference.step()
        with static.stream: static.step()
        with graph.stream: graph.step(replay=True)
        cp.cuda.Stream.null.synchronize()
        static.stream.synchronize()
        graph.stream.synchronize()
        maximum=0.
        for attr in ('policy','regret','accumulator'):
            for k,a in getattr(reference,attr).items():
                b=cp.asnumpy(getattr(static,attr)[k])
                c=cp.asnumpy(getattr(graph,attr)[k])
                np.testing.assert_array_equal(b,c)
                np.testing.assert_allclose(b,cp.asnumpy(a),atol=1e-10,rtol=1e-8)
                maximum=max(maximum,float(np.abs(b-cp.asnumpy(a)).max()))
        assert int(graph.counter.get())==t
        maxima.append(maximum)
    saved={k:cp.asnumpy(a) for k,a in graph.average().items()}
    with graph.stream:
        graph.reset()
        for _ in range(32): graph.step(replay=True)
    graph.stream.synchronize()
    for k,a in graph.average().items(): np.testing.assert_array_equal(cp.asnumpy(a),saved[k])
    with graph.stream:
        for _ in range(32): graph.step(replay=True)
    graph.stream.synchronize()
    assert int(graph.counter.get())==64
    try: graph.step(replay=True)
    except ValueError: pass
    else: raise AssertionError('horizon overflow was not refused')
    rows.append(dict(case=case,reference_max_abs=max(maxima),
                     replay_bitwise_equal=True,reset_identical=True,counter_and_horizon=True))
    graph.close()
    static.close()
print(json.dumps(dict(passed=True,rows=rows),indent=2))
