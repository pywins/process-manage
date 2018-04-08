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

    def start(self, *args, **kv):
        signal.signal(signal.SIGQUIT, self.quit_handler)
        self.run(*args, **kv)

    def quit_handler(self):
        self.alive = False
