# River tree expansion 001

Question: does direct full-hand LP still give a certified reference at useful cost
when the same reached river states allow betting after a check and one raise response?

Keep four observed actual-pot/equal-stack states, 1081 holdings per role, collision-only
joint ranges, odd-chip ties, Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, and 2^20 value
scaling. The blueprint ranges remain factorized and fallback-heavy.

Three nested menus: baseline (check ends through forced check-back; half/pot bet then
fold/call); checkback (second player can also bet half/pot after check); raise (either
first bettor may face an all-in raise, then fold/call only). Opening sizes are capped
by real effective stacks and deduplicated using engine actions. Only case 1 admits
a raise addition. The other three raise cells explicitly alias their checkback cells.
All 12 declared cells and nine distinct games remain in the census.

Public nodes come from the existing engine. Each private hand has its own realization
flow at every information set. Sparse sequence-form saddle-point LPs optimize both roles;
no private-hand grouping, leaf prediction, or transfer of a policy across the new nodes.
Two LPs per distinct game: maximum 18, each 10 seconds / 20000 iterations, 1e-9 primal
and dual feasibility tolerance. Original weighted binary64 payoffs are scored separately.

Convert each returned realization plan to behavior by normalizing nonnegative child
weights. At zero own reach, use uniform behavior. Round each simplex by largest remainder
to an exact 2^48 grid (stable action-order ties). Paths have at most two choices per role.
Exact integer arithmetic evaluates unrestricted per-role responses by public-tree dynamic
programming; acceptance remains full gap <=1e-8, hence exploitability <=5e-9, normalized
by 10/actual pot. Record quantized behavior and raw LP vectors. Numerical solver success
and the independent certificate are separate outcomes; retain returned policies on timeout
when present, and retain absence/refusal when no policy exists.

Controls before scoring: all four engine trees' nesting and all-in aliasing; every expanded
terminal tested on a win, tie and loss; simplex/zero-reach controls; small-game exact LP and
exhaustive deterministic response enumeration. Full baseline equilibrium-bound intervals
must overlap the preceding corrected reference. Separate verifier processes rebuild every
game and certificate, compare literal rational subgame values, and never optimize.

Each worker/verifier has a 180-second wall stop and sampled 3072 MiB private limit at 50 ms;
this is not a hard Job cap. Use the previously verified direct-interpreter process monitor.
Record setup, assembly, solve, certificate and complete worker costs, both LP statuses,
iterations, structural sizes/nonzeros, and observed process identity/memory. LP algorithms
change from the preceding dense specialized formulation, so the baseline is freshly solved
with the same new implementation. One timing/cell supports capacity observations, not stable
speed ratios. No budget extension, retry, selective replacement, or post-result tuning.

Completion is a census, not necessarily universal certification. Resource or certificate
failure is useful data about this implementation. This remains a restricted river tree:
no other opening sizes, non-all-in raises, re-raises, folded-card joint marginalization,
or multiway solving. Do not interpret changed equilibrium values across trees as win-rate
improvement. Retain outputs and update the existing consolidation; no production adoption.
