"""Load the retained multi-action evaluator, input builder and coordinator."""
from bridge import ROOT, HISTORY, c
from pathlib import Path
import sys
import importlib.util

PRIOR = HISTORY/'multibet-group-diagnostic-001'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


m = load('multi', PRIOR/'verification-tools/multi.py')
d = load('frozen_diagnostic', PRIOR/'verification-tools/experiment.py')
