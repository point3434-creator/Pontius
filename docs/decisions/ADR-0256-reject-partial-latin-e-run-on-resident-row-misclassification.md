# ADR-0256: Reject partial Latin-E run on resident-row misclassification

- Status: accepted process correction; strategy campaign result rejected
- Date: 2026-08-22
- Implements: ADR-0255
- Clean preregistration commit: `acbed0a5ab902eff1930a00cac6be7f9cba7afbe`
- Frozen config SHA-256: `1bc0176be60bc0db010ac5baa086294d2c151dcb64dce658e78ad1b8d15df6f8`
- Frozen runner SHA-256: `52fb20202d94b0f289718c04a12241674abfd639ea898bc66749f41c57013698`
- Result artifact: none written

## Formal result

Reject the ADR-0255 campaign invocation before any strategy conclusion or
promotion decision. The frozen runner completed the first Latin-E target in
memory, then stopped during the second target's first construction-oracle cut
classification with:

`fresh convex exact duplicate response remains violated`

The list-comprehension assignment never completed and no result artifact was
written. The first target's final retreat label was therefore computed but not
printed, persisted, inspected, or used by any later candidate. The second
target stopped before its final retreat label. Latin-F was never touched.

A post-mortem debugger replay reproduced the same branch so that local
construction variables could be inspected. That replay necessarily recomputed
the first target's unobserved final label; it was again deliberately not
inspected or persisted. The diagnostic evidence below comes only from the
second target's adaptive construction oracle, not from either final retreat
label. Because no complete six-target artifact exists, neither invocation can
support value, breadth, timing, or transfer claims.

## Identification

The failing target was
`panel_1/blocker_heavy/checks_then_bet_seat3`, acting seat 2. Its first exact
oracle marked seats 1, 2, and 4 as more than `1e-9` above their master epigraphs:

| Seat | Exact minus epigraph |
|---:|---:|
| 1 | `2.3732123098293978e-9` |
| 2 | `3.0732739399956088e-9` |
| 4 | `1.5618888611927326e-9` |

All three exact response signatures were already present in the source row
library. Re-evaluating those resident affine rows at the candidate matched the
oracle's raw gains within `4.98e-16`. The master's recorded maximum inequality
residual was `3.0732743017125586e-9`, numerically identical to the largest
apparent epigraph violation. Its equality error was zero, duality gap was
`2.26e-17`, and the exact candidate remained cap-feasible with zero cap
violation.

Therefore no response facet was missing. The runner classified an already-
resident constraint's accepted LP feasibility residual as a new response
violation because the cut trigger was `1e-9` while the independently verified
master primal gate was `1e-8`. The fail-closed duplicate guard correctly
stopped execution, but its diagnosis was too coarse.

## Corrective scope

The correction must be signature-first and label-blind:

1. If an oracle violator is an opponent with a new exact response signature,
   extract and add that facet as before.
2. If its signature is already resident, require the resident row to reproduce
   the exact oracle gain within `2e-11`, require the residual to stay within the
   unchanged `1e-8` master primal ceiling, record it explicitly, and do not
   pretend a duplicate row is a new cut.
3. For the acting seat, use its single invariant gain row as the resident row
   even if an exact best-response tie changes the diagnostic action signature;
   the same row-identity and residual ceilings apply.
4. Require every first-oracle violator to be accounted for as either a verified
   resident residual or a newly extracted exact facet, and require every new
   opponent signature to be cut.

No target, order, actor, posterior, objective, master tolerance, separation
allowance, cap allowance, retreat factor, acceptance predicate, materiality
threshold, ledger, or promotion rule may change.

The corrected campaign should also strengthen the label barrier from per-
target to campaign-wide: construct and freeze all six candidates before
running any final retreat certificate. Because six resident h32 contexts do
not fit simultaneously, final certification may reconstruct one pinned context
at a time. That reconstruction is an experimental scheduling cost, not live
work; it must be timed and its identities rechecked, while the final oracle
itself remains fully charged to the target's street ledger.

## Freshness consequence

Latin-E target 1 is no longer a never-computed label. It remains label-blind:
neither its value nor acceptance status was observed before freezing this
correction, and it had no causal path to the target-2 defect or the corrected
algorithm. A corrected result may therefore report it only as a deterministic,
label-blind reconstruction inside the originally precommitted panel, with this
caveat explicit. Targets 2–6 retain unopened final retreat labels. Latin-F
remains the fully untouched confirmatory reserve.

## Decision

Seal this invocation as a process rejection with no strategy result. Create a
hash-pinned v2 preregistration that changes only resident-row classification and
the campaign-wide label barrier, run all controls from a clean commit, and do
not open another final label until every Latin-E candidate has frozen
successfully.
