# Frozen size-repair confirmation 001

Confirm the unchanged bettor size-split rule on eight unseen boards, two per texture,
uniform and polarized regimes: sixteen cases. Select with the existing SHA-256 deck
sequence and per-texture admission, excluding every historical plan's boards plus
development/holdout boards and suit relabelings. Freeze before evaluating any board.
No board replacement, extra cases, retuning or second repair after results.

Generate each new combined-menu baseline using frozen preference groups (K=16),
96 hands per role, pot 10, stacks 20, check/half-pot/pot, and size-specific call/fold.
Train both roles to 50k with the frozen multi-action trainer. Certify each asymmetric
group limit with existing LP and exact-rational bounds. Measure bettor witness cost
separately from caller certificate and common initial-policy generation.

Apply the pilot unchanged: one bettor split by pot-vs-half advantage, one compensating
merge, strict-positive maximum net witness gain, deterministic tie ordering. Train
candidate bettor to 10k and 50k; continue incumbent bettor from 50k to 100k. Keep the
baseline caller byte-identical. Exact worst-case bettor value determines acceptance,
ties allowed. The 10k candidate is diagnostic only. Caller group and policy never change.

Fresh bettor witness acquisition is included in repair component cost. Both branches
get 50k additional bettor updates, not equal computation. Exclude common preparation,
diagnostic proposed-group LP, scoring and verification; retain these separately.
No equal-time, live-latency or end-to-end bot claim.

Frozen descriptive criteria: both accepted arms nonworse in every case; accepted repair
mean improves on incumbent and, separately, accepted continuation by >1e-6 chips.
Report all cases, board/texture/regime means and rejected repairs. Equal case weighting
equals equal board weighting because both regimes are always retained. This is a small
balanced held-out panel, not a population confidence interval or proof for all boards.

Reuse unchanged pilot proposal, trainer, acceptance and exhaustive partition verifier;
only case counts are adjusted in pilot.py, with source diff retained. Verify all
initial policies independently by replay, certify baseline and proposed group limits,
and audit all gates by independent terminal-payoff sums. No verifier LP solving.

Nine inherited analytic tests, direct suit-permutation novelty audit, all 30 prior
milestones checked. Python 3.14.6, one BLAS thread, no allocation tracing, 900 seconds
per phase, inherited 10-second/20k-iteration LP limits, no hard RSS cap. Retain every
outcome and any failure; no automatic retry. No adoption, commit, push or production code.
