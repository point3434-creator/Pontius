# Soft-assignment pilot: prepared for the retained run

Read design.md for the research question, population, primary endpoint and limits.
Read soft.py for assignment construction, exact certificates and the regret learner.
Read experiment.py for binding, reconstruction, execution, replay and reporting.
The final plan digest and exact command are recorded in freeze.json. plan.json
pins source, the observed case records, the frozen model and preparation checks.

No learned-game-model implementation, new training, or library refactor is in scope.
This is a fixed geometric soft-assignment test inspired by the first paper, not
an Embedding CFR reproduction. The capacity comparison follows the second paper's
useful hypothesis. LAMIR's depth/capacity interaction remains a later question.

The main run has not been invoked. Author checks use synthetic data only and are
not a cold review. Existing source, test files and research milestones are read-only.
No commit, push, publication, deployment or adoption is authorized by this packet.

The final action requires controller approval of the frozen retained plan:
one worker followed by its verifier, each with a 1,800-second timeout, no hard RSS
cap. No automatic retries. A successful run retains both captures, row-level
strategies and assignments, exact certificates, summary, audit and a manifest.

One hardening obligation is deliberately kept narrow: a consumed output directory
after interruption is not automatically reusable. Resolve a failed invocation
explicitly rather than erasing it. This follows the preceding research runners.
