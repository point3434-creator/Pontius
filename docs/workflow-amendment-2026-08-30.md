# Prospective workflow amendments — 2026-08-30

Authority: the controller's 2026-08-30 rulings, recorded with ADR-0485.
Read alongside `docs/workflow.md`; this amendment governs the specific
conflicts below. The original workflow remains preserved at the accepted
ADR-0478 SHA-256:
`2ea6b7c849ec4d991ae68fcc9b069b6892b51c5831f5d21a424a709fec05b7bf`.

## Retire CodeRabbit

The controller ruled: "im getting rid of coderabbit we dont need it".
CodeRabbit's role and Stage 5 sweep are removed for the current uncommitted
preregistration and future review work. No replacement external-service gate
is introduced, and no installation, authentication, or review transmission
is required. An unrun or failed historical sweep remains unrun or failed;
this ruling never relabels it as a pass.

All other workflow requirements remain: immutable candidate refs and
blob-derived manifests, independent cold review at the declared tier,
applicable isolated verification, explicit authorization for each ceremonial
commit, push after authorized commit, and attributed single-writer verdict
records. Removing CodeRabbit grants no experiment, broad-profile capability,
integration, or commit authority.

## Resolve contradictory procedural requirements prospectively

When procedural statements conflict or form a circular dependency, identify
the conflict and intended guarantees, select a coherent sequence that retains
those guarantees, and record the reasoning and narrow amendment before relying
on the new sequence. A circular process requirement is a specification defect
to repair; it need not keep development indefinitely parked.

This does not permit altering historical evidence, rerunning consumed owners,
tuning against opened results, fabricating measurements, waiving correctness
criteria, or claiming an unproved safety property. Genuine unestablished
preconditions remain explicit blockers. The controller's existing rulings
are not repeatedly submitted for the same approval.

For increment one, the authorized resolution is the ADR-0485 order: contract,
implementation, source seal, separate rehearsal, measured operating bounds,
then one-shot authorization. No measured bound or invocation authority is
implied by the contract opening. The reviewed final decision still needs its
specific ceremonial-commit authorization under the unchanged workflow.
