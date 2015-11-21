# -*- coding: utf-8 -*-

# Import python libs
import logging

if not hasattr(logging, 'TRACE'):
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, 'TRACE')
if not hasattr(logging, 'GARBAGE'):
    logging.GARBAGE = 1
    logging.addLevelName(logging.GARBAGE, 'GARBAGE')


pytest_plugins = 'pytester'
