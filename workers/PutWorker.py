# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 下午8:41
# @Author  : yx.wu
# @File    : PutWorker.py

import time

from workers.base import BaseWorker


class PutWorker(BaseWorker):
    def run(self, *args, **kv):
        print("run ...")
        for x in range(20):
            print(x)
            time.sleep(1)
        print("end ...")
