# ADR-0257: Preregister label-blind Latin-E replication with global barrier

- Status: accepted corrective preregistration before any remaining Latin-E final label
- Date: 2026-08-22
- Follows: ADR-0255 and ADR-0256
- Config: `experiments/configs/h32-fresh-convex-retreat-replication-v2.json`
- Config SHA-256: `2cc2feadaf065a106ffb382f91f70a4ee46f75fef10be044a39703dad38923fc`
- Runner SHA-256: `063db8b71ecea1cfe13895ad496f6d631897b64b837852273c70dae1c98105fd`
- Control SHA-256: `281d603f6de125c3e5b275d707bef120dbe405844966cfc133164fa802937a9d`

## Question

Can ADR-0255's frozen six-target half-retreat campaign execute without
misclassifying verified resident-row LP residuals as missing response facets,
and does its preregistered material-value branch pass after every candidate is
frozen behind a campaign-wide label barrier?

This is a label-blind correction, not a redesign. ADR-0256 identified the
failure using only target 2's construction-oracle rows. Target 1's final label
was computed twice by the failed and debugger invocations but was never
printed, persisted, inspected, or available to this correction. Its v2 value
must be described as a deterministic label-blind reconstruction, not as a
never-computed label. Targets 2–6 retain unopened final retreat labels.

## Frozen scientific design

Preserve every substantive ADR-0255 choice byte-for-byte:

- the six Latin-E target identities and manifest order;
- one target per source, observed bettor, and last-responder acting seat;
- no opportunity, TV, value, position, or prior-outcome selection;
- one charged resident warm step per target;
- the 512-information-set, 1,024-policy-variable, six-epigraph one-seat master;
- normalized guard `1e-10` and raw guard `3e-9` derived only from payoff span;
- LP and projection tolerance `1e-10`, epigraph allowance `1e-9`, cap allowance
  `2e-11`, and quality allowance `1e-10`;
- all newly exposed opponent response facets added in one multi-cut round, at
  most one resolve, fixed retreat factor `0.5`, and exactly two all-seat oracles
  per target;
- exact final cap, positive-value, `1.48e-9` interior-slack, measured-ledger,
  and effective-conservative-ledger acceptance;
- strict material value above `0.001`, at least four of six material targets,
  both range families, and all schedules fit before Latin-F can be separately
  preregistered; and
- immutable external blueprint, zero candidate emissions, zero Latin-F labels,
  null population claim, and null global-optimality claim.

No first-target value or status is present in the v2 config. No result from any
target can alter any later candidate or the promotion threshold.

## Corrected response classification

The first exact oracle still marks every seat whose raw gain exceeds its master
epigraph by more than `1e-9`. For each marked seat, classify by response
identity before deciding whether to generate work.

For an opponent whose exact response signature is new, extract the same exact
open-axis row and add it to the multi-cut. For an opponent whose signature is
already resident, evaluate that resident row at the candidate and require:

- absolute resident-row-to-oracle gain error at most `2e-11`; and
- exact gain minus master epigraph at most the unchanged verified master primal
  ceiling, `1e-8`.

Record such a row as a resident response residual and do not duplicate it. For
the acting seat, the own-BR invariance identity makes its single gain row
authoritative even if an equal-valued best-response tie changes the diagnostic
action signature; apply the same two numerical gates.

Fail unless every oracle-marked seat is accounted for by exactly one of these
classes and every genuinely new opponent signature is cut. A mismatched
resident row or residual above `1e-8` still aborts before the final label. This
does not widen a scientific tolerance: `1e-8` was already ADR-0255's frozen and
verified master primal ceiling. It only prevents the stricter cut-discovery
threshold from asking for a row that is provably already in the master.

## Campaign-wide label barrier

Strengthen execution order without changing a candidate:

1. reconstruct target 1, perform its warm step, build rows, solve, run its first
   construction oracle, classify/generate rows, resolve at most once, form its
   half-retreat, pass every prelabel check, and freeze the candidate;
2. release that GPU context and repeat for targets 2–6;
3. verify that all six barriers are at `candidate_frozen`, each construction
   reports zero final strategy labels, and the campaign event is
   `all_candidates_frozen`; only then
4. run the six independent final retreat certificates in the original target
   order.

This campaign barrier ensures that another new-position construction defect
cannot consume earlier final labels. Candidate policies and affine profile rows
are small CPU objects; do not retain six 5.6-GB device contexts.

For each final certificate, reconstruct the pinned target context, then require
the source checkpoint, posterior, blueprint, retreat policy, payoff span,
source-gain vector, and cap vector to reproduce before opening the oracle. Time
that reconstruction and report it separately. It is excluded from the 15-second
live ledger because a live decision retains the resident context continuously;
the reconstruction exists only to implement the development campaign's global
barrier under finite GPU memory. The final oracle's complete measured time
remains charged exactly once.

## Ledgers and authority

The live ledger remains warm step + eleven initial rows + master solve(s) +
first construction oracle + new cut extraction + final retreat oracle + the
50-ms retreat/envelope floor + 1,000-ms emission reserve. The effective
conservative total remains the larger of measured live time and
`13,967.6157 ms`. Both must fit 15 seconds for shadow acceptance.

Cold candidate setup and certificate-context reconstruction are measured and
gated below 120 seconds each but are not live components. Pool total must stay
at or below 12 GB and physical free memory at or above 1 GB. Total campaign
time must stay below 1,200 seconds.

The independent factor-`0.5` retreat oracle remains the sole safety and final
quality authority. The construction oracle is adaptive within its target only.
The bounded one-round endpoint still has no complete-separation, certified-gap,
or global one-seat-optimality claim.

## Promotion and claims boundary

Apply ADR-0255's promotion branch without adjustment. If at least four accepted
retreats each exceed `0.001`, both range families occur among them, and every
schedule fits, authorize only a separately preregistered Latin-F confirmation.
Otherwise retain ADR-0252's known-target evidence and leave Latin-F unopened.

A clean v2 artifact may report a six-target label-blind shadow measurement and
the exact target-level outcomes. It cannot erase ADR-0256's target-1 caveat or
claim population performance, full-game safety, multi-seat composition,
cross-street validity, deployment strength, global optimality, or broad poker
quality.

## Decision

Commit ADR-0256, the corrected runner, v2 config, controls, this ADR, roadmap,
and generated status from one clean tree. Run the entire CPU suite. Only then
invoke v2 once, audit the artifact against every frozen gate, and seal the
promotion or rejection branch before any Latin-F work.
