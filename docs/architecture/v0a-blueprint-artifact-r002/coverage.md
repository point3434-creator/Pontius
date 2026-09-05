# FIX coverage: v0a-blueprint-artifact-design/r002

Deferred cold-review input: record an independent invariant and related-path
inventory before opening this file. This is a design coverage claim, not an
implementation test receipt or a claim of a completed feature.

## Category and discovery

Contract: a codec-admitted immutable source has a portable full-key data encoding;
successful export is accepted by import with unchanged policy identity. The
admitted scalar domain must be explicit and independent of ambient decimal
conversion settings. An unrelated, ungrounded byte count must not silently limit
the policy population. Prior r001 Review B named these three gaps; the controller
authorized only their documentation correction, not source opening.

Discovery compared every key/action/history field and source ID with the existing
immutable value constructors, their canonical JSON/digest paths, the two proposed
codec APIs and their acceptance map. Python's primary integer-conversion and JSON
documentation supplies the decimal threshold and surrogate behavior independently
of the proposed codec. The original fixtures and runtime/replay oracles remain
unchanged. No whole-runtime or parked-analyzer audit was added.

## Related paths and correction coverage

1. Capacity: remove the raw and canonical byte ceiling, its failure classification
   and its adoption wording from both design documents. Keep no hard memory/time
   or hostile-resource-exhaustion guarantee. Explicitly include a schema-valid
   above-former-limit round-trip control within the existing test budget.
2. Integers: cover raw JSON token conversion, every integer family in a nested
   key/history/action, exact-source graph validation, key serialization, source
   digest and export/reimport. The uniform upper bound is `10**640 - 1`; existing
   narrower field/sign ranges remain binding. The threshold derives from the
   documented minimum CPython setting, not a measured bankroll or guessed size.
   Reject longer raw tokens before conversion and over-range exact integers before
   formatting/hashing. No codec process-global setting change is admitted.
3. Strings: cover decode after escape processing and encode before hashing/output.
   Source ID is the only freely chosen admitted string value; versions and enum
   labels are fixed, object members are closed. Both directions exclude all
   surrogate code points but preserve valid astral characters without normalization.
   The round-trip promise applies to codec-admitted sources, not every object an
   older, more permissive constructor can instantiate.

## Evidence and acceptance controls

This round uses static document-to-contract inspection and frozen-byte identity
checks only. There is no executable codec and no runtime or test result is claimed.
The corrected acceptance text requires the following future public checks:

- Independent raw JSON and exact source graphs at the numeric upper bound and
  immediately beyond; decode/digest/encode/decode closure for accepted values.
- CPython 3.11.15 first, then 3.14.6, in fresh snapshots. The focused codec suite
  additionally starts with the documented minimum decimal threshold, without a
  new launcher or a codec-side global-setting edit.
- Lone high and low surrogates refused in both directions, valid escaped pairs
  and astral source IDs admitted, and successful export always reimportable.
- A generated, valid above-former-byte-limit empty-policy control, not a larger
  checked-in fixture population or an operational capacity benchmark.
- All original field, exact-type, malformed-input, real controlled-action,
  complete-hand, independent-reader, miss, illegal-hit and boundary controls.

Falsifiers: an otherwise valid in-domain value cannot traverse the unchanged
digest at the minimum supported conversion setting; an export accepts a source
string that its import must reject; or a former byte ceiling remains normative.
Any such observation invalidates the corresponding correction claim.

## Limits and preserved scope

No claim proves whole-hand reachability, policy quality, arbitrary resource safety
or hostile installed-module mutation. The unchanged constructors/runtime retain
their existing jobs; the codec does not implement another poker validator.
The new source/test paths, direct imports, real consumer, six precise registration
exceptions, line/fixture budgets and future implementation-round budget are
unchanged. r001 and its issued reports remain immutable. No source, test, CI,
registration or sealed evidence byte changes in this documentation-only round.
