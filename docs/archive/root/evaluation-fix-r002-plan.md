# r002 correction coverage plan, recorded before edits

Candidate r001: 96aad82a482a0f37b13490df1bf03c1c74a860ca.
This is a prospective specification correction; no evaluator implementation exists.
Required findings A-I1 and A-I2 are independently verified by source/doc inspection.

A-I1 category: an action cause observed in versioned event decision/failure frames
must not disappear into propagated child_failed or capture-deficiency labels. Discovery
followed host.WIRE_FIELDS, event failure handling at host lines 739-742 and 915-918,
the proposed exact trial schema, and all summary/fallback/timing descriptions.
Cover valid delivery_rejected, duplicate decision/failure observations, conflicts,
null identity, missing/malformed records and unverified failed prefixes. Add a precise
observation channel and metric-to-authority/unknown map. No second engine validation.

A-I2 category: parseable final bytes can survive failed/late publication operations.
Enumerate result and completion create/write/flush/close/readback, source/deadline
verification, interruption and visibility release. Use one ephemeral empty pending
guard before any final file; consumers refuse while present. Verify both closed files
and deadline before publication commit; only then remove the guard once as postcommit
visibility release. Failed precommit paths retain guard and files. Explicitly exclude
visibility-release latency from deadline promise; serialized time is preparation time.
Only that empty guard may be removed, not retained artifacts or roots. Include real-file
late/failed full-marker operations and delayed/ambiguous release controls after adoption.

For this docs-only proposal, RED evidence is the frozen r001 missing field and missing
completion lifecycle/predicate demonstrated by the review scenarios. GREEN evidence
will be corrected normative scenario coverage and fresh independent review; no native
runtime correctness claim or unapproved payload execution. Actual finite behavioral
RED/GREEN controls remain mandatory in the later adopted source round. Coverage is
limited to these failure classes; arbitrary OS durability/hostile writers are excluded.
Falsifiers: a schema-valid action cause cannot be represented honestly, or late/failed
precommit publication can satisfy the consumer predicate, or release latency is claimed
to fit the deadline. This draft will be frozen as deferred coverage with exact refs.
