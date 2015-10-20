# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt
    ~~~~~~~~~~

    PyTest Salt Plugin
'''

# Import python libs
from __future__ import absolute_import
import sys
import logging

# Import 3rd-party libs
import py

TERMINAL = py.io.TerminalWriter(sys.stderr)  # pylint: disable=no-member
FORMATTER = logging.Formatter(
    '%(asctime)s,%(msecs)03.0f [%(name)-5s:%(lineno)-4d]'
    '[%(levelname)-8s] %(message)s',
    datefmt='%H:%M:%S'
)

CONSOLEHANDLER = logging.StreamHandler(TERMINAL)
CONSOLEHANDLER.setLevel(logging.FATAL)
CONSOLEHANDLER.setFormatter(FORMATTER)
if not hasattr(logging, 'TRACE'):
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, 'TRACE')
if not hasattr(logging, 'GARBAGE'):
    logging.GARBAGE = 1
    logging.addLevelName(logging.GARBAGE, 'GARBAGE')

logging.root.addHandler(CONSOLEHANDLER)

HANDLED_LEVELS = {
    2: logging.WARN,    # -v
    3: logging.INFO,    # -vv
    4: logging.DEBUG,   # -vvv
    5: logging.TRACE,   # -vvvv
    6: logging.GARBAGE  # -vvvvv
}

log = logging.getLogger('pytest.salt')
log.info('pytest salt logging has been setup')


def pytest_cmdline_main(config):
    '''
    called for performing the main command line action. The default
    implementation will invoke the configure hooks and runtest_mainloop.
    '''
    verbosity = config.getoption('-v')
    if verbosity > 1:
        CONSOLEHANDLER.setLevel(HANDLED_LEVELS.get(verbosity, verbosity > 6 and 6 or 2))
