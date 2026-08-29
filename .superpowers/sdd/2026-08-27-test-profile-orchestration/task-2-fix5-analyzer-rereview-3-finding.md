# Task 2 fix round 5 — analyzer scoped rereview 3 finding

Findings 2–5 from scoped rereview 2 are addressed. One load-bearing successor
finding remains and is also new breakage from that fix.

`with` cannot prove non-fallthrough merely because its body raises: a context
manager `__exit__` may suppress the exception. Lock
`with contextlib.suppress(RuntimeError): raise RuntimeError` followed by a
protected call. `_flow_statement` must preserve a conservative suppression-to-
normal successor, `_statements_terminate_without_fallthrough` must not classify
the enclosing `with` as terminal without a proved non-suppressing manager, and
reconciliation must not mark the following sink proved-unreachable. The smallest
safe default is that an unresolved context manager may suppress.

Add RED evidence before the code change, focused GREEN, full direct and isolated
inventory suites, all-zero write/check, reconciliation/static gates, and append a
report section. Analyzer/discovery only; all existing safety and scope constraints
remain binding.
