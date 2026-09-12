"""RED: predictor input with no bet-size information."""
from bridge import np

def design(raw,bet,conditioned):
    x=np.asarray(raw,float)
    z=np.column_stack((x,np.zeros(len(x))))
    return np.column_stack((np.ones(len(x)),z,
        *[z[:,i]*z[:,j] for i in range(12) for j in range(i,12)]))

