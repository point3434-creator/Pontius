# ADR-0517: Permit one unchanged blueprint workload invocation

- Status: accepted one-run exploratory authority upon its separately authorized decision commit
- Date: 2026-09-08
- Follows: ADR-0516
- Base-Commit: 0801ddc05a800b652457fb06a92a739168c7a4b0
- Invocation-Authority: one qualify then one run at the exact absent root, no retry
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0517
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Execute and retain the unchanged workload's single exploratory run
- Front-Door-Blockers: known qualification and monitoring limitations; workload results unmeasured

## Decision

Permit one exploratory invocation of the unchanged representative blueprint workload
admitted by ADR-0516, implementing the controller's direction to run what exists
without rework. Execute the public qualify mode once, then run once only if the
retained qualification succeeds and its recorded stage stays within 1800 seconds.
Read and retain the result, including failure and partial observations. No retry,
resume, replacement success or further implementation change is authorized.

ADR-0516 preserves the two NOT CLEAN reviews and records the single-use exception
to normal source acceptance. This decision does not repair their findings or turn
the output into evidence of compliant monitoring, deployment readiness, playing
strength or a worst-case latency bound. Numerical findings retain their observed
case counts and limitations; final standing remains exploratory even if the raw
report's internal clean flag is true.

## Exact source, authority and roots

Source exception commit: 0801ddc05a800b652457fb06a92a739168c7a4b0.
Source tree: fa812931eefb20dea05a2b7477496e6a30a27d81.
Full raw source-manifest SHA-256:
958aaad2c821e2e465e9c5addbfcf350a4cccc70f5467d40bd9b7431f230e16c.

The fixed authority file is
docs/architecture/v0a-blueprint-workload-r001/invocation-authority.json.
Its exact required single-line declaration follows. This machine-checked line is
the deliberate exception to the 100-column prose preference; do not wrap it.

Workload invocation authority: `docs/architecture/v0a-blueprint-workload-r001/invocation-authority.json`; SHA-256 `268794980282d5633749bcadec2a370fe90bbae183c138202b5a9135c428ee22`.

Unchanged execution-protocol SHA-256:
28d2a421dfbbefc57e12fa0248759e4fe9b60b3bf1de60b8274cf8d6b5914760.
The recipe is the exact compact sorted JSON plus LF for
{"version":"workload-r002-recipe-v1"}, SHA-256:
6dd686d82d6033c6fa2f2ea5e11f16ae7c2ba172c04f99d5059bab21b8a82ae5.

Reserve D:/bww515/as-is-run-001 as the one absent result root. Its parent already
exists; qualify creates the root exclusively. Do not create it during preparation.
Use one fresh exact-source snapshot at D:/bww515/as-is-source-001/s for both
interpreters, at this final invocation commit. This source root must also be absent
before the approved setup. Administrative captures belong outside
the result root at D:/bww515/as-is-operator-001.

Use actual CPython 3.11.15 at D:/Pontius-tools/py311/Scripts/python.exe first and
CPython 3.14.6 at D:/Pontius/.venv/Scripts/python.exe for the fixed confirming subset.
Freeze actual redirector/resolved executable hashes, venv configuration, version,
source, environment and generated input identities through the unchanged admission.
The snapshot has LF raw blobs, snapshot cwd/PYTHONPATH, -B -P, a scrubbed environment
and absolute C:/Program Files/Git/cmd/git.exe as PONTIUS_GIT in native Windows form.

This final decision must be the real published origin/master. Use ordinary clone or
fetch from that published state; do not manufacture the tracking ref. Every source
exception blob except the permitted generated STATUS must remain identical, with
only this decision and authority added. The fifteen r003 implementation blobs remain
exactly the source reviewed at 2e1457046c640045fe0b404bfc3d6f78cd5e4b45.

## Fixed execution and standing

The unchanged r002 design and execution protocol supply the complete recipe,
8192 table and 1152 independent query trajectories, structural qualification,
prefix capacity, timing/memory/reuse populations, interpreter subsets and all seven
numerical interpretation rules. Derived input, artifact and ordered-cell hashes
are frozen by qualify before measured dispatch. The planned session population
remains 104 stock plus 16 diagnostic one-hand trials. Do not double, shrink or
reorder it after observing a result.

The unchanged runner supplies a nominal 1800-second qualification stage and one
3600-second measured envelope across both interpreters. Source setup outside those
declared origins is separately recorded. Retain actual elapsed values and every
failed/interrupted/unattempted cell; do not enlarge a bound to obtain completion.
H-01 means the qualification limit is imperfectly enforced internally. Inspect
qualification-result.json before calling run: any refusal, nonzero exit, secondary
cause, unverified cleanup, missing result or stage_ns above 1800000000000 closes
measurement. This external read does not alter or certify the implementation.

G1 remains accepted for this use: pre-ready direct-worker memory lacks the promised
continuous sampling. Do not claim that interval was observed or that the 3 GiB
trigger bounded it. Keep the existing observed resource threshold, native cleanup,
capture/file limits and shorter session/child bounds. The operator may stop for a
user interruption or observed resource pressure, preserving whatever exists.

No concurrent tests, review scans, profiling outside the declared diagnostics or
sync may run during unprofiled timing. Administrative preparation and source checks
are not performance measurements. Retain original raw captures and public-reader
output; append operator interpretation rather than editing producer records.
If the public reader refuses, preserve that refusal and identify which results
remain interpretable without inventing a clean full report.

## Adoption and closure

The prepared ADR-0516 and ADR-0517 objects remain proposals until the exact combined
commit/push action is authorized. That approval may bundle publication with this
one staged invocation; no further launch confirmation is then required.
Generate STATUS with the unchanged renderer and check the new metadata on both
supported interpreters. These small metadata checks do not stand in for the waived
source-acceptance suites and are not new poker invocations.

This decision consumes one new invocation identity, not an r004 correction or a
retry of any earlier owner. Qualification failure closes run. Preserve the entire
attempt and issue a descriptive result with the known review limitations. Any later
optimization, repeat, source change or result-decision commit needs its own scope.
