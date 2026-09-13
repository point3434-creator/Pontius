from pathlib import Path
import difflib
old=Path(__file__).parent/'probe.py'
dest=old.parent/'trace-correction'
dest.mkdir(exist_ok=False)
text=old.read_text()
text=text.replace("sources={str(p.resolve()):p.read_text().splitlines() for p in trace_sources()}",
                  "sources={os.path.normcase(str(p.resolve())):p.read_text().splitlines() for p in trace_sources()}")
text=text.replace('sources[frame.f_code.co_filename]',
                  'sources[os.path.normcase(frame.f_code.co_filename)]')
text=text.replace('if frame.f_code.co_filename not in sources or',
                  'if os.path.normcase(frame.f_code.co_filename) not in sources or')
text=text.replace("for p in sources+[Path(__file__)]: pins[str(p)]=e.d.digest(p)",
    "for p in sources+[Path(__file__),HERE/'monitor-check.json',HERE.parent/'probe.py',\n"
    "                       HERE.parent/'plan.json',HERE.parent/'run/receipt.json']:\n"
    "        pins[str(p)]=e.d.digest(p)")
text=text.replace("def selftest():\n",'''def selftest():
    # Exact isolated-worker import spelling must exercise the original mismatch.
    from scipy.optimize import linprog
    sources={os.path.normcase(str(p.resolve())) for p in trace_sources()}
    raw={str(p.resolve()) for p in trace_sources()}
    functions={'_clean_inputs','_format_A_constraints','_linprog_highs','_highs_wrapper'}
    seen={}
    def observe(frame,event,arg):
        if event=='call' and frame.f_code.co_name in functions:
            key=frame.f_code.co_filename
            if os.path.normcase(key) in sources:
                seen[frame.f_code.co_name]=dict(file=key,original_filter_matches=key in raw)
        return None
    sys.settrace(observe)
    try:
        result=linprog([-1.],A_ub=sparse.csc_matrix([[1.]]),b_ub=[1.],
                       bounds=[(0,1)],method='highs-ds')
    finally:
        sys.settrace(None)
    assert result.success and result.x.tolist()==[1.]
    assert set(seen)==functions,seen
    assert not any(v['original_filter_matches'] for v in seen.values()),seen
''')
text=text.replace("sparse_bytes=buffers['matrix']['bytes']))", "sparse_bytes=buffers['matrix']['bytes'],trace_boundary_control=seen))")
text=text.replace("receipt.update(label=job['label'],events=len(events),last_source=events[-1]['source_line'])",
    "assert any(v['function']=='_highs_wrapper' for v in events), 'native boundary missing'\n"
    "        receipt.update(label=job['label'],events=len(events),last_source=events[-1]['source_line'])")
(dest/'probe.py').write_text(text,encoding='utf-8',newline='\n')
(dest/'probe.diff').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),
    text.splitlines(True),fromfile='original/probe.py',tofile='trace-correction/probe.py')),
    encoding='utf-8',newline='\n')
print(dest)
