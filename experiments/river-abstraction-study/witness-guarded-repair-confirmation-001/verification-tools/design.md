# Guarded repair confirmation 001

User request: "Let's build and run it" approves the previously proposed fresh-board
test of the complete repair-and-accept procedure. No adoption, commit or push.

Sixteen untouched boards, four in each existing texture stratum, selected by
hash-shuffled decks with seed witness-guarded-repair-confirmation-001. Exclude
all boards in the 23 historical milestone plans and library development/holdout
lists under all 24 suit relabelings. Freeze selection before any new-board score.
Retain board identities and rejected-universe sources. No reselection or retries.

Keep the frozen ordinary-preference model, 78-column design, 16 occupied groups
per seat, 96 holdings per seat, pool 0, uniform/polarized regimes, pot 10, stacks
20/20, bets 5 and 10. Thus 64 paired cases. One split and one merge per seat,
selected using the original exact witness-gain rule. No model fitting or tuning.

Build each new game's baseline witness and run the unchanged repair. Start
fresh solvers from uniform; original checkpoints 10k/50k, repaired 1k/10k.
The gate receives only the matrix, groups and the two saved 10k profiles.
For bettor L=min_y V(x,y), and caller security=-max_x V(x,y), accept each repaired
role independently iff its exact security value is at least the original's.
Exact equality is allowed. Otherwise keep that role's original groups and policy.
Invalid inputs stop the run. No numeric tolerance or certificate-based selection.
Only after acceptance compute the repaired grouping's certificate for analysis.

Primary safety condition: every guarded profile has exact exploitability no
greater than its matched original10k. Primary utility condition: safety passes
and mean half-pot difference is below -1e-6 chips. These are descriptive acceptance
criteria on this fixed stratified panel, not population confidence intervals.
Report both bets, boards, textures, regimes and every leave-one-board-out mean.
Report raw repairs too. Original50k is an additional iteration-budget control,
not an equal-compute comparison. No six-max, full-range or BB/100 claim.

Time gate selection separately, including both exact policy evaluations and
validation. Exclude subsequent score verification and diagnostic LP from that
gate timer. Report all cost components and the component-sum production path:
input preparation + original witness LP + proposal + original10k setup/updates
+ repaired10k setup/updates + acceptance. This excludes diagnostic scoring,
the extra original40k iterations, repaired LP, serialization and verifier work.
It is a component sum, not an independently timed standalone production launch.

Verify all inputs, 256 asymmetric certificates, 256 saved profiles and 64 selected
profiles. Replay 3,840,000 updates with verifier LP calls forbidden. Independently
enumerate each permitted exchange, reconstruct exact security from terminal
payoff sums, and verify the mixed policy with the established exact evaluator.
Independently audit all summary arithmetic and board freshness. Retain all results.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread, no allocation tracing.
900 seconds per sequential worker/verifier phase; no hard RSS cap. The same
mathematical nonregression guarantee is limited to the fully known two-player
one-bet game and the exact saved policies being compared. No cold-review claim.
