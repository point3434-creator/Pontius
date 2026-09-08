# ADR-0148: Preregister numerically corrected target-transfer rerun

## Status

Frozen after ADR-0147 and before any corrected target rerun.

## Sole correction

Reuse the complete ADR-0146 configuration, implementation, twelve-target
order, two-step search, six-candidate portfolio, fixed-envelope selection,
certificate semantics, resource ceilings, and outcome-neutral gates byte for
byte.

Replace only the rejected exact warm-start policy-digest gate with the
established numerical contract: maximum probability error at most `1e-12` and
mean information-set total variation at most `1e-13`.  Record both errors and
retain the exact digest identities as diagnostics.

The instrumentation subclasses the same resident solver and measures its
policy immediately after the existing warm-start call.  It does not add a
search step, candidate, quality call, target, or outcome branch.

## Decision rule

A full rerun passes only if the corrected numerical warm-start gates and every
unchanged ADR-0146 gate pass.  No observed v1 selection is a gate or hypothesis
target.  The v1 outcome remains diagnostic until independently reproduced by
this clean successor run.
