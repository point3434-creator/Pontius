"""One pytest entry point for the behavioral suites in cases.json."""

from __future__ import annotations

import importlib
import io
import json
import os
import sys
import time
from pathlib import Path
import unittest

import pytest


OUTCOMES = []
RUN_CONTEXT = None
RUN_STARTED = None

SUITES = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def record_test_run(request):
    global RUN_CONTEXT, RUN_STARTED
    from pontius.execution import begin_run, child_context, CONTEXT_ENV

    RUN_STARTED = time.perf_counter()
    RUN_CONTEXT = begin_run(Path(__file__).resolve().parents[1], allow_working_tree=True)
    os.environ[CONTEXT_ENV] = child_context(RUN_CONTEXT)
    request.config.pluginmanager.register(sys.modules[__name__], "pontius-run-journal")


def pytest_sessionfinish(session, exitstatus):
    if RUN_CONTEXT is None:
        return
    from pontius.execution import finish_run

    count = sum(outcome["tests"] for outcome in OUTCOMES)
    skipped = sum(outcome["skipped"] for outcome in OUTCOMES)
    report = dict(
        status="passed" if int(exitstatus) == 0 else "failed",
        summary=(
            f"{count} unittest cases exercised; {skipped} skipped; pytest exit {int(exitstatus)}"
        ),
        pytest_exit_code=int(exitstatus),
        suites=OUTCOMES,
    )
    finish_run(
        RUN_CONTEXT,
        "pytest " + " ".join(session.config.invocation_params.args),
        report,
        time.perf_counter() - RUN_STARTED,
    )


@pytest.mark.parametrize("module_name", SUITES, ids=SUITES)
def test_behavior(module_name):
    module = importlib.import_module(module_name)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    assert suite.countTestCases(), f"Empty suite: {module_name}"
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    OUTCOMES.append(
        dict(
            module=module_name,
            tests=result.testsRun,
            skipped=len(result.skipped),
            passed=result.wasSuccessful(),
            output=output.getvalue(),
        )
    )
    if result.testsRun == len(result.skipped):
        pytest.skip(output.getvalue())
    assert result.wasSuccessful(), output.getvalue()
