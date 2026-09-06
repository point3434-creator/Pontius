# Seeded deals for the watch-first session

Authority: this design opens source work only through adopted ADR-0502.
Base: cc22fdb67f572a53257cd092c01d192f1a8db5ab. Tier C.

## Shape and boundaries

Add tools/v0a_seeded_deals.py. It is an inert, standard-library-only module with
pure deal generation plus a small file CLI. It materializes the existing
pontius-v0a-table-session-v1 JSON format. It does not import Pontius, load the sealed
host/session, start a process, play a hand, select a policy or read any result.
All src/pontius bytes and all existing poker tools remain unchanged.

The saved request owns the seed and requested hand count; the output file owns
the full dealer schedule. Keep both files. A success receipt binds their digests.
The existing session reader admits the generated session independently; a generator
receipt grants no runtime authority. The seed and complete schedule are dealer
inputs, never added to policy observations, event frames or terminal projections.

Reusable pure API:

- deal_for_hand(seed, hand_index): return a fresh dict with private_hands and
  board_runout, using only the two explicit values. hand_index is exact int 0..15.
- generate_session(seed, hand_count): return a fresh existing-format session dict,
  with exact int hand_count in 1..16. It calls the same per-hand algorithm.

seed in both APIs is an exact str of 64 lowercase hexadecimal characters, decoded
to 32 bytes. No implicit trimming, case conversion, time seed or global RNG state.
Invalid public arguments raise the tool's typed Refusal with code input_invalid.
Each invocation returns independent lists/dicts; callers cannot mutate a later
generation through an earlier result. Import and pure calls perform no file I/O,
subprocess, environment mutation, wall-clock query or optional dependency import.
Future training code may reuse this dealer function under its own source opening;
this design creates no learner or league and gives them no execution permission.

## Exact versioned shuffle recipe

Algorithm label: sha256-counter-fisher-yates-v1.
Domain bytes: ASCII pontius-v0a-seeded-deals-v1 followed by one zero byte.

For zero-based hand_index h, begin an independent word stream. For block counter
c = 0,1,...,127, compute SHA-256 over the concatenation of:

1. the domain bytes above;
2. the decoded 32 seed bytes;
3. h as exactly four unsigned big-endian bytes;
4. c as exactly four unsigned big-endian bytes.

Consume each 32-byte digest as eight consecutive unsigned big-endian 32-bit words,
from bytes 0..3 through 28..31. A word is consumed at most once. Do not reseed per
draw, reverse digest bytes, share stream state across hands or skip words by outcome.
The maximum is 128 blocks / 1024 words per hand. Exhaustion raises generation_limit;
it must not silently select a modulo-biased index or obtain another seed.

Start deck as the card-ID list [0,1,...,51]. For i = 51 down through 1, let b=i+1
and L=2^32-(2^32 mod b). Consume words until w<L; reject w>=L. Set j=w mod b and
swap deck[i] with deck[j]. This exact descending Fisher-Yates recipe is independent
of Python's random.shuffle implementation. The rejection step avoids simple modulo
reduction bias; no statistical certification, cryptographic deployment guarantee,
or exact uniformity over every finite seed is asserted.

For this hand, button=h mod 6 and first dealt seat=(button+1) mod 6. For offset
k=0..5, assign cards deck[k] and deck[k+6] to seat (first+k) mod 6. Sort each private
pair in ascending card-ID order to satisfy the existing deal contract. Board reveal
order is deck[12:17]; no burn cards are modeled. Remaining cards are not emitted.
The six pairs and five board cards must contain exactly 17 distinct IDs in 0..51.

Each hand's deck is shuffled afresh. Cards may recur across different hands, as at
a real table; never reject a repeated card or repeated deal across hands. Different
seeds need not be collision-free. Increasing hand_count preserves every earlier
hand's deal because h, not the requested count or prior outcomes, keys each stream.

## Request and materialized session

CLI: --request ABSOLUTE_PATH --output ABSOLUTE_PATH, both required, no abbreviation.
--help prints usage without generation or file publication. Invalid CLI syntax exits
2 with argparse usage. There is no seed-selection, auto-launch, append or overwrite
flag, and no JSON input on stdin. Explicit requests avoid losing an implicit seed.

Request bytes: nonempty UTF-8, at most 1024 bytes; reject BOM and any CR byte,
duplicate object keys, floats, nonfinite values, invalid Unicode/JSON and extra keys.
Root is exactly an object with version, seed, hand_count. version is the literal
pontius-v0a-seeded-deals-request-v1. seed and hand_count have the pure API domains.
Limit JSON integer tokens to two decimal digits before conversion; count validation
rejects signs/ranges not accepted by the exact 1..16 domain, including bool values.
Escaped JSON spellings of the same accepted string are permitted; request byte
digests may differ while the resulting session bytes remain identical.

Session object has exactly the existing fields: version, button, controlled_seat,
starting_stacks, small_blind, big_blind, opponents and hands. Use these fixed values:

- version: pontius-v0a-table-session-v1; button: 0; controlled_seat: 3.
- starting_stacks: six copies of 200; small_blind: 1; big_blind: 2.
- opponents: [passive,passive,passive,null,passive,passive], as JSON strings/null.
- hands: ordered deal_for_hand(seed,h) objects for h=0..hand_count-1.

No seed, hash, hand index, expected result or new metadata field is inserted into
this sealed session schema. Each hand has exactly private_hands and board_runout.
Encode session bytes with json.dumps(sort_keys=True,separators=(',',':'),
allow_nan=False), UTF-8, followed by one LF. The result must be <=16384 bytes.
The request and session alone suffice to regenerate and inspect the exact schedule;
the success receipt associates their raw-byte identities for convenience.

Varying stacks, blinds, controlled seat, initial button, opponents or table size
is outside this first generator. The existing session still carries actual stacks,
rotates the button and may stop before consuming all requested deals. A generated
schedule is not a promise that its host will play every hand or keep six seats funded.

## File publication and failure meaning

The CLI runs on Windows CPython under -B -P. Both paths are absolute D-local paths,
without parent traversal. Request, output parent and every ancestor must be regular
non-reparse files/directories of the appropriate kind. Output's parent must already
exist. Reject an existing output of any kind, including an empty file or directory.
Do not create parent directories, replace files, use temporary rename publication,
retry an output operation or remove a partial output after failure.

Read request with a bounded binary read and compare file identity before/after:
device, inode, size and mtime_ns, plus raw bytes on revalidation. Hold immutable raw
request bytes. Generate and validate the complete bounded session in memory first.
Revalidate the request before publication. Create output with exclusive binary mode
xb; issue one write and require its count to equal the complete encoded byte length.
Flush, fsync and close. Reopen boundedly and verify exact output bytes and stable
file identity, and revalidate the request again before the success receipt.
These are stable-path checks on trusted local storage, not a hostile-directory-race
sandbox or an atomic transaction across input, output and stdout.

Success receipt is one compact sorted-key UTF-8 JSON object plus LF, with exactly:
version=pontius-v0a-seeded-deals-result-v1, status=generated,
algorithm=sha256-counter-fisher-yates-v1, seed, hand_count, request_sha256,
session_sha256 and session_bytes. Digests are lowercase 64-hex SHA-256 of the exact
raw files. session_bytes includes the terminal LF. It is not a poker result or
claim of source/operating authorization. Write stdout once, at most 4096 bytes,
and require full count; do not retry on short write or final publication error.

Ordinary accepted-CLI failures exit 1, with one best-effort bounded ASCII stderr
line REFUSED <code> followed by LF. No success JSON is emitted before completion.
Codes: input_invalid for request parsing/domain/path/read/revalidation failure;
generation_limit for exhausted word budget or oversized generated session;
output_failed for output path/create/write/flush/fsync/close/readback/receipt failure;
environment_invalid for unsupported platform, implementation or missing -B/-P;
internal_error for other ordinary exceptions. KeyboardInterrupt exits 130 and emits
REFUSED interrupted if possible. No retry of reporting failures, and no fabrication
of an output hash or successful generation after an incomplete publication.

If a file was created before any later failure or interruption, retain it as-is.
It may be a prefix or even complete bytes; without successful completion it remains
an unaccepted output of that invocation. Never delete it or rerun over its pathname.
The saved request remains available independently of final stdout capture.

## Independent acceptance and controls

Before production implementation, independently compute and retain the three-hand
known-answer fixture from the literal recipe, using seed
000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f.
The reference calculation must not import or copy the production generator. Freeze
literal card allocations and canonical session bytes as expected_session.json;
review the block packing, byte order, draw rejection, shuffle direction and dealing
order independently. These are declared correctness vectors, not sampled poker runs.

Behavior tests must establish the three-hand known answer, all 52 shuffled IDs before
projection, the 17-card uniqueness/domain invariant, pair ordering, board order,
button-relative dealing, cross-hand independence, prefix stability at counts 1/3/16,
fresh returned containers, no ambient RNG dependence, and identical exact bytes on
actual 3.11.15 and 3.14.6. Invalid types/bools/counts/seeds must refuse consistently.

Exercise the real bounded-index helper with declared finite word iterators to force
w=L-1, w=L, w=2^32-1, repeated rejection and exhaustion. The production path uses
the actual SHA-256 word stream; known-answer checks must never mock that digest.
These controlled-word tests replace draw inputs, not the shuffle/index algorithm or
its outcome oracle. Include a semantic mutation of byte order or hand index that
the literal known-answer expectations reject; do not require an empirical histogram
or claim that a finite sample proves randomness.

Boundary tests cover exact request schema and size, duplicate/extra keys, Unicode,
integer/floating/bool rejection, minimum int_max_str_digits=640, existing outputs,
wrong roots, static reparses, request drift, real file-prefix retention after a
controlled short write, real flush/fsync/close/readback failures at declared I/O
seams, final stdout short write with no retry, interruption and import inertness.
Real files and actual affected I/O paths must supply observable effects; controlled
failure triggers cannot replace the publication implementation or expected result.
Static reparse rejection is not renamed proof of an adversarial race defense.

Both new suites must prove generated 1-,3- and 16-hand bytes are admitted by the
unchanged session Schedule and real TableInput/card contracts under the existing
public admission/load route in fresh snapshots. Keep all seed/generation metadata
outside those objects. No generated poker hand needs to run for this data-boundary
acceptance. Existing named session/host regression suites retain their own fixed
correctness controls; no demonstration or research population is opened.

## Implementation bounds

New files: tools/v0a_seeded_deals.py; tests/test_seeded_deals.py;
tests/test_seeded_deals_boundary.py; tests/fixtures/seeded_deals/request.json;
tests/fixtures/seeded_deals/expected_session.json. No other production namespace.
Allowed tool imports: __future__, argparse, hashlib, json, os, pathlib, re, stat,
sys, and their explicitly imported public members. No random, secrets, time,
subprocess, dynamic import/exec or optional/Pontius imports. Tests may use the
existing public session/host/card decoding routes only for scoped correctness.

At most 350 production LF lines, 650 combined new-test LF lines, two fixtures
totaling 4096 bytes, and 200 manual registration added/removed lines. Generated
inventory/profile outputs and separate decision metadata are counted separately.
The larger test allowance protects independent shuffle/dealing oracles plus real
publication failures, without copying a runtime, native owner or test framework.

One initial source candidate and at most one bounded correction. Two independent
Tier C reviews for substantive source; qualified mechanics require ADR-0492.
After CLEAN review, run both new suites, tests/test_v0a_table_session.py,
tests/test_v0a_table_session_boundary.py, tests/test_v0a_table_host.py,
tests/test_holdem_cards.py and tests/test_inventory_and_profiles.py, inventory
generator --check, real stabilization boundary gate, and the new request decoder
control at int_max_str_digits=640. Use actual 3.11.15 first, then 3.14.6, in fresh
D-local exact-candidate snapshots with -B -P, scrubbed environments, bound cwd/src,
actual version/module-origin preflight and absolute PONTIUS_GIT. Source-seal only
after exact review/acceptance. Stop before a third candidate, unexplained census
drift, scope/budget expansion, private-host access or any sealed poker-source edit.
