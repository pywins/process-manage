# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : base.py

import abc


class BaseWorker(object):
    @abc.abstractmethod
    def run(self, *args, **kv):
        pass
