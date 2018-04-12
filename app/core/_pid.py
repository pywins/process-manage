# -*- coding: utf-8 -*-
# @Time    : 2018/4/12 下午10:14
# @Author  : yx.wu
# @File    : _pid.py
import fcntl
import os, stat


class PIDManager:
    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._pid_file = None

    def acquire(self):
        self.__enter__()

    def release(self):
        self.__exit__()

    def __enter__(self):
        try:
            if os.path.exists(self._path):
                if not os.path.isfile(self._path):
                    raise FileExistsError(f"The pid file {self._path} is a directory.")
            self._pid_file = open(self._path, "a+")
            fcntl.flock(self._pid_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            pid = open(self._path, "r").read()
            raise SystemExit(f"Process id {pid} Already running , pid to {self._path}")
        # except PermissionError:
        #     os.chmod(self._path, stat.S_IWGRP)
        #     self.acquire()

        self._pid_file.seek(0)
        self._pid_file.truncate()
        self._pid_file.write(str(os.getpid()))
        self._pid_file.flush()
        self._pid_file.seek(0)
        return self._pid_file

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        try:
            self._pid_file.close()
        except IOError as err:
            if err.errno != 9:
                raise
        os.remove(self._path)