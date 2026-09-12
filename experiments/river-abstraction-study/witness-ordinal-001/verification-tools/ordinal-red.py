"""RED: repeated zero-threshold action labels."""
from loader import np,pref
THRESHOLDS=(-.25,0.,.25)

def targets(advantages):
    a=np.asarray(advantages,float)
    return np.repeat(pref.targets(a),3,axis=1)
