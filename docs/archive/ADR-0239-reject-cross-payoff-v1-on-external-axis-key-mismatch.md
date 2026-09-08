# ADR-0239: Reject cross-payoff v1 on external-axis key mismatch

- Status: rejected execution; no coefficient or timing result accepted
- Date: 2026-08-22
- Implements: ADR-0238
- Clean preregistration commit: `65b811a`
- Result artifact: none

## Failure

The single ADR-0238 invocation validated its frozen hashes, runtime, source and
capacity parents, reconstructed the tight continuation target, ran one warm
step, built the 31 retained endpoints and their zero-contraction own rows, and
entered the cross-payoff matrix stage. It completed the first acting seat's
four source-profile passes, then rejected while constructing that seat's first
opponent fixed-response tape:

```text
ValueError: fixed response node probability shape differs
```

The response-splice primitive used `layout.nodes[node].information_keys`.
Continuation layouts retain the embedded full-game hand-key axis, while the
bound posterior context supplies a separate external 32-hand axis. The
accepted leaf-adjoint paths already resolve information keys against the
external axes; the new helper did not. Its h4 control used identical embedded
and external axes and therefore could not expose the mismatch.

Partial device work occurred before the rejection, but no matrix completed and
no result path was written. No coefficient comparison, complete timing sample,
memory decision, certificate, quality row, strategy label, generated policy,
or emission occurred. All process state and partial timings are rejected.

## Decision

Reject v1 as evidence. Preserve ADR-0238's algebra, single tight target, 24+30
pass workload, teacher comparison, numerical ceilings, wall ledger, promotion
rule, and claims boundary.

Authorize one external-axis-only successor. Its response splice must require
the explicit `hands_by_player` tuple, reconstruct each key with the accepted
`_information_key(layout, player, hand, node.history)` helper, and validate the
source row shape against that external axis. Add a mutation control in which
the embedded layout and external axes differ. The successor must use a new
config, runner, primitive, test, result path, and clean commit; it may not reuse
any v1 process state.
