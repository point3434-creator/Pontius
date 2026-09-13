import os
import runpy
import sys
from pathlib import Path
assert sys.version_info[:3] == (3,14,6)
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[k]='1'
here=Path(__file__).resolve().parent
os.environ['CUPY_CACHE_DIR']=str(here/'kernel-cache')
sys.path[:0]=[str(here),'D:/Pontius/experiments/river-gpu-execution-001',
             'D:/Pontius/.venv/Lib/site-packages',
             'D:/Pontius/tmp/group-opt-author/venv/Lib/site-packages']
target=sys.argv.pop(1)
sys.argv[0]=str(here/target)
runpy.run_path(sys.argv[0],run_name='__main__')
