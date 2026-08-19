# Risk Register

| ID | Risk | Warning sign | Mitigation / stop condition |
|---|---|---|---|
| R1 | Metrics fail to predict full-game strength | Exact improvements reverse in every realistic league | Freeze hidden suites; build independent responders; stop architecture work if measurement is untrustworthy |
| R2 | Incorrect rules or regret math | Failure to reproduce small known games | Slow reference, property tests, differential implementations; correctness blocks optimization |
| R3 | Multiplayer CFR gives misleading apparent convergence | Self-play improves while unilateral deviations grow | Report exact NashConv in tractable games; compare current, average, and snapshot policies |
| R4 | Neural leaves have low MSE but damage root play | Root harm worsens on insertion | Root-aware gates; retain blueprint continuation; stop scaling the model until targets are fixed |
| R5 | Adaptive search neglects rare adversarial branches | Restricted responder steers into cold lines | Minimum coverage and worst-case vulnerability budgets |
| R6 | Learned scheduler overfits its oracle | Beats heuristic only on training games | Hidden games, conservative uncertainty bonus, permanent heuristic fallback |
| R7 | Premature kernel optimization | Fast synthetic benchmark with no end-to-end gain | Optimize only captured representative traces |
| R8 | Host/GPU memory exhaustion | Peak use leaves no transient headroom | Target <=48 GB host and <=13 GB GPU steady state; report bytes per structure and enforce quotas |
| R9 | Single-developer scope overload | Multiple incomplete subsystems | One active checkpoint, three immediate tasks, explicit kill criteria |
| R10 | Agreement bias hides flaws | Decisions contain no opposing evidence | Mandatory dissent format and falsifying experiment for consequential choices |
| R11 | Inaccessible Pluribus prevents headline comparison | Internal league becomes sole evidence | Maintain a Pluribus-style control, independent responders, and precise limited claims |
| R12 | Shallow resolving damages a strong blueprint even with exact leaves | Exact-control NashConv exceeds blueprint NashConv | Require paired exact-control gate, variant-neutral anchoring, and an explicit blueprint/no-op fallback before neural scaling |
| R13 | Anchor and no-op thresholds overfit independent errors in a tiny game | Selected coefficient reverses under correlated errors or a new player count | Freeze selection rules before held-out games; require reach-weighted structured-error and multiplayer gates |
