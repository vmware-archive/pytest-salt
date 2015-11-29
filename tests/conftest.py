# -*- coding: utf-8 -*-

# Import python libs
import logging

if not hasattr(logging, 'TRACE'):
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, 'TRACE')
if not hasattr(logging, 'GARBAGE'):
    logging.GARBAGE = 1
    logging.addLevelName(logging.GARBAGE, 'GARBAGE')


pytest_plugins = 'pytester', 'tornado'


def pytest_configure(config):
    config._inicache['log_format'] = '%(asctime)s,%(msecs)04.0f [%(name)-5s:%(lineno)-4d][%(processName)-8s][%(levelname)-8s] %(message)s'
