# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 下午8:41
# @Author  : yx.wu
# @File    : put_worker.py

import time

from app.core.worker_base import BaseWorker


class PutWorker(BaseWorker):
    def run(self, *args, **kv):
        print("run ...")
        for x in range(10):
            print(x)
            time.sleep(1)
        print("end ...")
