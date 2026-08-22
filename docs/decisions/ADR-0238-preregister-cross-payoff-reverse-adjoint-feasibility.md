# ADR-0238: Preregister cross-payoff reverse-adjoint feasibility

- Status: accepted preregistration before any cross-payoff h32 pass
- Date: 2026-08-22
- Follows: ADR-0237
- Config: `experiments/configs/h32-cross-payoff-adjoint-feasibility-v1.json`
- Config SHA-256: `700da7e0a3e27d3e9e158019308faf0357d99f7a63a945cc800bd0f7b24b02f6`
- Primitive: `src/pontius/cross_payoff_leaf_adjoint.py`
- Primitive SHA-256: `58475dfb7e4b42e814602612758067a146cbef6f5291ee100ec0e35f97944271`
- Implementation: `src/pontius/h32_cross_payoff_adjoint_feasibility.py`
- Implementation SHA-256: `6adceecd2b439378b5c00e377885eaaf254785f597288ce169c7f9fd1fb340d2`
- Primitive control SHA-256: `8bfd6bb650bfb52eb0b9f79b22257246926c3f07949d18189284028fcc2b11cb`
- Runner control SHA-256: `deadb82056cf7711219e9d0b2572578b91f2164f7d65379a6dd22f3e3ed2c4ba`

## Question

ADR-0237 shows that a second fixed direction family is structurally distinct
but cannot fit all retained streets when every ray is priced independently.
Can the accepted leaf-adjoint contraction instead recover the complete local
payoff and gain Jacobian across all 31 continuation blocks at a fixed cost,
accurately and cheaply enough to construct one new certificate-guided
direction inside the 15-second street boundary?

This is an engineering and algebra feasibility question only. It does not ask
whether a generated direction has value.

## Frozen identity

The ordinary CFR leaf adjoint omits the traverser's policy factors and uses the
traverser's payoff automata. The algebra does not require those roles to name
the same seat. For payoff seat `j` and acting seat `i`, use seat `j`'s terminal
payoff automata while omitting seat `i`'s policy factors. The resulting action
numerators are the exact coefficients of `u_j` with respect to every seat-`i`
behavioral row.

For `BR_j`, replace only seat `j`'s source policy by the immutable source best-
response action tape, then repeat the cross-payoff adjoint with seat `i` open.
Within the source selector-stable region this gives the exact coefficient of
`BR_j`. Therefore the gain coefficient is `dBR_j - du_j`. For `i = j`,
`dBR_i = 0` exactly.

The primitive must fail closed on payoff-seat/automaton mismatch, incomplete
response maps, unavailable actions, off-seat leakage, multiple changed public
nodes, and non-mass-preserving policy rows. A deterministic h4 control already
matches the existing selector-stable affine teacher for all six payoff seats
to Float64 rounding under a deliberately large one-node edit. That control is
not h32 evidence.

## Frozen h32 workload

Use exactly the tight retained Latin-D target
`panel_2/balanced/checks_then_bet_seat1`, which had the largest expanded ledger
in ADR-0237. Reconstruct its immutable restricted average-64 blueprint, run
exactly one accepted device-fold continuation DCFR step, and construct the 31
retained regret-vertex endpoints. Generate no second direction and open no
strategy label.

For each acting seat:

1. obtain its own profile-utility coefficient from the accepted zero-
   contraction affine path for each block;
2. run four source-profile cross-payoff passes;
3. infer the fifth opponent profile coefficient from exact six-seat zero-sum;
4. run five opponent-BR-spliced cross-payoff passes; and
5. project every block owned by that acting seat onto the retained action
   tables.

The complete matrix therefore requires exactly 24 cross-profile and 30 fixed-
response passes, independent of the 31-direction library width. Time the 54
passes as one uninterrupted matrix stage before running the charged affine
teacher. Then recompute all `31 × 6 = 186` teacher rows and compare profile,
response, and gain coefficients. Serialize only maximum errors, counts,
timings, memory, and provenance—not coefficient values or quality labels.

## Frozen wall ledger and promotion rule

Price:

```text
one resident continuation warm step
+ complete measured cross-payoff matrix
+ 10 ms deterministic optimizer reserve
+ 10 ms affine-envelope reserve
+ 1,250 ms independent winner-proof reserve
+ 1,000 ms synchronization/emission reserve
```

Authorize a separate label-free safe-cone optimizer prototype only if:

- all 186 profile, response, and gain coefficients match the accepted affine
  teacher within `2e-11`;
- the source utility vector has zero-sum residual at most `2e-11`;
- every structural, provenance, runtime, memory, immutable-emission, and no-
  label gate passes; and
- the complete ledger is at most 15 seconds.

Latency and the comparison with ADR-0237's 31-row baseline are decision
variables, not validity gates. If the matrix is accurate but misses the clock,
retire this complete-matrix live implementation while retaining the exact
cross-payoff identity for off-clock or narrower uses. Do not select fewer
payoff rows after observing timings.

## Claims boundary

The run executes zero certificates, serializes zero quality rows, emits only
the immutable blueprint, and creates no policy from the coefficients. A pass
authorizes only a label-free tiny-LP direction-constructor prototype. It makes
no strategy-quality, deployment, composition, population, or broad poker-
strength claim. No two-player safe-solving theorem is imported into the
six-player envelope.

## Decision

Commit this ADR, config, primitive, implementation, and controls before the
first h32 cross-payoff pass. Run once from that clean preregistration commit and
follow the frozen branch without opening strategy labels.
