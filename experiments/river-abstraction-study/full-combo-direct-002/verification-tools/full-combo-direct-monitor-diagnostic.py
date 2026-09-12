import sys
sys.path.insert(0, 'D:/Pontius/tmp/full-combo-direct-author')
import experiment as e
api = e.ct.WinDLL('psapi').GetProcessMemoryInfo
api.argtypes = [e.wt.HANDLE, e.ct.POINTER(e.Memory), e.wt.DWORD]
api.restype = e.wt.BOOL
base = 'C:/Users/point/AppData/Local/Python/pythoncore-3.14-64/python.exe'
code = 'import os,time; x=bytearray(128*1024**2); print(os.getpid(),flush=True); time.sleep(.5)'
records = []
for executable in (e.sys.executable, base):
    with e.subprocess.Popen([executable, '-B', '-c', code], stdout=e.subprocess.PIPE,
                            text=True) as child:
        reported = int(child.stdout.readline())
        info = e.Memory()
        info.cb = e.ct.sizeof(info)
        assert api(int(child._handle), e.ct.byref(info), info.cb)
        records.append(dict(executable=executable, observed_pid=child.pid,
            executing_pid=reported, private_bytes=info.PrivateUsage))
        assert child.wait(timeout=5) == 0
assert records[0]['executing_pid'] != records[0]['observed_pid']
assert records[1]['executing_pid'] == records[1]['observed_pid']
assert records[0]['private_bytes'] < 10*1024**2
assert records[1]['private_bytes'] > 128*1024**2
e.write(e.Path(__file__).with_suffix('.json'), dict(passed=True, records=records))
print(records)
