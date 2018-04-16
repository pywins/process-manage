#!/usr/bin/env python

import os
import os.path

# from distutils.core import setup, Command
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='precess-manage',
    version='0.1',
    description='Manage your process (Master Worker Mode)',
    long_description=open('README.md').read(),
    keywords=["precess-manage", "pywins"],
    author='pywins',
    install_requires=['pysingleton', 'setproctitle', 'toml', 'pid'],
    packages=['precess-manage'],
    license="MIT",
    classifiers=[
        'Development Status :: 1 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6+',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
