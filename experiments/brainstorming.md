# Brainstorming: ideas, revisions, and open questions

Reviewed 2026-09-08. [Completed evidence](RESULTS.md) · [Priorities and evidence connections](research-roadmap.md)

**The useful direction is a compact baseline policy plus selective search,
supported by trustworthy terminal values and affordable reuse.** The notes offer
several ways to build that system; they do not establish which combination wins.
The strongest new candidate is exact folded-card evaluation with reusable
preparation. Regularization, adaptive actions, and decision-focused continuation
models are separate experiments, not an architecture already selected.

This page consolidates brainstorming in
`C:/Users/point/Documents/Codex/2026-09-05` and `D:/Pontius Research`.
Some notes report disposable mathematical or numerical probes. Those are
**external reported checks**, not adopted Pontius experiments; we did not run
their scripts or reproduce their results. The folders also contain papers and
copies of reports. This is a synthesis of the main report/revision chain, not
independent verification of every paper or supporting log.

## Ideas worth retaining

| Research avenue | Useful proposal | Current interpretation |
|---|---|---|
| Exact multiway terminals | Compute legal card-assignment mass and payouts without materializing every joint deal. Later notes give two six-dealt constructions. | A promising alternative representation for a specific terminal contract. Reported checks do not establish a complete full-deck resolver, its derivatives, or live speed. [Construction review][construction] |
| Folded-card bunching | Retain the card-removal information carried by folded players. Precompute compatibility when their range factors are fixed. | The Sept 8 review makes reuse the missing comparison: two active players with four folded seats need not repeat all six-seat work at every update. Preparation cost, validity lifetime, and strategy impact remain unmeasured in Pontius. [Fresh review][fresh], pp. 6–9 |
| Numerically stable evaluation | Use higher precision for products/moments, positive reference sums, and structured conditioning where legal mass is tiny. | FP32 inputs plus FP64 arithmetic is a candidate, not a universal precision policy. Input quantization and arithmetic error need separate references. Head/tail decomposition alone does not guarantee stability. [Construction review][construction]; [round five][round5] |
| Regularized search | Compare a fixed-reference, prior-anchored update with existing CFR-family controls; vary temperature independently of initialization and reference refresh. | A serious comparison arm under imperfect leaves. No established last-iterate quality or memory advantage; exact-leaf and no-search controls remain essential. [Second report][second]; [revised brainstorm][revised] |
| Adaptive legal action menus | Allocate a small menu to the current state; preserve reference mass when splitting or duplicating equivalent actions. | Connects directly to Pontius's width-three result. Invariance is a cheap prerequisite for regularized refinement; actual new sizes still require fresh strategic evaluation. [Second report][second], action-measure discussion |
| Continuation values and refresh | Start from analytic values where useful, learn or sample a residual, and focus accuracy on errors that change decisions or profitable deviations. | Better motivated than training for average value error alone. A leaf model, trustworthy uncertainty measure, and useful refresh rule are still missing. [Follow-up][followup]; [round-three review][review3] |
| Compact trained blueprint | Distill an offline teacher into a policy the bot can load; retain the teacher's ranges, action menu, and continuation convention. | An important deployment bridge. A long-budget teacher with exact terminal utilities is not automatically an equilibrium teacher. Representation and coverage need explicit choices. [Initial report][initial] |
| Opponent uncertainty | Compare complete continuation profiles, latent opponent types, and robust versus expected-payoff objectives. | Preserve type–hand association and information-set consistency. Persistent per-hand types are one model, not universally required. Optimizer temperature is not an estimate of opponent rationality. [Follow-up][followup] |
| Compute allocation and acceleration | Reuse valid computations, batch terminal work, then consider GPU kernels, warm starts, and mixed-fidelity search. | Promising only with a real consumer and measured refresh cadence. Nearby beliefs can suggest a candidate; they do not certify that cached values or policies remain valid. [Round five][round5]; [fresh review][fresh] |

## Corrections that must travel with the ideas

- **Card marginals are insufficient in general.** Two folded-hand distributions
  can have identical single-card marginals but different legal mass after active
  cards are excluded. This refutes sufficiency, not every approximation retaining
  richer pair information. Likewise, multiplying already conditioned marginals
  is not the same as conditioning independent reach factors once.
- **Dealt and active players are different counts.** A folded player stops
  competing for a pot but still occupies cards. Three active plus three folded
  seats still require six dealt factors for exact evaluation. Side-pot
  eligibility must be separate from card participation.
- **The derivative proof was narrowed.** The scalar five-opponent contraction
  argument does not prove that its full Hessian has the same cost. The corrected
  construction uses four-opponent occupation queries or a scalar calculation per
  hero. Those routes must not be credited with a general transpose interface.
- **Precision failures survive the revisions.** The construction review reports
  an unflagged 34.17% relative error in an all-FP32 path, 1.811% in a proposed
  mixed-precision path, and negative mass from a direct FP64 fallback on another
  concentrated case. Later
  repairs address tested families; they do not settle every dense full-deck case.
- **Early timing and architecture tables are hypotheses.** Synthetic 12–19 ms
  routines, estimated GPU multipliers, and proposed online tiers are not complete
  decision timings. Pontius retains its **14,000 ms work cutoff / 15,000 ms action
  boundary**, irrespective of the notes' 30-second framing.
- **Search sensitivity is not strategic harm.** Policy movement, scalar leaf
  RMSE, solver residual, and belief KL each miss relevant distinctions. A
  leaf-to-policy Jacobian is rectangular; policy sensitivity alone is not an
  objective for a safe leaf model. Evaluate the resulting policy independently.
- **Action labels can alter a regularized target.** Duplicating a move should
  not receive extra preference merely because it has more labels. A declared
  reference measure is necessary; chips, pot fractions, and log sizes express
  different priors.

These corrections are recorded across the [revised brainstorm][revised],
[follow-up][followup], [round-three review][review3],
[construction review][construction], and [fresh review][fresh]. Earlier claims
remain recoverable in the source files; they are not current conclusions here.

## How the source chain developed

| Source batch | Contribution and reading guidance |
|---|---|
| Sept 5 initial report and [first additional brainstorm][answer2] | Broad blueprint/search/neural architecture, reuse, action and opponent-model ideas. Read as the starting proposal, with subsequent corrections. |
| Sept 6 [second report][second], [revised brainstorm][revised], and [follow-up][followup] | Sharper regularization experiments, action-measure issue, terminal formulas, and explicit retractions about marginals, safety, and opponent regimes. |
| [Exact-multiway brainstorm][round3] and [round-three review][review3] | Four-/five-hand constructions, precision concerns, and corrections to derivative and decision-sensitivity claims. |
| [Five-way precision brainstorm][round4] and C-only [six-dealt construction review][construction] | Two constructive six-dealt routes; retained-output obstruction; concentrated-range numerical failures. |
| [Six-dealt precision and tiering][round5] | Additional reported dense 14-card checks: all 91 hero hands for strict wins, eight for ties, eight for ties with three folded opponents. This is not dense full-deck six-hand certification. Online/offline tiers remain proposals. |
| D-only [Sept 8 fresh review][fresh] | Prioritizes fixed-fold compilation, semantic/precision controls, and strategy-level bunching tests. Its author explicitly did not reproduce the contraction or GPU work; its recommendations are conditional. |

The 27 document paths shared by both research trees were byte-identical when
compared. They count once, not as corroboration. The two second-answer filename
variants in D: are duplicate copies; so are the two “novel research” PDFs. The
C-only construction review and D-only standalone revisions were both included.
The PDF-only reports were read through text extraction; their source PDFs remain
the references. Supporting probe outputs were not promoted to project results.

For an implementation reference, b-inary's Rust postflop solver documents exact
combination counting for up to four folded players. Its API also documents
increased terminal cost when bunching is enabled. That makes it useful source
material for semantics and data lifetime, without establishing our proposed
river compiler's speed or recommending a dependency migration.
[Official documentation](https://b-inary.github.io/postflop_solver/postflop_solver/)
and [bunching API](https://b-inary.github.io/postflop_solver/postflop_solver/struct.PostFlopGame.html#method.set_bunching_effect).

## Maintenance

Update this page when an idea is added, corrected, tested, or retired. Keep
reported external checks separate from Pontius findings. When a project
experiment resolves an idea, link its family summary and update the
[roadmap](research-roadmap.md); preserve the original hypothesis and any failed
version. External paths are machine-local; these summaries preserve the useful
conclusions, while detailed reproduction still depends on those source files.

[initial]: <C:/Users/point/Documents/Codex/2026-09-05/deep-research-plugin-deep-research-work/work/report-source.md>
[second]: <C:/Users/point/Documents/Codex/2026-09-05/deep-research-plugin-deep-research-work/work/second-review/report-source.md>
[followup]: <C:/Users/point/Documents/Codex/2026-09-05/deep-research-plugin-deep-research-work/outputs/six-max-follow-up-notes-2026-09-06.md>
[review3]: <C:/Users/point/Documents/Codex/2026-09-05/deep-research-plugin-deep-research-work/outputs/six-max-round3-review-and-fiveway-extension-2026-09-06.md>
[construction]: <C:/Users/point/Documents/Codex/2026-09-05/deep-research-plugin-deep-research-work/outputs/six-max-round4-review-six-dealt-construction-2026-09-06.md>
[answer2]: <D:/Pontius Research/six-max-30s-second-answer-2026-09-06.md>
[revised]: <D:/Pontius Research/six-max-revised-paper-brainstorm-2026-09-06.md>
[round3]: <D:/Pontius Research/six-max-round3-exact-multiway-brainstorm-2026-09-06.md>
[round4]: <D:/Pontius Research/six-max-round4-fiveway-precision-brainstorm-2026-09-06.md>
[round5]: <D:/Pontius Research/six-max-round5-six-dealt-precision-and-tiering-2026-09-06.md>
[fresh]: <D:/Pontius Research/six_max_poker_fresh_review-1.pdf>
