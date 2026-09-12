# Exact-mean formatting limit

The worker and verifier completed successfully. The first retain.py invocation failed
before writing summary.json, the report or archive: converting an exact Fraction mean
to text exceeded CPython's default 4,300-digit integer-string limit.

Retention was invoked again with -X int_max_str_digits=20000. This raises a finite
formatting limit for trusted, locally computed rational results. No executable bytes,
plan pins, policies, scores, decisions or experiment outputs were changed. The
worker and verifier were not rerun. The second retention invocation must pass every
existing evidence and arithmetic assertion before publishing the local archive.
