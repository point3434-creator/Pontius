# Fresh-board witness pilot r001 disposition

Build readiness: PASS. Specification: PASS. Engineering: PASS for the frozen
pre-execution scope. The coordinator read and accepts the single opposing review.
No actionable finding or documentation advisory requires another correction round.
The report, pre-check inventory and evidence are retained byte-exact in
reviews/review-01/. Their original labels and context disclosures are preserved.

Author verification: 95 affected tests passed, zero failures/errors/skips, with
ResourceWarning promoted to error under Python 3.14.6; Ruff passed. The opposing
review independently ran eight pilot tests and 13 inherited synthetic tests,
reconstructed the board and hand-pool selections, tested varying synthetic
aggregations, and verified all seven candidate, 17 freeze and 12 source pins.
Its detailed checks and limitations remain in the report. The reviewer received
general injected context, including the supplied memory summary; it did not open
prior reviews, dispositions, result archives or memory files. This is a fresh
independent review with disclosed context, not an unqualified cold-pass claim.

The candidate fixes eight fresh boards, three separately seeded 96-holding pools
per seat on each board and two range regimes: 48 cases. Both range regimes use
the same holdings within each board/pool. The grouping formula and occupied
capacity controls are unchanged. Four control banks are generated afresh for
every case, then the candidate is solved: 480 LP calls including witness creation.
The information budget remains oracle-assisted, not a practical-feature claim.

The question is sensitivity to board and pool selection. Complete case values
are certified on the selected games; those numerical intervals are not sampling
confidence intervals. The report treats eight boards as the board-level units,
preserves every case and regression, and reports pool/board spread plus fixed
leave-one-board-out comparisons. It makes no all-board significance, natural-play
frequency, six-max strength or BB/100 claim. No fresh-board score was inspected
during preparation or review, and no alternative panel was selected after scoring.

All four prior milestones and the preceding packet were hash-verified by the
coordinator during freeze and remain unchanged. The reviewer did not independently
inspect historical archives because its handoff prohibited them. Metadata edits
preserve predecessor bytes; the research overview gains only an appended link.
No prior computational source is changed by this candidate.

The next gate is the controller's separate one-shot approval of plan.json under
SHA-256 535a3fa5b4d55d8bc6cc29763c63b5ab41f89cf0ea190bca90f9c00a5a8c9d2c.
Use approval-template.txt. Worker timeout: 1,200 seconds, one sequential worker
and one BLAS thread; each LP has five seconds and 10,000 iterations. Parent
reconstruction, verification and I/O are outside that timeout. No process RSS cap
is imposed. These are stop bounds, not measured runtime or memory guarantees.

Actual completion, certificate widths and outcomes on the 48 fresh cases remain
unmeasured. The output directory and authorization file are absent. This
disposition authorizes no pilot execution, retry, adoption, commit, push or
subsequent experiment. All work remains uncommitted.
