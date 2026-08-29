# Task 2 fix round 5 — analyzer scoped rereview 2 findings

Four earlier findings are addressed (mapping child union, comprehension effect
cardinality, independent census, expanded dict storage). The following four
findings plus one new breakage remain load-bearing. Add exact RED cases before
production edits, then run focused, full, isolated, regeneration, and static gates.

1. Preserve control-flow successors, not only environments, through every nested
   compound. When every `if`/match/try/loop branch returns, raises, breaks, or
   continues, following statements on that path are unreachable and may not be
   evaluated or counted. Apply the same successor model in `_statements` and
   `_runtime_call_bounds`; lock nested all-terminating branches followed by a
   sensitive call.
2. Exceptional successors must include potentially throwing expressions in all
   compound headers after mutations: `if`/while tests, with context expressions,
   for iterators, match subjects, and match guards, not only standalone Call/Await
   statements or explicit raises. Join exact post-header states or poison
   ambiguity for handlers.
3. Conditional decorator resolution requires observed canonical import provenance.
   `_conditional_callable_name` may not default an absent root to itself. A bare or
   rebound `unittest.skipIf` root without explicit canonical binding is unresolved.
   Lock missing-provenance and alias-import canonical cases.
4. Meter every call-bound traversal and secondary `ast.walk` against the same
   per-item/child budget and translate recursion failures. The budget must thread
   through `_expression_call_counts`, `_runtime_call_bounds`, helper recursion,
   literal-child passes, and all related walks; lock a deep form that passes the
   execution visitor but exhausts the call-bound pass.
5. New breakage: `_SensitivePreclassifier` must use checked/budgeted cardinality for
   `range` length and repetition multiplication. Raw `len(range(...))` and
   `repeated *= bound` are forbidden; values above 2,147,483,647 yield the stable
   bounded error/blocker.

All prior analyzer/discovery requirements and no-transaction/no-payload/
no-capability/no-OneDrive/no-commit constraints remain binding.
