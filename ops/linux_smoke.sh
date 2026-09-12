#!/usr/bin/env bash
# One-shot check that Pontius runs on this Ubuntu host, before any training work.
# Reports host capacity, installs the pinned interpreter, runs the suite, and
# lists the tools-layer guards that will refuse to run off Windows.
#
#   ./linux_smoke.sh ~/Pontius
set -uo pipefail

repo="${1:-$HOME/Pontius}"
cd "$repo" || { echo "no repository at $repo"; exit 2; }

echo "== host =="
echo "cores:  $(nproc)"
echo "memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "kernel: $(uname -sr)"
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
    echo "cgroup v2 controllers: $(cat /sys/fs/cgroup/cgroup.controllers)"
else
    echo "cgroup v2: ABSENT - systemd MemoryMax will not cap a run on this host"
fi

echo
echo "== interpreter =="
if ! command -v uv >/dev/null; then
    echo "uv missing; install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 2
fi
uv python install 3.14 || exit 2
uv sync --group dev || exit 2
uv run python -c 'import sys, numpy; print(sys.version); print("numpy", numpy.__version__)'

echo
echo "== behavioral suite =="
uv run pytest -p no:cacheprovider -q 2>&1 | tee /tmp/pontius-smoke.log
status=${PIPESTATUS[0]}

echo
echo "== platform guards that still bind this repository to Windows =="
grep -rn --exclude-dir=__pycache__ --exclude-dir=.venv \
    -e "os.name == 'nt'" -e 'os.name == "nt"' -e PureWindowsPath -e CREATE_SUSPENDED \
    tools/ src/ || echo "none found"

echo
echo "pytest exit ${status}; full log at /tmp/pontius-smoke.log"
exit "${status}"
