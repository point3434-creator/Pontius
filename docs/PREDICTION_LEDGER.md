# Prediction Ledger

This ledger freezes prospective forecasts before their outcomes exist. It is
reporting-only: no forecast, probability, score, or resolution may select a
sample, alter a gate, relax a kill criterion, authorize a successor, or enter a
research claim. The ADR chain remains the sole experiment authority.

## Scoring contract

- Forecasts were supplied on 2026-08-24 after ADR-0343 and before the first
  responder-raise or full-width-capacity result.
- Resolve a forecast only from a later committed ADR or an explicitly named
  independent review. Absence of a result leaves it open; it is not a loss.
- Use the literal frozen gate where one is named. Do not reinterpret a failed
  gate from a later systems or quality result.
- Record `won`, `lost`, or `void`. Use `void` only when the project permanently
  abandons the question or the stated comparison becomes impossible without
  changing its meaning.
- The numerical score is the binary Brier loss `(p - y)^2`, where `p` is the
  stated probability and `y` is one for `won` and zero for `lost`. Lower is
  better. Voids and open forecasts are not scored.
- Forecast 1 contains two probabilities and therefore two separately scored
  propositions. Every other numbered forecast is one compound proposition;
  all material conjuncts must hold to win.
- Diagnostics written after a semicolon explain the prediction but are not an
  extra score unless the resolution rule says otherwise.

## Open forecasts

### 1a — Literal full-width preflight fails the clock (80%)

> The full-width preflight fails the clock as-is.

Resolution: `won` if the first frozen literal full-width river capacity
preflight fails its preregistered charged-wall gate; `lost` if it passes that
gate. The forecast also predicts a 10–300x h32 cost and possible VRAM strain;
record those as calibration diagnostics without changing the binary result.

Status: open.

### 1b — Certified truncation becomes the accepted answer (65%)

> The eventual answer isn't brute width, it's certified truncation.

Resolution: `won` if the eventual accepted production full-range route solves
a certified retained support and exactly bounds discarded probability mass as
its primary representation; `lost` if literal full-axis solving is accepted as
the production route without that mechanism. A preflight result alone cannot
resolve this forecast.

Status: open.

### 2 — Responder-raise semantics pass; capacity bites first (70%)

> Sequence form holds; response-row growth is the first binding failure, and
> preparation-bank row prefetch is the accepted recovery.

Resolution: `won` only if the legal responder-raise semantic/sequence-form gate
passes, the first later responder-raise scaling rejection is a frozen capacity
or row-growth gate rather than a semantic/math gate, and the accepted recovery
uses preparation-bank response-row work. Otherwise `lost`; it remains open
until all three events can be judged.

Status: open — ADR-0345 satisfies the first semantic conjunct. The first later
scaling failure and any accepted preparation-bank recovery remain unobserved,
so no Brier score is recorded.

### 3 — First blueprint run is stopped by its watchdog (60%)

> The blueprint's first training run gets caught by its own watchdog inside 48
> hours on a real but repairable abstraction or lattice pathology; the second
> run goes the distance.

Resolution: `won` only if the first sealed training invocation is aborted
within 48 wall-clock hours by the operational slice audit for a subsequently
confirmed repairable defect and the second sealed invocation completes its
frozen run. A plumbing-only abort or an operator stop does not qualify.

Status: open.

### 4 — Polymatrix residual is small and publishable (70%)

> Real six-max self-play approximately decomposes, producing a positive and
> plausibly publishable empirical result.

Resolution: `won` if a preregistered real six-max polymatrix measurement passes
its frozen small-residual criterion and a later independent research review
identifies the measurement as novel, defensible publication material. No
external publication is required or authorized by this ledger.

Status: open.

### 5 — Late-street resolving beats blueprint by at least 10x (75%)

> At real posteriors, certified resolving recovers at least an order of
> magnitude more late-street decision value than blueprint-only play.

Resolution: use only a future preregistered equal-context, equal-unit chip-EV
improvement ratio. `Won` requires a conservative lower bound of at least 10.0
for resolver improvement divided by blueprint improvement under that frozen
definition. NashConv, systems throughput, and unlike games cannot resolve it.

Status: open.

### 6 — Likelihood-native off-tree handling wins, with translation retained (65%)

> The likelihood-native mechanism beats pseudo-harmonic translation on the
> adversarial bake-off, while pseudo-harmonic translation survives as a cheap
> subroutine in the accepted hybrid.

Resolution: `won` only if likelihood-native handling wins the bake-off's frozen
primary conjunct and the accepted successor explicitly retains pseudo-harmonic
translation as a subordinate reuse step.

Status: open.

### 7 — v0a arrives in two weeks and never emits an illegal action (80%)

> v0a plays its first complete hand within two weeks of lane-opening; through
> its first thousand hands the spine emits no illegal action, while two or
> three interface defects are caught by legality revalidation or fallback.

Resolution: lane-opening is ADR-0343 on 2026-08-24, so the first complete v0a
hand must be retained by 2026-09-07 inclusive. `Won` additionally requires
zero illegal emissions in the first retained 1,000 complete hands and two or
three distinct interface defects safely caught by revalidation or fallback.

Status: open.

### 8 — The first alien play is a small sizing discovery (60%)

> Before any strength campaign, v0b finds a non-human geometric-to-stacks bet
> amount whose genuine layer-two value is certified; it initially looks like a
> typo rather than a dramatic bluff.

Resolution: `won` if a pre-strength-campaign committed result identifies an
off-conventional sizing amount and independently certifies positive layer-two
chip value under its frozen comparison. Descriptive novelty alone is not
enough.

Status: open.

### 9 — Certification wins the equal-compute final exam (60%)

> Certified resolving beats uncertified resolving at equal compute because
> fail-closed variance control outweighs the cycles spent on certificates.

Resolution: `won` if the future frozen equal-compute primary strength metric
favors the certified arm under its required uncertainty interval. Systems
results, unequal compute, or mixed chip/NashConv units cannot resolve it.

Status: open.

### 10 — A first lane invocation rejects on plumbing, then passes corrected (85%)

> At least one first frozen invocation in the responder-raise, literal
> full-width-capacity, or blueprint/integration lanes rejects on a plumbing
> gate and a preregistered corrected successor passes. The full-width preflight
> is the forecasted site.

Resolution: `won` when both the typed plumbing rejection and the later
corrected pass are committed for at least one named lane. A semantic,
statistical, quality, or capacity rejection is not plumbing and does not
qualify.

Status: open.
