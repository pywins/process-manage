# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : worker_base.py
import functools
import os
import signal
import uuid
import asyncio
from abc import abstractmethod
from multiprocessing import Queue, Process, Value
from setproctitle import setproctitle
from singleton import singleton
from app import logger

WORKER_EXIT_CODE_ERROR = -1
WORKER_EXIT_SUCCESS = 0


class BaseWorker(object):
    def __init__(self):
        self.alive = True

    @abstractmethod
    def run(self):
        pass

    def start(self, proc_shared_value):
        signal.signal(signal.SIGQUIT, self.quit_handler)
        self.run()
        proc_shared_value.value = WORKER_EXIT_SUCCESS

    def quit_handler(self):
        self.alive = False


class WorkerException(Exception):
    pass


class WorkerMetadata:
    """
    The metadata for a worker.
    The main application will manage a list of object which create from this class.
    """

    def __init__(self, worker: BaseWorker):
        self.flag = uuid.uuid1()
        self.title = self.flag
        self.target = worker.start
        self.worker = worker
        self.proc_shared_exit_code = None

    def reset(self):
        self.proc_shared_exit_code = None


class _Process(Process):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)

    def start(self):
        setproctitle(self.name)
        super().start()


@singleton()
class WorkerManager:
    def __init__(self):
        self.worker_count = 0
        self.worker_info = {}
        self.worker_ctrl = Queue()
        self.worker_reap = asyncio.Queue()
        self.lock = asyncio.Lock()
        self.sig_exit = [signal.SIGEMT, signal.SIGQUIT]
        self.max_worker_number = 1

    async def ctrl_worker_task(self):
        while True:
            await asyncio.sleep(1)
            # check the worker count
            if self.worker_count >= self.max_worker_number:
                continue
            # check the waiting queue
            if self.worker_ctrl.empty():
                continue
            # check meta data
            meta = self.worker_ctrl.get()
            if not isinstance(meta, WorkerMetadata):
                continue
            with await self.lock:
                self.new_worker(meta)
                self.worker_count = len(self.worker_info.keys())

    async def reap_worker_task(self):
        while True:
            await self.worker_reap.get()
            # collect the zombie state process's pid, if there is empty, await when the next SIGCHLD single come
            reap_pids = self.get_quit_pids()
            if not reap_pids:
                continue

            # maybe two or more process will killed or stopped at the same time
            # we must check all of the processes
            for pid in reap_pids:
                # in multiprocess, the worker count must been lock, but this function is a generator,
                # and we have locked for the next function
                with await self.lock:
                    if pid not in self.worker_info.keys():
                        continue
                    meta = self.worker_info.get(pid)
                    del self.worker_info[pid]
                    self.worker_count = len(self.worker_info.keys())
                # restart if need
                if not isinstance(meta, WorkerMetadata):
                    continue
                # check the shared exit code
                proc_shared_exit_code = meta.proc_shared_exit_code.value
                if proc_shared_exit_code == WORKER_EXIT_CODE_ERROR:
                    meta.reset()
                    self.worker_ctrl.put(meta)
            # done from the queue
            self.worker_reap.task_done()

    async def entry(self):
        reap_worker = asyncio.ensure_future(self.reap_worker_task())
        ctrl_worker = [self.ctrl_worker_task()]
        await asyncio.wait(ctrl_worker)
        reap_worker.cancel()

    def init(self, max_worker_num):
        self.max_worker_number = max_worker_num
        loop = asyncio.get_event_loop()
        try:
            for signum in self.sig_exit:
                loop.add_signal_handler(signum, functools.partial(self.handle_exit, signum, loop))
            loop.add_signal_handler(signal.SIGCHLD, functools.partial(self.handle_child, signal.SIGCHLD, None))
            loop.run_until_complete(self.entry())
        except KeyboardInterrupt as e:
            loop.stop()
            logger.error(f"Exit by {e}")
        finally:
            loop.close()

    def append(self, worker_class, worker_number):
        if issubclass(worker_class, BaseWorker):
            while worker_number > 0:
                meta = WorkerMetadata(worker=worker_class())
                meta.title = f"ProcessManager {worker_class}-{worker_number}"
                self.worker_ctrl.put(meta, False)
                worker_number -= 1

    def new_worker(self, meta: WorkerMetadata):
        logger.debug(f"start worker{meta}")
        meta.proc_shared_exit_code = Value('i', WORKER_EXIT_CODE_ERROR)
        proc = _Process(target=meta.target, name=meta.title, args=(meta.proc_shared_exit_code,))
        proc.start()
        self.worker_info[proc.pid] = meta

    def handle_child(self, signum, frame):
        """
        signal processor, record a sigchild has occurred.
        so the function will return quickly.
        :param signum:
        :param frame:
        """
        del frame
        self.worker_reap.put_nowait(signum)

    @staticmethod
    def handle_exit(signum, loop: asyncio.AbstractEventLoop):
        logger.error("got signal %s: exit" % signum)
        loop.stop()

    @staticmethod
    def get_quit_pids():
        """
        Using waitpid() function to get the child process's pid which quited.
        """
        pids = []
        while True:
            try:
                child_pid, status = os.waitpid(-1, os.WNOHANG)
                # no more child in zombie status, break and reap child processes
                if not child_pid:
                    break
                exitcode = status >> 8
                logger.info(f"Child process {child_pid} exit with code {exitcode}!")
                pids.append(child_pid)
            except OSError as e:
                logger.debug(f"Handle SIGCHLD failed.{e}.")
                break
        return pids
