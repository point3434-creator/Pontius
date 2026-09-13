"""Python 3.14-only bootstrap; no installation or environment mutation."""
import os
import sys
import runpy
from pathlib import Path

assert sys.version_info[:3] == (3, 14, 6)
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
HERE = Path(__file__).resolve().parent
sys.path[:0] = ['D:/Pontius/tmp/group-opt-author/venv/Lib/site-packages', str(HERE)]
target = sys.argv.pop(1)
sys.argv[0] = str(HERE / target)
runpy.run_path(sys.argv[0], run_name='__main__')
