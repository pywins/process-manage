# -*- coding: utf-8 -*-
# @Time    : 2018/4/5 下午9:28
# @Author  : yx.wu
# @File    : __init__.py
import logging
from .configurator import load, env
from .logger import Logger

# load configure
load('conf/app.conf')

# create logger
logging.setLoggerClass(logger.Logger)
logger = logging.getLogger('ProcessManager')
logger.setLevel(getattr(logging, env("log_level", "log", "DEBUG"), "DEBUG"))
