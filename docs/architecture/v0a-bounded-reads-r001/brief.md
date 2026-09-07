# Bounded reads in paired evaluation v2

The controller asked to follow the completed performance pass's recommendations:
adopt the measured read-bound correction, remeasure, and examine non-empty
blueprint lookup cost. This brief bounds the first production successor and the
associated diagnostics. Decision adoption remains an exact final commit step.

## Change and invariants

Add `tools/v0a_evaluation_v2.py` as a versioned copy of the sealed v1 runner. Change
its own admitted origin from v1 to v2 and change only the stable-file read request
from `cap + 1` to `observed_size + 1`. Preserve all other executable behavior:
cap admission, before/after handle identity, named-file identity, ancestor identity,
exact byte length, source checks, child CLI, action clocks, cleanup and publication.
The request and result schemas remain v1 because their meaning is unchanged; the
runner source commit and manifest identify v2. New executions use new identities.

The existing helper remains `tools/v0a_evaluation_contract.py`. The v2 source
manifest includes v2 plus that helper and the same inherited source population.
The v1 runner, helper, game/policy code, fixtures, tests and old results stay intact.
Do not turn this into a generalized loader, caching framework, or policy change.

Tier C: the changed read bound sits in an integrity boundary, so two independent
source reviews cover the frozen candidate. Existing fixed integer-cap callers are
the compatibility scope; arbitrary malformed cap objects are not a new API promise.

## Exact implementation surface

Base: commit `5845f32f010a44d924abc2f50ae142d1c6adec1b`, tree
`16700b0b258288cf623e88a241abf264e8b08763`, branch
`codex/evaluation-bounded-reads`, worktree
`C:/Users/point/.codex/worktrees/fa55/Pontius`.

Seams: native file/handle/ancestor identity; Git source admission and captured
raw loading; parent/child execution; publication and completed-artifact reading;
closed import policy and generated CPU test registration. The companion design
maps each seam to its unchanged invariant and acceptance observation.

Add the v2 runner and `tests/test_v0a_evaluation_v2.py`. Narrowly update these
current registration surfaces, prospectively authorized for this successor:

- `tools/check_stabilization_boundaries.py`: register the v2 origin and apply the
  existing closed import/loader checks with its exact new self-origin.
- `tools/generate_test_inventory.py`: register the one new CPU test suite.
- `tests/test-inventory.json` and `tests/test-profiles.toml`: regenerate only new
  membership/census effects, preserving historical identities and grants.
- `tests/test_inventory_and_profiles.py`: necessary registration/census expectations.
- `.github/workflows/ci.yml`: add the one new suite; preserve all existing checks.

Record these narrow prospective supersessions in the final successor ADR. No
other sealed source change is in scope. Generated STATUS follows the final ADR.

Budget: at most 650 new production lines, 350 new test lines and 100 manual
registration lines; generated inventory/profile data and documentation excluded.
The duplicated runner is justified by immutable sealed source: it is a versioned
624-line copy with a two-location delta, not a new orchestration implementation.
One initial candidate and at most two bounded correction rounds. Escalate an
unresolved invariant/design issue rather than adding unrelated machinery.

## Acceptance and ground truth

Ground truth is the existing exact file/identity contract, native file effects,
and hand-checked control outcomes. A bounded read request must fail a resource
ceiling test against the old implementation and pass with v2. Test actual bytes
and file handles, not text matching or a mock implementation of the reader.

Cover empty and ordinary files, cap boundaries and oversize rejection, growth,
shrinkage, named-file and ancestor replacement, and growth followed by restored
size/mtime. The restored-growth control must distinguish a deliberately wrong
`read(size)` implementation, demonstrating the extra-byte protection. Verify v2
source admission and continued use of its public reader/publication contract.
The import guard must accept both exact runner origins and reject a wrong v2
self-origin, forbidden import, and altered captured loader. Verify the reused
helper against its sealed base bytes and read a real v1 completed artifact with v2.

Run the new suite and affected unchanged evaluation/import/inventory/status
checks in fresh D-local snapshots, actual Python 3.11.15 before 3.14.6, with -B -P,
scrubbed environments and absolute native Git. Preserve raw evidence and exact
candidate identity. The final reviews bind frozen Git blobs and their manifest.

## Diagnostic continuation and dependency

After correctness, run a fresh v2 fixed 12-trial cost control and parent/child
profile, with the prior diagnostic input definition and fresh output identities.
Keep these explicitly non-evidentiary performance observations and compare full
action sequences/settlements without using chip values to select a policy.
Measure synthetic non-empty blueprint sizes through existing public lookup/provider
interfaces as a separate cost-only probe; no trained strategy or strength claim.
Use the existing Python/OpenSpiel reference review to guide interpretation.

Only successor adoption and claims about its performance depend on this change.
Training design, existing source, historical results and unrelated work do not.
Stop when the candidate is reviewed, qualified, measured and concrete for final
commit approval. Choose any next optimization from the new measurements; do not
bundle unmeasured changes into this successor.
