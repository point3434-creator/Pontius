# ADR-0510: Preregister the first paired evaluation rehearsal

- Status: accepted rehearsal-only preregistration upon its separately authorized decision commit
- Date: 2026-09-07
- Follows: ADR-0509
- Base-Commit: bd71f4b11dcc0177283431a4ec468fdc152e7686
- Invocation-Authority: none until exact single rehearsal launch authorization
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0510
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Authorize one paired cost rehearsal, then prepare measured evaluation closure
- Front-Door-Blockers: rehearsal unrun; measured operating closure and evaluation invocation unadmitted

## Decision

Preregister one supervised, non-evidentiary cost rehearsal of the exact paired
evaluation source sealed by ADR-0509. The controller asked to proceed toward the
first bounded evaluation. ADR-0482 and ADR-0485 require scaled rehearsal provenance
before freezing operating budgets; source correctness tests do not supply that
authority. This rehearsal is the necessary preparation step, not the evaluation.

The companion contract is docs/architecture/v0a-paired-prereg-r001/preregistration.md.
Its literal rehearsal-request.json fixes the entire synthetic schedule before play.
No source, existing test, fixture, policy, registration or historical decision changes.
The intended subsequent descriptive evaluation has two new deals, these same two
lineups and all six positions: 24 pairs and 48 trials. This is a planning target,
not an admitted population, measured ceiling, scientific sample or invocation grant.
Its fresh seed/request and operating limits require a later measured closure.

This draft has no effect until its exact reviewed decision commit is authorized
and made. The commit alone does not launch anything. Exact approval may expressly
bundle commit/push with the single rehearsal below; otherwise launch needs its own
approval. No generic historical launch authorization transfers to this owner.

## Bootstrap and standing

Prospectively extend ADR-0485's source-seal/rehearsal bootstrap solely to this named
outer paired workflow. Its sealed implementation already exists. The source-only
closures in ADR-0489, ADR-0506, ADR-0508 and ADR-0509 are superseded only to permit
this separately authorized rehearsal. ADR-0482's measure-before-freeze requirement
remains binding. The existing executable correctness namespace and evidentiary=false
remain literal, under external rehearsal-only authority, as the earlier display
exceptions used their external standing. No new machine-enforced authorization
interface is claimed. The unique rehearsal suffix/root cannot authorize a comparison.

The rehearsal request's 360000 ms trial and 9000000 ms shared limits are declared
bootstrap safety settings, not measured operating ceilings or hypothesis gates.
They preserve the accepted 15000 ms action wall, 1000 ms emission reserve and all
inherited host/session limits. A 360000 ms trial allows the inherited 300000 ms
hand interval plus startup/validation allowance; this arithmetic is a reason for
the safety choice, not measurement. Twenty-four full trial-plus-5000 ms reserves
and a 240000 ms preparation/publication allowance total 9000000 ms (150 minutes).
This is not an expected duration, aggregate memory/disk guarantee, hard OS wall or
visibility-by-deadline promise. The operator can stop earlier for resource pressure.
Unknown or missing resource measurements remain unknown and block any later closure
that needs them. No unmeasured setting becomes an operating gate by adoption here.

There is exactly one bootstrap launch opportunity, no automatic successor and no
unattended restart. Its report ends this bootstrap. Failure requires diagnosis and
a new explicit decision, never a reroll, resumed root, larger limit or replacement
arm. The existing two-consecutive-infrastructure-deaths stand-down rule remains
binding. Any operational lane budget is established at measured closure, counts
all later owners including failures and cannot reset on a successor. No operational
owner, calendar budget or campaign is opened by this one preparatory run.

## Exact source and inputs

Execution source: bd71f4b11dcc0177283431a4ec468fdc152e7686.
Whole source tree: 54a257f4f2957696b9d33e7338ce140206a3f578.
Use a fresh D-local --no-hardlinks detached clone, core.autocrlf=false and no overlay.
Verify the complete tracked working tree against raw source blobs before launch.
Retain the clone. The wrapper performs its unchanged continuing source admission.
Important raw SHA-256 bindings:

- tools/v0a_evaluation.py:
  3a041143fb1ef7e0ac84cfb5306d619873fec3f7d8ac0079c791637e113389f5
- tools/v0a_evaluation_contract.py:
  b62170553c20acce17bead44391904c53be43cf0cc59c0fd2fb9b47743e988ad
- tools/v0a_seeded_deals.py:
  d54a6ccca415dd63c59f806f079c587266894a3c84203cda3deda97a9bb0e5bd
- tools/v0a_table_session.py:
  a91464ee5f414342d888bcbc403a1a4de1f81c7e3d912c595cd681258502d19d
- tests/fixtures/table_host/empty_blueprint.json:
  f10540623dcb1a725d60831ca367e0e3f1e519b14ebf68da8f36afa840e45258

The request is exactly the 352 ASCII/LF bytes of the companion JSON, SHA-256:
67af9c6fb677af40937c7640e391bdabcf7f0c27a0a261ac9efdbbf98ddf8359.
It uses the existing all-zero-seed synthetic correctness vector as rehearsal data,
not a fresh evaluation seed or random sample. No entropy, search or card generation
occurs during proposal preparation. Deal index 0, initial button 0, seat_start 0;
lineup 0 is five passive opponents. Lineup 1, clockwise from the controlled seat,
is fold_to_bet, min_raise_once, passive, shove_once, passive. Both are fixed now,
before this rehearsal, for coverage of the already accepted scripts.

One deal x two lineups x six positions gives twelve matched pairs and 24 sessions.
Every pair shares the same cards/input; all six stacks reset to 200, blinds 1/2.
Physical cards and button stay fixed across rotation. Pair order is lineup then
rotation. Even zero-based pairs run baseline-rules-v1 then blueprint-v1; odd pairs
reverse that order. No result or timing observation changes this sequence.

## Single launch and retention

Reserve D:/Pontius/tmp/v0a-paired-rehearsal-run-001 only after exact launch approval
and adoption. It must remain absent through proposal acceptance. Its source/ is the
source checkout, process-temp/ holds TEMP/TMP, request.json is an exact byte copy,
and output/ remains absent until the public wrapper exclusively creates it.
The source, request and output are disjoint siblings. Preserve all other run roots.

Use actual CPython 3.11.15 at D:/Pontius-tools/py311/Scripts/python.exe with -B -P,
source cwd, PYTHONPATH=<source>/src, PYTHONNOUSERSITE=1, PYTHONIOENCODING=utf-8,
and absolute PONTIUS_GIT=C:\Program Files\Git\cmd\git.exe. Scrub the parent environment
except SystemRoot, WINDIR, SystemDrive, COMSPEC, USERPROFILE, APPDATA, LOCALAPPDATA
and those explicit task variables. Verify executable/version/flags/cwd before launch.
The public payload is exactly one invocation; line breaks separate arguments:

```text
-B -P tools/v0a_evaluation.py
--request D:/Pontius/tmp/v0a-paired-rehearsal-run-001/request.json
--output-root D:/Pontius/tmp/v0a-paired-rehearsal-run-001/output
--evaluation-id pontius-v0a-evaluation-v1-correctness-rehearsal-001
```

Create-new the external approval, source/input identities, expanded argv/environment
and launch intent before Popen. Any reservation collision, failed preflight, unknown
launch, interruption or lost supervision consumes this opportunity and stops it.
The operator stays active, retains raw stdout/stderr and actual exit, observes the
existing descendant/cleanup behavior, and never sends poker actions or modifies files.
The wrapper alone generates the synthetic deal and starts its fixed units; no separate
dealer call, warm-up, test run, additional interpreter run or private execution path.

Retain a parent monotonic start immediately before process creation and end after
observed process exit. Capture complete wrapper stdout/stderr with 64 KiB diagnostic
caps each; overflow is an operator stop, retained as incomplete. A consumer read of
the completed root follows at most once after exit, using unchanged read_completed;
measure it separately and never use a marker or exit code as a substitute. This
read-only consumer does not authorize another wrapper invocation. If it refuses,
report the retained attempt as incomplete for publication; do not repair its files.
No pending guard, partial file, intent, snapshot, request or failure is deleted.

## Measurements and interpretation

Retain one cost-only report under the run root, with exact identities, real exits,
completion/refusal state, raw record hashes and scope-labelled measurements. Record
parent launch-through-exit elapsed time, the separate consumer-check duration,
per-unit elapsed_ns prefixes from unchanged unit result.json, file counts and byte
totals after termination. Distinguish source admission, final publication, release,
consumer work and measurement boundaries; prepared result elapsed_ns and per-unit
prefixes do not certify later operations. The companion specifies the coverage map.

Do not print or rank the rehearsal's net chips, pair deltas or aggregate, and do not
use them for a fit, gate, strategy choice, lineup choice, threshold, quality claim or
future population selection. Raw records necessarily retain those fields, with
rehearsal standing; validating their structural consistency is not quality evidence.
No correctness-acceptance or calibrated-performance claim arises from this run.
Rehearsal costs may inform the subsequent measured operating closure only.

The later evaluation, if separately admitted, reports exact chip sums and a rational
mean over all 24 planned pairs, plus declared lineup/seat breakdowns, fallback,
timing and separate failure scopes. A partial matrix has no aggregate. Its two
deals and repeated rotations do not establish significance, a win-rate estimate,
independent-sample count of 24, statistical superiority or playing strength. No
confidence interval, favorable-sign gate or policy selection is designed here.
If resource or identity evidence is inadequate, retain the gap and prepare the
needed bounded work; this rehearsal alone does not clear all operating prerequisites.

## Proposal acceptance

Tier C because rehearsal authority, identity, cost provenance and evidence meaning
are protected. Exactly four documentation/configuration paths change: this ADR,
the companion preregistration.md, rehearsal-request.json and generated STATUS.md.
No application source or existing fixture/test changes. Finalizer: Codex coordinator.
Freeze one immutable candidate and complete two fresh independent CLEAN reviews,
then status --check and all twelve status tests on actual 3.11.15 first and 3.14.6
second, each fresh exact-candidate D-local snapshot with actual-version/module-origin
preflight, scrubbed -B -P, cwd/src and absolute native Git. Independently verify raw
pins, literal request, derived counts, exact scope and reserved run-root absence.
No dealer, poker, evaluation, resource rehearsal or inventory payload runs here.

One initial candidate and at most three within-scope correction rounds; all outcomes
remain retained. The existing residual/root-cause rules bind. A new source change,
expanded execution or exhausted review budget needs its own controller ruling.
After all gates, request the exact decision commit/push and single launch authority.
Neither preparation nor a review ref grants adoption or execution. Full operating,
research, training, H32, league, human play, neural loading, compiled work, analyzer
repair, cleanup and ref retirement remain closed; all prior owners stay consumed.
