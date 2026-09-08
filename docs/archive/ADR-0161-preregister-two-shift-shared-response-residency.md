# ADR-0161: Preregister two-shift shared response residency

- Status: accepted and preregistered
- Date: 2026-08-21
- Depends on: ADR-0127 through ADR-0132, ADR-0158 through ADR-0160

## Context

ADR-0160 showed that the h32 terminal-numerator response overlay is only 413,232 unique numeric bytes per target and that incremental atomic certificates take 0.252–1.006 seconds. Cold construction still takes 9.46–12.99 seconds because every target currently rebuilds the multi-gigabyte resident automaton payload.

This is distinct from the bet-amount affine sharing closed by ADR-0128 through ADR-0132. The one-size automaton half vectors depend on hand axes, split topology, and terminal automata, but not on target belief weights. The existing contraction contract already binds `CuPyResidentAutomatonCache` to `workspace.topology` and `CuPyResidentBeliefCache` to the exact workspace. The additive implementation makes that separation explicit: one immutable shared automaton bundle and one belief/response context per target.

## Frozen workload

Use the largest retained one-size family, balanced h32, on the canonical ADR-0107 board. Construct the two retained target shifts in fixed order: local blocker followed by all-seat strength. Both must reproduce their retained descriptors and average-64 blueprint digests.

Compile exactly one six-seat automaton bundle from their shared topology. Keep it live. Bind both target workspaces simultaneously, each with its own resident belief cache and source-relative blueprint response cache. Do not compile a second automaton bundle. Evaluate the six retained blueprint source responses for each context as part of response-cache construction and compare them with the existing frozen teachers.

This creates no new strategy-quality labels. It replays twelve existing blueprint seat labels solely to validate cross-belief cache reuse.

## Frozen measurements and gates

Report shared automaton bytes, per-target belief bytes, unique two-context response bytes, actual pool used/total, physical free memory, bundle construction time, each context's belief and response construction time, middle rank, and the hypothetical byte bill had the automaton payload been duplicated.

Require:

- two contexts and twelve source seat evaluations;
- zero new strategy-quality labels;
- exact target, policy, and shared-topology identity;
- utility, best-response, and deviation-gain errors at most `1e-9`;
- at most 5 GB shared device numeric state and 1 MB unique response state;
- CuPy pool total at most 12 GB;
- physical free memory at least the existing `5,184,456,164`-byte non-cache reserve;
- bundle construction below 120 seconds, each context binding below 60 seconds, and the audit below 600 seconds.

The existing headroom rule remains conjunctive: both physical free memory and pool headroom below 12 GB must exceed `5,184,456,164` bytes. Its result is reported, not used to change the workload.

## Interpretation

A pass establishes that both target beliefs can remain ready around one topology/automaton payload without semantic drift or unsafe residency. It does not establish end-to-end 15-second search, because cold blueprint response construction is still charged here and no scheduler or search runs.

A topology or exactness failure rejects cross-target reuse. A headroom failure retains single-context residency. No outcome authorizes strategy selection, atom packing, union composition, additional action sizes, or a strategy-quality claim.
