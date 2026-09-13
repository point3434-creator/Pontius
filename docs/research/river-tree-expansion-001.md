# River tree expansion 001

The nine-cell direct-solving census completed: seven saved solutions passed exact
verification, while two expanded deep-stack cells were stopped by the sampled memory
limit. All four re-solved baseline controls agree with the earlier corrected equilibrium
bounds. Universal full-range capacity did not pass. All outcomes are retained.

## Design and comparison

Keep the four observed actual-pot states, factorized public-history ranges, all 1081
private holdings per role, and collision-only joint population. Compare three nested
trees using the same sparse sequence-form LP implementation:

1. Baseline: check ends through a forced check-back; half/pot bets face fold or call.
2. Checkback: after the first check, the second player can check or bet half/pot.
3. Raise: add an all-in raise against either player's opening bet, then fold or call.

The engine caps and deduplicates sizes by the real stack. In cases 0, 2 and 3, the
opening size is already all-in, so the raise variant equals checkback. Those three
cells explicitly reuse the identical result; they are not new solves or replications.
There are 12 declared cells and nine distinct games. The deeper case has pot 29,
effective stack 186, opening sizes 14 and 29, and the added raise-to is all-in at 186.

The sparse LP uses realization-flow constraints per hand and public information set,
with payoff value units scaled by 2^20. Returned behavior is normalized and rounded
by largest remainder to an exact 2^48 simplex grid; zero-own-reach nodes use uniform
behavior. The certificate evaluates this explicit policy on the original weighted
binary64 matrices using exact integer best responses, including off-path opportunities.
Gap <=1e-8 remains the acceptance rule (exploitability <=5e-9 normalized chips).

## Observed capacity

Times below include game setup, sparse assembly, both LP calls, policy conversion and
exact certificate. Complete process time additionally includes startup, binding checks
and output retention; separate verification is reported later. One observation per cell.

| Case | Tree | Terminal paths | Compute s | Whole worker s | OS peak commit MiB | Outcome |
|---|---|---:|---:|---:|---:|---|
| 0 | baseline | 3 | 3.126 | 4.591 | 1283.4 | Strict pass |
| 0 | checkback | 5 | 8.486 | 9.981 | 2149.0 | Strict pass |
| 1 | baseline | 5 | 6.182 | 7.668 | 2082.3 | Strict pass |
| 1 | checkback | 9 | not completed | 4.091 | 3331.6 | Memory stop |
| 1 | raise | 17 | not completed | 7.291 | 6236.5 | Memory stop |
| 2 | baseline | 3 | 2.873 | 4.422 | 1256.9 | Strict pass |
| 2 | checkback | 5 | 10.045 | 11.516 | 2161.0 | Strict pass |
| 3 | baseline | 3 | 2.918 | 4.392 | 1268.0 | Strict pass |
| 3 | checkback | 5 | 8.183 | 9.633 | 2122.2 | Strict pass |

The three shallow-stack expanded trees took 8.18-10.05 seconds of compute versus
2.87-3.13 seconds for their controls, with peak worker commit around 2.1 GiB versus
1.2-1.3 GiB. Complete expanded worker times were 9.63-11.52 seconds; this does not
establish live bot latency, which also includes runtime transport and other work.

The deep-stack checkback and raise cells exceeded the 3072 MiB sampled private
memory limit before returning a saved solution. The monitor observed OS peak commit
of 3331.6 and 6236.5 MiB respectively. A 50 ms sampled stop cannot prevent allocation
overshoot and is not a hard Job memory cap. Both workers were killed and their failures
retained; neither receives a policy-quality or completed-solve claim. The receipts do
not isolate assembly, solver conversion or factorization as the responsible allocation.

This compares nested trees under one implementation. The older specialized dense LP
and this generic sparse formulation have different storage and variables; the fresh
baseline controls prevent attributing that implementation change to action expansion.
The memory stops demonstrate a limit of this implementation/envelope, not proof that
direct solving is inherently infeasible or that neural approximation is required.

## Exact strategy results

| Case | Tree | Exploitability | Strict pass |
|---|---|---:|---|
| 0 | baseline | 2.770764272e-15 | Yes |
| 0 | checkback | 8.540129192e-16 | Yes |
| 1 | baseline | 8.374918094e-16 | Yes |
| 2 | baseline | 2.875595541e-16 | Yes |
| 2 | checkback | 8.32774424e-16 | Yes |
| 3 | baseline | 8.023715905e-16 | Yes |
| 3 | checkback | 4.606405156e-16 | Yes |

No scores are imputed for the two stopped cells. The three identical raise aliases
inherit their checkback policies and certificates without new measurements.
Changes in equilibrium values across different trees are not playing-strength gains.

## Verification failure and separate correction

All four initial preflight tests passed, covering actual engine tree nesting/aliasing,
all expanded terminal paths under win/tie/loss, grid normalization and zero own reach,
and small-game sequence-form solving versus exhaustive deterministic responses.

The first separate verifier then failed on every saved case: a deliberately small
private-card subset happened to have no legal joint deals, so every payoff was zero.
The coefficient exponent helper called min() on an empty sequence. This affected the
verification path after full-case scoring, not the saved LPs or full-case certificates.
The failed receipts and original source are retained unchanged under run/ and author/.

A separately copied verifier adds only default=53 to that minimum, choosing denominator
1 when all payoffs are zero. Its regression reproduces the old failure and checks exact
zero lower/upper/value/gap after correction. No positive-matrix formula changes. The
source diff and both digests are in post-verification/. No optimization was rerun.

The corrected verification re-created every full certificate and passed all seven.
It also required each baseline equilibrium interval to overlap the prior reference,
checked 87 engine terminal outcomes, and checked 42 literal rational
subgames. Additional nonzero two-hand subgames enumerated 435 deterministic
responses and matched exact best-response bounds. No verification stage called an LP.

Fourteen completed LP results are saved (two per successful cell). Eighteen calls were
the declared maximum; the two stopped workers provide no retained solver-call status,
so their internal progress is not claimed. Each LP had a 10-second / 20000-iteration
limit and 1e-9 feasibility tolerances. Each worker/verifier had a 180-second stop and
sampled 3072 MiB limit, with observed/executing PID identity checked on completed work.

The original campaign took 78.253 seconds, including the failed first
verification attempts and memory-stopped cells. Corrected verification added
17.669 seconds; it is separate from solve timing. The original receipt's
all_processes_verified=false is preserved and supplemented, not rewritten as passing.

Plan SHA-256: e53d20923332e1a1ca93242580d9b4085228464b3de362376104534a31f6562b

## What to do next

The numerical reference now works beyond check-or-bet on the shallow states, but the
larger deep-stack tree exposes a memory problem. The next bounded diagnostic should
measure matrix assembly, copies/conversions, and solver workspace separately on these
same stopped cells. Then compare one targeted storage or formulation change under the
same game and certificate. Do not widen the envelope or switch to a learned policy just
to hide a preventable memory cost. A resource refusal remains useful evidence.

This remains a restricted heads-up river model: only half/pot opening sizes, one all-in
raise layer, no other raises or re-raises, and no joint folded-card marginalization.
The four states use an early fallback-heavy policy's factorized ranges. No fresh-board
generalization, six-max strength, neural-versus-tabular ranking, or production adoption.
All 36 previous milestones are preserved. No production modules changed, commit or push.
