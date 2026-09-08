# ADR-0159: Preregister the h32 atomic incremental-response preflight

- Status: accepted and preregistered
- Date: 2026-08-21
- Depends on: ADR-0107, ADR-0125, ADR-0126, ADR-0154, ADR-0157, ADR-0158

## Decision

Run one frozen h32 systems-and-exactness preflight of the source-relative terminal-numerator response cache before using atomic clean-fringe results for any search decision.

The corpus is the four retained ADR-0107 targets: two range families crossed with two target shifts. The immutable anchor is each target's retained blueprint. The parent bundle is retained `search_current1`. Before any new atomic quality label is measured, form its exact changed-infoset manifest, partition by acting seat, and select the lexicographically first changed infoset for each of seats 0 through 5. Apply each selected atom alone at scale 1.0. This creates exactly 24 ordered diagnostic atoms.

The complete six-seat resident leaf-adjoint evaluator is an exactness teacher only. For each atom, it supplies the full utility, best-response, and deviation-gain vectors. The incremental verifier uses immutable blueprint gains, immutable blueprint NashConv, the retained guard and payoff span, and seat order `(0,1,2,3,4,5)`. Compare every evaluated prefix entry and the exact stop reason/seat to the complete teacher.

## Frozen measurements

For every target record:

- resident-static and response-cache cold construction time, separately and combined;
- raw and identity-deduplicated persistent response-cache numeric bytes;
- device free bytes and CuPy pool used/total bytes after static-cache construction, response-cache construction, and all atoms;
- maximum source terminal middle rank;
- incremental certificate wall time, affected/full/reused terminal counts, response-action flips, and exactness errors per atom;
- certificate-only fit under a 15,000 ms street budget with 0, 250, 500, and 1,000 ms reserves.

The wall-clock rows exclude search, atom extraction, scheduling, and selection. They therefore answer only whether the certificate itself fits the stated remainder; they are not end-to-end deployment ledgers.

## Outcome-neutral gates

Require four targets, six atoms per target, 24 new diagnostic policy labels, 144 complete-teacher seat evaluations, retained policy identity, deterministic atom identity, source and evaluated-prefix errors at most `1e-9`, exact stop identity, at most 1 GB of unique response-cache numeric state, at most 12 GB CuPy pool reservation, at least 1 GB reported free device memory, at most 120 seconds cold construction per target, at most 60 seconds per atomic certificate, and at most 1,200 seconds total audit time.

Do not gate on admission rate, binding-constraint mix, deadline fit, response flips, affected-terminal fraction, speedup, or any quality direction. Those are results.

## Scope guards

The 24 labels cannot select a policy, reorder atoms, compose atoms, authorize a union, tune a threshold, schedule a context, or support a strategy-quality claim. The anchor stays immutable across all atoms; a completed atom does not become an incumbent. Any later union requires exact union recertification under a separately preregistered packing rule. The first execution is systems and exactness evidence only.
