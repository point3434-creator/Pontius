# ADR-0233: Shared payoff semantics and runner contracts retire repeat defects

- Status: accepted process correction
- Date: 2026-08-22
- Review scope: ADR-0228 through ADR-0232 implementation line

## Findings

The continuation strategy runner and its widened-selector predecessor normalize
quality and construct the raw acceptance guard from the configured stack. The
game-derived one-size continuation payoff span is also 30, so all recorded
ADR-0228 and antecedent values remain numerically correct. At two sizes the
quantities diverge: retaining the formula would silently shrink guards and
normalized values by a factor of 1.6. This repeats the semantic-alias defect
family prohibited by ADR-0129.

The resident GPU record-to-hand fold also clamped its reach input in place
while the host fold did not, and its RawKernel assumed C-contiguous Float64
record matrices without enforcing that contract. No current caller observes
the mutation and all current matrices are contiguous, so accepted fold and
timing results stand.

Finally, seven recent rejected invocations were runner plumbing failures rather
than scientific outcomes. Repeated direct reads of changing pass-bit paths,
hand-assembled environment payloads, and one-off result gate tables imposed a
real correction-cycle tax despite correctly preserving the evidence boundary.

## Corrections

`payoff_semantics.py` is now the mandatory source for raw guard conversion and
quality normalization in every new runner. Its helpers accept a layout and
read only `layout.game.payoff_span`. A two-size counterexample proves that the
stack cannot substitute. An AST test inventories every byte-pinned historical
stack/span expression by exact file, line, and semantic kind; any addition or
movement fails the suite. Historical runners remain unchanged so their frozen
implementation hashes and evidence provenance are not rewritten.

The byte-pinned GPU fold remains immutable. Its `resident_record_to_hand_fold_v2`
successor clamps each reach only after loading it inside the kernel. It
therefore leaves both record matrices unchanged, matching the host contract,
without allocating a second record matrix. Float64 and C-contiguity are checked
before the raw-pointer kernel launches; strided views fail closed. Every new
device-fold customer must route through this successor rather than silently
changing the implementation used by accepted historical differentials.

`runner_harness.py` centralizes artifact hashing/loading, contradictory pass-bit
detection, strict schema-path access, nested runtime/Git environment assembly,
matching top-level and gate pass fields, and finite JSON serialization. Every
new evidence runner must use these primitives rather than reimplementing them.

## Deferred minor issue

The affine seat proof still uses `selector_margin_allowance` as its intercept-
identity tolerance. The semantics are distinct, but changing that byte-pinned
primitive is not required for the held-out trial and no unsoundness was found.
A successor API must expose an explicit intercept-identity tolerance before the
two quantities need different values.

## Decision

Accept and seal the process correction before preregistering the held-out
one-step versus two-step continuation value trial. ADR-0228, ADR-0230, and
ADR-0232 remain valid; this ADR changes no strategy label or scientific result.

The next trial must use `raw_guard(layout, normalized)`,
`normalized_quality(layout, raw_quality)`, and the shared runner harness. Keep
the ADR-0230 frozen methodology: independent arms, latest-step regret vertices,
all 31 legal blocks, full-affine winner selection, one exact proof per arm, the
hard 15-second deadline, and immutable blueprint fallback. Make no strategy-
quality claim until that held-out result exists.
