"""Narrow Windows cuBLAS FP64 bridge; supported native capture, no CuPy patching."""
import ctypes as c
import os
from pathlib import Path

DLL=Path('C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/x64/cublas64_13.dll')


class Blas:
    def __init__(self,stream):
        self.directory=os.add_dll_directory(str(DLL.parent))
        self.lib=c.WinDLL(str(DLL))
        ptr=c.c_void_p
        self.lib.cublasCreate_v2.argtypes=[c.POINTER(ptr)]
        self.lib.cublasSetStream_v2.argtypes=[ptr,ptr]
        self.lib.cublasDestroy_v2.argtypes=[ptr]
        self.lib.cublasDgemm_v2.argtypes=[ptr,c.c_int,c.c_int,c.c_int,c.c_int,c.c_int,
            ptr,ptr,c.c_int,ptr,c.c_int,ptr,ptr,c.c_int]
        for name in ('cublasCreate_v2','cublasSetStream_v2','cublasDestroy_v2','cublasDgemm_v2'):
            getattr(self.lib,name).restype=c.c_int
        self.handle=ptr()
        self.check(self.lib.cublasCreate_v2(c.byref(self.handle)))
        self.check(self.lib.cublasSetStream_v2(self.handle,stream.ptr))
        self.one,self.zero=c.c_double(1),c.c_double(0)

    @staticmethod
    def check(status):
        if status: raise RuntimeError(f'cuBLAS status {status}')

    def product(self,a,x,out,transpose):
        n=a.shape[0]
        assert a.shape==(n,n) and a.flags.c_contiguous
        # Row-major A is column-major A.T. transpose=True computes A @ x.
        self.check(self.lib.cublasDgemm_v2(self.handle,int(transpose),0,n,1,n,
            c.byref(self.one),a.data.ptr,n,x.data.ptr,n,c.byref(self.zero),out.data.ptr,n))

    def close(self):
        if self.handle:
            self.check(self.lib.cublasDestroy_v2(self.handle))
            self.handle=c.c_void_p()
            self.directory.close()
