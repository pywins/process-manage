# -*- coding: utf-8 -*-
# @Time    : 2018/4/5 下午9:00
# @Author  : yx.wu
# @File    : configurator.py

import toml
from singleton import singleton


@singleton()
class Configurator:
    def __init__(self):
        self.config = {}

    def load(self, config_file):
        self.config = toml.load(config_file)
        return self.config

    def get(self, key=None, section=None, default=None):
        if not key:
            return self.config

        config = self.config if (not section) else self.config.get(section, None)
        if config:
            return config.get(key, default)
        return default


def load(config):
    Configurator().load(config_file=config)


def env(key=None, section=None, default=None):
    return Configurator().get(key, section=section, default=default)
