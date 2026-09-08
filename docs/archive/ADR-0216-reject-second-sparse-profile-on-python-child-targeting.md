# ADR-0216: Reject the second sparse profile on Python child targeting

- Status: accepted tooling rejection; no counter interpretation
- Date: 2026-08-21
- Depends on: ADR-0215
- Result: `experiments/results/h32-resident-sparse-ncu-profile-v2.json`
- Result SHA-256: `77fb2b516af4c16ef2c33262fb7b9ee1035be53b2de86a131adb6992308ae70d`
- Preregistered commit: `2ab6cfd`

## Result

The clean corrected invocation again completed both finite workloads with code
zero, no permission error, and a maximum CuPy pool of `961,623,552` bytes. The
run took `12.157262 s`. Explicit per-kernel summary output made stdout
nonempty, exactly `140` bytes per direction, but produced no raw CSV header or
kernel row. The non-vacuous core-metric, metric-finiteness, kernel-count, and
NVTX-identity gates all failed. Reject the artifact without interpreting a
counter value.

## Cause established by non-h32 intervention

After rejection, an otherwise identical tiny CuPy NVTX canary under
`--target-processes application-only` printed:

```text
No kernels were profiled.
Profiling kernels launched by child processes requires the --target-processes all option.
```

On this Windows Python installation, the venv launcher starts
`pythoncore-3.14-64/python.exe`; the CUDA kernels therefore belong to the child
target from Nsight's perspective. Repeating only that canary with
`--target-processes all` collected kernels and the frozen basic metrics.

The same canary also established that `--csv --print-summary per-kernel`
emits a long summary table and explicitly suppresses NVTX state in console
output. With `--target-processes all`, the ADR-0213 default summary mode emits
the expected wide per-launch raw table and includes the push/pop NVTX column.

These are non-h32 tooling observations collected only after v2 had already
failed. They support no Pontius pressure or performance claim.

## Correction boundary

Preserve v1 and v2. A final versioned correction may change only:

- `--target-processes application-only` to `--target-processes all`; and
- remove the v2 `--print-summary per-kernel` addition, returning to the
  ADR-0213 wide raw page with NVTX state.

Every h32 workload, metric set, replay mode, parser, classifier, threshold,
gate, and claim boundary remains frozen. The corrected driver must pin both
failed artifacts and decisions, prove the two corrected command tokens in a
control, and commit cleanly before another h32 collection.
