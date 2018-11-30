# -*- coding: utf-8 -*-
'''
pytestsalt.salt.loader
~~~~~~~~~~~~~~~~~~~~~~

Salt loader support
'''

# Import python libs
import os

THIS_MODULE_DIR = os.path.abspath(os.path.dirname(__file__))


def engines_dirs():
    yield os.path.join(THIS_MODULE_DIR, 'engines')


def log_handlers_dirs():
    yield os.path.join(THIS_MODULE_DIR, 'log_handlers')
