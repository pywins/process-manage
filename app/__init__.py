# -*- coding: utf-8 -*-
# @Time    : 2018/4/5 下午9:28
# @Author  : yx.wu
# @File    : __init__.py
import os
from .configurator import load, env
from pid import PidFile, PidFileAlreadyLockedError


def run(config):
    # load config
    load(config=config)
    # pid directory default is '/var/run'
    # in the PidFile class, will use default if the param piddir is None
    piddir = env('piddir', 'app')
    piddir = os.path.abspath(piddir)

    try:
        with PidFile('proc_mgr', piddir=piddir):
            # application start
            from .application import Application
            Application().run()
    except PidFileAlreadyLockedError:
        from .logger import logger
        logger.error("A process manager process is running.")
        exit(0)

