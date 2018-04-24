# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : worker_base.py
import importlib
import os
from setproctitle import setproctitle

from pid import PidFile, PidFileAlreadyLockedError
from singleton import singleton

from app import logger
from app.core import *
from .configurator import env


def run():
    title = env("title", 'app', 'ProcessManager')
    setproctitle(title)
    # pid directory default is '/var/run'
    # in the PidFile class, will use default if the param piddir is None
    piddir = env('piddir', 'app')
    piddir = os.path.abspath(piddir)
    try:
        with PidFile('proc_mgr', piddir=piddir):
            # application start
            Application().run()
    except PidFileAlreadyLockedError:
        logger.error("A process manager process is running.")
        exit(0)


@singleton()
class Application:
    def __init__(self):
        self.worker_manager = WorkerManager()

    def run(self):
        workers_config = env(key="workers")
        self._parse_all_workers(workers_config)
        num = env('max_worker_number', 'app', 1)
        self.worker_manager.init(max_worker_num=num)

    def _parse_all_workers(self, workers_config):
        """
        Start workers by config.
        :param workers_config:
        :return:
        """
        # step 1. append all workers metadata into a queue
        for worker_name in workers_config.keys():
            worker = workers_config.get(worker_name)
            self._parse_worker(worker_name, worker)

    def _parse_worker(self, name: str, worker: dict):
        if not worker:
            logger.error(f"Do not find worker({name}) config!")
            return

        if not worker.get("worker_package"):
            logger.error(f"Worker({name}) config do not have the 'worker_package' key!")
            return

        if not worker.get("worker_class"):
            logger.error(f"Worker({name}) config do not have the 'worker_class' key!")
            return

        worker_package = worker.get("worker_package")
        worker_class = worker.get("worker_class")
        worker_number = worker.get("worker_number", 1)

        try:
            module = importlib.import_module(worker_package)
            worker_class = getattr(module, worker_class)
            self.worker_manager.append(worker_class, worker_number)
        except TypeError as e:
            logger.error(f"Module {worker_class} is error.\n\t {e}")
