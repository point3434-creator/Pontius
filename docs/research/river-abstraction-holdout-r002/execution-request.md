# Holdout r002 execution request

This is the current plan. The r001 plan is superseded and must not be invoked.
Building and reviewing this candidate does not authorize its execution.

Plan: docs/research/river-abstraction-holdout-r002/plan.json
SHA-256: 7377d6a37503f8a11e54b06dafcd783ed29e3b0e523d3569bbcfe17dc2a2533c

The plan binds the current computational source bytes on
codex/river-abstraction-holdout, based on commit
1b4d1a0e26cd4da90ff74678de2e48ef53ec5599. It is not yet committed or pushed.
The code verifies source digests, Python 3.14.6 and NumPy 2.5.2 before reservation.

Workload: two declared holdout boards times uniform/polarized ranges; 96 hands
per player; all four unchanged methods; checkpoints 100, 1,000 and 10,000.
This produces 48 profiles. Four children run sequentially with one BLAS thread,
each with a 60-second timeout. Parent verification and I/O are outside that timeout.
No process RSS cap is imposed. Output is reserved atomically at
D:/Pontius-training/river-abstraction-study/holdout-001 and is never reused.

The final checkpoint is the headline comparison. Every case and checkpoint retains
method-minus-reference differences against uniform-equity and range-equity controls,
in chips and fractions of the pot. Negative differences favor the method; any
positive and negative case differences are labeled mixed, regardless of the mean.
The underlying payoff, CFR and abstraction algorithms remain unchanged.

No holdout evaluation has occurred. Execution requires the controller's approval
of this plan. Commit, push, subsequent experiments and source adoption are separate.
The suggested approval below is one physical line so it can be recorded verbatim.

