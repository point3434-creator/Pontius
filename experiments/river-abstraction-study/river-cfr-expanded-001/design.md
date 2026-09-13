# Expanded river CFR capacity test

User authorization: "Let's test it" following the proposed expanded-tree test.
Same retained case 001, including board, ranges, pot 29, effective stack 186,
and all 1,081 legal hands per role. Test both earlier memory-limited trees:
checkback (second player may bet after a check), and raise (also permits an
all-in response to one opening bet). Tree identity must match the frozen
river-tree-expansion-001 plan, member for member.

Reuse the CFR solver, tests and launch bootstrap byte for byte. Retain four
previously declared configurations: cfr_g4, dcfr_paper, pdcfr_matched, dcfr_code.
All parameters remain fixed. Omit the two unmatched-averaging controls to bound
the capacity study; no parameter tuning. Three fresh-process repetitions per
configuration per tree; 2,048 iterations, five original checkpoints, float64,
one numerical thread, alternating role 0 then role 1. Maximum 24 training
workers plus eight exact final-audit workers, each <=180 seconds and a sampled
3,072 MiB stop. No LP invocations, retries, GPU work or neural training.

Quality: the retained rational evaluator verifies final values and best-response
bounds after 2^48 behavior quantization. There is no completed full-range LP
reference for these two games; do not substitute the smaller game's equilibrium.
Final intervals across configurations must have nonempty intersection within
each fixed game. Strict gap <=1e-8 is separate from a valid approximate result.
Retain every run, including failure, with measured time, memory and residuals.
Do not call a faster iteration or successful allocation a solved game.

The question is whether iterative solving yields valid approximate policies
inside the same memory budget on the exact expanded games where LP stopped.
This is not a fresh-board confirmation, full NLHE solution or six-max guarantee.
No commit, push or policy adoption is included.
