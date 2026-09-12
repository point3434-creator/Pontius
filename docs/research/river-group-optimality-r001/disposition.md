# Fixed-group optimality r001 disposition

Build readiness: PASS. Specification: PASS. Engineering: PASS within the fixed
observed-case diagnostic scope. No material unresolved finding; no correction round.

The one independent review is retained byte-exact with its pre-test inventory and
all supplemental evidence under reviews/review-01/. Author verification passed 75
affected tests, zero failures/skips, with ResourceWarning promoted to error; Ruff
passed. The reviewer independently passed 10 focused tests and checked 36 synthetic
group-games / 72 asymmetric certificates against pure-strategy enumeration and
separate normal-form LP certificates. The rational checker does not trust LP status
or objective: it certifies feasible policies on exact encodings of the binary64
payoffs. A width over 1e-8 chips rejects the candidate.

Both author and reviewer reconciled the eight pinned cases and 96 saved profiles
without optimizing them. Semantic corruptions, parent certificate failure and
summary/manifest write failures were tested. The prior milestone bytes and holdout
computational sources remain unchanged. The test registry and attribute additions preserve their prior bytes here; the
research overview also links to this packet. Existing computational files are unchanged.

The reviewer disclosed automatically injected project history and a later parent
status message about author preflight. It did not open the author preflight evidence
or use that status to support its verdict. This is a fresh independent opposing
review, not an unqualified history-free cold pass. No additional reviewer was used.

The optima and certificate widths of the 96-hand saved cases are not yet measured.
The 300-second worker timeout and 5-second per-LP limits are bounds, not predictions.
Parent verification/I/O are outside that worker timeout; no RSS cap is imposed.
The exact bounds concern the encoded payoff game, not ideal pre-rounding card
probabilities. The avoidable gap combines policy-selection/objective effects and
finite training; it does not promise that more ordinary CFR iterations remove it.

Next gate: controller approval of plan.json by its SHA-256, as provided in
execution-request.md and the one-line approval-template.txt. No observed-case
optimization, commit, push, source adoption or later experiment is authorized by
this disposition. The output directory is absent; no invocation has been made.
