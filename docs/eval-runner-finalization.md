# Evaluation runner finalization

The controller authorized publication on 2026-09-10: "Let's commit and push".
This records acceptance of the reviewed r002 consolidation for the
`codex/eval-runner-consolidation` branch. It does not authorize a retained experiment invocation.

The reviewed source is the seven-file r002 overlay on
`1c7067448106cfa2aca3d57be879842d72293c61`. Its packet manifest is
`f8a63b7e64bbc017d539d94c916cea5a606e10fe48f5b55ef3ca6c3aa222cf93`.
The frozen guide and handoffs preserve their pre-publication wording; this record supplies
the later publication decision without rewriting the review history.

The initial cold pass found one material finalization-interruption defect and returned
NOT CLEAN / NOT SOUND. The r002 repair moved the transition out of signal deferral before
the final signal snapshot and inside the interruption exception boundary. The fresh opposing
repair review returned CLEAN / SOUND with no material finding, independently reproducing
the eight failing RED subcases, passing 35 focused cases, and passing 16 extra signal probes.

Author verification on the final repair passed 44 affected cases without skips, including two
disposable solve/export/real-host-agreement campaigns. The full r001 manifest had 49 passing
suites and two optional suites skipped (10 optional SciPy cases); it was not rerun for the
small finalization-only repair. Test and review limits remain explicit in the reports.

Durable publication: `v0a-eval-runner-consolidation/` in the Pontius-handoffs repository,
including byte-exact r001/r002 packets, original reviews, executable review receipts and the
five development test outcomes referenced by this branch's journal additions.

Current usage is documented in [the runner guide](eval-runner.md). An outcome JSON document
cannot override the launcher's nonzero exit. Every retained campaign still requires its own
reviewed binding, resource envelope and separate one-shot controller authorization.
