# Accounted immutable blueprint preparation: measured costs

These are fixed local engineering observations, not research or playing-strength evidence.
Source review closure and all prescribed acceptance gates preceded timing. The finite request,
table population, launchers, runtime identities and input hashes were recorded before the first
measured payload. No timing threshold was chosen afterward, and no concurrent test, review,
profiling or synchronization payload ran during these observations.

## Source and retained evidence

B: `363c9fb669e19a30375537ee5e92ea338a840a2d`.
Prepared candidate: `666cb43b097707a54733a51cd7930d55920a5af7`.
Prepared source manifest SHA-256:
`4ac5089861356eb3bfe25f8d4c2b45aff3c9b39b4306a51a66ea3f5d01fa4012`.

Retained root: `D:/Pontius/tmp/blueprint-preparation-implementation-20260907-001`.
Pre-timing definition: `r002-measure/pre-timing-definition.json`, SHA-256
`ce205a729918d1f73367bd3894fd6ba5aaefb236c6a8d23c34a641a79673a6be`.
Complete observations: `r002-measure/measurement-summary.json`, SHA-256
`c360a3ad9aeada31870af24001daefdcbe17a1c9b1fdb85a34e5ec930765db83`.
Source qualification and raw receipt/hash index: `r002-source-qualification.json`,
SHA-256 `9e79a7d7d53512fa00058f95521ff0a9bf9ba5c820625cac4ce7815f518155db`.

Each source/interpreter has a separate r002-cost-VERSION-SLOT directory with exact-source
snapshot, runtime preflight, intents, stdout/stderr, exit receipts, lookup/blueprint-costs.json
and sessions/verified-sessions.json. VERSION is base or prepared; SLOT is 311 or 314. The shared
matrix and both reader-consumption records are under r002-measure. All prior development and
administrative failure roots remain retained.

## Warm public calls

The table population matches ADR-0512: lexicographic unordered private-card pairs, a fixed
preflop six-player state, button zero, 200 chips each, blinds 1/2 and CALL entries. Three
warmups precede five batches of 20 calls for each first hit, last hit and miss. Each cell is the
median batch mean [minimum-maximum batch mean], in milliseconds. These are batch means, not
individual-call percentiles or tail latency. Ratio is B median divided by prepared median for
the same case and method.

### CPython 3.11.15

| N | Case/method | B ms | Prepared ms | Ratio |
| ---: | --- | ---: | ---: | ---: |
| 0 | miss/lookup | 0.0143 [0.0142-0.0166] | 0.0301 [0.0285-0.0379] | 0.5x |
| 0 | miss/provider | 0.0525 [0.0517-0.0557] | 0.0667 [0.0658-0.0777] | 0.8x |
| 16 | first/lookup | 0.1122 [0.1120-0.1184] | 0.0283 [0.0281-0.0307] | 4.0x |
| 16 | first/provider | 0.1521 [0.1499-0.1530] | 0.0665 [0.0650-0.0674] | 2.3x |
| 16 | last/lookup | 0.1106 [0.1096-0.1123] | 0.0285 [0.0282-0.0289] | 3.9x |
| 16 | last/provider | 0.1510 [0.1503-0.1541] | 0.0665 [0.0652-0.0707] | 2.3x |
| 16 | miss/lookup | 0.1103 [0.1102-0.1128] | 0.0282 [0.0280-0.0285] | 3.9x |
| 16 | miss/provider | 0.1508 [0.1502-0.1654] | 0.0659 [0.0658-0.0672] | 2.3x |
| 128 | first/lookup | 0.7772 [0.7754-0.7945] | 0.0282 [0.0280-0.0290] | 27.6x |
| 128 | first/provider | 0.8285 [0.8227-0.8338] | 0.0662 [0.0655-0.0668] | 12.5x |
| 128 | last/lookup | 0.7794 [0.7774-0.7985] | 0.0281 [0.0280-0.0284] | 27.8x |
| 128 | last/provider | 0.8263 [0.8225-0.8310] | 0.0660 [0.0654-0.0665] | 12.5x |
| 128 | miss/lookup | 0.7842 [0.7804-0.7919] | 0.0283 [0.0282-0.0310] | 27.7x |
| 128 | miss/provider | 0.8313 [0.8281-0.8339] | 0.0669 [0.0663-0.0715] | 12.4x |
| 1024 | first/lookup | 6.2443 [6.2370-6.2632] | 0.0283 [0.0282-0.0293] | 220.4x |
| 1024 | first/provider | 6.3358 [6.3035-6.3737] | 0.0656 [0.0651-0.0668] | 96.6x |
| 1024 | last/lookup | 6.2536 [6.2489-6.3522] | 0.0281 [0.0281-0.0319] | 222.4x |
| 1024 | last/provider | 6.5400 [6.5179-6.7303] | 0.0654 [0.0652-0.0699] | 100.1x |
| 1024 | miss/lookup | 6.7414 [6.5228-7.0908] | 0.0280 [0.0279-0.0287] | 240.5x |
| 1024 | miss/provider | 6.6080 [6.5289-7.1467] | 0.0659 [0.0651-0.0668] | 100.3x |

### CPython 3.14.6

| N | Case/method | B ms | Prepared ms | Ratio |
| ---: | --- | ---: | ---: | ---: |
| 0 | miss/lookup | 0.0145 [0.0143-0.0156] | 0.0292 [0.0287-0.0314] | 0.5x |
| 0 | miss/provider | 0.0518 [0.0510-0.0530] | 0.0665 [0.0659-0.0676] | 0.8x |
| 16 | first/lookup | 0.0980 [0.0974-0.0983] | 0.0290 [0.0289-0.0314] | 3.4x |
| 16 | first/provider | 0.1368 [0.1363-0.1375] | 0.0663 [0.0662-0.0680] | 2.1x |
| 16 | last/lookup | 0.0974 [0.0970-0.0981] | 0.0294 [0.0291-0.0325] | 3.3x |
| 16 | last/provider | 0.1362 [0.1359-0.1372] | 0.0667 [0.0663-0.0675] | 2.0x |
| 16 | miss/lookup | 0.0977 [0.0957-0.0998] | 0.0291 [0.0288-0.0295] | 3.4x |
| 16 | miss/provider | 0.1337 [0.1332-0.1384] | 0.0668 [0.0665-0.0739] | 2.0x |
| 128 | first/lookup | 0.6754 [0.6733-0.6989] | 0.0300 [0.0296-0.0326] | 22.5x |
| 128 | first/provider | 0.7106 [0.7059-0.7236] | 0.0667 [0.0665-0.0689] | 10.7x |
| 128 | last/lookup | 0.6679 [0.6675-0.6725] | 0.0296 [0.0295-0.0303] | 22.6x |
| 128 | last/provider | 0.7088 [0.7026-0.7123] | 0.0671 [0.0660-0.0692] | 10.6x |
| 128 | miss/lookup | 0.6685 [0.6641-0.6730] | 0.0294 [0.0292-0.0300] | 22.7x |
| 128 | miss/provider | 0.7147 [0.7050-0.7223] | 0.0663 [0.0657-0.0668] | 10.8x |
| 1024 | first/lookup | 5.3148 [5.3017-5.3460] | 0.0292 [0.0287-0.0306] | 181.7x |
| 1024 | first/provider | 5.4051 [5.3771-5.4352] | 0.0671 [0.0656-0.0694] | 80.6x |
| 1024 | last/lookup | 5.2841 [5.2663-5.2894] | 0.0293 [0.0291-0.0301] | 180.7x |
| 1024 | last/provider | 5.3652 [5.3299-6.7422] | 0.0663 [0.0658-0.0672] | 81.0x |
| 1024 | miss/lookup | 5.5128 [5.4357-6.3894] | 0.0291 [0.0289-0.0299] | 189.6x |
| 1024 | miss/provider | 5.5271 [5.4908-6.7255] | 0.0662 [0.0657-0.0686] | 83.4x |

Every measured selection checks the real action, hit/miss label and source digest. Provider
calls check the literal action and reason. The final consumer requires equal table digest and
provider configuration in both sources. The separate correctness suite demonstrates one real
whole-table serialization during preparation and none during repeated prepared selections; the
old provider repeats that work.

## Cold construction and Python allocation

Five fresh observations per size separate source construction, lookup preparation and provider
construction. Each timing cell is a median [minimum-maximum] in milliseconds. B lookup
preparation is only an identity wrapper, since its direct lookup uses the existing source; it
must not be interpreted as an owned setup equivalent. Provider setup is measured in both
versions and includes each provider's ownership work.

### CPython 3.11.15

| N | Construction | B ms | Prepared ms |
| ---: | --- | ---: | ---: |
| 0 | source | 0.0016 [0.0012-0.0034] | 0.0013 [0.0010-0.0045] |
| 0 | lookup setup | 0.0002 [0.0001-0.0003] | 0.0068 [0.0047-0.0102] |
| 0 | provider setup | 0.0107 [0.0091-0.0132] | 0.0118 [0.0095-0.0143] |
| 16 | source | 0.1949 [0.1903-0.2016] | 0.1944 [0.1919-0.2004] |
| 16 | lookup setup | 0.0003 [0.0002-0.0004] | 0.3891 [0.3879-0.3992] |
| 16 | provider setup | 0.4105 [0.4083-0.4904] | 0.4029 [0.3912-0.4481] |
| 128 | source | 1.4712 [1.4575-1.5134] | 1.4309 [1.4263-1.4404] |
| 128 | lookup setup | 0.0003 [0.0002-0.0004] | 3.0674 [3.0328-3.1168] |
| 128 | provider setup | 3.1827 [3.0991-3.2532] | 3.0772 [3.0376-3.1044] |
| 1024 | source | 12.0272 [12.0130-12.4088] | 11.4711 [11.3092-11.6797] |
| 1024 | lookup setup | 0.0003 [0.0002-0.0004] | 24.7091 [24.4622-29.0011] |
| 1024 | provider setup | 25.8749 [25.5806-30.0832] | 24.4737 [24.3160-25.0170] |

| N | Objects kept alive | B retained/peak bytes | Prepared retained/peak bytes |
| ---: | --- | ---: | ---: |
| 0 | source + lookup | 584/1,040 | 2,047/3,031 |
| 0 | source + provider | 2,033/3,387 | 2,368/3,609 |
| 16 | source + lookup | 8,800/10,728 | 35,654/42,678 |
| 16 | source + provider | 34,545/42,670 | 35,975/42,774 |
| 128 | source + lookup | 57,912/69,512 | 239,926/289,542 |
| 128 | source + provider | 232,129/289,534 | 240,247/289,638 |
| 1024 | source + lookup | 452,152/501,640 | 1,832,630/2,219,870 |
| 1024 | source + provider | 1,770,169/2,219,862 | 1,832,951/2,219,966 |

### CPython 3.14.6

| N | Construction | B ms | Prepared ms |
| ---: | --- | ---: | ---: |
| 0 | source | 0.0013 [0.0010-0.0030] | 0.0013 [0.0010-0.0032] |
| 0 | lookup setup | 0.0002 [0.0001-0.0004] | 0.0048 [0.0046-0.0082] |
| 0 | provider setup | 0.0095 [0.0085-0.0144] | 0.0092 [0.0087-0.0131] |
| 16 | source | 0.1931 [0.1914-0.2022] | 0.1969 [0.1932-0.2005] |
| 16 | lookup setup | 0.0002 [0.0001-0.0002] | 0.3901 [0.3892-0.4358] |
| 16 | provider setup | 0.3826 [0.3815-0.3987] | 0.3918 [0.3900-0.4043] |
| 128 | source | 1.5031 [1.4615-1.5647] | 1.4545 [1.4443-1.4711] |
| 128 | lookup setup | 0.0002 [0.0001-0.0006] | 3.0623 [2.9390-3.2047] |
| 128 | provider setup | 3.0170 [2.9453-3.0314] | 2.9652 [2.9283-3.0534] |
| 1024 | source | 12.0882 [11.8658-12.1627] | 11.5461 [11.4896-11.6090] |
| 1024 | lookup setup | 0.0003 [0.0002-0.0005] | 24.2321 [23.9032-24.5265] |
| 1024 | provider setup | 25.1158 [24.5532-26.4472] | 23.8157 [23.5780-24.0080] |

| N | Objects kept alive | B retained/peak bytes | Prepared retained/peak bytes |
| ---: | --- | ---: | ---: |
| 0 | source + lookup | 696/1,120 | 2,351/3,014 |
| 0 | source + provider | 2,281/3,224 | 2,560/3,398 |
| 16 | source + lookup | 6,992/8,600 | 31,242/34,582 |
| 16 | source + provider | 30,077/34,518 | 31,451/34,574 |
| 128 | source + lookup | 38,176/49,736 | 194,450/221,910 |
| 128 | source + provider | 186,605/221,846 | 194,659/221,902 |
| 1024 | source + lookup | 289,120/338,504 | 1,460,542/1,680,346 |
| 1024 | source + provider | 1,398,033/1,680,282 | 1,460,751/1,680,338 |

Memory comes from separate tracemalloc passes over a newly constructed source and its retained
lookup/provider. It includes the prepared owned graph, exact-key index and cached canonical
bytes. Existing observations, interpreter allocations, native allocations and whole-process RSS
are excluded. This is not an artifact-size or process memory bound. Runtime preparation remains
inside the charged hand-start interval; the work cutoff, action wall and preparation-bank rules
retain their original values.

## Three-hand nonempty sessions

| Interpreter | Strategy | B parent seconds | Prepared parent seconds |
| --- | --- | ---: | ---: |
| 3.11.15 | blueprint-v1 | 4.3771845 | 4.5397811 |
| 3.11.15 | baseline-rules-v1 | 4.3794324 | 4.3934023 |
| 3.14.6 | blueprint-v1 | 4.3988497 | 4.3246639 |
| 3.14.6 | baseline-rules-v1 | 4.3632401 | 4.3579703 |

Each cell is one fresh three-hand session with the existing explicit deals and one nonempty
raise-to-6 blueprint entry. The table hits the first controlled preflop decision and misses
later decisions. Across all eight sessions (24 hands), the full actions, settlements and carried
stacks match the predeclared literal controls and match between sources for each strategy. Every
child exits zero, capture is untruncated, and all hands complete without failure causes. The
final carried stacks are [200, 199, 197, 206, 198, 200]. Baseline host fallback remains an
independent legacy lookup.

These short sessions use one table entry and few controlled decisions. They are behavioral
integration controls with descriptive elapsed time, not a repeated large-table throughput
benchmark. Each timing includes source checks, native process launch, independent host
validation, game transport and cleanup. Single observations cannot separate a small
implementation effect from operating-system scheduling noise.

## Fixed twelve-trial compatibility matrix

The one new CPython 3.11.15 v3 matrix completed in 46.1445104 seconds from parent launch through
exit. All 12 trials and six pairs completed with cleanup complete and no capture, action, hand,
session, work-cutoff or action-deadline failure. Full applied actions, settlements, carried
stacks and policy/fallback counters match the retained fixed control. Both B readers (v1/v2) and
all three candidate readers (v1/v2/v3) accept the same completed artifacts without schema
changes.

The request retains one fixed deal, the mixed five-opponent lineup, all six positions, both
existing strategies, the fixed seed, a 60,000ms trial allowance and a 900,000ms shared
allowance. The blueprint is empty. Its fresh preparation identity does not reopen ADR-0511's
consumed owner. Result JSON SHA-256:

`1016b785adf9be44c4c1883617b521878b687a939e691c05dc6aea750d865afb`.

ADR-0512's earlier v2 matrix took 49.2236669 seconds. That historical timing is not a
simultaneous source-controlled A/B observation: time, cache state and snapshot path differ. This
empty-table matrix mainly checks compatibility and retained reader semantics. The warm nonempty-
table measurements are the direct evidence for removing repeated table preparation work.

## Practical interpretation and next boundary

Preparation moves whole-table ownership, serialization and indexing into setup, then reuses the
result for repeated calls. The finite tables above expose both that setup/memory cost and the
measured warm-call benefit. The direct prepared provider is reusable for future Python analysis
or blueprint consumers; generating or training a blueprint still requires its own algorithm,
population and authority.

The current runtime uses the prepared source for both blueprint selection and mandatory baseline
fallback while retaining full legality and clock checks. Independent host validation still pays
its reference lookup cost. These results do not establish a universal 15-second response bound,
performance at millions of entries, better playing strength or a reason to migrate the engine to
a native language. A next performance decision should start from a prospectively fixed
representative workload and the existing profile of remaining source/identity-check overhead.
