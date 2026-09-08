# ADR-0277: Preregister pre-bet current-node action-width capacity

- Status: accepted label-free preregistration before any h32 pre-bet widened warm step, master, or candidate evaluation
- Date: 2026-08-22
- Follows: ADR-0276
- Reframes: ADR-0237 action-width successor
- Config: `experiments/configs/h32-pre-bet-action-width-capacity-v1.json`
- Config SHA-256: `4ee7f77a84d7638f304dbd7a8c51aea6eb5b6c0e7e9f9adbd0bc6eb4985b760a`
- Runner SHA-256: `db4cd478aaa95cee48fc50e6b75dbc36b1ed3bffe3d630f773c31f08904d2a1b`
- Runner control SHA-256: `4ff24f3bcc3a8f16a0c39cdb5fa751b30302d958faf349d7eb98f059461b6952`
- Sized-continuation primitive SHA-256: `cc05b3701a628a2cbd606f371bc7880037931f13a3c26c8d5505df6f4ed2da2c`
- Sized cross-payoff primitive SHA-256: `44fe8b8800c59ccdec375ba0307e7ca9cebd0e02c89e2f1db5d7b2269dc2aca7`
- Current-node row SHA-256: `b4f1d9e82b2cc2ddf7ce4b64483037e1e5b64e42387923bd8fd0dd1c950b27b0`
- Current-node axis SHA-256: `f1961c3d3c9974954b8c8e419f1e762bacd5b32866a889cfd5459849c1420319`

## Question

At the actual pre-bet decision, can the accepted resident one-seat master widen
the current action set from check/bet `3` to check/bet `3`/bet `6` while
retaining enough memory and 15-second capacity for one complete conservative
cut round and an independent final proof?

This is a label-free capacity experiment. It measures representation and work;
it does not evaluate whether the added size improves strategy quality.

## Scope correction

ADR-0237 named a continuation-root two-size preflight but did not distinguish
where that continuation begins. Rooting after an observed bet would make the
comparison vacuous: the current responder has fold/call in both games, because
the opening size has already been chosen. This preregistration therefore roots
before any bet, after zero through five observed checks. The current actor then
has two one-size actions and three two-size actions.

The full pre-bet continuation can revisit the current actor: that seat may
check, observe a later bet, and act again. Consequently the sufficient
path-single-visit behavioral shortcut used by the post-bet full-seat master is
invalid here. Do not apply it.

Open exactly the current root public node instead. Hold every later policy row
of the acting seat and every opponent row at the embedded immutable blueprint.
Payoff and fixed-response values are affine in this one node's probabilities
even though the remaining tree contains a repeated actor. If play reaches a
later decision, deployment solves that decision afresh. This is a deliberately
narrow live-decision scope, not a claim that the whole repeated-actor
behavioral axis is affine.

## Frozen target inventory

Cross all six retained source blueprints with acting seats `0..5`, in sealed
source order and then seat order, for 36 targets. Condition each target belief
only on the public checks by the earlier seats. Seat 0 uses the source belief
and the empty prefix. The complete CPU-only inventory has SHA-256
`52a847ab3fb3d2e3066ba7dd0808674e66a0bff805df7c9ee1db7820cc5aadf6`;
all 36 target identifiers and belief digests are distinct.

Every current node has 32 external h32 information sets. The one-size arm has
64 policy variables and the two-size arm has 96. The exact continuation
geometry by acting seat is frozen as follows:

| Arm | Public nodes, seats 0..5 | Terminal groups, seats 0..5 |
|---|---|---|
| one size | 385, 321, 257, 193, 129, 65 | 64, 63, 61, 57, 49, 33 |
| two size | 763, 636, 509, 382, 255, 128 | 127, 125, 121, 113, 97, 65 |

The immutable one-size average blueprint is restricted to each continuation.
The two-size bridge preserves check and bet-3 mass, assigns zero source mass to
bet 6, and copies the one-size response policy below each sized bet. All
payoff spans and raw guards must come from the compiled layout; stack is never
used as a span surrogate.

## Frozen arms and cache barrier

For every target compile, separately:

1. the one-size raw resident belief plus six raw automaton caches; and
2. the two-size resident belief plus six accepted scale-canonical affine
   automaton caches.

Record layout, automaton, and device-cache construction time; host and device
persistent numeric bytes; raw-equivalent bytes; logical and stored middle-rank
width; maximum middle rank; logical automata and shared bases; GPU-pool use and
headroom; and physical-device free memory.

Complete the cache-only phase for all 72 arms before any runtime arm begins.
An arm is safe only when pool total is at most `12,000,000,000` bytes, pool-cap
headroom is at least `5,184,456,164` bytes, and physical free memory is at least
the same non-cache reserve. If any arm fails, execute zero h32 warm steps and
stop at the memory result. Do not rescue the campaign by selecting positions
after seeing cache outcomes.

## Conditional runtime work

Only if all 72 caches pass the global barrier, reconstruct every target and
execute exactly one warm resident DCFR step in each arm: 72 steps total, one
per target-arm pair. Warm-start mass is `0.1` times the layout-derived payoff
span. Record numerical warm-start identity and the complete resident work
ledger.

Then compute only the exact embedded-blueprint inputs needed to price the
current-node master:

- six profile-payoff passes;
- five opponent fixed-response-payoff passes;
- six exact source gain rows;
- one current-node restricted master; and
- one projected master policy used only to verify current-node scope.

The acting seat's best-response value remains invariant under its own current-
node edit. Opponent rows keep acting and payoff roles separate. Source values,
gain coefficients, caps, master variables, epigraph values, and lower bounds
must not be serialized.

Constructing the restricted master policy is not permission to evaluate it.
Execute zero master-candidate endpoints, retreats, certificates, or strategy-
quality evaluations. Require every changed policy row to belong to public node
zero, require every later own-policy row to remain byte-for-byte equal to the
blueprint, emit no candidate, and report the immutable one-size blueprint as
the only external policy.

## Frozen capacity proxy

For each arm price one complete conservative cut round as:

```text
one warm step
+ eleven initial row passes
+ first master solve
+ 2 * max(measured source all-seat oracle, measured warm step)
+ measured five-opponent fixed-response row subtotal
+ max(measured first master, 500 ms)
+ 1,250 ms independent final-proof reserve
+ 50 ms retreat/envelope reserve
+ 1,000 ms synchronization/emission reserve
```

The two oracle proxies reserve the first candidate endpoint and the post-cut
endpoint. The added response-row subtotal reserves all five opponent cuts; no
observed active-set sparsity may reduce it. The second-master floor and final
proof are separate. Cold construction is reported but remains outside the
prepared live ledger.

An acting position is admitted only if its two-size proxy fits `15,000 ms` on
all six source blueprints and every process, memory, identity, row, projection,
master, finite, no-label, and immutable-emission gate passes. Report one-size
capacity beside it, but promotion is decided by the two-size arm. A passing
subset of sources within one position cannot authorize anything.

## Controls

The exact sized-continuation control compares empty and check prefixes with
the corresponding full-tree subtrees, including remapped terminals and
topology checks. The cross-payoff control separates acting and payoff roles
and matches raw resident reads and independent dense endpoints. The current-
node row control matches dense endpoints on a repeated-actor topology.

A deliberate off-node contamination changes one later policy row and must
make the local-row prediction disagree with the endpoint teacher. This proves
the scope guard has teeth. A complete h2 resident composition control must
also build both cache arms, warm once, construct all eleven passes and one
master, and confirm that its unevaluated candidate changes only node zero.

Checkpoint every completed target with the byte-truth atomic helper introduced
after ADR-0276. The recorded digest must equal a reread of the persisted bytes;
canonical-text hashes are not accepted as checkpoint identity.

## Decision branches

- **Any cache unsafe:** stop before all warm and master work. Retain the
  accepted one-size live system and the canonical cache only as off-clock
  infrastructure.
- **All caches safe, no position fits:** retain one-size action width. Do not
  infer that bet 6 lacks value.
- **One or more positions fit:** authorize only a separately preregistered
  strategy-quality experiment on those complete positions. The present master
  candidate remains unopened.
- **Any mechanism or process gate fails:** reject the invocation. Do not repair
  its schema, tolerance, target list, reserve, or timing formula after h32 work.

Non-gating prediction: the accepted canonical representation should make all
two-size caches memory-safe, while later acting positions should have more
capacity because their continuation subtrees are smaller. The experiment may
falsify either statement without becoming a failed scientific result.

## Claims boundary

A pass establishes only h32 pre-bet current-node representation, exact affine
row construction at the embedded blueprint, and position-scoped conservative
capacity. It makes no one-size-versus-two-size quality, optimizer-convergence,
direction-obsolescence, deployment-latency, population, multi-seat,
composition, cross-street, chip-EV, AIVAT, full-width, exploitation, or poker-
strength claim. The independent exact certificate remains the only future
emission authority.

## Decision

Commit the primitives, runner, config, controls, this ADR, roadmap, and
generated status from one clean tree. Invoke the frozen h32 runner exactly
once. Do not inspect a master candidate, tune by position, or open a widened
strategy label inside this capacity campaign.
