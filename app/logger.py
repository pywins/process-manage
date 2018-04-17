# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 上午10:07
# @Author  : yx.wu
# @File    : logger.py

import logging
import sys

from app.configurator import env

LOG_HANDLE_FILE = "file"
LOG_HANDLE_STDOUT = "stdout"


class _Stream2Logger(object):
    """
    Redirect the stream like stdout or stderr into the logger.
    The stdout and stderr could bee assign with a new object which have a write function,
    like write(self, buf). So we define a class for it.
    example : sys.stderr = StreamToLogger(logger, logging.DEBUG)
    """

    def __init__(self, logger_object: logging.Logger, logger_level=logging.ERROR):
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


class Filter(logging.Filter):
    """
    add stack info while logging level >= Error
    """

    def __init__(self, trim_amount=5):
        self.trim_amount = trim_amount

    def filter(self, record):
        import traceback
        if record.levelno >= logging.WARNING:
            record.stack_info = ''.join(
                str(row) for row in traceback.format_stack()[:-self.trim_amount]
            )
        return True


class Logger(logging.Logger):
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
        log_format = "[%(levelname)s] %(asctime)-15s [%(process)d]  %(message)s %(filename)s(%(lineno)d)"
        date_format = "%Y-%m-%d %X"
        formatter = logging.Formatter(log_format, date_format)
        log_out = env("log_out", "log", [LOG_HANDLE_STDOUT])
        log_path = env("log_file", "log")
        if log_path and LOG_HANDLE_FILE in log_out:
            # create file handler
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(level)
            # add handler and formatter to logger
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)

        # self.addFilter(Filter())
        self.info("logger module have been loaded")

        # create stdout handler
        if LOG_HANDLE_STDOUT in log_out:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(level)
            # add handler and formatter to logger
            stdout_handler.setFormatter(formatter)
            self.addHandler(stdout_handler)

        # redirect stdout & stderr
        sl = _Stream2Logger(self)
        # sys.stdout = sl
        sys.stderr = sl
