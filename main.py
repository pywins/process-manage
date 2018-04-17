# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : worker_base.py

import os

from app import application

if __name__ == '__main__':
    application.run()

    print(f'All subprocesses done.{os.getpid()}')
