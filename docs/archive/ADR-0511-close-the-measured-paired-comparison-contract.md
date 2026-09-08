# ADR-0511: Close the measured paired comparison contract

- Status: accepted bounded descriptive comparison contract upon its authorized decision commit
- Date: 2026-09-07
- Follows: ADR-0510
- Base-Commit: dfd5a5c6a9d8aae6cbbae667f9b0716c59362eed
- Invocation-Authority: none until exact single comparison launch authorization
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0511
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Authorize the single 48-trial descriptive paired comparison
- Front-Door-Blockers: comparison unrun; strength and full-evaluation resource evidence absent

## Decision

Retain ADR-0510's completed, non-evidentiary cost rehearsal and close only the
measured operating contract for one descriptive paired comparison. The controller
asked to proceed to this measured decision after the completed rehearsal. The
companion operating-contract.md, cost-basis.json and evaluation-request.json under
docs/architecture/v0a-paired-closure-r001/ are normative with this decision.
No candidate bytes take effect until exact review, acceptance and decision adoption.
Commit approval and launch approval are distinct; exact approval may bundle both.

Prospectively supersede ADR-0489's deferred operational opening and ADR-0508/0509's
source-only prohibition solely for this named comparison under separate launch
authority. ADR-0510's consumed rehearsal stays closed. This is a descriptive local
engineering comparison of two fixed existing policies, not research/strength,
league, real play, training, tuning or an operational opening of other v0a owners.
The unchanged correctness namespace and evidentiary=false remain literal. External
authority permits only the descriptive arithmetic below; no machine-enforced
authorization or research evidentiary status is claimed.

## Retained cost provenance

The sole rehearsal remains at D:/Pontius/tmp/v0a-paired-rehearsal-run-001.
Its cost-report.json SHA256 is
b5ea6a530713d94a23c6670b8881c094e896c76dc8d5f17ece2f47d230ea5d1e;
output-file-inventory.json SHA256 is
9bec9a2d2d6c8fc54462030832a39c8b543c07a8f1d694f80d5f672ac4e85bd0.
The companion cost-basis.json pins thirteen original provenance records. All raw
evidence stays at its retained local paths; no off-machine backup is asserted here.

Observed: 24/24 trials and 12/12 pairs completed; the one public reader passed;
all 24 unit cleanup records report complete. Parent launch-through-exit time was
184.531 seconds, the separate reader 1.016 seconds, and the maximum unit elapsed
prefix 7.891 seconds. Retained output was 137 regular files totaling 466940 bytes.
Parent intervals include supervisor scheduling and up to one second of polling.
Unit elapsed_ns ends before unit result publication. Whole result total_elapsed_ns
also precedes final publication; neither is a complete per-trial or total wall.
No timing subtraction is used to invent disjoint cost attribution.

Rehearsal poker values were not printed, ranked or used for any decision. Costs
alone supply provenance. The earlier source tests retain their correctness standing.
This decision never turns rehearsal completion into correctness or quality evidence.

## Measured choices and their limits

Let T=7.891 s (maximum unit prefix), R=1.016 s (reader interval), W=184.531 s
(whole parent interval), and S=466940 bytes (retained output). Use population
multiplier two and discretionary margin four. The margin is engineering judgment,
not a fitted coefficient, confidence bound or measured worst-case multiplier.

- Trial allowance: round up 4*(T+R) to 10 s = 40 s = 40000 ms. Adding the
  whole reader interval is a conservative proxy allowance for unmeasured unit
  publication; it does not identify or upper-bound that publication interval.
- Shared internal allowance: round up [48*(40+5)+4*(W+R)] to 60 s = 2940 s,
  or 2940000 ms (49 minutes). The inherited 5 s reserve is unchanged. The
  additional term is conservative slack, not a decomposition of measured work.
- External single-reader allowance: round up 2*4*R to 5 s = 10 s.
- Post-termination retained-output acceptance cap: round up 2*4*S to 1 MiB
  = 4194304 bytes. This bounds accepted retained output, not peak disk use.

The comparison population is the already planned twofold expansion: two fresh
deals, the same two lineups, six positions and two arms = 24 pairs/48 trials.
Unpadded linear projections 2*W=369.062 s and 2*S=933880 bytes are planning
estimates only. Different cards can change action counts, runtime and output.
No new-deal worst-case, success probability or complete host-resource guarantee
follows. If these prospective allowances fail, retain the failure; do not enlarge
them to make this owner pass, thin the population or replace a failed arm.

The wrapper enforces its unchanged trial/shared deadline and prelaunch admission.
Shared time starts before deal generation, after source admission. Publication
commits within that deadline; postcommit guard release and CLI return can be later.
No total-source-admission, visibility-by-deadline or hard OS wall is claimed. The
40 s trial can expire before the inherited 300 s hand limit; that is a retained
whole-comparison failure, not permission to censor a long hand and average survivors.
The 15000 ms action wall, 1000 ms emission reserve and native containment are unchanged.

## Resource applicability and lane breakers

ADR-0489 requires naming a missing limit's consumer and protected property. This
fixed CPU-only serial comparison has no model load, training, GPU, concurrency
expansion or resource-performance hypothesis. It preserves the source's finite
input/action/capture limits, native child containment, one-trial-at-a-time launch,
active operator supervision and immediate stop for resource pressure.
No aggregate peak-memory or peak-disk ceiling is asserted or waived: neither is
an acceptance claim of this bounded descriptive operation. Peak process-tree memory,
peak disk and action-latency distributions remain unknown and block any later
consumer that requires them, including the applicable full-evaluation profiles.
If preflight discovers a required host safety limit that this contract cannot
establish, refuse this opportunity; do not treat absence of measurement as zero.

Existing 4 MiB child stdout, 64 KiB child stderr, 2 MiB decoded stdout and other
source schema limits stay unchanged. Observed maximum unit stdout was 26374 bytes
and stderr zero; this is finite coverage, not proof these limits suffice on new cards.
The separate output cap is checked by regular-file inventory after termination,
before descriptive consumption. It neither monitors nor certifies peak occupancy.
Source checkout tracked bytes were 352068715 and stay separate from output and
supervisor diagnostics. All limits and failures retain their actual scope.

Open a lane budget of exactly one operational invocation: the smallest nonzero
allocation, grounded in one completed 24-trial rehearsal and the fixed twofold
work expansion above. This is a policy cap, not an inferred population statistic.
Reservation collision, failed preflight, unknown launch, interruption or failure
spends the opportunity. Completion also exhausts it and requires a written
architecture checkpoint with an explicit park-or-continue ruling before any
successor source seal or owner. There is no automatic second invocation. The
two-consecutive infrastructure/lifecycle/authorization-deaths stand-down remains;
every later admitted owner including failed owners counts and cannot reset history.

## Acceptance and next action

Five paths only: this ADR, operating-contract.md, cost-basis.json,
evaluation-request.json and generated STATUS.md. No source, test, old fixture,
policy, registration, earlier decision or retained artifact changes. Tier C:
measured authority, consumption gates, population, identity and outcome meaning.
Ground truth is the governing contract, raw retained measurements and sealed public
source; calculations and margin choices are explicitly the author's design.
Finalizer: Codex coordinator. Only this comparison waits on this closure.

Freeze one immutable candidate. Obtain two fresh independent CLEAN reviews, then
status --check and twelve status tests on actual 3.11.15 first, then 3.14.6,
each from a fresh exact-candidate D-local snapshot with scrubbed -B -P, cwd/src,
actual version/module-origin probe and absolute native Git. Independently verify
all cost pins, formulas, literal request, source identity and reserved-root absence.
No source or poker correctness tests, dealer, reader, rehearsal or comparison runs
during proposal acceptance. One initial plus at most three within-scope correction
rounds; ordinary residual/root-cause rules apply. Scope expansion needs a ruling.

After acceptance, request exact commit/push and single comparison launch authority.
Retain failure or complete descriptive report afterward; do not issue a favorable
quality verdict. Research ADR-0280 and runtime ADR-0307 stay authoritative. No
strength, full league, real play, H32, neural, GPU, compiled, analyzer, cleanup,
ref retirement, training or historically consumed owner is opened.
