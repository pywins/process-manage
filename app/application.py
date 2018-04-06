# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : base.py

import os
import select
import signal
import sys
from multiprocessing import Process
from singleton import singleton

from .decorator import wins_coro
from .configurator import env
from .logger import logger

from workers.base import BaseWorker


@singleton()
class Application:
    def __init__(self):
        self.config = {}
        self.workers = {}
        self.list_reap_pid = []
        self.checker = self.check_workers()

    def run(self):
        workers_dir = env("workers_dir", section="workers")

        logger.info("app started")

        self.setup()
        self.start_workers(workers_dir)

        # # init the checker generator
        # self.checker.send(None)

        while True:
            # just simple suspend
            select.select([], [], [], 1.0)
            pass

    def start_workers(self, workers_dir):
        """
        根据给的目录，获取到所有的子进程工作类，并创建子进程，将必要的信号留存，以备后续使用
        :param workers_dir:
        :return:
        """
        workers_dir = os.path.abspath(workers_dir)
        # TODO  No module named 'PutWorker' if comment
        sys.path.append(workers_dir)

        for module_name in os.listdir(workers_dir):
            if module_name == "__init__.py" or module_name == "base.py" or module_name[-3:] != ".py":
                continue

            module_name = module_name[0:-3]
            module = __import__(module_name, globals(), locals())

            try:
                class_name = getattr(module, module_name)
                o = class_name()

                if isinstance(o, BaseWorker):
                    p = Process(target=o.run)
                    p.start()
                    self.workers[p.pid] = {"cls": class_name}

            except TypeError as e:
                logger.error(f"Module {module_name} is invalid. See the worker rules.")
            except Exception as e:
                logger.error(f"Error raised: {type(e)}{e}")

    def setup(self):
        self.init_signals()

    def init_signals(self):
        signal.signal(signal.SIGCHLD, self.handle_child)

    def handle_child(self, signum, frame):
        """
        SIGCHLD 信号处理方法，主要工作，记录子进程 ID
        :param signum:
        :param frame:
        :return:
        """
        logger.info("Try clear zombie child process.")
        next(self.checker)

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
                if pid not in self.workers.keys():
                    continue

                worker = self.workers.get(pid)

                if not isinstance(worker, dict) or 'cls' not in worker.keys():
                    del self.workers[pid]
                    continue

                class_name = worker.get('cls')
                logger.info(f"Restart worker{class_name}")
                o = class_name()
                p = Process(target=o.run)
                p.start()
                self.workers[p.pid] = worker

                del self.workers[pid]

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
                self.list_reap_pid.append(child_pid)

            except OSError as e:
                logger.error(f"Handle SIGCHLD failed.{e}.")
                break
