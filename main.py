# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : base.py

import os

from app.application import Application

workers_dir = './workers'


if __name__ == '__main__':
    app = Application()

    config = {'workers_dir': workers_dir}

    app.run(config)

    print(f'All subprocesses done.{os.getpid()}')
