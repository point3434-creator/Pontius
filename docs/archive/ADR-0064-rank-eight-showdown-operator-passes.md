# ADR-0064: Rank-eight showdown operator passes the strategic screen

**Status:** Implemented; every frozen gate passed

**Date:** 2026-08-19

## Result and provenance

The ADR-0063 screen decomposed the 64 distinct six-player terminal payoff types
for balanced and blocker-heavy full Cartesian axes at four and five hands per
seat. It evaluated six fixed caps plus an untruncated control. The four-hand
root slice crossed two exact belief mixture sizes and three policies, producing
28 spectral rows and 84 root-strategic rows.

The frozen configuration SHA-256 is
`65f500e3366494730fd6d73744b7735df15e52e12d4e7c92654ee4e27561cf35`.
The result is
`experiments/results/showdown-value-operator-rank-screen-v1.json`, SHA-256
`718aa8217dd2c39fcfa91efe7755eb78712a6cdd4f6049ac869e06d7a3a34a3c`.
It ran from clean commit
`1dcc5076fcd3b7ed40618b6dba0dcf9c368bc835` in 35.913 seconds.
All 357 tests passed in 52.978 seconds before the frozen run.

## Exactness controls

Every exact control passed:

- terminal grouping plus compatible-deal gathering error: exactly `0.0`;
- literal terminal-override strategic error: exactly `0.0`;
- literal override action mismatches: `0`;
- untruncated maximum operator error: `6.91092e-11`;
- untruncated maximum root-strategic error: `6.66134e-14`;
- untruncated response-action mismatches: `0`; and
- zero-sum projection error for every arm: exactly `0.0`.

The untruncated operator error is Float64 SVD reconstruction noise and remains
below the frozen `1e-10` gate. Its negligible root effect and action identity
validate the terminal-override measurement path.

## Rank result

| Arm | Max operator error | Max normalized root error | Action mismatches | Four-hand storage ratio | Verdict |
|---|---:|---:|---:|---:|---|
| rank 1 | `33.2762` | `0.205944` | 2,347 | `0.00586` | reject |
| rank 2 | `28.9295` | `0.107654` | 487 | `0.01953` | reject |
| rank 4 | `28.6982` | `0.009702` | 7 | `0.07031` | reject |
| rank 8 | `6.95e-11` | `2.23e-15` | 0 | `0.19531` | **pass** |
| rank 16 | `6.95e-11` | `2.21e-15` | 0 | `0.63281` | storage reject |
| rank 32 | `6.91e-11` | `2.19e-15` | 0 | `1.13281` | rank/storage reject |
| untruncated | `6.91e-11` | `2.22e-15` | 0 | `2.13281` | exact control |

Rank 8 is the sole frozen safe arm. Across both four-hand families, the first
five players' 64 dense operators occupy 10,485,760 bytes. The conservative
fixed-cap TT layout occupies 2,048,000 bytes, a `5.12x` reduction. At five
hands, it occupies 2,790,400 bytes versus 40,000,000 dense bytes, a `14.33x`
reduction.

This is not a lucky root cancellation. Rank 8 reconstructs the entire payoff
operator to SVD roundoff. Measured maximum numerical TT ranks are:

- four-hand balanced: `(1, 4, 5, 5, 5, 4, 1)`;
- four-hand blocker-heavy: `(1, 4, 4, 7, 5, 3, 1)`; and
- five-hand families: `(1, 5, 7, 6, 6, 4, 1)`.

The cap therefore exceeds every measured numerical bond rank. The storage
accounting is conservative because fixed rank-8 cores retain numerically zero
directions that an operator-specific exact-rank layout could omit.

## The rank-four cliff

Rank 4 appears attractive by tensor error and storage alone but is
strategically unsafe. It flips responses in three of twelve root cases:

- balanced, three-component, hashed-dense: one flip;
- blocker-heavy, one-component, uniform: five flips; and
- blocker-heavy, one-component, hashed-pure: one flip and `0.009702`
  payoff-normalized root error.

The aggregate seven flips are small compared with rank 1, but one is enough to
reject the arm. This directly supports the project's rule that Frobenius error
or average leaf error cannot select a representation rank.

## Interpretation

The signed showdown operator is low rank on these axes because it is a structured
winner-comparison function, while many player/contender operators are constant.
Median numerical bond rank is one; only operators involving relevant contenders
need the larger state.

Rank 8 is evidence for the representation family, not yet for online latency or
full-range rank. The screen reconstructs dense tensors to obtain exact labels.
Real boards can expose many more distinct hand-strength levels; winner-comparison
rank may grow with those levels. Independent per-terminal TTs also ignore
sharing across contender sets and public histories.

## Direct contraction design

Advance rank 8 to an exact factor–TT contraction gate. Split six seats `3+3` as
in ADR-0061. For one TT payoff operator:

1. contract the first three TT cores for every compatible left-half assignment,
   producing a vector at the middle TT bond;
2. contract the last three cores backward for every compatible right-half
   assignment;
3. multiply those vectors by each nonnegative belief component's unary partial
   weight;
4. accumulate right features, now of size
   `mixture_components * middle_rank`, under every used-card subset;
5. inclusion-exclusion query the vector compatible with each left card mask;
   and
6. sum component-weighted left/right dot products.

This generalizes the proven scalar factor contraction without reconstructing
`h^6`. With three belief components and rank 8, incidence values widen from
three scalar component weights to 24 signed features. The mask topology is
unchanged and can be cached by board/hand axes/split. Report the larger numeric
workspace and Python object overhead honestly.

Only after scalar payoff expectations match explicit enumeration should this
be lifted through public policies and best-response conditional values. Online
fixed-policy value/action contraction and offline all-player certification
remain separate budgets.

## Neural implication

If rank grows on wider boards, the exact spectra still reveal the right neural
inductive bias: encode per-hand strength/blocker features by seat, preserve
permutation-aware contender structure, enforce zero sum, and train root/action
losses. A generic dense joint-range MLP would discard structure that the exact
experiments have now isolated.

## Dissent protocol

**Confidence:** very high in the frozen four-hand strategic result; high in the
five-hand spectral replication; moderate that exact low rank persists on wider
boards; low that Python TT machinery predicts native runtime.

**Opposing evidence:** rank 8's four-hand storage margin is only `0.1953` versus
the frozen `0.25` ceiling, and full-range strength diversity can raise ranks.
Exact compatibility may also dominate direct contraction cost.

**Largest risk:** calling dense-reconstruction compression a latency win before
the factor–TT network is contracted directly.

**Cheapest falsification:** on wider axes and new boards, any response flip at
rank 8, or a direct factor–TT contraction whose incidence width erases the
storage/time advantage over cached MITM or sampling.
