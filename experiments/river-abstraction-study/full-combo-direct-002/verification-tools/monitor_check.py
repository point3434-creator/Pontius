"""Real worker allocation plus normal and stopped paths, with PID identity."""
import experiment as e
folder = e.HERE/'monitor-checks'
folder.mkdir(exist_ok=False)
normal = dict(case_timeout_seconds=5, private_limit_mib=3072)
command = [e.BASE_PYTHON, '-I', '-S', '-B', '-c', 'import time; time.sleep(2)']
ok = e.monitor([e.BASE_PYTHON, '-I', '-S', '-B', '-c', 'print(123)'], normal, folder, 'success')
assert ok['exit'] == 0 and ok['stop_reason'] is None
allocation = e.monitor(e.child_command([str(e.HERE/'allocate.py')]), normal, folder, 'allocation')
assert allocation['exit'] == 0 and allocation['stop_reason'] is None
pid = int((folder/'allocation-stdout.txt').read_text().strip())
assert pid == allocation['observed_pid']
assert allocation['sampled_peak_private_bytes'] > 128*1024**2
timeout = e.monitor(command, dict(normal, case_timeout_seconds=.1), folder, 'timeout')
assert timeout['exit'] != 0 and timeout['stop_reason'] == 'wall_time_limit'
memory = e.monitor(e.child_command([str(e.HERE/'allocate.py')]),
                   dict(normal, private_limit_mib=64), folder, 'memory')
assert memory['exit'] != 0 and memory['stop_reason'] == 'sampled_private_memory_limit'
e.write(e.HERE/'monitor-check.json', dict(passed=True, cases=4))
print('monitor checks: 4/4 passed')
