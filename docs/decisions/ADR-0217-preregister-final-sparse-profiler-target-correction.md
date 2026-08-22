# ADR-0217: Preregister the final sparse-profiler target correction

- Status: accepted tooling correction before any final corrected h32 counter collection
- Date: 2026-08-21
- Depends on: ADR-0213 through ADR-0216
- Config: `experiments/configs/h32-resident-sparse-ncu-profile-v3.json`
- Config SHA-256: `8da7424f3ebddb680ad4753cc78c2646e5bc2a3cf1edc15de2c8f955a73a1280`
- Final driver: `src/pontius/h32_resident_sparse_ncu_profile_v3.py`
- Final-driver SHA-256: `603b083d504f9027ac840eeb542957da561c630efe7f59a6f4f0ad43f2cb28e0`
- Final control: `tests/test_h32_resident_sparse_ncu_profile_v3.py`
- Final-control SHA-256: `37d8904f53b868cb84ccfa70d9aab7386aa8754958a24350218fb1a64412e683`

## Decision

Run one final corrected profile. Change `--target-processes` from
`application-only` to `all` so Nsight follows the venv launcher's child Python
process. Remove v2's `--print-summary per-kernel` option and restore the
original ADR-0213 wide raw page, which retains the NVTX push/pop column.

The v3 config hash-pins both rejected result artifacts, both rejection ADRs,
the v2 config, driver, and control, plus the final driver and control. The
final driver delegates every gate and result field to the v2 harness while
substituting only the corrected profiler invocation. It invokes the unchanged
ADR-0213 workload with the unchanged v1 config.

## Non-h32 controls

A tiny CuPy NVTX canary established before this preregistration that:

- `application-only` returns no kernel and tells the caller to use target
  `all` for child-launched kernels;
- target `all` collects the canary kernels;
- CSV per-kernel summaries suppress NVTX state and use a long metric table;
  and
- target `all` with the default summary mode emits the expected wide raw table
  with the push/pop NVTX range.

The source control requires target `all`, raw page output, and absence of the
per-kernel summary token. It also prevents v3 from overwriting v1 or v2.

## Stop rule and claim boundary

All ADR-0213 h32 operators, values, directions, width, warmups, NVTX names,
metric set, replay mode, parser, classifier, thresholds, gates, and limitations
remain frozen. No prior failed process state is reused.

If v3 still fails, stop the profiler line rather than issue another same-day
h32 correction. Preserve the failure and move to the action-conditioned corpus
with the accepted ADR-0212 wall ledger. If v3 passes, report only its frozen
diagnostic pressure class; any optimization still requires a separate
ordinary-wall differential.

No branch makes a strategy-quality, transfer, deployment, population,
kernel-speedup, roofline, hardware-comparison, or GPU-purchase claim.
