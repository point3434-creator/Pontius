# Task 1 report — stable errors and immutable domain models

## Status

Implemented the evidence package's dependency-light typed-error and immutable-model
layer.  Production imports are limited to the standard library and sibling evidence
modules.  The package initializer exports only the five typed errors and the four
public state/assessment interfaces.

Local commit: `bbf98f822173fb2a6b0cb84aa910293ad05c0ee5`

## Files

- `src/pontius/evidence/__init__.py` — limited public exports.
- `src/pontius/evidence/errors.py` — `EvidenceError` and its five stable typed
  subclasses, with recursively frozen sorted error context.
- `src/pontius/evidence/model.py` — frozen, slots-based evidence identities,
  authorization states, manifest models, and retained-v7 assessment models.
- `tests/test_evidence_errors_and_model.py` — six focused contract tests.

## TDD evidence

The disposable snapshots were created outside OneDrive with the absolute Git
executable, then populated with the exact current Task 1 files.  Each payload was
executed only from its snapshot with the copied non-reparse interpreter and
`PYTHONPATH` set exactly to `H/src`.

### Initial RED

Snapshot: `C:\Users\point\AppData\Local\Temp\pontius-evidence-task1-red-d0c414d266f243e8bd54c492896ea3c3`

Exact payload command:

```powershell
$env:PYTHONPATH = (Join-Path $harnessItem.FullName "src")
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

The bootstrap contract in Task 1 was used (absolute executable and harness checks,
non-reparse checks, push to `H`, and `PYTHONPATH=H/src`).  Exit status: `1`.

```text
Traceback (most recent call last):
  File "...\tests\test_evidence_errors_and_model.py", line 6, in <module>
    from pontius.evidence.errors import (
ModuleNotFoundError: No module named 'pontius.evidence'
EXIT_STATUS=1
```

This is the required missing-package RED, rather than a test setup failure.

### Focused wrapper-count RED

After the initial GREEN review identified the independent count invariant, I added
one test first.  It was run in a newly captured snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-evidence-task1-wrapper-red-bb0f19fceb4b42dc99563f6302ac4ed2`.

Exact payload command:

```powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit status: `1`.

```text
FAIL: test_manifest_and_assessment_models_are_frozen_and_type_checked
AssertionError: ValueError not raised
Ran 6 tests in 0.001s
FAILED (failures=1)
EXIT_STATUS=1
```

The smallest change added wrapper count/tuple-length checks.

### Final GREEN and regression

Fresh snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-evidence-task1-final-green-f7acbaff746d45c0a196b6d523b0930c`.

Exact payload command:

```powershell
$env:PYTHONPATH = (Join-Path $harnessItem.FullName "src")
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit status: `0`.

```text
test_authorization_models_normalize_paths_and_enforce_exact_values ... ok
test_error_context_rejects_unsupported_values_before_construction ... ok
test_evidence_file_identity_is_frozen_normalized_and_validated ... ok
test_identity_and_git_values_reject_boolean_or_invalid_identity_values ... ok
test_manifest_and_assessment_models_are_frozen_and_type_checked ... ok
test_public_errors_keep_stable_fields_and_immutable_context ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
EXIT_STATUS=0
```

## Self-review

- Error contexts are recursively immutable (`MappingProxyType`, tuples, and
  frozensets), mapping keys are sorted, and unsupported values reject before an
  exception is constructed.
- Every public model is `@dataclass(frozen=True, slots=True)` and normalizes
  repository-relative paths while rejecting absolute and escaping paths.
- All integer fields use exact `int` checks, so booleans are rejected; all public
  boolean fields use exact `bool` checks.
- Digests and Git identities require lowercase hexadecimal fixed lengths.
- Authorization paths are normalized, sorted, and de-duplicated; configuration
  bounds must be positive; manifest wrapper counts independently match tuple
  lengths.
- The focused test did not run from the development worktree.

`git diff --check` was run before staging and returned exit status `0`; staged
verification is recorded with the commit below.

## Concerns

The tool execution policy denied the final recursive cleanup commands despite
prior validation that all four snapshot directories were immediate children of the
resolved OS temp directory and had the expected `pontius-` prefix.  The disposable
snapshot directories therefore remain under `%TEMP%`; no repository file is
affected.  This is the only outstanding operational concern.

## Fix Round 1

### Changes

- Removed `EvidenceError` from `pontius.evidence` imports and `__all__`.  It
  remains available only from `pontius.evidence.errors`, leaving the initializer
  at the required five typed errors plus four user-facing state/assessment types.
- Added a focused package-boundary test that proves the base class is neither in
  `__all__` nor an initializer attribute.
- Reviewed all Task 1 production files for translation sites.  They only define
  constructors, validators, values, and exports; none translates a caught error.
  Therefore there is no real translation site in Task 1 for an `__cause__`
  regression test.  A synthetic `raise ... from ...` test was deliberately not
  added because it would test Python syntax rather than production behavior.

### TDD evidence

RED snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-evidence-task1-fix1-red-ee463d05b4ea48018a53a65228ae0c1a`

Exact payload command:

```powershell
$env:PYTHONPATH = (Join-Path $harnessItem.FullName "src")
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit status: `1`.

```text
FAIL: test_package_exports_only_the_specified_error_types
AssertionError: 'EvidenceError' unexpectedly found in
('AuthorizationPhaseError', 'AuthorizationState', 'EvidenceConfigurationError',
 'EvidenceError', 'EvidenceIntegrityError', 'LifecycleStateError',
 'LiveAuthorizationState', 'PreauthorizationState', 'RetainedV7Assessment',
 'RuntimeContractError')
Ran 7 tests in 0.001s
FAILED (failures=1)
EXIT_STATUS=1
```

Final GREEN snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-evidence-task1-fix1-final-green-d24ea2adebad4fca87ca3075ad4dd314`

Exact payload command:

```powershell
$env:PYTHONPATH = (Join-Path $harnessItem.FullName "src")
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit status: `0`.

```text
Ran 7 tests in 0.001s
OK
EXIT_STATUS=0
```

One initial GREEN snapshot was discarded because its directory-level overlay
nested the pending package instead of replacing the committed package.  The final
snapshot used file-level overlays and is the only GREEN result claimed above.

Local fix commit: `54de8607f433fd9fb1318cdb614badd2b67ec3d5`
