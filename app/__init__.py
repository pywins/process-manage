# -*- coding: utf-8 -*-
# @Time    : 2018/4/5 下午9:28
# @Author  : yx.wu
# @File    : __init__.py

from .application import Application
from .configurator import load


def run(config):
    # load config
    load(config=config)

    # application start
    Application().run()

