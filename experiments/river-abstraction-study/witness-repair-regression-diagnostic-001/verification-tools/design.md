# Witness repair regression diagnostic 001

User approved investigating the regressing cases and a dependable acceptance
check. This is retrospective exploratory analysis of all 96 cases from the
32-case pilot and 64-case fresh-board confirmation. Their outcomes are known.
No new holdout, model fitting, LP optimization, training, adoption, commit or push.

Reconstruct every game and ordinary-preference group from the frozen inputs.
Check both original and repaired asymmetric certificates and the two saved 10k
profiles. For each seat put all utilities in that seat's own maximization sign.
Let B(G,w) be the best value available to grouping G against fixed witness w.
Compute exactly on the original binary64 matrix interpreted as rational numbers:

  gain = B(new, old_witness) - B(old, old_witness)
  adaptation = B(new, old_witness) - B(new, new_witness)
  new_upper - old_upper = gain - adaptation

Certify the residual uncertainty using both endpoints of the retained saddle
intervals. Separately evaluate the same split and merge under the new witness,
and whether merging destroys feasibility of the retained old optimal policy.
Positive fixed-witness gain is not a minimax guarantee.

Compare three fixed acceptance rules, independently per seat:

1. Structural: accept if the retained original asymmetric optimal policy remains
   feasible under the proposed grouping. This preserves availability of that
   policy, but does not guarantee the newly trained 10k policy is better.
2. Floor: accept if the repaired own-value lower bound is at least the original
   own-value upper bound. Otherwise fall back. This protects representational
   quality, but does not directly guard the deployed finite-iteration strategy.
3. Security: accept if the repaired saved 10k strategy's exact worst-case own
   value is at least the original saved 10k strategy's value. Otherwise fall back
   for that seat. Equality is allowed. No tuned threshold or extra optimizer.

If L(x)=min_y V(x,y) and U(y)=max_x V(x,y), exploitability is (U(y)-L(x))/2.
Guard bettor L upward and caller -U upward separately. Independent per-seat
selection then cannot increase exploitability in this exact one-bet game.
Re-evaluate every mixed selected profile through the existing exact evaluator.
Do not extend this proof to multiplayer, approximate evaluators or unseen games.

Report raw/gated effects separately for each prior panel and bet size. Include
every case, rejected improvements, accepted regressions, structural failures,
floor failures, and worst cases. No claim that retrospective selection is a new
out-of-sample result, and no comparison of CPU cost from work we did not time.

Preserve original records byte-for-byte and append a distinct immutable milestone.
Python 3.14.6, one BLAS thread, pinned NumPy 2.5.2/SciPy 1.18.0. A single sequential
diagnostic worker gets 600 seconds; no hard memory cap. LP and training entry
points are disabled during the diagnostic. An analytic preflight plus one
already-observed pilot case exercise the math before the analysis plan freeze.
