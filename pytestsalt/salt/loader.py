# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2016 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


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
