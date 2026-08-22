# ADR-0274: Post-fold confirms safe value but not universal one-round closure

- Status: accepted fresh mixed result; universal current-decision closure rejected
- Date: 2026-08-22
- Implements: ADR-0273
- Clean preregistration commit: `57dacfcc4bc453feb94395a3356eb4f16c6640f8`
- Result: `experiments/results/h32-post-fold-closure-value-confirmation-v1.json`
- Result SHA-256: `783c80b9b6029da962e34cf7be50a3bea331ec5f8b04fd7398e98924b951f8b1`

## Process result

The single prospective GPU campaign passes every frozen provenance, parent,
manifest, current-actor, fold-setup, scoped-capture, restoration, digest,
barrier, identity, numerical, row, projection, timing, memory, response-
accounting, one-cut, reconstruction, oracle-ceiling, ledger, certificate,
emission, label-count, finite, and null-claim gate. It completes in `68.389 s`
offline and emits only the immutable blueprint on all six targets.

All six candidates freeze before any post-cut endpoint or final retreat label.
The setup and construction-capture bindings restore. Captured endpoint and
master-epigraph digests agree exactly with the byte-pinned core. The run uses
six first construction oracles, five post-cut endpoint oracles, and six final
retreat oracles: 17 exact all-seat evaluations in total.

## Fresh global-closure result

Universal one-round closure fails. One target closes at round zero; five need
the allowed cut round; only three of those five close after it. The total is
four of six globally closed endpoints.

The two failures are:

- `panel_1/blocker_heavy/checks_then_bet_seat1_then_fold_seat2`: acting seat
  3; first-round cuts for seats 0, 4, and 5; post-cut violating seats 0 and 5;
  exact `U - L = 0.0007763464340`; maximum epigraph violation
  `0.0004898408379`.
- `panel_3/balanced/checks_then_bet_seat4_then_fold_seat5`: acting seat 0;
  first-round cuts for seats 1, 2, and 3; post-cut violating seats 2 and 3;
  exact `U - L = 0.0003496428160`; maximum epigraph violation
  `0.0002047052028`.

Both endpoints are exactly cap-feasible. These are new response facets with
material bound gaps, not cap failures or a numerical-tolerance artifact. The
other four gaps are zero to `6.48e-11`.

This fresh result rejects the proposed universal current-decision direction-
demotion decision. Together with the retained post-call subgroup, ten of 12
fixed current-decision programs close by round one, but those contexts are
non-IID and two fresh counterexamples are sufficient to keep the fallback.

## Fresh safety and value result

The safe-value arm passes more strongly than preregistered. All six factor-
`0.5` retreats are independently exact-certified, cap-feasible, interior,
strictly positive, shadow-accepted, and above the `0.001` materiality floor.
Both range families are represented.

Exact delivered values range from `0.0020203102` to `0.0201211902`, with
median `0.0063506993` and pooled value `0.0471074700`. Minimum exact cap slack
is `1.499999876e-9`.

Thus the one-round multidimensional master remains a strong safe candidate
generator even when it does not yet hold a global-optimality proof. Do not
conflate failure of universal closure with failure to produce certifiable
value.

## Wall clock, memory, and numerics

Measured complete ledgers range from `2,997.076` to `5,337.317 ms`. Every
post-cut endpoint oracle is below the hard `1,000 ms` ceiling; the maximum is
`726.366 ms`. The conditional conservative total remains
`14,967.615699994712 ms`, leaving `32.384 ms` on every one-cut path.

Maximum GPU-pool total is `5,044,957,696` bytes and minimum physical free
memory is `10,465,837,056` bytes. Maximum initial-row, cut-row, profile,
master-primal, and master-dual errors are `9.58e-16`, `5.75e-15`, `2.31e-14`,
`1.38e-15`, and `3.99e-16` respectively.

The large measured slack does not override the frozen conservative ledger.
Another round cannot be admitted live under the current `13,967.616 ms` floor
without a separately preregistered runtime-contract argument.

## Decision

Accept and seal the process-valid fresh mixed result. Accept fresh transfer of
safe material value after a fold. Reject universal one-round current-decision
global closure and do not demote or retire direction generation.

Authorize one retrospective, target-isolated full-closure timing diagnostic on
only the two disclosed fresh failures. Preserve their order, setup, warm step,
master, exact oracle, cut semantics, caps, and tolerances; allow additional
rounds only off-clock and emit no candidate. Record rounds to closure and the
marginal cut, master, and endpoint-oracle costs after the already-failed first
round.

If both failures close with exactly one additional round, separately study a
component-wise deadline admission rule or evidence-backed conservative
repricing. Do not silently spend the measured slack or weaken the existing
floor. If either remains deep or stalls, keep one-round convex retreat as the
bounded safe generator and treat global closure as off-clock teacher evidence.

## Claims boundary

The six post-fold labels are fresh, but boards and source blueprints are
retained and the panel is non-IID. No candidate was externally emitted. This
result makes no deployment-rate, direction-obsolescence, multi-seat,
composition, cross-street, chip-EV, AIVAT, full-width, exploitation, or broad
poker-strength claim.
