# ADR-0168: Retrospective atomization exposes strong nonadditivity

- Status: accepted retrospective result; not preregistered
- Date: 2026-08-21
- Implements: ADR-0167
- Result: `experiments/results/retrospective-atomic-value-capture-v1.json`
- Result SHA-256: `53cdc1e6655e5008509d8f8ccbed1f222e874555375c5cd7de03c5a3c87fb38a`

## Methodological status

This is post-hoc evidence. The retained atomic labels were inspected before the
analysis contract was written. The audit made zero new solver calls and created
zero new strategy-quality labels. All seven integrity gates passed, but the
result describes only the frozen four-target corpus and cannot validate a new
ordering, packing rule, or strategy.

## Result

Across 24 retained atoms, 20 were envelope-complete, four were blueprint-cap
stops, and none were objective-bound. The fixed two-certificate scheduler
prefix exposed one complete atom and one cap stop per target. Its best available
complete atom captured only `0.0001388` to `0.007153` of the best retained
complete singleton's positive NashConv reduction.

The two local-shift `search_current1` bundles were envelope-complete and had
exact quality labels. Their positive NashConv reductions were `0.0046178894`
and `0.0033075524`. The best complete singleton captured only `6.09e-8` and
`1.69e-6` of those bundle reductions; the sum of all complete singleton values
captured only `1.22e-7` and `1.87e-6`. Their scalar six-atom interaction
residuals were `-0.0046136989` and `-0.0033035543`.

Both complete bundles contained one constituent atom that was cap-bound when
evaluated alone. The two all-seat-strength bundles were themselves cap-bound
and had no complete exact quality label in the verifier artifact; their partial
NashConv values were therefore not used as bundle values or interaction labels.

## Interpretation

On this corpus, one-infoset atomization preserves certificate mechanics but
does not preserve the bundle's material value. Safety is non-monotone in both
directions: a constituent can fail alone while its already-exactly-evaluated
bundle passes, and complete constituents cannot be assumed safe or valuable
when composed.

This weakens the case for spending the 15-second street budget on more isolated
singleton certificates. The current fixed seat order also has poor
retrospective coverage of even the bounded best-single oracle. Neither fact
authorizes reordering, because both were measured after label inspection.

The result does not establish why the interaction occurs, whether the same
pattern holds on new contexts, or whether any untested union is safe. The
negative scalar residual is a nonadditivity diagnostic, not a causal
decomposition.

## Decision

Keep the ADR-0166 scheduler as a systems-capacity result only. Do not optimize
its atom order from these labels and do not deploy a singleton-selected policy.

The next research experiment should be prospective on fresh targets or a truly
untouched holdout. Freeze a small, deterministic union library before labels,
recertify every attempted union exactly against the original blueprint anchor,
and compare certified value per wall-clock second under the same 15-second
ledger. Atomic certificates may be used as diagnostics, but never as
compositional safety proofs.
