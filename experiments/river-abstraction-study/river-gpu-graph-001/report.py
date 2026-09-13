"""Render the research report from freshly verified assessment rows."""
from pathlib import Path
import json
HERE=Path(__file__).parent
a=json.loads((HERE/'assessment.json').read_text())
assert a['complete']
lines=['# River GPU graph replay 001','',
'Graph replay accelerates the fixed DCFR+ solve while preserving final policy bytes.',
'All 18 workers completed two reset-separated solves each. Six independent exact',
'audits verified the common policies. This is execution improvement, not improved',
'strategy quality at the fixed 2,048-iteration budget.','',
'## Design and controls','',
'User authorization: "Let\'s test it", approving the proposed bounded graph-replay test.',
'Two unchanged case-001 expanded river games, each with 1,081 hands per player.',
'Checkback has 15 public nodes / 9 terminals; raise has 27 / 17. These are two',
'nested trees on one board/range pair, not two independent board samples.',
'Released-code DCFR+ is fixed: alpha 1.5, denominator 1.5, gamma 4, alternating',
'players 0 then 1, own-reach weighted averaging, float64 payoffs and state.',
'Three arms: prior eager CuPy; stable buffers with native cuBLAS, dispatched',
'eagerly; the identical stable operations captured as one alternating iteration.',
'The middle arm separates graph replay from the combined buffer/binding change.',
'Three rotated-order fresh workers per game/arm, two complete solves per worker.',
'The second solve resets all policy/regret/averaging state and both counters.',
'Reuse is measured only for the same game, not changed ranges, payoffs or topology.',
'',
'Python 3.14.6, CuPy 14.2.0, NumPy 2.5.2, RTX 5080. Frozen plan digest:',
'`facf02a1de6a61d0e5d645ccd4dd7a92bd3369ae0f74276281c4e03b99f2a81f`.',
'180 s per monitored worker, 3,072 MiB private-memory stop sampled every 50 ms.',
'CuPy pool limit 1,024 MiB excludes CUDA/library allocations outside the pool.',
'No source adoption, production edit, commit, push, or live bot invocation.','',
'## Correctness and the capture boundary','',
'The first test failed because the implementation did not yet exist. The first',
'CuPy implementation then refused cuBLAS calls during capture; both development',
'failure outputs are retained. They are not claims about the final frozen source.',
'A narrow Windows ctypes bridge calls the installed native cuBLAS Dgemm API',
'using a dedicated handle and fixed stream. It does not patch CuPy. Library',
'status codes are checked and handles are explicitly released after synchronization.',
'The runtime DLL is SHA-256 pinned but is not redistributed in this milestone.',
'',
'[NVIDIA documents native cuBLAS graph capture support](https://docs.nvidia.com/cuda/cublas/index.html#cuda-graphs-support).',
'CuPy handles capture/replay via its [Stream API](https://docs.cupy.dev/en/stable/reference/generated/cupy.cuda.Stream.html).',
'The one-iteration graph uses persistent buffers and a device counter indexing',
'precomputed, fixed-horizon discount weights. Capture must leave the counter at',
'zero; each replay advances it once. The host refuses work beyond the horizon.',
'',
'The final frozen gate checked all policy, cumulative regret and averaging state',
'for 32 iterations on both games: bitwise equality across all three arms.',
'Reset/replay also reproduced identical bytes, and counter/horizon checks passed.',
'All 36 full solves produced identical final bytes within their game across arms,',
'repeats and resets. This is stronger GPU-to-GPU parity than the preceding',
'experiment\'s CPU-to-GPU trajectory comparison; its prior failure remains unchanged.',
'',
'The six independent audits use the retained rational best-response evaluator',
'on 2^48-quantized policies and the original stored binary64 payoff coefficients.',
'Each agreed with the floating evaluator within 1e-10. Identical policy bytes',
'mean these audits cover all repeats and reset solves. No strict gap <= 1e-8',
'pass occurred; quality is the same checked approximation as the prior experiment.','',
'## Results','',
'Seconds, medians of three observations. First and reused solve clocks synchronize',
'the device. Capture excludes prior compilation/warmup; both are charged separately.','',
'| Game | Arm | First solve | Reused solve | Preparation | Capture ms |',
'|---|---|---:|---:|---:|---:|']
for r in a['rows']:
    capture=f"{r['capture_median']*1000:.3f}" if r['arm']=='graph' else 'none'
    lines.append(f"| {r['case']} | {r['arm']} | {r['first_solve_median']:.3f} | "
        f"{r['reused_solve_median']:.3f} | {r['preparation_median']:.3f} | "
        f"{capture} |")
lines += ['', '| Game | Replay vs eager | Replay vs static | Two-solve audited speedup |',
          '|---|---:|---:|---:|']
for c in a['comparisons']:
    lines.append(f"| {c['case']} | {c['graph_vs_eager']:.2f}x | "
                 f"{c['graph_vs_static']:.2f}x | {c['two_solve_audited_speedup']:.2f}x |")
lines += ['', 'Two-solve audited speedup uses full fresh worker wall time for both solves,',
'plus twice the separately observed fresh exact-audit process time. Only one',
'audit per game/arm was actually run; charging it twice is conservative accounting,',
'not a claim that two audit invocations executed or an integrated bot latency.',
'First accounted cost sums measured import/transfer, construction, warmup, initial',
'reset, capture, solve, average/download, float scoring and exact audit computation.',
'It excludes bootstrap/pin checks/process teardown, so is not end-to-end wall time.','',
'| Game | Arm | First accounted + audit s | Two solves + two audits s | Host peak MiB | Pool MiB |',
'|---|---|---:|---:|---:|---:|']
for r in a['rows']:
    lines.append(f"| {r['case']} | {r['arm']} | {r['accounted_first_with_audit']:.3f} | "
        f"{r['two_solve_plus_two_fresh_audits']:.3f} | {r['host_peak_mib']:.1f} | "
        f"{r['gpu_pool_mib']:.1f} |")
lines += ['', 'Host peaks are maximum sampled private memory across the three workers.',
'Pool bytes are allocator reservations, not complete device-memory attribution.',
'All monitored workers exited zero without a resource stop. The filesystem kernel',
'cache was warmed by development and frozen preflight tests. Warmup is measured',
'inside every worker, but none of these figures means an empty kernel cache.',
'Graph launch/instantiation costs that occur on first replay remain in its solve clock.',
'', 'Final exploitability (half the best-response gap), identical across arms:']
for r in a['rows']:
    if r['arm']=='graph': lines.append(f"- {r['case']}: {r['exploitability']:.15g}.")
lines += ['','Units are ten per starting pot; divide by ten for fraction of pot.',
'', '## Interpretation and next question','',
'The static/native eager control remains much slower than graph replay. Repeated',
'dispatch was therefore a material cost on these actual full-range river solves.',
'Capture was repaid within the first observed 2,048-iteration solve on both games.',
'The assessment also reports a linear capture-only break-even interpolation; that',
'is not a measured short-horizon latency or a guarantee about different games.',
'Preparation and CPU auditing remain important, but do not erase the gain here.',
'', 'Freeze this execution result and return to strategy quality: spend the saved',
'time on more iterations, then measure independent error under declared total-time',
'budgets. Do not assume error falls monotonically or that faster execution alone',
'makes the bot stronger. A larger compiler or more kernel optimization is not the',
'next priority. Neural/tabular/hybrid research remains a separate later question.',
'These small public trees and three local repeats establish neither six-max',
'strategy quality nor a live full-hand deadline.','']
with (HERE/'report.md').open('x',encoding='utf-8',newline='\n') as f:
    f.write('\n'.join(lines))
