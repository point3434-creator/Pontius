import sys,json,math
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,'D:/Pontius-worktrees/eval-runner-consolidation/src')
import numpy as np
from pontius.river_abstraction_study import PayoffGame,CFR
w=np.array([[3,6,7,1],[4,2,6,5],[4,6,6,2]],dtype=float)
q=w/52; z=np.array([[0,-1,1,1],[1,1,0,1],[1,-1,0,-1]])
c=CFR(PayoffGame(q,q*z*5,q*5,q*z*10,None,'tie'))
c.step()
x=np.array([1.,1.,1.])
f=math.fsum(float(q[i,3])*x[i]*-5 for i in range(3))
a=math.fsum(float(q[i,3])*x[i]*-float(z[i,3])*10 for i in range(3))
exact_f=-sum(Fraction(int(w[i,3]),52)*5 for i in range(3))
exact_a=-sum(Fraction(int(w[i,3]),52)*int(z[i,3])*10 for i in range(3))
assert exact_f==exact_a==Fraction(-10,13)
record={'exact_fold_and_call':str(exact_f),'compact_player1_last_hand_regrets':c.regrets[1][-1].tolist(),'scalar_fold':f,'scalar_call':a,'scalar_regrets':[f-(f+a)/2,a-(f+a)/2],'compact_current_call':float(c.current()[1][-1]),'diagnostic_classification':'Exact rational indifference; floating-point sign at regret zero changes the subsequent policy trajectory. Not a payoff/BR formula failure.'}
print(json.dumps(record,indent=2)); Path('D:/Pontius/tmp/river-study-review-01/tie-diagnostic.json').write_text(json.dumps(record,indent=2)+'\n')
