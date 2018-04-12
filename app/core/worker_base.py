# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : worker_base.py
import os
import uuid
import signal
import threading
import select
from abc import abstractmethod
from multiprocessing import Queue, Process, Value

from singleton import singleton
from app.logger import logger
from app.decorator import wins_coro

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
        try:
            self.run()
            proc_shared_value.value = WORKER_EXIT_SUCCESS
        except Exception:
            pass

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


class _WorkerListener(threading.Thread):
    """
    Define a new type for thread.
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        logger.debug(f"thread {name} init")
        super().__init__(group, target, name, args, kwargs, daemon=daemon)


@singleton()
class WorkerManager:
    MAX_WORKER_NUMBER = 4

    def __init__(self):
        self._lock = threading.Lock()
        self._worker_queue = Queue()
        self._worker_queue_listener = None
        self._sig_child_queue = Queue()
        self._worker_count = 0
        self._worker_checker = self._check_workers()
        self._worker_info = {}

    def init(self):
        if not self._worker_queue_listener:
            self._worker_queue_listener = _WorkerListener(
                name="WorkerQueueListener", target=self._cb_worker_queue_listener
            )
            self._worker_queue_listener.setDaemon(True)
            self._worker_queue_listener.start()
        self._init_signals()

    def join(self):
        self._cb_sig_child_queue_listener()

    def append(self, worker_class, worker_number):
        if issubclass(worker_class, BaseWorker):
            while worker_number > 0:
                meta = WorkerMetadata(worker=worker_class())
                meta.title = f"python {worker_class}----{worker_number}"
                self._worker_queue.put(meta, False)
                worker_number -= 1

    def _cb_worker_queue_listener(self):
        while True:
            if self._worker_count < self.MAX_WORKER_NUMBER:
                meta = self._worker_queue.get()
                if isinstance(meta, WorkerMetadata):
                    with self._lock:
                        self._new_worker(meta)
                        self._worker_count = len(self._worker_info.keys())
            else:
                select.select([], [], [], 1)

    def _cb_sig_child_queue_listener(self):
        while True:
            self._sig_child_queue.get()
            with self._lock:
                next(self._worker_checker)

    def _new_worker(self, meta: WorkerMetadata):
        logger.debug(f"start worker{meta}")
        meta.proc_shared_exit_code = Value('i', WORKER_EXIT_CODE_ERROR)
        proc = Process(target=meta.target, name=meta.title, args=(meta.proc_shared_exit_code,))
        proc.start()
        self._worker_info[proc.pid] = meta

    def _init_signals(self):
        signal.signal(signal.SIGCHLD, self._handle_child)

    def _handle_child(self, signum, frame):
        """
        signal processor, record a sigchild has occurred.
        so the function will return quickly.
        :param signum:
        :param frame:
        """
        del frame
        self._sig_child_queue.put(signum)

    @wins_coro
    def _check_workers(self):
        """
        A generator for check all the zombie child process. It will run when the sigchild queue not empty.
        """
        while True:
            yield
            reap_pids = self._quit_pids()
            if not reap_pids:
                continue
            for pid in reap_pids:
                # in multiprocess, the worker count must been lock, but this function is a generator,
                # and we have locked for the next function
                meta = None
                if pid in self._worker_info.keys():
                    meta = self._worker_info.get(pid)
                    del self._worker_info[pid]
                    self._worker_count = len(self._worker_info.keys())
                # restart if need
                if meta and isinstance(meta, WorkerMetadata):
                    proc_shared_exit_code = meta.proc_shared_exit_code.value
                    if proc_shared_exit_code == WORKER_EXIT_CODE_ERROR:
                        meta.reset()
                        self._worker_queue.put(meta)

    @staticmethod
    def _quit_pids():
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
