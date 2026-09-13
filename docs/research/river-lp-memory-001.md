# River LP memory diagnostic 001

Both expanded deep-stack cells finished Python matrix assembly, SciPy conversion,
and native model loading below the 3072 MiB sampled limit. Their large memory
increase and stop occurred inside the first HiGHS native run() call. Copies are
measurable overhead, but the larger increase is native solve-time memory. This
locates an API boundary; it does not isolate presolve, simplex, or factorization.

## Frozen comparison

Reuse case 1 from river-tree-expansion-001: pot 29, effective stack 186, 1081 private
holdings per role and 1070190 compatible ordered deals. Run its successful baseline
control, expanded checkback tree, and tree adding one all-in raise layer. Keep all
payoffs, ranges, action menus, value scaling, LP algorithms/options and certification
unchanged. This is a same-case diagnostic, not a fresh-board strategy comparison.

The per-worker envelope is unchanged: 180 seconds and a 3072 MiB private-memory
stop sampled every 50 ms. Each LP retains highs-ds, 10 seconds, 20000 iterations,
and 1e-9 feasibility tolerances. The observer reads OS private memory at Python
source boundaries and the controller verifies the executing PID. No tracemalloc
or allocation tracing is used. Python line tracing and flushed records add work;
these instrumented times are not suitable for solver-speed comparisons.

## Memory result

First-player LP boundaries, in MiB. Each number is whole-worker memory at that
boundary, not exclusive ownership by the named component. The final column is OS
peak worker commit over the complete process, including both LPs for the baseline.

| Tree | Before linprog | After SciPy conversion | Before native run | Worker peak | Outcome |
|---|---:|---:|---:|---:|---|
| baseline | 289.5 | 434.6 | 558.9 | 2083.0 | Exact prior result |
| checkback | 446.2 | 706.3 | 929.3 | 3333.6 | Memory stop |
| raise | 786.6 | 1277.3 | 1697.8 | 6237.5 | Memory stop |

For checkback and raise, the last flushed marker is immediately before
_highs_wrapper.py:206, run_status = highs.run(). Neither call returned before its
worker was stopped. The native model-loading call at line 193 had returned. Every
observed OS high-water mark up to native run entry was below the sampled limit.
The rise from run entry to recorded worker peak was about 2404 and 4540 MiB.

The successful baseline also shows a large increase across the first native run:
about 1445 MiB in private memory from entry to return. Its two returned policies,
realization plans, payoff hashes and exact certificate equal the previous retained
baseline in both diagnostic attempts. Neither stopped cell has a saved policy or
quality result, and neither is credited as a completed solve.

The input path does make copies. In the checkback case, conversion of inequalities
to COO added about 147 MiB; stacking constraints temporarily added another 148 MiB.
The final CSC conversion reduced current memory. Native coefficient-vector copies
then added about 111 MiB, and passModel added another 112 MiB. Corresponding raise
figures were about 278, 279, 209, and 211 MiB. These are adjacent OS observations,
not allocation ownership proofs. Visible sparse buffers may share storage across
frames and must not be added together as if independent.

Removing copies may help, but this evidence does not establish that copy removal
alone would fit either expanded game. It also does not prove that direct solving
is inherently too costly or that a neural representation is required.

## Instrumentation defect and correction

The original frozen probe reproduced both stops and the exact baseline, but captured
only the outer solve() function. Under the isolated worker import, SciPy code filenames
contained mixed slash styles while the allowlist used resolved Windows paths. The
string comparison silently excluded its frames. The original probe, plan and all
outputs remain unchanged in author/ and run/ and are labeled incomplete evidence.

A separate trace-correction/ copy normalizes both lookup sides with normcase. Its
small LP control runs in the exact isolated import environment and checks all four
SciPy boundary functions. All four fail the original raw-path predicate and match
the corrected predicate. The full-run controller now also requires a native boundary
event. The corrected plan pins this control, the original attempt, and the unchanged
underlying experiment. No game, solver or budget change accompanies this correction.

Both monitor controls detected a 128 MiB allocation and checked sparse-buffer byte
accounting. The corrected retained runs captured 55898 baseline boundary events and
317 in each stopped worker, with PID identity checked for every event. The high
baseline count includes post-solve Python loops; it is not 55898 solver invocations.
Fresh post-run verification checked the marked boundaries, both exact control outputs,
all dependency pins, and all 3081 members of the 37 previous milestones.

The sampled stop is not a hard cap: the raise worker reached about 6.1 GiB before
termination despite the 3 GiB threshold. Neither capacity nor timing is guaranteed
by this monitor. No observations inside the native call were recorded, so presolve,
model transformations, simplex workspace and basis factorization remain unresolved.

Original attempt: 19.749 seconds for three workers.
Corrected attempt: 23.952 seconds for three workers.
These include diagnostic overhead and are retention facts, not performance rankings.
Runtime checked: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0.

Original plan SHA-256:
9952e44850e5a88a414a3b716929129528cfed54cc0711be87c584164fb89076

Corrected plan SHA-256:
1917df22d83f10350e862a5f8e4bf73b1793f7a35bea23a2214ff6ea560e6fbb

## Next decision and retained evidence

The next focused experiment should compare presolve enabled and disabled on these
same cells, retaining the same LP algorithm, matrix, exact acceptance rule and resource
limits. That is a diagnostic comparison, not a proposal to disable presolve permanently.
It can distinguish whether presolve materially changes this native memory boundary;
it cannot by itself isolate every subsequent native allocation. If that comparison
does not offer a practical improvement, reassess formulation or compression rather
than accumulating unmeasured wrapper micro-optimizations. No new run is implied here.

author/analysis.json contains the selected boundaries and adjacent memory changes;
author/verification.json contains independently recomputed boundary checks and the
prior-manifest preservation inventory. Observed SciPy Python sources are copied into
observed-scipy-source/. Complete traces are losslessly gzip-compressed to avoid adding
53 MiB of repetitive baseline text. trace-encoding.json binds the uncompressed sizes
and SHA-256 values, and decompression equality is checked before sealing. Expand a
trace before using a reader expecting the original .jsonl filename. Scratch scripts
retain their original absolute invocation paths; they are evidence, not new entry points.

This is restricted heads-up river research with factorized reached ranges, a limited
action tree, and no joint folded-card marginalization. No six-max playing-strength,
fresh-board generalization or production adoption claim. All 37 earlier milestones
are preserved. No production source was changed; this milestone is not committed or pushed.
