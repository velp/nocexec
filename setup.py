# -*- coding: utf-8 -*-
"""
NOCExec
-----------------------
Library for automation of management and configuration of network devices
"""
import sys
import os
from setuptools import setup

if sys.version_info < (2, 7):
    raise Exception("NOCExec requires Python 2.7 or higher.")

# Hard linking doesn't work inside VirtualBox shared folders. This means that
# you can't use tox in a directory that is being shared with Vagrant,
# since tox relies on `python setup.py sdist` which uses hard links. As a
# workaround, disable hard-linking if setup.py is a descendant of /vagrant.
# See
# https://stackoverflow.com/questions/7719380/python-setup-py-sdist-error-operation-not-permitted
# for more details.
if os.path.abspath(__file__).split(os.path.sep)[1] == 'vagrant':
    del os.link

setup(
    name="NOCExec",
    version="0.2a",
    packages=["nocexec"],
    author="Vadim Ponomarev",
    author_email="velizarx@gmail.com",
    url='https://github.com/velp/nocexec',
    license="MIT",
    description='Library for automation of management and configuration of network devices.',
    long_description=__doc__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Plugins',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    install_requires=["pexpect", "ncclient>=0.5"],
    tests_require=["mock>=1.0"],
    extras_require={'docs': ["Sphinx>=1.2.3", "alabaster>=0.6.3"]}
)