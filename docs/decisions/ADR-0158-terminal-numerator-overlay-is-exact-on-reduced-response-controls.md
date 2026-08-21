# ADR-0158: Terminal-numerator overlay is exact on reduced response controls

## Status

Accepted as the reduced physical implementation following ADR-0157. It
authorizes a separately frozen h32 atomic response preflight, not an h32 run,
strategy-quality claim, or deployment claim.

## Context

The accepted leaf-adjoint evaluator embeds every opponent public-path policy
factor in each target-omitted terminal contraction, then performs an exact
reverse public-tree pass. A localized candidate therefore does not require
recontracting a terminal whose target-omitted factors are byte-identical to the
immutable source. The candidate can overlay only changed terminal numerators
and replay the same reverse equations and selectors.

For the target player's own policy edits, every target-omitted terminal factor
is unchanged by construction. The target response value must be reusable, but
the fixed-profile value still changes through the target-policy fold in the
reverse pass.

## Engineering result

Add `src/pontius/incremental_leaf_adjoint_response.py`, SHA-256
`12dbf0e59ba13cba70cbaa81c60fb8ac4cfc16312d9834782d76b750052627dd`,
and `tests/test_incremental_leaf_adjoint_response.py`, SHA-256
`a01f2368684a9461bad0871c44e515ebbaf92e84c3d5d6362018b47475b0723d`.

The implementation compiles one immutable cache per target seat containing:

- the source probability tape and public parent/action metadata;
- every source terminal's normalized numerator vector;
- the complete source utility, response value, response actions, and tie
  diagnostics; and
- explicit persistent numeric bytes.

For each candidate and seat, it compares source and candidate target-omitted
path factors at every terminal, contracts only changed terms, overlays their
numerators, and replays the accepted reverse public-tree equations. Untouched
terminal arrays remain immutable source objects. Every call begins from that
source tuple; no candidate becomes an anchor.

The implementation supports both the transferred CPU contraction and the
accepted resident GPU contraction. Resident mode requires the belief cache,
the matching target automaton cache, and the matching CuPy incidence operator
together; partial resident configuration fails closed.

An integrated verifier compiles candidate probabilities once, evaluates seats
in a caller-frozen order, preserves cap-before-objective stopping, and emits a
complete quality vector only after all seats finish.

## Reduced controls

Five h3 six-player physical controls pass against the complete leaf-adjoint
reference:

1. every source cache reproduces its full source seat result and response
   actions;
2. a same-seat atom and its opponent-seat reads reproduce exact utilities,
   responses, gains, and action maps, while the same-seat response performs
   zero terminal recontractions;
3. call order followed by an identity read returns immutable source values;
4. a deterministic customer triggers at least one response-selector switch;
5. a blueprint-zero-reach atom leaves fixed utilities unchanged, changes an
   opponent response, and still matches the complete evaluator.

The integrated fixed-prefix control reproduces the complete six-seat gain
vector within `2e-14`. A manufactured cap then stops on the exact violating
seat after one incremental read.

The complete suite passes 608 tests with 22 optional GPU screens skipped.
No unpreregistered reduced-case wall time is promoted as evidence.

## Decision

Adopt the terminal-numerator overlay as the first exact physical response
bridge. Its next test is a frozen resident h32 preflight over deterministic
information-set atoms drawn from retained, already labeled rejected bundles.

The h32 preflight must freeze atom selection before execution, fully evaluate
each atom only as a mechanism teacher, compare every incremental prefix
coordinate and stop decision, and report:

- cache compilation and persistent bytes;
- changed public nodes and affected versus reused terminal numerators by seat;
- same-seat versus opponent-seat work;
- response action switches;
- incremental and complete resident wall time;
- observed conservative maximum and the 15-second ledger; and
- the independent cap/objective classification.

All atom outcomes are diagnostic. No atom may be selected for strategy quality,
no result may reanchor the blueprint, and no atomic certificate composes with
another without exact union recertification.

## Dissent

**Confidence:** very high in reduced exactness and source isolation; moderate
that terminal-by-terminal factor comparison remains cheap enough at h32.

**Opposing evidence:** even when few terminals change, building every candidate
factor tuple may become the dominant host cost. A public dependency index from
policy node to descendant terminals may be necessary.

**Largest unknown:** the affected-terminal fraction of real h32 atoms and the
resident kernel's efficiency on much narrower term batches.

**Cheapest falsification:** a clean h32 cache-only preflight on one frozen atom
per seat and target, with complete resident evaluation retained solely as the
exact mechanism teacher.
