#
# DICTIONARY ATTACK - Workers Know File
# Master - Worker Distribution
#
#

#timeExample.py
import libtest
import numpy
import hashlib
import math
from mpi4py import MPI
from time import sleep
from itertools import product
#FILENAME = "/realhuman_phill.txt"
#FILENAME = "/Users/Tobias/Google Drive/dev/MPI/dicts/cain.txt"
FILENAME = "/Users/Tobias/Google Drive/dev/MPI/dicts/500pwd.txt"
LOOKING_FOR_HASH = hashlib.md5("albert".encode('utf-8')).hexdigest()
PACKAGE_SIZE = 1

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

def get_job_data():
    job = numpy.zeros(1)
    global count
    count = count + 1
    job[0] = count
    return job

def do_job(data):
    return checksum_md5(int(data[0]))

#
# Job
#
def checksum_md5(pkgNumber = 0):
    if pkgNumber != 0:
        filename = FILENAME
        pwdPerSegement = PACKAGE_SIZE
        start = pwdPerSegement*(pkgNumber-1)
        end = pwdPerSegement*(pkgNumber)
        status = 0
        matchedPwd = ""
        stillData = False
        starttest = MPI.Wtime()
        with open(filename,'rb') as f:
            for line_num, line in enumerate(f):
                if start <= line_num:
                    if line_num <= end:
                        result = line.rstrip('\n')
                        str = unicode(result, errors='ignore')
                        if str:
                            if LOOKING_FOR_HASH.lower() == hashlib.md5(str.encode('utf-8')).hexdigest().lower():
                                matchedPwd = result
                                status = 2
                                break
                    else:
                        break
            #EOF
            else:
                status = 1
        # 1st Pos: 0 = Dont Stop, 1 eof, 2 pwdFound
        # 2nd Pos: Result Data, "" for Default
        # exmpl: [1, "password"] Stop, Result found
        result = [status,matchedPwd]
        return result
    return [1,""]

#
# Main
#
master = libtest.master_new(size-1,comm,MPI.INT, MPI.DOUBLE)
if rank == 0:
    print "\n----------INFO------------"
    print "Looking for Hash:" , LOOKING_FOR_HASH
    print "Size per Package: %d" % PACKAGE_SIZE
    print "--------------------------\n"
    
    while job_pending() or libtest.master_some_working(master):
        w_rank,command = libtest.master_listen(master)
        if (w_rank):
            if command == libtest.MW_ask_for_job:
                if job_pending():
                    job_data = get_job_data()
                    print "%d nach %d gesendet" % (job_data[0],w_rank)
                    libtest.master_send_work(master,w_rank,job_data)
                else:
                    libtest.master_suspend_worker(master,w_rank)
            elif command == libtest.MW_return_result:
                result_data = libtest.master_get_result(master,w_rank)
                #EOF
                if int(result_data[0]) == 1:
                    moreJobsPending = False
                #PWD found
                elif int(result_data[0]) == 2:
                    moreJobsPending = False
                    print "PWD found:",result_data[1]
    
            #print "%g von %d empfangen" % (result_data, w_rank)
            elif command == libtest.MW_job_done:
                libtest.master_free_worker(master,w_rank)
        sleep(0.00001)

    print "----------------End"
    print MPI.Wtime() - wt
    libtest.master_suspend_all_workers(master)
else:
    worker = libtest.worker_new(comm,MPI.INT,MPI.DOUBLE)
    status, data = libtest.worker_get_work(worker)
    while status:
        result_data = do_job(data)
        libtest.worker_send_result(worker,result_data)
        libtest.worker_done(worker)
        status, data = libtest.worker_get_work(worker)







