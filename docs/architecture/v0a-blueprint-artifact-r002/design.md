# Portable blueprint artifact: design r002

Status: proposed design, not an implementation or source-opening authorization.
Base: `7ee314b443e10896e87a2e194f24eddda31ff77d`.
Input: `docs/briefs/v0a-blueprint-artifact-brief.md` under ADR-0489.
Tier C: an external-data admission boundary for an existing immutable policy.

The controller approved drafting the additive codec and a narrowly scoped
registration amendment. The companion `source-opening-draft.md` states the
proposed exception. No existing source, test, registration or CI file changes
as part of preparing this packet. No owner, rehearsal or correctness run occurs.

## Goal, ground truth and coverage

Meet the brief's five acceptance criteria through one byte-level adapter into
`ImmutableBlueprintActionSource`. A nonempty policy loaded from data must select
the independently declared action through `HandRuntime` and complete a hand
through `ReplayHost` and `verify_successful_trace`. This is engineering behavior,
not strategy strength, training, an authoritative run or an operating-budget claim.

Ground truth is the existing key/action value contract, a handwritten JSON
fixture, declared public betting actions, and the existing independent chip-depth
settlement reader. Expected action and payout values are stated before execution;
neither the new encoder nor historical run output supplies the behavioral oracle.

Coverage is the closed v1 data schema below, not arbitrary serialization or proof
that every representable key is reachable in poker. Enumerate field/type/shape
failures from the schema and exercise them through both public codec operations.
Live-key matching and state-specific action legality remain the sealed runtime's
responsibility. No claim covers hostile monkey-patching of installed modules,
filesystem race safety, arbitrary process resources or policy quality.

## Boundary and public API

New package: `src/pontius/blueprint_artifact/`.
`__init__.py` is inert; callers import the two functions from `codec.py`:

- `decode_blueprint(raw: bytes) -> ImmutableBlueprintActionSource`.
- `encode_blueprint(source: ImmutableBlueprintActionSource) -> bytes`.
- `BlueprintArtifactError(ValueError)` is the common typed admission refusal.

The decoder accepts exact `bytes`, not a path, text, stream, callback or subclass.
The encoder accepts an exact source and the fixed exact record/value graph it
contains. Reject foreign subclasses before traversing or calling their methods.
Only fixed record classes, tuples, enum types and permitted scalar types are
traversed; no generic object serializer, reflection-derived schema or user hook.
Both directions apply the same numeric and Unicode domains below. An existing
source is codec-admitted only after these checks, not merely because its existing
constructor accepts it. In particular, encode refuses surrogate code points in
`source_id` before hashing or producing bytes; it does not repair or replace them.
Validate and reconstruct values before hashing or returning anything. Either the
whole policy/byte result is returned or a refusal is raised; no partial admission.

The codec has no file I/O, imports at request-selected paths, runtime dispatch,
clock, trace, network, subprocess or GPU behavior. Callers own ordinary file reads
and writes; loading an artifact does not grant authority to run it. The returned
object enters the existing `blueprint=` API unchanged, before the hand begins.

Direct internal imports are only `pontius.immutable_blueprint` and
`pontius.no_limit_betting`; direct standard-library imports are limited to
`__future__` and `json`. Existing transitive dependencies remain inherited, not
reimplemented. No parent-package re-export or import from the runtime back into
the codec is needed. This leaves all six `pontius.v0a` module bytes unchanged.

## Closed wire schema

Input is strict UTF-8 JSON without a BOM. Object member order and legal JSON
whitespace need not be canonical. Reject duplicate member names at every object
depth, including names made equal by JSON escape decoding. Reject unknown or
missing members, floats (including integral-looking ones), nonfinite constants,
trailing non-whitespace data and strings containing unpaired surrogates.
An integer field requires `type(value) is int`; a boolean never counts as one.

Every integer field has the additional v1 bound `0 <= value < 10**640`; narrower
field ranges and positive-only requirements below still apply. This is a decimal
conversion compatibility boundary, not a chip bankroll or measured resource cap.
Both supported CPython families document 640 as the minimum configurable nonzero
decimal conversion limit. Thus admitted values remain convertible even at that
setting, without changing interpreter-global state or the sealed digest path.
The derivation is the minimum threshold in the [3.11][py311-ints] and
[3.14][py314-ints] integer-conversion documentation, not an observed test maximum.

Decode limits every JSON integer token to at most 640 decimal digits, excluding
an optional minus sign, before decimal conversion (using the JSON integer hook,
not a new parser). Then enforce the numeric field's exact range; JSON grammar is
unchanged. Encode checks exact integers by value before any decimal formatting,
canonical-key serialization or policy digest. An over-range value is a typed
refusal, never an ambient conversion error. Do not derive the range from the
current process setting, disable the limit, or introduce a second digest format.

Strings in both directions must contain Unicode scalar values: no code point in
U+D800 through U+DFFF. Wire escape decoding happens before this check, so a valid
escaped surrogate pair becomes an accepted astral character. A Python source ID
containing surrogate code points is refused even if two appear adjacent. Preserve
valid strings exactly, without Unicode normalization or replacement characters.

The root has exactly three members:

- `version`: the string `pontius-v0a-blueprint-artifact-v1`.
- `source_id`: an exact string with at least one non-whitespace character;
  preserve it without trimming or Unicode normalization.
- `entries`: an array of objects, each with exactly `key` and `action`.

An empty entries array is valid and explicitly represents the existing passive
policy. Nonempty admission and actual table hits are mandatory acceptance cases.
Duplicate semantic keys are refused, even if their actions agree or their private
card ordering differs before canonicalization. Entry order has no policy meaning.

`key` is the object representation of `BlueprintDecisionKey.canonical_bytes()`:
exactly the following 17 members, with no new or omitted information.

| Members | Wire values |
| --- | --- |
| `version` | Exact string `blueprint-decision-key-v1` |
| `controlled_seat`, `button` | Integers in 0 through 5 |
| `private_hand` | Two distinct integer cards in 0 through 51 |
| `board` | Ordered array of distinct integer cards in 0 through 51 |
| `street` | `preflop`, `flop`, `turn` or `river` |
| `small_blind`, `big_blind`, `last_full_raise_size` | Positive integers |
| `starting_stacks` | Six positive integers |
| `stacks`, `total_contributions`, `street_contributions` | Six nonnegative integers each |
| `folded` | Six exact booleans |
| `pending_seats` | Ordered array of unique integers in 0 through 5 |
| `acted_at_bet` | Six values, each null or a nonnegative integer |
| `public_history` | Ordered array of the eight-field history arrays below |

Board width is respectively 0, 3, 4 or 5 for the four streets. Private cards are
canonicalized by the existing key constructor and cannot overlap the board.
The small blind is smaller than the big blind. JSON arrays become exact tuples;
only private-card ordering is normalized, not board, pending-seat or history order.

Each history array has exactly these ordered values:
`[street, seat, kind, raise_to, chips_committed, full_raise, return_seat, return_chips]`.
Street and kind use the same closed labels as the key and action. Seat is 0..5;
chips and return chips are nonnegative integers; full-raise is an exact boolean;
return seat is null or 0..5. Raise amount is null except for a positive integer
on `raise`. Apply the existing `BettingActionRecord` validation as well: folds
and checks commit zero, calls and raises commit positive chips, full-raise only
describes a raise, and a return seat and positive return chips occur together.

`action` has exactly `kind` and `raise_to`. Kind is `fold`, `check`, `call` or
`raise`. Raise-to is a positive integer only for `raise`, and null otherwise.
Construct the existing `BettingAction`, `BlueprintDecisionKey`, entry and source
types; retain their validators rather than replace poker semantics with the codec.
Wire-type checks still run first, including inside every nested history array.

There is deliberately no whole-deal object, future board, opponent-private hand,
policy callback, runtime configuration, hash-only substitute for a key, or import
target in this schema. A well-formed but unreachable key may load and never match;
the codec does not invent a second complete-hand reachability validator.

## Deterministic encoding and identities

Encode full keys, not the source's digest-only entry representation. Sort entries
lexicographically by their full key canonical bytes. Sort object members, use
compact separators and ASCII escaping, forbid nonfinite values, encode UTF-8 and
append exactly one LF. ASCII output is a deterministic subset of UTF-8.
Decoder acceptance of harmless formatting variation does not imply preservation
of the original formatting by the encoder.

Two separate identities remain explicit:

- Raw artifact identity is `SHA256(raw)` over exactly the externally supplied
  bytes. A caller can retain this using ordinary hashing; no new manifest engine.
- Existing policy identity is the returned source's unchanged `digest`, whose
  canonical representation binds source ID, key digests and action values.

Different whitespace or input entry order may change the raw hash without
changing policy identity. No self-declared hash inside the document is trusted
or needed. Export/import of a codec-admitted source preserves every key/action
and its policy digest; equivalent entry permutations export identically. Every
successful encode result must decode to the same policy digest.

The v1 codec sets no artifact-byte, entry-count or source-ID-length ceiling.
The arbitrary r001 byte ceiling is removed, not replaced with a guessed number.
Large schema-valid data is not refused merely for crossing that former ceiling.
This is not a capacity, hard memory/time or availability guarantee. The byte API
is not an exposed network service; operational quotas, if later needed, require
their own grounded decision and are not silently added to this schema.

Map invalid UTF-8, malformed JSON, schema/type/value failure, over-range integers
and excessive nesting to `BlueprintArtifactError` with a useful field/reason,
without invoking an untrusted value's representation or formatting hooks.
Do not catch `BaseException`, convert resource exhaustion into success, or claim
a hard allocation bound from validation. No disk mutation occurs.

## Acceptance map and independent controls

New tests reside in `tests/test_blueprint_artifact.py` and
`tests/test_blueprint_artifact_boundary.py`; at most 300 new test lines combined.
Use at most two tiny literal JSON fixtures under `tests/fixtures/blueprint_artifact/`:
`raise_control.json` and `history_control.json`, at most 8 KiB combined. The
fixtures are authored independently of the encoder. No fixture is created now.

1. Decode a handwritten nonempty fixture and compare every key field and action
   with separately constructed expected values. Include nonempty public history,
   nullable history fields, all action labels and a postflop board in codec cases.
   Assert encoder output against independently stated canonical bytes, not only
   against its own decoder; test equivalent entry order and empty-policy support.
2. From a declared public initial state (button 0, controlled seat 3, six stacks
   of 200, blinds 1/2), the loaded matching entry selects raise-to-6, not the
   passive call-to-2. Assert TABLE_HIT, the emitted action and one delivery through
   the real `HandRuntime`, not a policy helper double.
3. Complete that control through `ReplayHost`: opponents 4, 5, 0, 1, 2 fold.
   There is one controlled action; four uncalled chips return to seat 3, leaving
   a five-chip pot and payouts `(0, 0, 0, 5, 0, 0)`. Final stacks are
   `(200, 199, 198, 203, 200, 200)`. These are betting arithmetic, not a recorded
   successful run. Verify the trace with the existing independent reader using
   the separately constructed expected policy, not only the decoded object.
4. Use a nonmatching entry to assert passive fallback, and a matching raise-to-1000
   entry to assert `INVALID_BLUEPRINT_ENTRY` with no delivery. The latter is
   representable data but illegal in the controlled state; do not conflate the
   codec's representation check with the runtime's state-specific legality check.
5. Drive schema-derived corruptions through decode: duplicate names/keys, missing
   and unknown fields at every object level, each scalar-type family, enum labels,
   tuple/array widths, card overlap, nullable values, float/nonfinite values,
   unsupported versions, malformed encoding, trailing data and excessive nesting.
   Include a good first entry followed by a bad entry: no source is returned.
6. Export refuses foreign record/value subclasses and malformed exact graphs;
   a callback marker stays untouched. Assert no accepted partial bytes on failure.
   Exercise the public operations with temporary file bytes as well as literals;
   this demonstrates portability, not a claim of atomic or race-safe file storage.
7. Exercise the real source boundary gate on the new package. Negative source
   fixtures cover undeclared siblings, forbidden internal imports and a legacy
   origin importing the codec. Preserve the original six-file v0a population.

Within the same test budget, add explicit scalar/closure controls. Independently
authored raw JSON with a chip value of `10**640 - 1` must admit when its other
fields satisfy the existing validators; `10**640` and longer tokens must refuse.
The exact-source exporter applies the same boundary without stringifying the
rejected integer. Accepted cases traverse decode, unchanged `source.digest`,
encode and decode again. Repeat the focused codec suite at interpreter startup
with `-X int_max_str_digits=640` on each supported slot as well as their normal
configuration; do not add process spawning to the codec or a global-setting edit.
Both operations refuse lone high and low surrogates; valid escaped pairs and
literal astral source IDs preserve the same string and policy identity. A valid
empty policy whose nonblank ASCII source ID makes raw and canonical bytes exceed
the former one-MiB limit is a generated test control, not a third fixture file.
It must round-trip; no operational memory or latency claim follows from that test.

Declare fresh correctness-only hand, seed, policy and run identifiers prefixed
for this artifact task. The complete deal belongs to the new fixture host; only
its controlled hand and public state populate the literal policy key. Do not
reuse consumed owner identities or derive fixtures from rehearsal/results data.

Run focused checks on CPython 3.11.15 first, then 3.14.6, using the repository's
fresh D-local snapshot procedure. After CLEAN review, the proposed broader wall
is the new suites, the unchanged four v0a suites, `test_immutable_blueprint.py`,
and the existing direct CPU CI hard-gate population at the base (union, no need
to duplicate a suite). Include generator and boundary `--check` equivalents;
informational diagnostics are not promoted to acceptance gates. No guarded
scientific profile, owner, installed dependency or performance measurement.

## Registration, alternatives and stop rules

The exact new source/test paths and six existing registration-file delta scopes
are in `source-opening-draft.md`. This requires an explicit prospective exception
to sealed registration bytes; drafting that exception does not activate it.
Existing runtime, kernel, behavioral tests and retained evidence remain immutable.
No repair, new capability grant or soundness claim is made for the parked analyzer.

Rejected: editing the sealed blueprint/runtime to add serialization (unnecessary
coupling); a generic schema/serialization framework (larger admission surface);
hash-only policy files (cannot reconstruct keys); and copying the checker or
putting the codec in an unscanned location (would evade the real source boundary).

Easy mistakes are type coercion, a dropped history field, duplicate-key aliases,
using round-trip as the only oracle, confusing the two hashes, and broadening
registration into analyzer repair. The controls above target those boundaries.

Only the portable-artifact implementation depends on this design. Training,
evaluation and operating authority are neither selected nor prerequisites here.
The codec must fit 300 source lines including its inert initializer. Registration
changes must fit 100 manually added/removed lines, excluding generated bytes and
decision metadata; new tests and fixtures retain the separate bounds above.

This commission ends at one design packet. The proposed implementation budget is
one initial round and at most one bounded correction round, with the normal Tier C
independent reviews; no review waiver carries over from ADR-0489. Return to the
controller before exceeding a bound, changing a sealed runtime, reimplementing
poker semantics, repairing the analyzer or beginning a third implementation round.
A required behavioral defect gets RED then GREEN; implementation acceptance
requires CLEAN reviews and the stated wall. Design/source-opening review is
read-only and does not depend on yet-unimplemented runtime checks.
A recurrence on the same contract or WRONG SHAPE
requires a written design reassessment, not another automatic patch.

The remaining controller decision is whether to adopt this exact design and the
bounded registration exception after review. Code, tests, measurements, source
sealing, commits and publication are not authorized by this draft.

[py311-ints]: https://docs.python.org/3.11/library/stdtypes.html
[py314-ints]: https://docs.python.org/3.14/library/stdtypes.html
