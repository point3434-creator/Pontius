# Representative blueprint workload execution protocol

This prospectively completes the r002 design, without executing it. ADR-0515 opens
implementation and finite correctness controls only. A later invocation decision
binds this protocol, the exact source seal and its concrete source/runtime/input
manifest. No command in this document is authorization to measure now.

## Commands, identities and phase separation

The single public tool is `tools/v0a_blueprint_workload.py`. Its fixed modes are
`qualify`, `run`, `read` and internal `worker`; no arbitrary executable, code,
module, population size, sample count or threshold option. Public arguments are
absolute `--source-root`, `--run-root` and, for qualify/run, `--authorization`.
The authorization is a byte-bound document named by the later accepted invocation
decision, not an arbitrary user-created file accepted for having the right shape.
`worker` additionally names a cell ID already present in the frozen plan and may
only be launched by the controller's one admitted invocation. `read` is read-only.

The staged invocation claims one absent D-local run root before population work,
retains an exclusive creation marker, and never reuses a previous root or cell ID.
It freezes actual interpreter/venv identities, executable hashes, version output,
source commit/tree/raw file manifest, protocol digest and environment first.
Qualify produces the exact r002 corpus, structural checks, artifacts and case plan;
run verifies that retained qualification and executes the predetermined cells.
The authorization may bind the qualification recipe before derived input digests
exist; it must specify this two-stage derivation. The derived manifest is retained
and locked before the first measured worker. A refusal consumes the admitted stage
and closes measurement; no new seed search, resume or replacement successful run.

Actual interpreter order is CPython 3.11.15 at
`D:/Pontius-tools/py311/Scripts/python.exe`, then CPython 3.14.6 at
`D:/Pontius/.venv/Scripts/python.exe`. Record the redirector and resolved runtime
identities; refuse a missing or different version. Freeze these actual hashes at
invocation admission, before population construction, never after seeing timings.
Use `-B -P`, snapshot cwd, `PYTHONPATH=<snapshot>/src`, separate TEMP/TMP, and absolute
native `PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe` (record canonical Windows form).
Allow only required Windows/venv environment entries; strip inherited GIT_*,
PYTHON* and PONTIUS_* values before installing the declared ones.

Run from fresh non-reparse D-local exact-source snapshots. The protected B population
is every B-tracked path under src/, tools/, tests/ and .github/, plus B's root
pyproject.toml. Preserve all those raw blobs outside the six declared exceptions;
admit only the nine new code/control/fixture paths in source-contract.md. Root/tool
inventories and protected package incoming-edge checks refuse extra Python origins.
Bind the complete executed snapshot to the exact source-seal/invocation commit and
its raw tree manifest, including every document. B's historical metadata remains
unchanged except generated STATUS.md; that file and additive decision documents
must match the exact authorized opening/seal/invocation commits, not B's old front
door. No unbound exemption for governance files. Recheck the
complete admitted raw source/input manifest before and after each worker, including
HEAD, file/handle/ancestor identities. Execute captured verified tool bytes only.
The ordinary session performs its own unchanged repeated source/input validation.
No profiling, allocation tracing, concurrent tests, review scans or sync during
unprofiled timing. Fresh process/object does not imply a cold filesystem cache.

## Population, artifacts and deterministic order

Use r002's exact 8,192 table trajectories and 1,152 independent query trajectories,
seeds, stacks, policies, legal history bins and 256-action trajectory stop.
Qualification has a separate 1,800-second wall envelope, including native cleanup
requests; retain its actual costs. No full-population timing result comes from it.
Stream reference records in table chunks of 256 trajectories and query chunks of
128 trajectories, preserving the declared ordinal and within-hand action order.
Every research artifact has a 128 MiB maximum; oversize is a retained qualification
refusal. Keep individual chunks separate instead of creating one unbounded file.

Serialize passive entry objects with the unchanged artifact codec and fixed source
ID `workload-r002-passive`. Codec output sorts entries by canonical key; table
membership remains the prescribed interleaved witness prefix. Use those ordered
members for N_fit, never reinterpret the codec's sort order as population order.
Encoded length is the empty root length plus every serialized row and inter-row
comma. Check the derived length against full codec bytes for every requested size,
N_fit and N_fit+1; the last must exceed 1,048,576 bytes. Freeze source digest,
artifact SHA-256, per-key canonical byte totals and cached canonical table length
as distinct fields. Report the full row census by street and disjoint bins
0, 3-5, 7-9, 15-17, 31-33, and other, including empty categories.

Query order is deal, controlled seat, stack profile, lineup, strategy, then action
ordinal, with each factor in the r002 listed order. Table-witness selection uses
trajectory/action order within the prescribed interleaving. Diagnostic hits must
belong to N_fit; choose the first 100 distinct eligible contexts per bin. A bin
with no N_fit hit remains uncovered; natural traffic and required structural query
coverage are reported independently. The source census freezes every selected
context ID, expected key/action/digest/hit value and full reference transcript.

Build the unique size union once. The 3.11 order is 0 and N_fit construction/memory,
Part 1 history diagnostics, Part 2 reuse, Part 3 sessions, then Part 4's remaining
ascending sizes and legacy/prepared comparisons. A size shared with N_fit is one
cell with two labels. The 3.14 order is 0/N_fit/8,192 construction/memory (unique,
in that order), history bins 0/31-33, H=1/8 reuse, then its fixed session subset.

## Direct workers and timing records

Run one fresh process per construction observation, memory observation and reuse
arm/group. Separate five construction, five traced-memory and five untraced-memory
workers for each requested interpreter/unique-size cell. For construction, record
read, codec decode/admission, prepared-provider construction and first proposal,
and one outer read-start through first-proposal interval. Measure canonical source
serialization and SHA-256 of retained canonical bytes separately afterwards; they
are independent diagnostics, not an additive decomposition of preparation.
The initial observation is the first controlled query context in frozen order.

Traced workers construct the admitted source plus prepared provider after starting
tracemalloc. Raw artifact bytes and that first observation already exist; list their
ownership explicitly as excluded from incremental Python allocations but included
in process memory. Untraced workers record idle, after read, after decode, after
prepare and after first proposal, with lifetime peaks separately. Sampling runs
from the supervisor, not a timing worker's Python thread. A worker retains source,
provider, raw bytes and first observation through the final memory sample.

History operation order is key construction, hash, prepared-map lookup,
decision identity, full prepared provider; bins are ascending. Each cell uses
r002's five blocks of 20 warmups, 20 batches of 100 and 2,000 individual calls.
For each block, pair hit/miss subblocks as hit, miss, miss, hit. Each subblock
gets 10 warmups, 10 batches and 1,000 individual calls: totals per class remain
20/20/2,000. If one class is empty, retain that missing class and run only the
other's two subblocks. Choose contexts cyclically in the frozen list; reconstruct
prebuilt keys before timing. Batch and individual phases store results for later
validation, with no codec or report write inside their measured intervals.

Record timer metadata, 10,000 empty brackets, five empty 100-call batches and five
100-call loop/result-retention controls before history timings. Keep these controls
unsubtracted. Hash outputs are compared within process; Python hash randomization
must not be confused with the stable SHA-256 key identity. Normal GC stays enabled.
Use the r002 5% bracket sensitivity rule and empirical/batch eligibility labels.

Reuse uses the exact 32 frozen query sequences and H values from r002, taking the
first H sequences for each group. For each H, launch four paired repetitions in
fresh/retained, retained/fresh, retained/fresh, fresh/retained order. Source read
and admission finish before the arm's outer interval; initial preparation is
inside it. Fresh prepares before every hand; retained prepares once and hashes
before every hand including the first. Retain all selections, then validate
action/key/hit/digest parity outside the outer interval. Report inner preparation
and hash intervals plus the outer elapsed total, not their sum. Counters and
retained results have the same lifetime in both arms; report actual query counts.

Legacy/prepared comparisons at 1,024/8,192/65,536 use exactly r002's five blocks,
20 warmups per block and 20/10/2 measured calls per hit and per miss, respectively.
For size N, select the first 100 distinct hit contexts from that prefix's witnesses
and the first 100 distinct misses from the frozen query corpus, each in declared
order. Retain fewer when fewer exist; zero is uncovered. Cycle these fixed lists
continuously across blocks without resetting to the first context each block.
Give both providers the same resulting sequence; construct fresh query objects.
Within a block, alternate hit/miss and alternate provider-first by block parity.
Warmups alternate hit/miss (ten of each) separately for each provider. No legacy
tail distribution is inferred from these small reference denominators.

## Sessions and profile attribution

The session's public arguments are `--session`, `--blueprint`, `--session-id`,
`--strategy`, `--auto`, `--format json`; its report is captured from stdout.
Freeze each complete argv in the plan before timing. No evaluator successor,
quiet flag, output-path option or unsupported session argument is introduced.
The unprofiled controller launches the unchanged session script directly. A
diagnostic worker installs sys.setprofile and executes the same captured session
entry point with identical arguments. Neither route replaces session functions or
changes its own real child command. Include outer launch-to-verified-exit wall for
both, with session-body wall separately for phase closure.

3.11 base case order is deal 0/1, seats 0..5, lineups 0/1, artifacts empty/N_fit,
strategies blueprint/baseline: 96 unprofiled cases. Insert each of the 12 matching
diagnostics immediately before its base case for even diagnostic ordinal, after
for odd ordinal. Eligible diagnostics are deal 0, seats 0/2/3, lineup 0 and both
artifacts/strategies. 3.14 uses deal 0, seats 0/3, lineup 0 and both artifacts/
strategies (eight base cases); only the four loaded counterparts are diagnostic,
with the same even/odd insertion rule. Total 104 unprofiled plus 16 diagnostic.
Each trial is one hand with fresh stacks and identifiers, with no selection by
observed outcome. IDs use fixed prefix plus interpreter/case ordinal within the
existing 40-character session suffix limit.

Profile points bind to these unchanged B files and raw blobs:

```text
tools/v0a_table_session.py  5b0608b74e46a5366d3412a11aa06c850110960e
tools/v0a_table_host.py     7beb178989b3ff98b684093ce4022667a1c61ece
```

Match normalized exact filename and co_qualname. Session points: Admission.__init__,
Admission.check, Schedule.derive, Session.prepare, Session.validate, Session.play_hand,
Session.run. Host points: Source.__init__, Source.check, OwnedInput.check,
ChildConnection.__init__, ChildConnection.send, ChildConnection.receive,
ChildConnection.finish, WireConsumer.ready, WireConsumer.provider_expected,
WireConsumer.decision, WireConsumer.settlement, WireConsumer.exchange,
WireConsumer.complete, Table.start_event, Table.next_event. Categories and nested
initialization precedence are exactly r002's table. Session.run supplies the outer
orchestration span; time outside it is residual. Reduce ordered raw call/return
events by deepest eligible category, closing every selected span. A path-specific
method may legitimately have zero calls (for example a strategy-specific check);
require all applicable entry/exit pairs and never invent a missing duration.

Profile inflation uses paired outer wall. Phase percentages use the corresponding
diagnostic outer wall, with startup/outside-body residual included, so the exclusive
sum closes to that same denominator. Above 25% inflation invalidates quantitative
dominance eligibility. Main-thread wall phases include waiting and cannot be summed
with child ledger compute. Missing spans, negative durations or nonclosing totals
invalidate attribution. No guessed distribution of the residual.

Decode the raw child stdout retained in each host hand result through the accepted
wire/result schema. Join ledger action identity to the frozen controlled decision,
street, history, natural hit/miss and first/later label. For baseline decisions,
retain actual fallback use and table membership separately; a primary baseline
choice is not mislabeled a table hit. First-to-act seat 3 retains its complete
first response elapsed_ns; other seats' preparation is not added to later response
wall. Preserve aggregate preparation, compute/uninstrumented portions, failure
flags and exact observed margins at their original scopes.

## Resource envelope, outputs and interpretation

The measured payload has one 3,600-second envelope across both interpreters from
first measured worker launch to final verified worker exit, including controller
gaps and validations. Qualification, snapshots/reviews and final read-only report
rendering are outside it and separately recorded. All shorter existing session/
child bounds remain. Do not start another cell after a stop or budget expiry.

Use the unchanged host Job abstraction for kill-on-close native ownership. Create
each worker suspended/no-window, assign before resuming, and own its descendants;
ordinary session children retain their own existing containment. Sample direct
worker private commit at least every 100 ms; above 3 GiB requests job termination.
Bind samples to the actual interpreter PID reported by the worker and verified
inside the owned job; the venv redirector PID alone is not the measured process.
Record possible overshoot and separate cleanup time. Timeout, interrupt, capture
overflow and worker failure also terminate owned descendants, preserve raw outputs
and close the census with failed/interrupted/unattempted statuses. Do not delete
failed roots or retry to replace a failure. Observe cleanup independently.

Controller worker captures are limited to 64 MiB stdout and 256 KiB stderr; stop on
overflow and retain the prefix/truncation flag. Existing host child stdout/stderr
limits remain 2 MiB/64 KiB. Structured artifact and per-cell output files are
create-only, LF UTF-8 JSON/JSONL with 128 MiB per file. Stream large populations and
samples in the frozen chunks; a limit refusal is not silently split after failure.
For every cell retain intent, argv/environment/source/input digests, raw outputs,
exit/cleanup, timing units, observation counts and explicit terminal status. A
top-level manifest hashes every retained file; raw binary captures keep exact bytes.

The report applies all r002 rules without refitting: 1,400 ms first-to-act warning,
N_fit below 8,192, eligible phase at least 50% and 100 ms in two diagnostics,
H=8 median reuse saving at least 10 ms and 20% with all four pairs positive,
instrument-eligible miss p95 at least 1 ms, byte-work R above 1.25 (with separate
sorting proxy), and N_fit peak private commit at least 512 MiB. Use integer ns/bytes
for recorded observations; preserve units and compute nearest-rank percentiles
only at the specified sample sizes. Report inconclusive conditions and all triggered
rules. Give naturally weighted traffic separately from diagnostics and each
interpreter separately. An invalid or incomplete input cannot yield a clean report.
