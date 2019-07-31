import mwlib as MWL
import numpy as np
import hashlib
import math
import gpu_init as GPU_Init
from mpi4py import MPI
from time import sleep



#
# Settings
#
MAX_PASSWORD_SEARCH_LEN = 6
HASH_VALUE = "ZZZZZZ"
#
# Init
#
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


jobCounter = 0 #Job jobCounterer
workerSize = size-1 # Workers without Master
moreJobsPending = True
passwordSearchLen = 1
passwordFound = False


#
# Job Management
#
def job_pending():
    global moreJobsPending
    if moreJobsPending:
        return jobCounter<workerSize
    else:
        return False

#MASTER AREA
def get_job_data():
    job = np.zeros(20)
    global jobCounter
    jobCounter = jobCounter + 1
    #0:Job Number
    job[0] = jobCounter
    #1:Current PW Search Length
    global passwordSearchLen
    job[1] = passwordSearchLen
    for i in range(2,len(HASH_VALUE)+2):
        job[i] = ord(HASH_VALUE[i-2])
    return job

#WORKER AREA
def do_job(data,aocc,pwlen,pwstring):
    #Init OpenCl Stuff
    BF_GPU = GPU_Init.CL(pwlen)
    
    #Load Kernel Code
    BF_GPU.loadProgram()
    
    #Init Buffers for Kernel
    BF_GPU.popCorn(pwstring)
    #Execute GPU Code
    flag, pwValue = BF_GPU.execute(data,aocc,rank)
    if flag == 1:
        returnObj = [2,pwValue]
    else:
        returnObj = [0,""]
    return returnObj


#
# Main
#
master = MWL.master_new(size-1,comm,MPI.INT, MPI.DOUBLE)


if rank == 0:
    print "\n\n\n\n\n\n\n"
    print "\n----------INFO------------"
    print "Size of Cluster: %d" % workerSize
    print "--------------------------\n"
    print "Press Enter to start..."
    print raw_input("")
    wt = MPI.Wtime()
    passwordFound = False
    while ((passwordSearchLen <= MAX_PASSWORD_SEARCH_LEN) and passwordFound == False):
        print "LEN PW SEARCH:",passwordSearchLen
        while job_pending() or MWL.master_some_working(master):
            w_rank,command = MWL.master_listen(master)
            if (w_rank):
                if command == MWL.MW_ask_for_job & job_pending():
                    if job_pending():
                        job_data = get_job_data()
                        print "Paket Nr. %d zu Worker Nr. %d gesendet" % (job_data[0],w_rank)
                        MWL.master_send_work(master,w_rank,job_data)
                    else:
                        MWL.master_send_fake_work(master,w_rank)
                elif command == MWL.MW_return_result:
                    result_data = MWL.master_get_result(master,w_rank)
                    if int(result_data[0]) == 2:
                        moreJobsPending = False
                        if not passwordFound:
                            print "****************************\nThe matching Password is: %s \n****************************" % result_data[1]
                            print MPI.Wtime() - wt
                            MWL.master_suspend_all_workers(master)

                        passwordFound = True
                elif command == MWL.MW_job_done:
                    MWL.master_free_worker(master,w_rank)
        #Reset for new PW Len
        passwordSearchLen += 1
        moreJobsPending = True
        jobCounter = 0

    print "----------------End"
    print MPI.Wtime() - wt
    MWL.master_suspend_all_workers(master)
else:
    worker = MWL.worker_new(comm,MPI.INT,MPI.DOUBLE)
    status, data = MWL.worker_get_work(worker)
    while status:
        pwstring = ""
        jobnr = int(data[0])
        pwlen = int(data[1])
        if len(data) > 2:
            i = 2
            while int(data[i]) != 0:
                pwstring +=chr(int(data[i]))
                i+=1
        if jobnr != -1:
            result_data = do_job(jobnr,workerSize,pwlen,pwstring)
        else:
            result_data = [0,0]
        MWL.worker_send_result(worker,result_data)
        MWL.worker_done(worker)
        status, data = MWL.worker_get_work(worker)

