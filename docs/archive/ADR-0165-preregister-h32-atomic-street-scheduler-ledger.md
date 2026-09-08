# ADR-0165: Preregister the h32 atomic street-scheduler ledger

- Status: accepted and preregistered
- Date: 2026-08-21
- Depends on: ADR-0155 through ADR-0164

## Question

With the shared topology, both balanced target contexts, blueprint response overlays, and warm-started solvers prepared off-clock, how much deterministic atomic certification can one actual resident warm step buy inside a 15-second decision boundary?

This is the first clock that includes candidate generation and atom construction rather than combining historical timing rows. It remains a systems ledger, not a strategy-quality experiment.

## Frozen workload

Use the two retained balanced h32 target shifts in local-blocker then all-seat-strength order. Before either street clock:

- construct the one shared automaton bundle and both target-specific belief/response contexts;
- instantiate one pristine resident DCFR solver per context;
- warm-start each solver from its immutable average-64 blueprint with regret mass `0.1 * payoff_span`; and
- apply the accepted allocator trim lifecycle.

Each target is an independent one-step street trial. Immediately before its clock, release only unreferenced pool blocks. Start the clock immediately before `solver.step()`. Charge:

1. the complete alternating six-seat resident warm step;
2. current-policy extraction;
3. changed-atom manifest construction;
4. construction of all six lexicographically selected one-infoset policies in acting-seat order 0 through 5;
5. every deadline check and attempted incremental response certificate; and
6. explicit blueprint selection.

Packing is not invoked because union composition remains forbidden. The immutable blueprint is emitted in both trials regardless of atom outcomes. No complete strategy-quality evaluator is called.

## Deadline discipline

Reserve the final 1,000 ms for unmeasured action emission. The certification cutoff is therefore 14,000 ms. Before starting any certificate, require at least 1,250 ms to remain before that cutoff. The start reserve exceeds ADR-0164's 1,025.06 ms observed maximum by 224.94 ms.

After a certificate returns, use its result only if completion occurred by 14,000 ms. A late result is discarded and no later atom may start. If the start guard fails, stop immediately. In all cases select the immutable blueprint. Report the actual pre-emission clock plus the fixed reserve; deadline fit is an outcome, not a mechanism gate.

The 1,000 ms emission tail is still a reserve, not an observed action-emission distribution. Therefore even two fitting rows cannot authorize deployment or a tail-latency claim.

## Identity and gates

The actual one-step current policy may differ in digest because of GPU reduction order. Compare it with retained `search_current1` at maximum probability error and mean infoset TV at most `1e-9`. The six selected keys must match ADR-0160 exactly. For every attempted atom, compare its evaluated response prefix with the retained row within `1e-9`, and require exact stop and work identity.

Require two target rows, two search steps, twelve generated atoms, zero new complete strategy-quality labels, exact target and blueprint identity, correct deadline discipline and blueprint emission, search below 60 seconds, extraction below 30 seconds, each certificate below 60 seconds, pool total below 12 GB, physical free memory above 1 GB, and total audit time below 600 seconds.

Do not gate on certificates attempted, certificates completed before cutoff, envelope outcomes, or whether either full ledger fits 15 seconds.

## Interpretation

A clean fit establishes deterministic prepared-context capacity for these two trials, subject to the unmeasured emission reserve. A miss identifies whether search or certification consumed the boundary and must fall back to the blueprint. Neither result selects an atom, estimates value capture, authorizes packing, or makes a strategy-quality claim.
