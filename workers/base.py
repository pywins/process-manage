# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : base.py

import abc
import signal


class BaseWorker(object):
    def __init__(self):
        self.alive = True

    @abc.abstractmethod
    def run(self, *args, **kv):
        pass

    def handle_quit(self, signum, frame):
        self.alive = False

    def start(self, *args, **kwargs):
        """
        graceful stop subprocess
        :param args:
        :param kwargs:
        :return:
        """
        # TODO more signal handler
        signal.signal(signal.SIGQUIT, self.handle_quit)
        self.run(*args, **kwargs)
