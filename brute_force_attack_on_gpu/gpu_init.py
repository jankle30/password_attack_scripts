import pyopencl as cl
import numpy as np
import os
import time
import hashlib
import math

#************************************
#           GPU SETTINGS

os.environ['PYOPENCL_COMPILER_OUTPUT'] = '0'
os.environ['PYOPENCL_CTX'] = '0' #Change Back to '0' on Cluster

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
MAX_PASSWORD_LENGTH = 10
CHARSET_LENGTH = 63

MAX_THREADS = 2**14
INNER_GPU_KERNEL_LOOP = 1024





#***********************************

class CL:
    def BruteInc(self,brute, setLen, wordLength, incBy):
        i = 0
        while(incBy > 0 & i < wordLength):
            add = incBy + brute[i]
            brute[i] = add % setLen
            incBy = (int)(add / setLen)
            i+=1
    
    def __init__(self,search_pw_len):
        self.outta_py_gpu_call_loop = int(math.ceil(((CHARSET_LENGTH**search_pw_len) / np.float128(MAX_THREADS) / INNER_GPU_KERNEL_LOOP)))
        self.passwordLength = search_pw_len
        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx,properties=cl.command_queue_properties.PROFILING_ENABLE)

    def loadProgram(self):
        src = reduce(lambda accum, filename: accum + open(filename, "r").read(), ["gpu_md5lib.cl", "gpu_brute.cl"], "")
        self.program = cl.Program(self.ctx, src).build()

    def popCorn(self,hashValue):
        self.mf = cl.mem_flags
        
        currentBrute = np.zeros(MAX_PASSWORD_LENGTH, dtype=np.uint32)
    
        hash = hashlib.md5(hashValue.encode('utf-8')).hexdigest();
        #print("#START - Looking for MD5-Hash: %s" % hash);

        hashValue = np.array([c for c in hash])
        settingsValue = np.array ([self.passwordLength, CHARSET_LENGTH], dtype=np.uint32)
        
        self.buf_in_currentBrute = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=currentBrute)
        self.hash_buffer = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=hashValue)
        self.settings_buffer = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=settingsValue)

        self.passwordValue = np.array(['\0','\0','\0','\0','\0','\0'])
        self.password_buffer = cl.Buffer(self.ctx, self.mf.WRITE_ONLY | self.mf.COPY_HOST_PTR, hostbuf=self.passwordValue)

        charSet = np.array([c for c in CHARSET])
        self.buf_in_charSet = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=charSet)
        
        destDummy = np.array(range(10), dtype=np.uint32)
        self.dest_buf = cl.Buffer(self.ctx, self.mf.WRITE_ONLY, destDummy.nbytes)

    def execute(self,computerNumber,maxComputerNumber,rank):
        self.amountTime = 0
        #print "RANGE FROM TO", (computerNumber-1) * int(math.ceil(np.float128(self.outta_py_gpu_call_loop) /  maxComputerNumber)),computerNumber * int(math.ceil(np.float128(self.outta_py_gpu_call_loop) /  maxComputerNumber))
        
        for i in range((computerNumber-1) * int(math.ceil(np.float128(self.outta_py_gpu_call_loop) /  maxComputerNumber)),computerNumber * int(math.ceil(np.float128(self.outta_py_gpu_call_loop) /  maxComputerNumber))):
            if i <= self.outta_py_gpu_call_loop:
                if i%100 == 0:
                    print "i is: %i on comp: %i" % (i,rank)
                #reset/ init
                currentBrute = np.zeros(MAX_PASSWORD_LENGTH, dtype=np.uint32)
                self.BruteInc(currentBrute,CHARSET_LENGTH,self.passwordLength,i*INNER_GPU_KERNEL_LOOP*MAX_THREADS)
                self.buf_in_currentBrute = cl.Buffer(self.ctx, self.mf.READ_ONLY | self.mf.COPY_HOST_PTR, hostbuf=currentBrute)
            
                destDummy = np.array(range(10), dtype=np.uint32)
                self.dest_buf = cl.Buffer(self.ctx, self.mf.WRITE_ONLY, destDummy.nbytes)
            
                #print "\nCurrent Brute: ", currentBrute;
                exec_evt = self.program.execBrute(self.queue, (MAX_THREADS,), (256,), self.buf_in_currentBrute,self.buf_in_charSet, self.dest_buf,self.hash_buffer,self.password_buffer, self.settings_buffer)
                
                #exec_evt = self.program.execBrute(self.queue, (MAX_THREADS,), (256,), self.buf_in_currentBrute,self.hash_buffer,self.password_buffer, self.settings_buffer)

                pwdChars = np.empty_like(self.passwordValue)
                cl.enqueue_read_buffer(self.queue, self.password_buffer, pwdChars).wait()



                elapsed = 1e-9*(exec_evt.profile.end - exec_evt.profile.start)
                self.amountTime += elapsed
                #print("Execution time per %i threads: %g s  - %i T/s \n"  % (MAX_THREADS*INNER_GPU_KERNEL_LOOP , elapsed,(MAX_THREADS*INNER_GPU_KERNEL_LOOP/elapsed)) )
                if ("".join(pwdChars) != ""):
                    #print ("**********************************\nFOUND PASSWORD: %s  \n**********************************\n" % ("".join(pwdChars)))
				    return 1,("".join(pwdChars))
				    break
        return 0,""
#print "#END - Execution time: %g s - %i Words\n" % (self.amountTime, MAX_THREADS*INNER_GPU_KERNEL_LOOP*(i+1))

