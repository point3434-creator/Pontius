# Blueprint lookup performance candidate

This bounded change caches the SHA-256 identities of immutable blueprint keys and
sources after their first digest read. It leaves the legacy linear lookup and the
separate prepared-library/provider comparison intact. It is awaiting opposing review.

The private slot is inherited from a non-dataclass base. It does not enter dataclass
fields, equality, hash, repr, replacement, or wire encoding. Exact-field admission
reconstructs a new graph, so neither stale nor forged caller caches are authoritative.
No full canonical byte strings are retained. First reads still serialize and hash;
concurrent first reads can redundantly compute the same digest on immutable values.

The contract assumes the source graph remains immutable after construction. Direct
object.__setattr__ tampering can leave a stale digest on that caller-owned object.
Runtime/provider admission and the artifact encoder still rebuild/validate fields;
they must be used at the existing trust boundaries. This cache is not a mutation detector.

## Measured effect

Python 3.14.6, warm process, five batches of 20 operations, synthetic preflop CALL table.
Times are median batch means. Memory was measured in a separate tracemalloc experiment;
tracing was off throughout timings. These measurements establish lookup cost, not strength.

| Operation, 1,326 entries | Before | Candidate |
| --- | ---: | ---: |
| Legacy lookup | 6.711 ms | 0.120 ms |
| BlueprintProvider proposal | 6.832 ms | 0.158 ms |
| Prepared lookup | 0.029 ms | 0.030 ms |
| Provider construction | 31.509 ms | 31.440 ms |

Full-graph construction plus first identity retained about 150 KB more Python allocation
(468,976 -> 618,927 bytes); peak traced allocation was 834,498 -> 845,114 bytes.
Construction timings use prebuilt entries; the separate memory experiment constructs
the entire graph. Raw samples and the reproducible benchmark are in the review packet.
The single-process timings are local observations, not confidence intervals or an SLA.

The legacy scan remains O(n); enumerating n entries through it remains O(n squared).
The measured dominant repeated hashing cost is removed. Further indexing, host migration,
package lazy imports and research-module retirement are deferred to a measured need.

## Verification

- 349 cases, zero skipped, across 17 repository suites cover blueprint, provider,
  runtime, replay, workload and evaluator behavior on the candidate.
- 18 additional export/completion cases pass, including a real-host three-phase subset
  in a disposable checkout. Its file-copy list now includes immutable_blueprint.py;
  previously that test could exercise the old lookup module during dirty-tree checks.
- Five new unit tests cover repeated reads, stale/forged caches, admission, replacement,
  dataclass views, copy and pickle. The serialization regression fails on frozen base.
- The retained 1,081-hand artifact re-encodes byte-for-byte (1,010,990 bytes). Full
  membership result objects are equal between base and candidate: 1,081 hits, no
  disagreements, same source identity. This is an in-memory diagnostic, not a retained run.
- Changed Python files pass Ruff; git diff --check passes.

Packet: D:/Pontius-handoffs/v0a-blueprint-lookup-performance/r001/.
Base: d4488fee970e10ac96a5b4a33f8d3fc9ff86c05b.
No retained phase is authorized by this change. Historical runs retain their original source.
