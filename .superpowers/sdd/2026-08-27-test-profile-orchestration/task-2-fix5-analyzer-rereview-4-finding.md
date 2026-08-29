# Task 2 fix round 5 — analyzer scoped rereview 4 finding

Frozen analyzer rereview-3 patch SHA-256:
`727487d8226c37b6cdfea54e84862b01bf417d9bca001958ae685c6c2826d406`
(5,349 bytes).

The context-manager exception-suppression finding is addressed: body raises
remain exceptional successors and are also retained as conservative normal
successors because an unresolved context manager may suppress them.

One Important regression remains. Removing all `ast.With`/`ast.AsyncWith`
handling from `_statements_terminate_without_fallthrough` also makes a body
ending in `return`, `break`, or `continue` appear to fall through, even though
context managers cannot suppress those control transfers. Runtime counting can
therefore include an unreachable following sensitive sink, and helper-return
analysis can append a spurious implicit `None` result.

Required correction: distinguish suppressible exceptional termination from
unsuppressible control transfer. Preserve the normal suppression successor for
body exceptions while retaining terminal classification for `return`, `break`,
and `continue`. Add exact RED/GREEN coverage for the runtime-counting and helper-
return paths, including loop transfer cases needed to lock the contract.

No transaction/I/O, payload, capability, OneDrive, commit, merge, or push work
is authorized in this correction.
