# Actual river stack transfer 001

Continue the approved transfer direction with the same four reached situations, public
ranges and frozen K=16 grouping. Change only payoff/menu construction to respect their
actual pots and remaining equal live stacks. No new capture, fitting or repair variant.

Replay each retained public prefix through the existing engine. Query half-pot and pot
raise targets using its minimum-raise and round-to-even integer rules. A target at or
above the remaining stack maps to the legal all-in action. Record every case, including
those where both sizes map to that same action. Such a case is structurally not applicable
to this size-choice repair. Refuse the solver entry for it; do not manufacture duplicate
action labels, substitute other sizes, or replace the situation. No pooled strength mean
will treat an inapplicable case as an evaluated zero-gain observation.

The already-read input census is three inapplicable cases and one applicable case:
pots/stacks 279/76, 29/186, 368/44 and 318/45. The applicable menu is 14/29 chips.
This census is a domain observation, not an unseen-case selection result. Outcomes of
the actual-payoff solve remain uncomputed at freeze.

On the applicable case, run the unchanged predecessor solve_case workflow: both incumbent
roles 50000 updates, fixed caller thereafter, one frozen split/merge proposal from an
asymmetric witness, 50000 fresh bettor updates, exact nonworse gate, and continued solving
matched to the measured repair work in 250-update blocks. Include both gate times in
reported total component times. Preserve its 1000000-extra-update cap, 1e-8 certificate
gap and all proposal/negative-result records. No hyperparameter adjustment after results.

The game is still the restricted river tree: bettor check ends in showdown; bettor bet
allows caller fold/call only. It omits other legal sizes, caller bets after a check, and
reraises. It is not a solve of the entire captured engine state. Both seats have equal
remaining stacks and matched contributions at these river starts, so no side pots arise.

Represent centered bettor payoff as engine net payoff plus the bettor's initial committed
chips minus half the initial pot. Check win/loss is +/-P/2; called bet win/loss is
+/-(P/2+b); fold gives P/2. A tie gives +0.5 or -0.5 when the initial pot is odd, depending
on the engine's seat-ordered odd-chip award. This centering changes no strategy comparison.
Multiply all matrix payoffs by 10/P to use normalized chips comparable to the predecessor;
also report actual-chip exploitability by multiplying by P/10. This conversion does not
make comparisons between different underlying games a causal estimate of improvement.

Preserve raw and effective public ranges and their existing 1e-6 floor, pairwise collision
rule and full 1081-combo populations. Folded-player ranges remain unmodeled. Reuse the
exact previous group labels; do not retrain a preference model for the new pot/stack.

Before freeze: four adapter tests, including sixty literal engine settlement checks over
check/fold/call and wins/ties/losses, identity of joint weights and groups, and refusal
of collapsed-size cases. Verify the retained predecessor and every earlier milestone.
After execution: fresh process reruns all four domain/settlement audits, verifies all
coefficients, replays learner updates, and rechecks all certificates and acceptance gates
using the unchanged predecessor verifier, without new LP solves.

One worker, one BLAS thread, Python 3.14.6 and the existing compiled evaluator. No tracing;
1800-second timeout per execution/verification phase; no hard RSS cap. Retain a new named
milestone and report. All previous milestones and unrelated dirty files stay unchanged.
No production edits, checkpoint training, commit or push.

Decision: establish where this mechanism is applicable and whether the one eligible
example retains a benefit. One example cannot establish generalization. Inapplicability
is evidence about this repair, not evidence that those river states need no solving.
