# Task 2 fix round 5 — analyzer task-review findings

The frozen analyzer slice `task-2-fix5-analyzer-review.patch` is rejected.
Address every Important finding below with a deterministic RED reproduction,
focused GREEN evidence, the complete inventory suite, and an appended fix report.
Do not touch transaction/I/O code.

1. `tools/generate_test_inventory.py:7140-7157`: unsupported mapping evaluation
   returns on the first unresolved key without evaluating later children. Lock
   `backend = {runtime_key(): 0, "gpu": cp}; backend["gpu"].arange(1)` and
   evaluate every child before unioning sensitivity.
2. `:7396-7439`: comprehension walrus effects propagate for zero iterations.
   Lock `launch = subprocess.run; [(launch := print) for _ in range(0)];
   launch(...)`. Zero cardinality retains incoming state; possibly-zero or
   filter-dependent execution joins incoming/executed state and blocks sensitive
   ambiguity.
3. `:7966-7986, :8089-8090, :6295-6339`: while proofs ignore terminators and
   repeated condition evaluation. Lock a `continue` before the progress update
   and a protected while condition. Model break/continue/return/raise successors,
   never analyze after a terminator, require all continuing paths to prove a
   finite bound, and count condition evaluations separately.
4. `:7816-7817, :8012-8014`: an ordinary potentially throwing call after an
   environment mutation still gives handlers the pre-try state. Propagate
   post-statement exceptional successors, join or poison ambiguity, and never
   substitute incoming state for missing exceptional state.
5. `:421-426, :440-449, :503-505`: a rebound canonical `unittest` root can be
   resurrected. Require explicit canonical provenance, retain unresolved
   tombstones after any root rebinding, centralize binder extraction, and include
   `MatchStar.name` and `MatchMapping.rest`.
6. `:8773-8775`: literal-child `_ExecutionScopeVisitor` bypasses the shared budget
   and `RecursionError` translation. Route every child traversal and subsequent
   walk/call-bound pass through the shared metered entry point. Lock the 900-term
   module-scope child expression.
7. `:9168-9226, :9607-9624`: sensitive-site reconciliation is circular because
   its census uses the same resolved flow as dispositions. Build an independent,
   conservative preclassification sensitive-site census and reconcile each entry
   exactly once; the zero-iteration walrus reproduction must be detected.
8. Minor but in scope: `:7440-7442` checks only comprehension iterations against
   4,096. Check fully expanded output cardinality, including both key and value
   storage for dict comprehensions, before allocation.

All earlier round-5 requirements, exact budgets, canonical corpus/digests, zero
capability scopes, no-payload/no-OneDrive/no-commit constraints remain binding.
