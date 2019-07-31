#
# DICTIONARY ATTACK - Master Only Knows File
# Master - Worker Distribution
#
#

#timeExample.py
import mwlib
import numpy
import hashlib
import math
from mpi4py import MPI
from time import sleep
from itertools import product
#FILENAME = "/Users/Tobias/Downloads/rockyou.txt"
FILENAME = "/Users/Tobias/Downloads/realhuman_phill.txt"
#FILENAME = "/Users/Tobias/Google Drive/dev/MPI/dicts/cain.txt"
#FILENAME = "/Users/Tobias/Google Drive/dev/MPI/dicts/500pwd.txt"
LOOKING_FOR_HASH = hashlib.md5("~~3mily~~".encode('utf-8')).hexdigest()
PACKAGE_SIZE = 1000000 #219.438    +0 223.69

count = 0
moreJobsPending = True
suffix_len = 0

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
wt = MPI.Wtime()


#
# Job Management
#
def job_pending():
    global moreJobsPending
    return moreJobsPending

def get_job_data(f):
    filename = FILENAME
    pwdPerSegement = PACKAGE_SIZE
    wordArray = []
    for i in range(pwdPerSegement):
        lines = f.readline().rstrip('\n')
        wordArray.append(lines)
        if not lines:
            global moreJobsPending
            moreJobsPending = False
            break
    return wordArray

def do_job(data):
    status = 0
    matchedPwd = ""
    if data:
        for value in data:
            str = unicode(value, errors='ignore')
            if str:
                if LOOKING_FOR_HASH == hashlib.md5((str).encode('utf-8')).hexdigest():
                    matchedPwd = value
                    status = 2
                    break
    result = [status,matchedPwd]
    return result


#
# Main
#
master = mwlib.master_new(size-1,comm,MPI.INT, MPI.DOUBLE)
if rank == 0:
    print "\n----------INFO------------"
    print "Looking for Hash:" , LOOKING_FOR_HASH
    print "Size per Package: %d" % PACKAGE_SIZE
    print "--------------------------\n"
    global input_file
    input_file=open(FILENAME, "rb")
    counter = 0
    while job_pending() or mwlib.master_some_working(master):
        w_rank,command = mwlib.master_listen(master)
        if (w_rank):
            if command == mwlib.MW_ask_for_job:
                if job_pending():
                    job_data = get_job_data(input_file)
                    print "%d nach %d gesendet" % (counter,w_rank)
                    counter += 1
                    mwlib.master_send_work(master,w_rank,job_data)
            elif command == mwlib.MW_return_result:
                result_data = mwlib.master_get_result(master,w_rank)
                print "calc done %d" % (w_rank)
                if int(result_data[0]) == 2:
                    moreJobsPending = False
                    print "Password Found:",result_data[1]
    
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







