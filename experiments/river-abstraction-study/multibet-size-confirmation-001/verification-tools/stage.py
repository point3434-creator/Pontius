"""Reuse the pilot with only census, identity, reporting and cost-accounting edits."""
from pathlib import Path
from hashlib import sha256
import difflib
import json

HERE = Path(__file__).resolve().parent
PILOT = Path('D:/Pontius-worktrees/eval-runner-consolidation/experiments/'
             'river-abstraction-study/multibet-size-repair-001')
digest = lambda b: sha256(b).hexdigest()
assert digest((PILOT/'milestone-manifest.json').read_bytes()) == (
    'ae835016813436938e13b67e862effa0d0c1d3ab4af5d24d01310992f764ae84')
manifest = json.loads((PILOT/'milestone-manifest.json').read_bytes())
assert all(digest((PILOT/p).read_bytes()) == v for p, v in manifest.items())
edits = {}
for src, dst in [('experiment.py', 'pilot.py'), ('retain.py', 'retain.py')]:
    raw = (PILOT/'verification-tools'/src).read_text()
    text = raw
    if dst == 'pilot.py':
        text = text.replace('/8', '/16').replace('cases=8', 'cases=16')
        for field in ('lp_calls', 'bettor_trajectories', 'decisions', 'proposed_certificates',
                      'incumbent_certificates', 'independent_gate_audits'):
            text = text.replace(field+'=16', field+'=32')
    else:
        text = text.replace('multibet-size-repair-001', 'multibet-size-confirmation-001')
        text = text.replace("audit['cases'] == 8", "audit['cases'] == 16")
        text = text.replace('== 16', '== 32').replace("len(set(choice['groups'][0])) == 32",
                                                    "len(set(choice['groups'][0])) == 16")
        text = text.replace('1200000', '2400000').replace('range(8)', 'range(16)')
        text = text.replace('/8', '/16').replace('len(previous) == 29', 'len(previous) == 30')
        text = text.replace('Bettor size repair 001', 'Bettor size confirmation 001')
        text = text.replace('eight known cases', 'sixteen fresh cases')
        text = text.replace('Four existing boards, uniform and polarized ranges. No fresh-board claim.',
                            'Eight unseen boards, two per texture, uniform and polarized ranges.')
        text = text.replace('cached_witness_repair_seconds', 'full_witness_repair_seconds')
        text = text.replace("row['proposal_seconds']+candidate['setup_seconds']+",
                            "parent['witness_seconds']+row['proposal_seconds']+"+
                            "candidate['setup_seconds']+")
        text = text.replace('Recorded repair cost includes proposal, training setup/updates and acceptance.',
                            'Repair cost includes fresh bettor witness, proposal, training and acceptance.')
        text = text.replace('The witness is reused from the previous diagnostic, so its acquisition cost is excluded.',
                            'Caller certificate and initial policy generation are preparation costs, separately retained.')
        text = text.replace('1,200,000 bettor updates replayed; 16 incumbent and 16 proposed certificates checked.',
                            '2,400,000 bettor updates replayed; 32 incumbent and 32 proposed certificates checked.')
        text = text.replace('Sixteen exact acceptance decisions', 'Thirty-two exact acceptance decisions')
        text = text.replace('All 29 earlier', 'All 30 earlier')
        text = text.replace('Four new analytic checks and five inherited checks passed before freeze.',
                            'Nine inherited analytic checks and a direct suit-permutation novelty audit passed.')
        text = text.replace('No population, full-range, multiway or live-bot claim.',
                            'Small balanced confirmation panel; no full-range, multiway or live-bot claim.')
        text = text.replace("previous = read(HERE/'preflight.json')['prior_milestones']", '''
summary['panels'] = {}
for category in ('texture', 'regime', 'board'):
    labels = sorted({str(r[category]) for r in cases})
    summary['panels'][category] = {}
    for label in labels:
        subset = [r for r in cases if str(r[category]) == label]
        avg = {k: sum((Q(r['values_exact'][k]) for r in subset), Q(0))/len(subset)
               for k in means_q}
        summary['panels'][category][label] = dict(cases=len(subset),
            means={k: float(v) for k, v in avg.items()},
            repair_minus_control_exact=str(avg['repair']-avg['continuation']))
previous = read(HERE/'preflight.json')['prior_milestones']'''.strip())
        # Formatting only: preserve expressions while wrapping the longer cost sum.
        text = text.replace("parent['witness_seconds']+row['proposal_seconds']+candidate['setup_seconds']+",
                            "parent['witness_seconds']+row['proposal_seconds']+\n            "+
                            "candidate['setup_seconds']+")
    (HERE/dst).write_text(text, encoding='utf-8', newline='\n')
    edits[dst] = dict(source_sha256=digest(raw.encode()), generated_sha256=digest(text.encode()),
        diff=''.join(difflib.unified_diff(raw.splitlines(True), text.splitlines(True),
                                        fromfile='pilot/'+src, tofile='confirmation/'+dst)))
(HERE/'reuse-provenance.json').write_text(json.dumps(edits, indent=2)+'\n', encoding='utf-8')
print({name: len(value['diff']) for name, value in edits.items()})
