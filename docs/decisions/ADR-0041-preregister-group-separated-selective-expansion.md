# ADR-0041: Preregister group-separated selective-expansion opportunity

**Status:** Accepted — evidence completed by ADR-0042

**Date:** 2026-08-19

## Question

Does the per-target action-width opportunity observed on the one-board pilot
survive fresh development boards after source blueprint quality is controlled?

This experiment measures whether adaptive branching is worth a later causal
selector. It does not fit that selector, authorize exact-label no-op decisions,
select a native layout, or make a multiplayer claim.

## Frozen configuration

The machine-readable configuration is
`experiments/configs/river-selective-expansion-development-v1.json`.
Its canonical JSON SHA-256 is
`3740d5a9ae9293eb71bdc3a6491cf6b5e22d40289918534755c0a414ce46e3d9`.

It freezes:

- generator seed `20261007`, twelve candidate board groups, four range
  families, and development split only;
- four hands per player and the full `0.25P/0.50P/0.75P` by
  `1.50P/2.00P` action universe;
- the nested `b1r1`, `b2r1`, `b3r1`, and `b3r2` expansion chain from ADR-0039;
- source DCFR checkpoints 512, 1,024, 2,048, and 4,096;
- a maximum source NashConv/payoff-span ratio of `1e-5`;
- online DCFR with the single fixed pseudo-regret mass
  `0.1 * payoff_span`;
- work budgets equivalent to 4, 8, 16, 32, and 64 full-tree iterations;
- two support-preserving 1%-TV blocker reweights and one factorized likelihood
  update per context; and
- exact hashes of `selective_tree.py` and `river_selective.py` so the tested
  expansion and completion semantics cannot change silently.

The first source checkpoint satisfying the normalized quality threshold is the
blueprint for that context. If no checkpoint passes, the blueprint-strength
gate fails and no action-width conclusion may pass, even if candidates are
still emitted for diagnosis. Offline source construction and its exact quality
checks are reported but not charged differently across masks.

## Information boundary

Every target has a dedicated `boundary_online_features` object constructed
before target best responses or candidate labels are evaluated. Only the
following feature families are allowed:

1. source river context and range geometry;
2. target river context and range geometry;
3. target-minus-source context changes;
4. the known probability-delta geometry; and
5. public-action occupancy and entropy under the fixed blueprint and current
   target range.

Feature names containing `nash`, `exploit`, `best_response`, `future`, `gain`,
`label`, `reduction`, or `oracle` are forbidden. Source blueprint quality is
offline provenance, not an online feature. Target blueprint NashConv and all
candidate evaluations remain in label fields only.

Every solver checkpoint may additionally record a timed
`solver_probe_features` object containing only its current regret aggregates
and policy movement. These features must be collected before full-game
candidate evaluation. Their time is reported separately and must be charged by
any later scheduler that uses them.

The selection-free analysis fixes `b1r1` at work budget 4 as the paid probe and
budget 32 as the primary future opportunity target. It may rank individual
features by Spearman correlation but may not fit, choose, or evaluate a rule on
the same artifact.

## Primary metric

For every target at full-tree-equivalent budget 32:

- `full+no-op = max(0, reduction from b3r2)`;
- `mask-oracle+no-op = max(0, maximum reduction across all four masks)`; and
- opportunity is the sum of `mask-oracle+no-op - full+no-op`.

Exact full-game NashConv supplies these labels. All masks use the same source
blueprint, target range, warm strength, and deterministic state-work budget.
The oracle is explicitly undeployable.

## Preregistered gates

The opportunity result passes only if all of the following hold:

1. at least five development board groups are generated and no validation or
   test context is materialized;
2. every selected source blueprint has normalized NashConv at most `1e-5`;
3. every ADR-0039 structural, full-mask, schema, and policy-completion invariant
   passes under the frozen source hashes;
4. aggregate budget-32 mask-oracle/no-op opportunity is at least 5% of the
   aggregate full-mask/no-op reduction; and
5. strictly positive mask opportunity occurs in at least 60% of development
   board groups.

The denominator in gate four must be positive. Ties within `1e-12` are not
positive group opportunity. These thresholds are not changed after the result
is inspected.

Passing means only that adaptive branching has enough exact opportunity to
justify a separately frozen transparent-selector screen. Failing means we
deprioritize mask scheduling on this workload and do not rescue it by changing
warm strength, budget, feature, or board subset.

## Secondary reports

Report, without promotion:

- fixed-mask quality/work at every budget;
- mask and no-op winner counts;
- per-family and per-target-kind opportunity;
- per-group primary-budget opportunity;
- leave-one-group-out best-fixed-mask transfer;
- boundary-feature ranks against search opportunity and mask advantage; and
- paid `b1r1` checkpoint-four feature ranks against budget-32 mask advantage.

Python wall time remains a serial reference replicate. Deterministic state
visits are the primary cost until a native selective-leaf opcode exists.

## Dissent protocol

**Prior from ADR-0040:** the one-board fixed-warm mask/no-op oracle was 11.43%
above full/no-op, but the best fixed arm was full expansion and blind search
harmed several targets.

**Largest risk:** action-width labels may be dominated by range-family or
blueprint-strength artifacts rather than reusable decision-local signals.

**Falsifier:** failure of either the 5% aggregate opportunity gate or the 60%
positive-group gate ends this adaptive-mask branch for the current exact river
workload without retuning.
