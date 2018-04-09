# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : worker_base.py
import os
import abc
import signal
import uuid
import threading

from multiprocessing import Value, Queue, Process

import time
from singleton import singleton

from app.core.logger import logger
from app.decorator import wins_coro


class BaseWorker(object):
    def __init__(self):
        self.alive = True

    @abc.abstractmethod
    def run(self):
        pass

    def start(self):
        signal.signal(signal.SIGQUIT, self.quit_handler)
        self.run()

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
        self.target = worker.start
        self.worker = worker
        self.pid = None
        self.alive = None


class _WorkerListener(threading.Thread):
    """
    Define a new type for thread.
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        logger.debug("Worker Listener init")
        super().__init__(group, target, name, args, kwargs, daemon=daemon)


@singleton()
class WorkerManager:
    MAX_WORKER_NUMBER = 7

    def __init__(self):
        self._lock = threading.Lock()
        self._worker_listener = None
        self._sig_child_listener = None
        self._worker_info = {}
        self._worker_queue = Queue()
        self._sig_child_queue = Queue()
        self._worker_count = 0
        self.list_reap_pid = []
        self.checker = self.check_workers()

    def init(self):
        if not self._worker_listener:
            self._worker_listener = _WorkerListener(name="WorkerListener", target=self.worker_listener_callback)
            self._worker_listener.start()

        if not self._sig_child_listener:
            self._sig_child_listener = _WorkerListener(name="SigChildListener", target=self.sig_child_listener_callback)
            self._sig_child_listener.start()

        self.init_signals()

    def append(self, worker_class, worker_number):
        if not self._worker_listener or not self._sig_child_listener:
            self.init()

        if issubclass(worker_class, BaseWorker):
            while worker_number > 0:
                meta = WorkerMetadata(worker=worker_class())
                self._worker_queue.put(meta, False)
                worker_number -= 1

    def worker_listener_callback(self):
        while True:
            if self._worker_count < self.MAX_WORKER_NUMBER:
                meta = self._worker_queue.get()
                if isinstance(meta, WorkerMetadata):
                    self._new_worker(meta)
                    self._worker_count += 1
            else:
                time.sleep(5)

    def sig_child_listener_callback(self):
        while True:
            self._sig_child_queue.get()
            next(self.checker)

    def _new_worker(self, meta: WorkerMetadata):
        logger.debug(f"start worker{meta}")
        proc = Process(target=meta.target)
        proc.start()
        meta.pid = proc.pid
        self._worker_info[meta.pid] = meta

    def init_signals(self):
        signal.signal(signal.SIGCHLD, self.handle_child)

    def handle_child(self, signum, frame):
        """
        SIGCHLD 信号处理方法，主要工作，记录子进程 ID
        :param signum:
        :param frame:
        :return:
        """
        self._sig_child_queue.put(1, False)

    @wins_coro
    def check_workers(self):
        """
        检查子进程是否异常：如果子进程的处理在主进程的管理对象中，则重启，如果是异常数据则丢弃
        :return:
        """
        while True:
            yield
            self.get_zombie_pid()

            if not self.list_reap_pid:
                continue

            for pid in self.list_reap_pid:
                pass

            logger.debug("after reap zombie process.")

    def get_zombie_pid(self):
        while True:
            try:
                child_pid, status = os.waitpid(-1, os.WNOHANG)

                if not child_pid:
                    logger.debug("No child process was immediately available!")
                    break

                exitcode = status >> 8
                logger.info(f"Child process {child_pid} exit with code {exitcode}!")

                if exitcode > 0:
                    self.list_reap_pid.append(child_pid)

            except OSError as e:
                logger.error(f"Handle SIGCHLD failed.{e}.")
                break

