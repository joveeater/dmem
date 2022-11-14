from ctypes import *
import sys

class iovec(Structure):
    _fields_ = [("iov_base",c_void_p),("iov_len",c_size_t)]
    
if('linux' in sys.platform):
	libc = CDLL("libc.so.6")
	vread = libc.process_vm_readv
	vread.argtypes = [c_int, POINTER(iovec), c_ulong, POINTER(iovec), c_ulong, c_ulong]
	vwrite = libc.process_vm_writev
	vwrite.argtypes = [c_int, POINTER(iovec), c_ulong, POINTER(iovec), c_ulong, c_ulong]
elif('win32' in sys.platform):
	from ctypes.wintypes import *
	PROCESS_VM_READ = 0x10
	PROCESS_VM_WRITE = 0X20
	PROCESS_VM_OPERATION = 0x8

	k32 = WinDLL('kernel32')
	k32.OpenProcess.argtypes = DWORD,BOOL,DWORD
	k32.OpenProcess.restype = HANDLE
	k32.ReadProcessMemory.argtypes = HANDLE,LPVOID,LPVOID,c_size_t,POINTER(c_size_t)
	k32.ReadProcessMemory.restype = BOOL
	k32.WriteProcessMemory.argtypes = HANDLE,LPVOID,LPVOID,c_size_t,POINTER(c_size_t)
	k32.WriteProcessMemory.restype = BOOL

else:
	raise Exception("System not supported")


class MemoryScanner:
	def __init__(self, pid, base, size):
		self.pid=pid
		self.base=base
		self.size=size
		
		self.gamecube_base=0x80000000
		if('win32' in sys.platform):
			self.handle = k32.OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION, 0, self.pid)


	if('linux' in sys.platform):

		def read(self, offset, size):
			local = (iovec*1)()
			remote =  (iovec*1)()
			buf = (c_char*size)()
	
			local[0].iov_base = cast(byref(buf),c_void_p)
			local[0].iov_len = size
			remote[0].iov_base = c_void_p(self.base-self.gamecube_base+offset)
			remote[0].iov_len = size
			
			res=vread(self.pid, local, 1, remote, 1, 0)
			if(res!=-1):
				return buf
			else:
				raise OSError("Could not read other process")

		def write(self, offset, size, data):
			local = (iovec*1)()
			remote =  (iovec*1)()
	
			local[0].iov_base = cast(byref(data),c_void_p)
			local[0].iov_len = size
			remote[0].iov_base = c_void_p(self.base-self.gamecube_base+offset)
			remote[0].iov_len = size
			
			res=vwrite(self.pid, local, 1, remote, 1, 0)
			if(res!=-1):
				return True
			else:
				raise OSError("Could not write to other process")		

	elif('win32' in sys.platform):
		def read(self, offset, size):
			buf = (c_char*size)()
			s = c_size_t()
			if(k32.ReadProcessMemory(self.handle, offset, cast(byref(buf),c_void_p), size, byref(s))):
				return buf
			else:
				raise OSError("Could not read other process")

		def write(self, offset, size, data):
			s = c_size_t()
			if(k32.WriteProcessMemory(self.handle, offset, cast(byref(data),c_void_p), size, byref(s))):
				return True
			else:
				raise OSError("Could not write to other process")

	else:
		raise Exception("System not supported")
	

	def read1(self, offset):
		s=self.read(offset, 1)
		return ord(s[0])

	def read2(self, offset):
		s=self.read(offset, 2)
		t=(ord(s[0]) << 8) + ord(s[1])
		return t

	def read4(self, offset):
		s=self.read(offset, 4)
		t=(ord(s[0]) << 24) + (ord(s[1]) << 16) + (ord(s[2]) << 8) + ord(s[3])
		return t
		
	def readString(self, offset):
		s=""
		n=self.read1(offset)
		i=1
		while(n!=0):
			s+=chr(n)
			n=self.read1(offset+i)
			i+=1
		return s
	
	def write1(self, offset, data):
		buf = (c_char*1)(data&0xff)
		return self.write(offset, 1, buf)

	def write2(self, offset, data):
		buf= (c_char*2)((data>>8)&0xff, data&0xff);
		return self.write(offset, 2, buf)
		
	def write4(self, offset, data):
		buf=(c_char*4)((data>>24)&0xff, (data>>16)&0xff, (data>>8)&0xff, data&0xff);
		return self.write(offset, 4, buf)


def ifConnected(state, cb):
	try:
		return cb(state)
	except OSError:
		return None
