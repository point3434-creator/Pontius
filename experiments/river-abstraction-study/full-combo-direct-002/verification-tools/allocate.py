import os
import time
x = bytearray(128*1024**2)
print(os.getpid(), flush=True)
time.sleep(.3)
