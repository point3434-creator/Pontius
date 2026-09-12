# Frozen size-aware river repair baseline

Status: frozen research baseline, recorded 2026-09-12.

Controller instruction: "Let's freeze this then any other tricks for our subgane solver"

This records the confirmed method as a stable comparator for future research.
It does not adopt a production bot policy or authorize a new experiment, commit, or push.
The existing experiment, source snapshots, results, and report remain unchanged.

## Method and domain

- Heads-up river toy game: check, half-pot bet, or pot bet; observed-size call/fold response.
- Pot 10, stacks 20, 96 holdings per role; all compatible deals in each declared case.
- Preference-model grouping with 16 groups per role.
- Retain the incumbent 50,000-update caller policy unchanged.
- Propose one bettor split by strict pot-versus-half-pot value preference against the witness.
- Merge two other groups to keep capacity at 16; select the largest positive net witness gain
  with the frozen deterministic tie rule.
- Train the proposed bettor grouping from scratch for 50,000 updates.
- Accept only if exact full-hand worst-case bettor value is nonworse than the incumbent;
  otherwise retain the incumbent. The 10,000-update checkpoint is diagnostic only.
- Comparator: another 50,000 incumbent bettor updates, with the same acceptance requirement.

The witness proposes a change; the independent worst-case check decides acceptance.
The acceptance gate is part of the baseline, not an optional addition.

## Evidence

[Pilot](river-multibet-size-repair-001.md) and
[fresh-board confirmation](river-multibet-size-confirmation-001.md) retain all outcomes.
Confirmation used eight previously unseen boards, two per texture class, with uniform and
polarized ranges: 16 cases. Thirteen proposals improved and were accepted; three were rejected.
Accepted repair beat accepted continuation in 13 cases and in every board-level mean.

Mean exploitability, in chips (lower is better):

| Incumbent | Accepted repair | Accepted continuation |
|---:|---:|---:|
| 0.02075323124 | 0.01885414193 | 0.02067985756 |

This is a 9.15% reduction versus incumbent and 8.83% versus accepted continuation.
Measured incremental cost including a fresh bettor witness, proposal, training, and gate was
2.162 seconds per case versus 1.913 seconds for continuation plus gate, about 13% more.
Common baseline preparation and diagnostic certification are outside that timing comparison.
These are not equal-time results or measurements of live bot latency.

Confirmation archive: `experiments/river-abstraction-study/multibet-size-confirmation-001/`.
SHA-256 identities:

```text
milestone-manifest.json
3ec8544fa91ccc4566675086689e12359f4f4194a9461bcf6684cc7c9e52bda9
report.md (also the linked confirmation report)
7578f00a5392f1b7d8cbf1751b742c8bc4e46da6361d1612b480e3375b0a2f05
plan.json
8c5b28d1a543744819234afafab9a9822e029e249758c531edd038974d7c784a
```

## Interpretation and stopping point

Evidence supports this guarded one-step method on the declared river cases. It does not establish
six-player strength, earlier-street performance, population-wide poker improvement, or safe
nested live subgame solving. Exact within-case evaluation removes deal-sampling noise for the
declared holdings; eight fresh boards do not exhaust board or range diversity.

Further split variants, caller repair, or repeated repair rounds are not automatic next steps.
Keep this comparator fixed. A new method should answer a distinct question and preserve its own
non-improvements. A useful next question is whether a different regret update reaches the same
certified quality faster with grouping held fixed. Measure residual above the grouping floor,
as well as total exploitability, so a representation limit is not mistaken for slow convergence.
No such follow-up run is launched by this freeze.
