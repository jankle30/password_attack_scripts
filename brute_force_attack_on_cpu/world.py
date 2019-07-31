#timeExample.py
import mwlib
import numpy
import hashlib
import math
from mpi4py import MPI
from time import sleep
from itertools import product
#
# Settings
#
PASSWORD = "f0rm"

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
MAX_LENGTH = 4
LOOKING_FOR_HASH = hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()

#
# Init
#
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
wt = MPI.Wtime()
count = 0
amountOfPackages = 0
suffix_len = 0
moreJobsPending = True


#
# Job Management
#
def job_pending():
    global moreJobsPending
    if moreJobsPending:
        return count<amountOfPackages


def get_job_data():
    job = numpy.zeros(1)
    global count
    count = count + 1
    job[0] = count
    return job

def do_job(data):
    pkgNumber = int(data[0])
    max_short_len = min(suffix_len, MAX_LENGTH)
    status = 0
    matchedPwd = ""
    if pkgNumber == 1:
        # 1st Package
        # oooo|.|.|.|.
        for length in range(1, max_short_len + 1): #(1,4) -> 3 Runden
            for t in product(CHARSET, repeat=length):
                result = "".join(t)
                if LOOKING_FOR_HASH == hashlib.md5(result.encode('utf-8')).hexdigest():
                    matchedPwd = result
                    status = 2
                    break

    else:
        # start from the 2nd Package
        # xxxx|o|.|.|.
        count = 1
        for length in range(max_short_len + 1, MAX_LENGTH + 1):
            for t in product(CHARSET, repeat=length-suffix_len):
                count +=1
                if count == pkgNumber:
                    prefix = "".join(t)
                    for u in product(CHARSET, repeat=suffix_len):
                        result = prefix + "".join(u)
                        if LOOKING_FOR_HASH == hashlib.md5(result.encode('utf-8')).hexdigest():
                            matchedPwd = result
                            status = 2
                            break

    #    result = numpy.zeros(1)
    #    result[0] = 1
    #    return result
    returnObj = [status,matchedPwd]
    return returnObj


#
# Brute Force Package Calculator
#
def calcPackageNumber(pkgNumber):
    max_short_len = min(suffix_len, MAX_LENGTH)
    status = 0
    matchedPwd = ""
    if pkgNumber == 1:
        # 1st Package
        # oooo|.|.|.|.
        for length in range(1, max_short_len + 1): #(1,4) -> 3 Runden
            for t in product(CHARSET, repeat=length):
                result = "".join(t)
                if LOOKING_FOR_HASH == hashlib.md5(result.encode('utf-8')).hexdigest():
                    matchedPwd = "a"
                    status = 2
                    break

    else:
        # start from the 2nd Package
        # xxxx|o|.|.|.
        count = 1
        for length in range(max_short_len + 1, MAX_LENGTH + 1):
            for t in product(CHARSET, repeat=length-suffix_len):
                count +=1
                if count == pkgNumber:
                    prefix = "".join(t)
                    for u in product(CHARSET, repeat=suffix_len):
                        result = prefix + "".join(u)
                        if LOOKING_FOR_HASH == hashlib.md5(result.encode('utf-8')).hexdigest():
                            matchedPwd = "a"
                            status = 2
                            break
                                
#    result = numpy.zeros(1)
#    result[0] = 1
#    return result
    resultObj = [status,matchedPwd]
    return resultObj


#
# Main
#
master = mwlib.master_new(size-1,comm,MPI.INT, MPI.DOUBLE)
splitNumber = 50 # Can be equal to the amount of processes
expected = sum(len(CHARSET)**i for i in range(1, MAX_LENGTH + 1)) # 26^4 + 26^3 + 26^2 + 26^1
suffix_len = int(math.log((expected/splitNumber),len(CHARSET))) 
realSizePerPackage = len(CHARSET)**suffix_len
amountOfPackages = int(math.ceil(expected / realSizePerPackage))


if rank == 0:
    
    
    print "\n----------INFO------------"
    print "Charset Length: %d" % len(CHARSET)
    print "Looking for Hash:" , LOOKING_FOR_HASH
    print "Expected: %d" % expected
    print "Size per Package: %d" % realSizePerPackage
    print "Amount of Packages: %d" % amountOfPackages
    print "suffix len: %d  -> PKG1: %d" % (suffix_len,sum(len(CHARSET)**i for i in range(1, suffix_len + 1)))
    print "--------------------------\n"
    print "Press Enter to start..."
    print raw_input("")

    while job_pending() or mwlib.master_some_working(master):
        w_rank,command = mwlib.master_listen(master)
        if (w_rank):
            if command == mwlib.MW_ask_for_job:
                if job_pending():
                    job_data = get_job_data()
                    print "Paket Nr. %d zu Worker Nr. %d gesendet" % (job_data[0],w_rank)
                    mwlib.master_send_work(master,w_rank,job_data)
            elif command == mwlib.MW_return_result:
                result_data = mwlib.master_get_result(master,w_rank)
                if int(result_data[0]) == 2:
                    moreJobsPending = False
                    print "****************************\nThe matching Password is: %s \n****************************" % result_data[1]
            #print "%g von %d empfangen" % (result_data, w_rank)
            elif command == mwlib.MW_job_done:
                mwlib.master_free_worker(master,w_rank)
    print "----------------End"
    print MPI.Wtime() - wt
    mwlib.master_suspend_all_workers(master)
else:
    worker = mwlib.worker_new(comm,MPI.INT,MPI.DOUBLE)
    status, data = mwlib.worker_get_work(worker)
    while status:
        result_data = do_job(data)
        mwlib.worker_send_result(worker,result_data)
        mwlib.worker_done(worker)
        status, data = mwlib.worker_get_work(worker)







