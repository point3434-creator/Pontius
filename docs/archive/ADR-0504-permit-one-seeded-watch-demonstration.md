# ADR-0504: Permit one seeded watch demonstration

- Status: accepted demonstration-only exception upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0503
- Base-Commit: 81187c71c50e83126f7222c053780f8be524d4fa
- Invocation-Authority: none until exact generation-and-session launch authorization
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0504
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Authorize one seeded watch demo; formal operation/research closed
- Front-Door-Blockers: exact demo launch approval pending; formal operating prerequisites open

## Decision

Prospectively permit one separately authorized supervised demonstration that joins
the sealed seeded-deal generator to the sealed watch-first session. Save three
shuffled hands from the exact seed below, then display that schedule once in
automatic text mode. The controller can follow it on a phone without terminal
input. Preserve the existing six-seat setup, passive opponents and empty blueprint.
This is visible product behavior, not correctness acceptance or a strength result.

The proposal has no effect before its exact decision commit is authorized and made.
The commit alone grants no launch. One approval may explicitly name commit/push and
the exact complete generation-and-session sequence; otherwise launch needs its own
approval. Neither a generic historical approval nor the existence of source grants it.

This is a narrow prospective exception to the execution closures in ADR-0489,
ADR-0500 and ADR-0503, and to ADR-0485's operational prerequisites solely for this
named non-evidentiary display. Formal operating, rehearsal, experimental, resource
calibration, training and research prerequisites remain binding. ADR-0501's earlier
fixed demonstration is completed and consumed; this does not repeat its identity.

As in ADR-0501, permit the unchanged executable correctness namespace solely under
this external demonstration authority. Preserve literal IDs, trace modes, fields
and evidentiary=false. A correctness name does not turn this display into a test;
no new machine-enforced scientific authorization interface is claimed or patched.

## Exact source, saved seed and commands

Use source commit 81187c71c50e83126f7222c053780f8be524d4fa in a fresh detached
D-local --no-hardlinks clone with core.autocrlf=false and no overlay. Verify its
entire tracked working tree against raw Git blobs before generation and again
before the session. Retain the snapshot. These snapshot-relative bindings are exact:

- tools/v0a_seeded_deals.py, SHA-256
  d54a6ccca415dd63c59f806f079c587266894a3c84203cda3deda97a9bb0e5bd.
- tools/v0a_table_session.py, SHA-256
  13b98563a92f1d2d78116d4efa2e6d4b15f491d623397166b3b1618e5276ef09.
- tests/fixtures/table_host/empty_blueprint.json, SHA-256
  f10540623dcb1a725d60831ca367e0e3f1e519b14ebf68da8f36afa840e45258.

Reserve only D:/Pontius/tmp/v0a-seeded-watch-run-r001 as the disjoint run root.
It remains absent until exact launch approval and adoption. Its source subdirectory
is the source checkout and cwd; process-temp holds TEMP/TMP. Do not reuse any prior
demo, correctness, experiment, rehearsal, output, owner or lifecycle root.

The one seed was obtained during proposal preparation from a single .NET
RandomNumberGenerator.GetBytes(32) call, before generating or observing any cards:
64544b2c06f1056467f7aff5033eead6f7845ba43ca03afbe4508ca741d249de.
Retain the original seed-selection.json and request.json under
D:/Pontius/tmp/v0a-seeded-watch-opening-r001/. No reroll or outcome-based selection.
The request is exactly these ASCII bytes followed by one LF, with no BOM:

```text
{"hand_count":3,"seed":"64544b2c06f1056467f7aff5033eead6f7845ba43ca03afbe4508ca741d249de","version":"pontius-v0a-seeded-deals-request-v1"}
```

Request size: 139 bytes. Request SHA-256:
83f34fd9bdd0cc3cf066cac4cdba6a623b8479faf78425265babf8a3c743bd4c.
The complete population is fixed by that request and ADR-0502's exact adopted
sha256-counter-fisher-yates-v1 recipe, not chosen from inspected candidate schedules.
No expected cards, winner, action sequence, payout or favorable result is selected.

Use D:/Pontius-tools/py311/Scripts/python.exe, actual CPython 3.11.15, for both
payloads; verify actual implementation/version and -B -P flags before each. Use
absolute PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe, snapshot-root cwd/src,
PYTHONNOUSERSITE=1 and PYTHONIOENCODING=utf-8. Scrub all other parent variables
except SystemRoot, WINDIR, SystemDrive, COMSPEC, USERPROFILE, APPDATA and LOCALAPPDATA.
No GPU, optional packages, network play, preloaded policy or import overlay.

After approval, create-new the root, request and operator records. Copy the exact
request bytes above without re-encoding or regenerating the seed. The first payload:

```text
-B -P tools/v0a_seeded_deals.py
--request D:/Pontius/tmp/v0a-seeded-watch-run-r001/request.json
--output D:/Pontius/tmp/v0a-seeded-watch-run-r001/session.json
```

Retain original stdout receipt, stderr and actual exit. Continue only after exit 0,
one complete canonical LF JSON receipt with the exact sealed schema and version,
status generated, the fixed algorithm/seed/count/request hash, and a regular
non-reparse session.json whose actual byte length and SHA-256 match the receipt.
Require the request still matches its pinned bytes and the output is at most 16384
bytes. Record the generated session's raw hash and size before any session launch.
Do not regenerate output, reroll a seed, inspect results to select another schedule,
or turn a partial output or missing receipt into permission to continue.

The second payload, at most once and only after those checks:

```text
-B -P tools/v0a_table_session.py
--session D:/Pontius/tmp/v0a-seeded-watch-run-r001/session.json
--blueprint
D:/Pontius/tmp/v0a-seeded-watch-run-r001/source/tests/fixtures/table_host/empty_blueprint.json
--session-id pontius-v0a-table-session-v1-correctness-seeded-watch-001
--format text
--auto
```

Line breaks separate arguments for readability; each block is one invocation.
The unchanged public session admission validates all deals before a poker child
launches. Never bypass it or substitute a private host loader. The inherited child
suffixes end in correctness-table-seeded-watch-001-h01, -h02 and -h03.
No generation receipt or seed metadata enters the schedule or policy observation.

Population: exactly three generated deals, six initial 200-chip stacks, blinds 1/2,
initial button 0, Pontius seat 3 and five passive opponents. Completed stacks carry
and the button rotates under the existing session contract. An inherited stop can
end before three completed hands. The empty blueprint uses legal passive fallback;
this demonstration introduces no trained policy or improved decision mechanism.
Text reveals the bot's own cards, current public board, actual actions and results.
Do not publish opponents' private pairs or future boards from the saved schedule.

## Supervision, limits and retained outcomes

One generation attempt followed by at most one session launch; zero retries.
Create-new separate generation/session intent records before starting each payload.
Record approval, adopted decision, exact source/input identities, expanded argv
and environment first. Root reservation or preflight failure, ambiguous launch,
nonzero generation, incomplete capture, interruption or hash drift stops the whole
sequence. Retain every file and prefix; never erase the root to recover another try.
No concurrent attempt, automatic restart or unattended resumption is allowed.

Automatic play means no between-hand keyboard input is required; it does not mean
unattended execution. The operator stays present, relays available terminal output
to the controller, and stops an unresponsive payload. Ctrl+C retains the existing
caller-observable interruption contract. If the relay fails or supervision is lost,
stop the process tree and record an incomplete operator stop, not accepted completion.
Never send poker actions or edit the schedule, opponents, policy or source mid-run.

The generator retains its 1024-byte request, 16384-byte session and 4096-byte receipt
bounds. Preserve the existing 15000 ms action wall and 1000 ms emission reserve,
256 actions/events per hand, 60-second exchange wait within 300-second hand deadline,
2 MiB child stdout/64 KiB stderr per hand, 4096-byte text lines and 4 MiB session text.
Inherited failures, partial captures and native cleanup retain their exact meanings.
These are source limits, not measured operating ceilings or a whole-session wall.
Blocked output is not covered by a newly claimed hard deadline. No aggregate disk,
process-tree memory or whole-session watchdog guarantee is introduced.

Retain raw generation output, saved request/session, all operator records, available
terminal output, actual exits and a final disposition. Label decoded/normalized or
incomplete captures honestly. Completion, early stop, interruption, failure and
unknown launch remain distinct. Do not rerun to improve the display or recover logs.
No measured cost, throughput, randomness quality, strategic strength, comparison,
ranking, policy selection, fit or tuning data may be inferred or reused from it.
Report an exposed defect; any fix needs a separate bounded source/correctness task.

## Proposal acceptance and closure

Exactly this new ADR and generated STATUS change. No source, tests, fixtures,
registration, workflow, sealed blueprint or historical decision bytes change.
Freeze one immutable Tier C candidate; obtain two independent fresh CLEAN reviews,
then run unchanged status --check and all twelve status tests on actual 3.11.15
first, then 3.14.6 in fresh exact-candidate D-local snapshots with the accepted
scrubbed -B -P procedure. Verify raw source pins, exact request and run-root absence.
Metadata gates perform no seeded generation or poker and grant no launch authority.
One initial proposal and at most one bounded correction; stop before a third round.

After review and gates, request exact decision commit/push and launch approval,
explicitly naming the complete single generation-plus-three-hand display if bundled.
The exception ends after this attempt. Additional schedules, demonstrations, humans
playing actions, rebuys, seat elimination, operating use, calibration, training,
self-play, league evaluation, H32, campaign, compiled work and analyzer repair stay
closed. All consumed owners and parked lanes retain their standing. No cleanup or
ref retirement. The next product or formal operating task remains a separate choice.
