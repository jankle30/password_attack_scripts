from collections import namedtuple
from mpi4py import MPI
from time import sleep
import numpy

num_working_workers = 0

MW_worker_free = 0
MW_worker_working = 1
MW_worker_suspended = 2

MW_listen_tag = 0
MW_send_job_data_tag = 1
MW_recv_result_data_tag = 2

MW_ask_for_job = 0
MW_return_result = 1
MW_job_done = 2



def testFunc (a,b):
    return MyStruct(a,b)



master_str = namedtuple("master_str","num_workers num_working_workers working comm job_dt result_dt")
worker_str = namedtuple("worker_str","comm job_dt result_dt")


def master_new(num_workers, comm, job_dt, result_dt):
    workers = []
    for i in range(num_workers):
        workers.append(MW_worker_free)
    m_s = master_str(num_workers,0,workers,comm,job_dt,result_dt)
    return m_s

def master_some_working (m):
    return (num_working_workers > 0)

def master_listen(m):
    status = MPI.Status()
    comm = m[3]
    flag = comm.iprobe(MPI.ANY_SOURCE,MW_listen_tag,status=status)
    if flag:
        command = comm.recv(source = status.Get_source(), tag = MW_listen_tag)
        return status.Get_source(), command
    return 0, -1

def master_send_work(m, w_rank, data):
    comm = m[3]
    working = m[2]
    comm.send(obj = data, dest = w_rank, tag = MW_send_job_data_tag)
    if working[w_rank-1] == MW_worker_free:
        working[w_rank-1] = MW_worker_working
        global num_working_workers
        num_working_workers += 1

def master_get_result(m, w_rank):
    comm = m[3]
    data = comm.recv(source = w_rank, tag = MW_recv_result_data_tag)
    return data

def master_free_worker (m, w_rank):
    working = m[2]
    if working[w_rank-1] == MW_worker_working:
        global num_working_workers
        num_working_workers -= 1
        working[w_rank-1]=MW_worker_free


def master_suspend_worker (m, w_rank):
    comm = m[3]
    working = m[2]
    emptyList = numpy.zeros(1)
    comm.send(obj = emptyList, dest = w_rank, tag = MW_send_job_data_tag)
    if working[w_rank-1]!=MW_worker_suspended:
        global num_working_workers
        num_working_workers -= 1
    working[w_rank-1] = MW_worker_suspended

def master_suspend_all_workers(m):
    comm = m[3]
    while (m[0] > 0):
        w_rank, command = master_listen(m)
        if w_rank:
            if command == MW_ask_for_job:
                master_suspend_worker(m,w_rank)
            else:
                comm.Abort()
        sleep(0.1)


def worker_new(comm,job_dt,result_dt):
    w_s = worker_str(comm, job_dt, result_dt)
    return w_s

def worker_get_work(w):
    status = MPI.Status()
    comm = w[0]
    comm.send(obj = MW_ask_for_job,dest = 0,tag = MW_listen_tag)
    data = comm.recv(source = 0, tag = MW_send_job_data_tag, status = status)
    return (status.Get_count(MPI.CHAR) > 0), data

def worker_send_result(w,data):
    comm = w[0]
    comm.send(obj = MW_return_result, dest = 0, tag = MW_listen_tag)
    comm.send(obj = data, dest = 0, tag = MW_recv_result_data_tag)


def worker_done(w):
    comm = w[0]
    comm.send(obj = MW_job_done, dest = 0, tag =MW_listen_tag)
















