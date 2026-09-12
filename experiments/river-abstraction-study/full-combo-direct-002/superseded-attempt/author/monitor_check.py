"""Exercise successful completion and both bounded process stop paths."""
import experiment as e

folder = e.HERE/'monitor-checks'
folder.mkdir(exist_ok=False)
command = [e.sys.executable, '-B', '-c', 'import time; time.sleep(2)']
normal = dict(case_timeout_seconds=5, private_limit_mib=3072)
ok = e.monitor([e.sys.executable, '-B', '-c', 'print(123)'], normal, folder, 'success')
assert ok['exit'] == 0 and ok['stop_reason'] is None and ok['samples'] > 0
timeout = e.monitor(command, dict(normal, case_timeout_seconds=.1), folder, 'timeout')
assert timeout['exit'] != 0 and timeout['stop_reason'] == 'wall_time_limit'
memory = e.monitor(command, dict(normal, private_limit_mib=0), folder, 'memory')
assert memory['exit'] != 0 and memory['stop_reason'] == 'sampled_private_memory_limit'
e.write(e.HERE/'monitor-check.json', dict(passed=True, cases=3))
print('monitor checks: 3/3 passed')
