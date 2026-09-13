import os
import runpy
import sys
from pathlib import Path

assert sys.version_info[:3] == (3, 14, 6)
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
here = Path(__file__).resolve().parent
os.environ['CUPY_CACHE_DIR'] = str(here / 'kernel-cache')
sys.path[:0] = [str(here), 'D:/Pontius/.venv/Lib/site-packages',
               'D:/Pontius/tmp/group-opt-author/venv/Lib/site-packages']
sys.argv[0] = str(here / 'experiment.py')
runpy.run_path(sys.argv[0], run_name='__main__')
