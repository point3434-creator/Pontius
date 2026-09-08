# Research and engineering results

Reviewed 2026-09-08. Start here for the current conclusions; follow a category
for methods, exceptions, and evidence. These are conclusions from Pontius's
linked local records, not a literature review or a new experiment.

Three maintained views serve different questions:

| View | Use it for |
|---|---|
| **Completed evidence — this page** | What Pontius actually measured, with seven linked family summaries. |
| [Brainstorming](brainstorming.md) | Ideas from both external research folders, their revisions, and what remains hypothetical. |
| [Research roadmap](research-roadmap.md) | How ideas connect to completed evidence, ranked next experiments, and the practical bot track. |

**Overall:** the research has produced useful reduced-game solvers, exact
evaluators, certified local improvements, adaptive bet menus, and accelerated
representation primitives. The bot and measurement harness provide working
integration paths. The evidence reviewed here does **not** yet establish a
strong full-game multiway policy or a complete full-width resolver that acts
within the live clock.

## Choose a question

| What do you need to know? | Category | Strongest supported conclusion / main limit |
|---|---|---|
| Which solver updates and leaf estimates work? | [Solver foundations](solver-foundations.md) | Rankings depend on game and budget. Exact-leaf controls expose resolver harm; low on-policy error alone does not make replacement safe. |
| When does additional search improve a policy? | [Safe search and scheduling](safe-search.md) | Exact certification with fallback retains useful reduced-game improvements. A small river scheduler transferred; h32 convex candidates have positive evidence, but one-round optimality and deadline fit are not universal. |
| Can we evaluate candidates more cheaply? | [Exact evaluation and reuse](exact-evaluation.md) | Dependency structure and reuse preserve tested values and decisions while reducing cost. Compilation and cache lifetime determine whether the complete decision benefits. |
| Which legal bet sizes should we retain? | [Action abstraction](action-abstraction.md) | A context-dependent three-raise menu recovered at least **97.23%** of available aggregate gain on 16 fresh qualified h4 river contexts. This does not select a global ladder or prove full-game transfer. |
| Can accelerated representations handle larger ranges? | [GPU solving and card representation](gpu-representation.md) | Reduced-game acceleration and a literal-45-card contraction primitive passed. Complete legal-context full-width resolving remains unestablished; later time projections failed and compiled calibration was incomplete. |
| What can the bot actually do, and what do game results mean? | [Bot integration and validation](bot-validation.md) | Legal runtime, replay, codec, and paired evaluation paths work within their tested scope. The fixed-policy comparison used only two deals and cannot establish strength. |
| What limits blueprint lookup and benchmarking? | [Blueprint representation and runtime cost](blueprint-performance.md) | Tested warm decisions are cheap. History-key size limits capacity; repeated preparation is a measured opportunity. The persistent-worker harness removed repeated startup verification. |

## Conclusions across categories

1. **Keep the reusable research capability.** Exact teachers, independent
   evaluators, legal game models, codecs, and accelerated primitives let us
   distinguish policy improvement from implementation error. Their value is
   demonstrated more broadly than any claim that the current bot is strong.
2. **Safe useful candidates and optimal solutions are different outcomes.**
   Positive certified h32 retreats survived cases where endpoint closure failed.
   Likewise, a lower aggregate NashConv does not guarantee every player improves
   or that coordinated opponents are covered. Preserve the objective and scope.
3. **Small adaptive choices can work; fixed shortcuts often failed transfer.**
   The fresh width-three sizing result is encouraging. Earlier recovery gates,
   leaf-risk rules, and a density-only skip rule failed for distinct reasons.
   Favorable reduced-game results still need new-game and live-path validation.
4. **Amortization is a recurring measured opportunity.** Tape compilation,
   resident GPU data, and blueprint preparation all benefit from reuse in
   specific workloads. The shared requirement is a valid lifetime, honest
   invalidation, and timing that includes setup and fallback.
5. **Fit, correctness, quality, and elapsed time must stay separate.** A
   full-card-domain primitive can pass while a legal-context consumer remains
   too expensive. An experiment can also fail administratively while its
   retained scientific payload supports a narrower, separately stated finding.

The [research roadmap](research-roadmap.md) now combines these findings with the
external brainstorming. It prioritizes a terminal semantic differential and
fixed-fold reuse study alongside a small trained-policy deployment bridge and
fresh deal/opponent evaluation. These are proposed priorities, not completed
results; the roadmap holds the detailed ordering and prerequisites.

## Keep this reference useful

Update the relevant category in the same work that produces a meaningful result,
correction, or implementation change affecting its claims. Include the question,
method/population, finding, limitation, source/run links, and review date. Preserve
negative and interrupted outcomes; do not overwrite an old failure with a later
success. Change this index only when the broader conclusion or priority changes.
Update the brainstorming status and roadmap when evidence resolves an idea or
changes the next useful experiment; external proposals remain labeled as such.
The [README working rules](../README.md#working-rules) make this a completion step;
there is no new automation, schema, approval document, or per-cell record.

| Need a particular record? | Location |
|---|---|
| Recent run completion, failure, or source identity | [Execution journal](../execution_journal.jsonl) |
| Latest operational summary | [Generated STATUS](../STATUS.md) |
| Original EXP-0001–0021 narrative and earlier harvests | [Archived historical ledger](../docs/archive/experiment-results-through-2026-09-08.md) |
| Original experiment/decision details | Linked from each category; retained under `docs/archive/` and the original report/artifact locations |

Coverage is a selective synthesis of the major result chains, not a file-by-file
audit of all experiments. Each category states its evidence boundary. Some raw
files are present, some are machine-local, and some are known only through
historical reports; availability and verification are stated where relevant.
No new experiments were run for this consolidation. Supporting data and code
were not deleted, and historical process instructions remain historical.

## Follow-on cleanup — 2026-09-08

This is the compact cleanup record; detailed test attempts, including failures,
live in the [execution journal](../execution_journal.jsonl). Findings and
recovery references follow below. No historical research or GPU campaign was
rerun. All unchanged tracked originals retired in these batches are recoverable
at `91f031e91c957a9b273c2ccc345421f7b286b416`; individual experiment sources
are cited with their findings. Ignored raw measurements need separate retention.

| Completed batch | Retirement and preservation | Net Python lines removed |
|---|---|---:|
| Historical-result tests and inventory | 20 fixed-result assertion tests, obsolete inventory test, and backup generator retired; evidence files and behavioral APIs retained | 2,520 |
| Experiment drivers | Three h32 drivers and tests, leaf-adjoint GPU audit/config test, actual-45 projection launcher/runner retired; eight projection behavioral checks retained | 4,595 |
| Isolated audits | Eight drivers and eight dedicated tests retired; 49-module bot/benchmark closure retained; three reusable tensor suites added | 6,529 |
| Mixed helper and staging copies | Factor-TT audit/test and two exact committed staging duplicates retired; tensor fixture moved into its consumer test | 1,875 |
| Root helper relocation | 59 previously uncommitted originals moved intact into the archive for checkpoint recovery; no deletion or code change | 0 |
| Root research launchers | Six launchers and selective-separation runner retired, including 16 obsolete lifecycle/admission test methods; seven separation controls retained | 708 |
| Device wrappers | Four runners and two fixed-width wrapper test modules retired, including 40 wrapper/admission methods; 20 shared-direct controls retained | 3,980 |
| Fixed-width fixture extraction | Final fixed-width runner retired; fixture moved into existing test; 15 behavioral controls retained | 677 |
| Original shared-direct runners | Original device launcher and artifact-capacity runner retired; shared fixtures and ten capacity arithmetic/reader controls retained | 758 runner lines |

**Original shared-direct launch:** did the public module entry point reach the
device experiment? At source `468fddf035add619a79c898dc4692dbe7b75b488`,
the Python module invocation exited 1 with `ModuleNotFoundError: No module named
'pontius'`. It produced no journal, bootstrap handshake, compiler/device work,
or numerical/capacity result; the prospective v1 JSONL is absent.
[Launch-failure report](../docs/archive/ADR-0421-retain-the-shared-direct-public-launch-failure.md).

**Shared-direct artifact capacity:** could the measured endpoints support a
larger validation run within its 180-second allowance? Source
`e0662641f0ff1d59e2576425ceab27d678ce3e6a` conservatively projected
**4,999.486743986 seconds** from recorded 10-/22-population endpoints and
rejected capacity. This is a projection, not measured 25-/45-population
performance. The [retained artifact](../artifacts/work_preflight/legal_river_quotient_shared_direct_artifact_capacity_v1.json)
has a documented checkout newline difference (9,183 local bytes versus 9,182
Git-blob bytes); canonical Git SHA-256 is
`9e6e3d45797eb9aeea8e91994f67e7ff641747a80a8d240799adfab1325961af`.
Arithmetic and the independent reader remain reusable.
[Capacity-rejection report](../docs/archive/ADR-0432-retain-the-shared-direct-artifact-capacity-rejection.md).

Latest completed verification covers **44 maintained suites / 552 cases**:
Python 3.11 **541 passed, 11 skipped**; Python 3.14 **542 passed, 10 skipped**.
Ten skips require optional SciPy; the additional 3.11 population case requires
`math.fma`. Separately, all three affected sparse-contraction cases passed in a
SciPy-enabled 3.14 environment. The last import scan covered 855 Python files;
no imports of the 40 retired library modules remained. Ruff name/import checks,
whitespace, 223 maintained local links, and generated STATUS passed. Broader
lint still flags retained test formatting; this is not a repository-wide lint pass.
Current inventory: 452 library, 386 test, 17 tool Python files; no root scripts.
These are CPU behavioral checks, not GPU throughput, live latency, or strength
measurements. Optional GPU suites remain without a claim that CPU runs cover them.

The checkpoint review found a worker-report race: stderr drained during cleanup
could leave a successful status despite errors. A deterministic regression
failed before the fix and passed afterward; final classification now considers
the drained errors. The follow-up review found no remaining issue in that fix.
The checkpoint includes the archived helper originals and journal-referenced
outputs/runtime metadata with their bytes preserved. Large work folders and
machine-local input corpora remain outside it; intermediate development source
digests are identities, not complete source snapshots.

### Experiment-driver cleanup

The h32 and leaf-adjoint findings remain in [Safe search](safe-search.md) and
[GPU representation](gpu-representation.md); configs, raw results, reusable
solvers, and projection arithmetic remain. Obsolete source-seal/uninvoked-owner
assertions were removed. The initial projection check exposed archived-source
and absent-result requirements; the initial restricted Windows runs failed
native trace-handle access and passed outside that sandbox. Failed attempts
remain in the journal. The native-simplex corrected assessment was already
absent locally, as stated in the action-abstraction summary.

## Harvests before retiring isolated audit drivers — 2026-09-08

These paragraphs preserve the question, method, outcome, and source for the
following one-off runs. The cited commits resolve locally. Their historical
JSONs are absent from this checkout, so the findings below are taken from the
archived reports, not newly checked raw measurements. The failed original
profiler produced no artifact. No configurations or result files are deleted.

**Public-tree quotient:** can shared public structure reproduce ordinary
evaluation more cheaply? The audit compared uniform, hashed-dense, and
hashed-pure policies on 19 disjoint/stress games, giving 57 exact profile
comparisons across several range families. Every correctness gate passed;
maximum ordinary-traversal disagreement was `2.13163e-14`, with zero response
action mismatches. This establishes the tested public-tree representation,
not a scalable full-width private-card operator. Source
`810166ae74132c2934ebc1dab8fa86538c1ca6fd`;
[report](../docs/archive/ADR-0060-public-tree-quotient-passes.md).

**Fixed-policy root tensor train:** can one compressed root tensor represent
complete public policies? The audit composed six-player policies through a
385-node river tree and compared them with an independent dense oracle on
four-/seven-hand axes. Exact controls passed, but rank caps 8, 16, and 32 all
missed the utility-error gate; maximum normalized errors were `0.0104775`,
`0.00304670`, and `0.000634182`, respectively. Higher caps also missed storage
economics. This rejected the fixed-cap representation, not the exact algebra.
Source `a41f1e17c8ed7fe0028d60c195e68a1b70606cf0`;
[report](../docs/archive/ADR-0068-public-policy-root-tt-rejected.md).

**Incremental policy-delta tensor cache:** does recomputing only changed nodes
and ancestors make candidate evaluation worthwhile? The audit compared guarded
incremental updates with cold/dense controls on four-/seven-hand axes and
several policy-edit patterns. Correctness passed, including exactly zero
incremental-versus-cold root error and no wrong signs among 120 tested utility
deltas. Four-use pooled speedup was `0.99181×`, failing the timing gate; both
seven-hand cases reached only `0.92×`. These are fixed-policy utility results,
not multiplayer safety certificates. Source
`a5cbd3696132dd380c91ecdf931b08f78de6dcd6`;
[report](../docs/archive/ADR-0070-policy-delta-tt-correct-four-reuse-rejected.md).

**Leaf-adjoint best-response evaluation:** does the dense-free evaluator recover
exact values and reveal useful policy improvement? Eight h4/h7 controls compared
utilities, best responses, and NashConv with dense evaluation; the worst
NashConv error was `7.11e-15`. On the two h32 families, step-two average-policy
NashConv fell from `14.6881`/`14.6288` to `4.16070`/`4.17056`. The CPU/GPU seat
comparisons reported speedups of `4.650×`/`4.407×`, including operator upload. These are
reduced-game results, not a general policy-strength or live-deadline claim.
Source `c1f3d2290f854461e97a29c1e2bac56138d75dde`;
[report](../docs/archive/ADR-0088-dense-free-nashconv-passes-two-step-policy-improves.md).

**Resident CFR semantic-identity rerun:** does the resident speedup survive
fresh trajectories compared numerically? The v2 driver reran the original
four-target workload in both orders with its h7 control. All successor gates
passed: pooled two-step speedup was `3.274×` marginal and `2.728×` including
cache construction, with maximum policy disagreement `8.275e-16`. None of
eight independently accumulated state digests matched; byte identity remains
unsupported. Source `9db362e197a69b0a2633e79672f6255979578891`;
[report](../docs/archive/ADR-0120-resident-cfr-is-the-wide-two-step-engine.md).

**Sustained resident execution and restart:** does the solver remain stable
through eight iterations, and what does restoring a checkpoint preserve? Four
trajectories matched numerical teachers and achieved `3.201×` marginal /
`3.052×` cache-charged speedups, but the sustained audit failed five bitwise
restart gates. The correction restored two pristine solvers from one canonical
checkpoint: immediate state/current/average identities matched, while subsequent
execution passed numerical and quality comparisons without bitwise equality.
The original failure remains a failure, and the corrected restart scope is
one target through iteration eight. Sources
`e4338736a038b221fe3b6533113e0929a33b2d28` and
`34e5991f5169921defcc26ededf4dbf72d71df0c`;
[sustained report](../docs/archive/ADR-0122-sustained-resident-cfr-is-stable-but-not-bitwise-deterministic.md),
[restart report](../docs/archive/ADR-0124-resident-cfr-restores-exactly-and-continues-equivalently.md).

**Original resident-step profiler:** which execution stages dominate a step?
The planned comparison used two retained timing-extreme targets and three
restarts each, but initialization failed with `KeyError: 'gates'` while reading
a parent pass flag. No target reconstruction, GPU replay, timing, or result
artifact occurred. This is an infrastructure failure, not performance evidence;
the later corrected profiler's measurements are separate. Source
`a28b3f2ce13b14ed068c95a5d3a8eed873d42df2`;
[report](../docs/archive/ADR-0196-resident-step-profile-v1-rejects-before-replay-on-parent-pass-key.md).

### Reusable capabilities kept from these families

| Capability for future experiments | Existing behavioral tests |
|---|---|
| [Public-tree tensor evaluator](../src/pontius/public_tree_tensor.py): shared public structure with exact profile and response evaluation | [Public-tree comparisons](../tests/test_public_tree_tensor.py) |
| [Public-policy tensor algebra](../src/pontius/public_policy_tt.py): compose policy values and compare with a dense oracle | [Public-policy comparisons](../tests/test_public_policy_tt.py) |
| [Incremental policy tensor cache](../src/pontius/incremental_policy_tt.py): update changed nodes and their ancestors | [Incremental/cold/dense comparisons](../tests/test_incremental_policy_tt.py) |
| [Leaf-adjoint evaluation](../src/pontius/leaf_adjoint_evaluation.py): utilities and best responses without dense joint tables | [Leaf-adjoint comparisons](../tests/test_leaf_adjoint_evaluation.py); optional SciPy |
| [Resident CFR](../src/pontius/resident_leaf_adjoint_cfr.py): solver updates with reusable device data | [Resident comparisons](../tests/test_resident_leaf_adjoint_cfr.py); optional CUDA |
| [Axis CFR checkpoints](../src/pontius/axis_cfr_checkpoint.py): serialize and restore reusable solver state | [Checkpoint tests](../tests/test_axis_cfr_checkpoint.py) |

The first three suites joined the maintained manifest before retirement.
Checkpoint-ladder and resident-audit helpers remain where retained callers need
them. The factor-contraction fixture was subsequently separated as described
below; an audit name alone is not grounds to delete its dependencies.

## Mixed-helper and root-staging cleanup — 2026-09-08

**Direct factor–tensor-train audit:** can an exact factorized card belief be
contracted with a signed tensor operator without materializing the dense joint
tensors? The audit compared direct contraction with reconstructed tensors and
enumerated joint controls across its fixed size/range/operator ladder. Maximum
direct-versus-reconstructed expectation error was `3.38e-14`; every frozen gate
passed. At ten hands per seat, pooled hot medians were `6.300 ms` direct versus
`1556.741 ms` enumerated (`247.12×`), excluding topology and belief compilation.
Rank eight was insufficient for exactness on the seven-hand extension, so this
does not establish a universal rank or live-decision speedup. Source
`2001743a64132768ff4f7cc454c08cfebaf8127e`;
[report](../docs/archive/ADR-0066-direct-factor-tt-contraction-passes.md).
The recorded `factor-tt-direct-contraction-audit-v1.json` is absent locally;
these are archived-report findings, not a rerun. The audit driver and its
frozen-workload tests were retired only after their synthetic tensor fixture
and existing determinism check moved to the consuming sparse-contraction test.
The reusable contraction implementation and its behavioral tests remain.

**Evaluation staging copies:** were `task1-contract-stage.py` and
`task1-tests-stage.py` independent tools or disposable copies? Direct byte
comparison found they exactly matched `tools/v0a_evaluation_contract.py` and
`tests/test_v0a_evaluation_contract.py` at commit
`bd71f4b11dcc0177283431a4ec468fdc152e7686`. The two untracked root duplicates
were removed; current contract/test files and the exact committed originals
remain. This is a duplicate-file finding, not a new evaluation experiment;
neither staging script was executed.

## Historical root-helper relocation — 2026-09-08

**Question:** can the historical evaluation scaffolding leave the project root
without losing uncommitted originals or disrupting maintained callers?
**Method:** scanned 897 active source, tool, test, CI, and root configuration
files for references to the 59 helper filenames; found none. Moved the 43
evaluation-process helpers and 16 paired-run helpers into
[the historical helper archive](../docs/archive/root-helpers/), preserving
their filenames. **Result:** all 59 before/after SHA-256 comparisons matched;
293,788 bytes and 5,170 lines were preserved. Root Python/PowerShell scripts
fell from 65 to six. No helper was executed, no production or test code changed,
and no new performance or playing-strength measurement was made.

These originals are included in the cleanup checkpoint under
`docs/archive/root-helpers/`; use `git log -- docs/archive/root-helpers/` to
locate their recovery commit. The earlier base
`91f031e91c957a9b273c2ccc345421f7b286b416` does **not** contain them. They retain
old absolute paths, root-relative assumptions, and publication commands and
are historical reference material, not supported entry points. The associated
paired-run findings and committed evaluation source are summarized in
[bot validation](bot-validation.md#evidence-and-recovery); relocating helper
code does not make machine-local raw results recoverable from Git.

## Final root research-launcher harvest — 2026-09-08

The six remaining root launchers are historical run entry points, not reusable
solver implementations. Before retirement, all six matched their Git HEAD
blobs after newline normalization. Their code is recoverable from
`91f031e91c957a9b273c2ccc345421f7b286b416`. The underlying arithmetic,
sample-plan, separation, and evidence-reader modules remain. Historical runner
modules and configs still describe their original commands; those campaigns
must be recovered in their original checkout, not invoked from this cleaned tree.

**Shared-direct device v2:** does the launcher-safe CUDA path produce matching
execution and evidence populations? The population-10 differential reached
evidence assembly, where the execution helper supplied seven sample rows and
the authority expected sixteen (56 versus 128 pairs). The run rejected with
zero accepted population rows; population 22 remained unopened. Source
`db01621604846316693e7dcc3cd52bbc0838da02`;
[report](../docs/archive/ADR-0426-retain-the-v2-population-sample-plan-rejection.md).
This is a sample-plan mismatch, not a measured capacity limit.

**Shared-direct device v3:** does sharing one immutable sample plan correct
that mismatch? Both complete populations 10 and 22 passed numerical, work,
and release controls; their validation walls were 9.348 s and 49.419 s.
Source `00d29e048d88ff4ece325b2a00866ddbd084617c`;
[report](../docs/archive/ADR-0429-retain-the-passing-shared-sample-plan-v3-validation.md).
These are bounded validation campaigns, not full-width decision latencies.

**Fixed-width device preflight v1:** can the positional/RRNS device candidates
reach compilation and numerical controls? NVCC returned 1 because `cl.exe`
was missing from PATH; no cubin or numerical result was produced. Public wall
was 0.820 s. Source `e70f300ccd3aa406d6c6a4493f6a4067222bf9e5`;
[report](../docs/archive/ADR-0442-retain-the-fixed-width-device-compiler-rejection.md).
The compiler setup failed; this does not reject the arithmetic.

**Fixed-width device preflight v2:** does a bound MSVC environment repair that
setup? The child failed its environment check before bootstrap because package
initialization prepended a CUDA runtime directory to PATH. The retained journal
contains zero scientific events, with 2.615 s public wall. Source
`3cf5d1d8f5667f7bf48102ed130f92fce33c9516`;
[report](../docs/archive/ADR-0445-retain-the-msvc-bound-zero-event-infrastructure-rejection.md).
This is an infrastructure failure, not a resource or numerical finding.

**Fixed-width device preflight v3:** does distinguishing compiler and child
runtime environments allow the reduced numerical campaign to complete?
All 42 candidate observations passed on complete-10 and signed-12. Positional
and batched RRNS met symbolic memory eligibility; resident-nine RRNS did not.
Public validation wall was 23.952 s. Source
`f271e6deeefe11f228d582c9734a166c0ba32b45`;
[report](../docs/archive/ADR-0448-retain-the-passing-split-runtime-fixed-width-device-preflight.md).
No candidate was selected and no actual-45 numerical call was made.

**Selective certified separation:** can selective 57-subset pricing and
conservative prefix bounds reproduce exhaustive global search? The archived
source assessment reported nine passing controls across complete-10/12
families, but no one-shot result was opened; the result file remains absent.
[Source assessment](../docs/archive/ADR-0454-source-seal-selective-certified-global-separation.md);
recoverable implementation at `91f031e91c957a9b273c2ccc345421f7b286b416`.
The exact pricing, bound, search, and independent-reader capability remains
with its behavioral tests. No measured pruning or performance result is inferred
from the unexecuted launcher.

The selective-separation runner's only caller was its lifecycle test; its code
is recoverable at the cleanup base above. Seven retained controls cover pricing,
bounds, exhaustive-search agreement, ties, malformed inputs, independent result
reconstruction, and artifact/device-free imports. Initial tests hit an archived
ADR admission path; that guard is removed from behavioral checks and isolated
inside the synthetic fixture. All seven then passed on both runtimes, including
mutated-work-receipt rejection. This does not validate historical source admission.

All five completed device journals remain locally present and their SHA-256s
matched the archived reports before cleanup. None was edited. Launcher-only
probes and current-checkout seals were retired; numerical and synthetic-reader
controls remain. Historical machine-bound environment suites were not rerun.

## Historical device-wrapper retirement — 2026-09-08

**Question/method:** an AST caller walk checked whether the five device runners
contained reusable helpers. Shared-direct v2/v3 had only their own test consumers;
fixed-width v2/v3 wrappers had no external test-helper consumers. **Result:** four
wrappers and two machine-bound wrapper test modules were retired; shared-direct
sample-plan and synthetic-reader controls remain. Their scientific results and
invocation SHAs are in the preceding harvest; all originals also exist at cleanup
base `91f031e91c957a9b273c2ccc345421f7b286b416`. The fifth runner's live
journal-writer fixture was extracted in the following step. Configs are unchanged.

The deleted fixed-width suites included wrapper-specific reader controls as well
as host/runtime checks; inherited numerical controls remain in the original
suite. Fixed-width v2/v3 readers and artifact-bound outcome assessors remain,
with one unresolved limitation: pre-deletion checks of their legacy outcome suites
returned six passes, one failure, and three errors in ten cases because dependency
checks expected `docs/decisions/ADR-0439...` before the archive move. Those suites
are outside the manifest. Their raw-identity/mutation controls remain, but this
cleanup neither repairs nor freshly validates the full historical read paths.

A focused shared-direct run exposed an old source-admission call in the synthetic
cubin fixture. It now extracts the same payload from the retained journal after
checking the journal's recorded byte count/SHA-256 and the payload's own size/hash.
No admission mock is used; the real classifier and readers execute. All 20
retained cases passed on both runtimes; failed attempts remain in the journal.

## Fixed-width synthetic-fixture extraction — 2026-09-08

**Question:** can the final fixed-width runner be retired while keeping its
numerical-reader controls? **Method:** its only importing caller now builds the
journal in memory in the existing test file, retaining the real codec, synthetic
observations, and independent reader. The reader validates the test file's actual
dependency bytes; this does not admit the historical experiment source.
**Result:** complete-success (570,577 bytes) and simulated infrastructure-failure
(4,417 bytes) journals matched the original writer byte for byte before deletion.
The runner is recoverable at `91f031e91c957a9b273c2ccc345421f7b286b416`;
its compiler-rejection finding and experiment SHA are harvested above.

Fifteen behavioral controls entered the manifest. Failure-terminal reading remains
covered; retired writer durability is not claimed. Initial checks exposed a brittle
source-text count and an old capacity admission path. Literal-escape checks now
use small armed/unarmed temporary inputs; population setup isolates only that
historical admission function, leaving real capacity, arithmetic, and representation
calculations active. A further check exposed Python 3.11's missing `math.fma`;
the population test declares this requirement without substitute arithmetic.
All fifteen passed on 3.14; fourteen passed and one skipped on 3.11. Failed attempts
remain in the journal. No library module, persistent fixture file, result artifact,
production arithmetic, or production reader changed. Historical worker names in
journal schemas and dependency inventories remain recovery metadata.

## Root work-folder cleanup — 2026-09-08

**Question:** do the eight remaining work folders and two handoff files contain
research capability or unique findings needed by future work? **Method:** inventory
all 7,402 files, inspect reports/review dispositions and scripts, search maintained
callers, and compare exact file bytes with Git blobs reachable from cleanup
checkpoint `7bdef39b741c5f9968a1187d3c49d3d05b99e915`. **Result:** no live callers
or reusable library implementation needing extraction were found. The folders
hold one-off diagnostics, administrative scripts, source/test staging copies,
review packets, failed development checks, and a virtual-environment bootstrap.

| Retired location | Files | Finding retained |
|---|---:|---|
| `blueprint-design-work/` | 2 | Preparation design/adoption helpers; no measured result |
| `blueprint-implementation-work/` | 67 | Preparation measurements and compatibility are already summarized; adoption `7242891bc8020d33737c3a027ef88d1b65bb2ace`; original failures/helpers preserved |
| `blueprint-workload-as-is/` | 46 | 18/341 cells completed; 883-entry cap result and incomplete-run caveats remain in the blueprint summary |
| `blueprint-workload-opening/` | 41 | Documentation review and staged design revisions; no performance execution |
| `blueprint-workload-review/` | 2 | Design-review bundle explicitly contains no new measurements |
| `blueprint-workload-source/` | 7,211 | Rejected lifecycle reviews and failed/passing development checks; no new research result inferred from test fixtures |
| `bounded-read-work/` | 19 | Adopted 12-trial bounded-read result: 49.2236669 s; report and helper originals retained |
| `performance-pass-20260907/` | 12 | Historical read-cost diagnosis, prototype identity and host-load caveats harvested below |
| Two evaluation handoff files | 2 | Proposed upload inventory/attributes, not evidence of a completed upload |

The additional useful finding is the original 500-file ABBA read probe:
**1.300 s to 0.328 s**, with identical returned bytes/identity tokens, at source
`5845f32f010a44d924abc2f50ae142d1c6adec1b`. Its four 12-trial diagnostic runs
preserved behavior, but the candidate was injected in memory and timing had
run-order/cache/host-load limitations. The [blueprint performance summary](blueprint-performance.md)
now preserves the numbers and the distinction from the later source-bound run.
The r003 workload review's stale qualification budget and pre-ready memory gap
are also summarized there as historical control-flow findings, not measured
deadline or memory excursions.

**Recovery:** [work-folders-2026-09-08.zip](../docs/archive/work-folders-2026-09-08.zip)
preserves 7,309 original files; 93 exact duplicates are recoverable from Git.
The ZIP's `README.txt` explains recovery, and `recovery.json` records all original
paths, byte counts, SHA-256s, and Git blob IDs where applicable. Every recovery
entry was checked against the original bytes before removal. The 222,391,380-byte
working set becomes one 28,019,285-byte archive. External raw-result directories
are not included. No historical script, poker experiment, or GPU run was executed.
