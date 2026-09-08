# ADR-0203: Preregister the final four-field selector-replay correction

- Status: accepted final correction preregistration before replay
- Date: 2026-08-21
- Corrects: ADR-0199 after ADR-0200 and ADR-0202
- Config: `experiments/configs/h32-retained-affine-selector-cascade-replay-v3.json`
- Config SHA-256: `6584b7de0431e811d1692f015bfa732faf080a2e2e2ed1fc6d8b6e3b1dbaf58d`
- Runner: `src/pontius/h32_retained_affine_selector_cascade_replay_v3.py`
- Runner SHA-256: `72e16a01bc1577a901868d6fbef31daac12dbf88db58b5711d512f5d76807701`
- Control test: `tests/test_h32_retained_affine_selector_cascade_replay_v3.py`
- Control-test SHA-256: `4a2601506b9e34cbeef1381c9678ac1e13ff842342457223766d9e20ed2adb8f`

## Final correction

ADR-0202 showed that ADR-0201's protective wrapper froze only two of the
imported helper's four legitimate fields. Pin the helper itself at
`12c7cba9deb1d6307c058120332c56f5a5446a9ca4045d0f34fbb01bb35a7fb4`
and require its literal schema:

```text
gpu_free_bytes
gpu_total_bytes
gpu_pool_used_bytes
gpu_pool_total_bytes
```

Preserve those four fields and values, then add only:

```text
gpu_physical_free_bytes := gpu_free_bytes
```

Reject a missing field, extra field, or preexisting alias. The v1 and v2
runners remain byte-identical.

## Provenance

The final wrapper pins the complete line:

- ADR-0199 config/runner/test/decision:
  `9f700db8...`, `04062b43...`, `31a6d43b...`, `49c06091...`;
- ADR-0200 rejection: `0bc2ab14...`;
- ADR-0201 config/runner/test/decision:
  `f911602f...`, `36addb29...`, `bf0f7be4...`, `44c1f2a7...`; and
- ADR-0202 rejection: `b6817f15...`.

The complete hashes are mandatory config fields; the abbreviations above are
only for readability.

## Scientific identity

Reuse ADR-0199 byte-for-byte for all target reconstruction, feature extraction,
semantic label ordering, candidate strata, capacity arithmetic, metrics,
predictions, negative controls, numerical/resource gates, and blueprint-only
emission. Discard both failed process states and recompute all 108 candidates
and 648 affine seat rows.

The wrapper changes no target, feature, label, K, cost, tie break, threshold,
score, or outcome branch. It may update only result provenance and record the
exact additive alias after the unchanged v1 function returns.

## Evidence boundary and decision

Run once from a clean successor commit. This is the final schema correction.
If the literal schema guard or any inherited scientific gate fails, reject the
replay line and stop for direct runner review; do not add a fourth wrapper.

A passing result remains retained development evidence only. It cannot support
a fresh-transfer, strategy-quality, deployment, composition, or population
claim.
