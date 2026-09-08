"""Copy the reviewed-in-progress proposal text into its isolated authoring tree."""
from pathlib import Path
root = Path('D:/Pontius/tmp/v0a-paired-prereg-r001/authoring')
local = Path(__file__).parent
for origin, relative in [
    ('paired-rehearsal-adr.md', 'docs/decisions/ADR-0510-preregister-the-first-paired-evaluation-rehearsal.md'),
    ('paired-rehearsal-preregistration.md', 'docs/architecture/v0a-paired-prereg-r001/preregistration.md'),
]:
    raw = (local / origin).read_bytes().replace(b'\r\n', b'\n')
    assert b'\r' not in raw and all(line.rstrip() == line for line in raw.decode().splitlines())
    with (root / relative).open('xb') as stream:
        assert stream.write(raw) == len(raw)
print('Two proposed documents installed; no source or runtime execution')
