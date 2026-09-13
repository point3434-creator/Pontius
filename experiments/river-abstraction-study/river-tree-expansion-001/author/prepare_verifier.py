from pathlib import Path
import hashlib
import json
import difflib

here=Path(__file__).resolve().parent
out=here/'post-verification'
out.mkdir(exist_ok=False)
old=(here/'tree.py').read_text()
before="min(int(np.frexp(np.abs(a[a!=0]))[1].min()) for a in arrays.values() if np.any(a))"
after="min((int(np.frexp(np.abs(a[a!=0]))[1].min()) for a in arrays.values() if np.any(a)), default=53)"
assert old.count(before)==1
new=old.replace(before,after)
(out/'tree.py').write_text(new,encoding='utf-8',newline='\n')
(out/'zero-payoff-fix.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
    fromfile='frozen/tree.py',tofile='verification/tree.py')),encoding='utf-8',newline='\n')
(out/'patch.json').write_text(json.dumps(dict(
    old_sha256=hashlib.sha256((here/'tree.py').read_bytes()).hexdigest(),
    new_sha256=hashlib.sha256((out/'tree.py').read_bytes()).hexdigest(),
    effect='default exponent only when every payoff coefficient is zero; no changed full-case score',
    new_solver_calls=0),indent=2)+'\n',encoding='utf-8')
