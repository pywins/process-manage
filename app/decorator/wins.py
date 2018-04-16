# -*- coding: utf-8 -*-
# @Time    : 2018/4/16 15:58
# @Author  : William
# @File    : wins.py

from functools import wraps


def wins_coro(func):
    @wraps(func)
    def primer(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen

    return primer
