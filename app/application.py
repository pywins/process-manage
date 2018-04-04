# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : base.py

import os
import signal
import sys
import time
from multiprocessing import Process

import singleton.singleton as singleton

from app.logger import logger


@singleton.Singleton
class Application:
    def __init__(self):
        self.config = {}
        self.workers = {}
        self.reap_pids = []

    def run(self, config):
        self.config = config
        workers_dir = self.config.get("workers_dir")

        logger.info("app started")

        self.setup()
        self.start_workers(workers_dir)
        self.check_workers()

    def check_workers(self):
        """
        检查子进程是否异常：如果子进程的处理在主进程的管理对象中，则重启，如果是异常数据则丢弃
        :return:
        """
        while True:
            time.sleep(1)

            if not self.reap_pids or not self.workers:
                continue

            for pid in self.reap_pids:
                logger.debug("1")
                if pid not in self.workers.keys():
                    self.reap_pids.remove(pid)
                    continue

                worker = self.workers.get(pid)
                logger.debug("2")
                if not isinstance(worker, dict) or 'cls' not in worker.keys():
                    self.reap_pids.remove(pid)
                    del self.workers[pid]
                    continue
                logger.debug("3")
                class_name = worker.get('cls')
                logger.info(f"Restart worker{class_name}")
                o = class_name()
                p = Process(target=o.run, args=())
                self.workers[p.pid] = worker

                self.reap_pids.remove(pid)
                del self.workers[pid]

    def start_workers(self, workers_dir):
        """
        根据给的目录，获取到所有的子进程工作类，并创建子进程，将必要的信号留存，以备后续使用
        :param workers_dir:
        :return:
        """
        workers_dir = os.path.abspath(workers_dir)
        sys.path.append(workers_dir)
        from workers.base import BaseWorker
        for module_name in os.listdir(workers_dir):
            if module_name == "__init__.py" or module_name == "base.py" or module_name[-3:] != ".py":
                continue

            module_name = module_name[0:-3]
            module = __import__(module_name, globals(), locals())

            try:
                class_name = getattr(module, module_name)
                o = class_name()

                if isinstance(o, BaseWorker):
                    p = Process(target=o.run, args=())
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
        while True:
            logger.info("Try clear Zombie child process.")

            try:
                child_pid, status = os.waitpid(-1, os.WNOHANG)

                if not child_pid:
                    logger.debug("No child process was immediately available!")
                    break

                exitcode = status >> 8
                logger.info(f"Child process {child_pid} exit with code {exitcode}!")

                self.reap_pids.append(child_pid)
            except Exception as e:
                logger.error(f"Handle SIGCHLD failed.{e}")
                break
