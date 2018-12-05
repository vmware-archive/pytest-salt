# -*- coding: utf-8 -*-
'''
pytestsalt.fixtures.log
~~~~~~~~~~~~~~~~~~~~~~~

Log server fixture which creates a server that receives log records
from external process to log them in the current process
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import sys
import logging

# Import pytest libs
import pytest

if sys.version_info > (3, 5):
    from pytestsalt.utils.log_server_asyncio import log_server_asyncio as salt_log_server
else:
    from pytestsalt.utils.log_server_tornado import log_server_tornado as salt_log_server


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def log_server_level(request):
    # If PyTest has no logging configured, default to ERROR level
    levels = [logging.ERROR]
    logging_plugin = request.config.pluginmanager.get_plugin('logging-plugin')
    try:
        level = logging_plugin.log_cli_handler.level
        if level is not None:
            levels.append(level)
    except AttributeError:
        # PyTest CLI logging not configured
        pass
    try:
        level = logging_plugin.log_file_level
        if level is not None:
            levels.append(level)
    except AttributeError:
        # PyTest Log File logging not configured
        pass

    level_str = logging.getLevelName(min(levels))
    return level_str


@pytest.fixture(scope='session')
def log_server(salt_log_port):
    log.warning('Starting log server')
    salt_log_server(salt_log_port)

    log.warning('Log Server Started')
    # Run tests
    yield
