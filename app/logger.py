# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 上午10:07
# @Author  : yx.wu
# @File    : logger.py

import logging
import sys


class _Stream2Logger(object):
    """
    Redirect the stream like stdout or stderr into the logger.
    The stdout and stderr could bee assign with a new object which have a write function,
    like write(self, buf). So we define a class for it.

    example : sys.stderr = StreamToLogger(logger, logging.DEBUG)

    """

    def __init__(self, logger_object: logging.Logger, logger_level=logging.INFO):
        """
        Create stream to logger object
        :type logger: object
        """
        self.logger = logger_object
        self.level = logger_level

    def write(self, buf):
        """
        Write stream to logger file or other handler.
        :param buf:
        """
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


class _Logger(logging.Logger):
    """
    Create my logger class which defined the format and the handlers.
    We will both send the message to the stdout and file.
    """
    def __init__(self, name, level=logging.DEBUG):
        """
        init logger and set all properties that we need.
        :param name:
        :param level:
        """
        logging.Logger.__init__(self, name, level)

        # create formatter
        log_format = "%(asctime)-15s [%(process)d] [%(levelname)s] %(message)s at %(filename)s(%(lineno)d)"
        date_format = "%Y-%m-%d %X"
        formatter = logging.Formatter(log_format, date_format)

        # create file handler
        log_path = "./log.log"
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)

        # add handler and formatter to logger
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)

        # create stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)

        # add handler and formatter to logger
        stdout_handler.setFormatter(formatter)
        self.addHandler(stdout_handler)

        # redirect stdout & stderr
        sl = _Stream2Logger(self, level)
        sys.stdout = sl
        sys.stderr = sl


# create logger
logger_name = "ProcessManager"
logging.setLoggerClass(_Logger)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)
