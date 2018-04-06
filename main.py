# -*- coding: utf-8 -*-
# @Time    : 2018/4/4 上午9:51
# @Author  : yx.wu
# @File    : base.py

import os
import app

if __name__ == '__main__':
    app.run('conf/app.conf')

    print(f'All subprocesses done.{os.getpid()}')
