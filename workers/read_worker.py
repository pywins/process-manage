# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 下午8:41
# @Author  : yx.wu
# @File    : put_worker.py
import random
import time

import os

from app.core.worker_base import BaseWorker


class ReadWorker(BaseWorker):
    def run(self, *args, **kv):
        print(f"{os.getpid()} run ...")
        length = random.randrange(5, 15)
        for x in range(length):
            print(f"{os.getpid()} {x}")
            time.sleep(1)
        print(f"{os.getpid()} end ...")
