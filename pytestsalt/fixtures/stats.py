# -*- coding: utf-8 -*-
'''
    pytestsalt.fixtures.stats
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test session process stats fixtures
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import os
from collections import OrderedDict

# Import 3rd-party libs
import psutil

# Import pytest libs
import pytest
from _pytest.terminal import TerminalReporter


class SaltTerminalReporter(TerminalReporter):
    def __init__(self, config):
        TerminalReporter.__init__(self, config)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        TerminalReporter.pytest_sessionstart(self, session)
        self._session = session

    def pytest_runtest_logreport(self, report):
        TerminalReporter.pytest_runtest_logreport(self, report)
        if self.verbosity <= 0:
            return
        if report.when != 'call':
            return
        if self.config.getoption('--sys-stats') is False:
            return

        if self.verbosity > 1:
            self.ensure_newline()
            self.section('Processes Statistics', sep='-', bold=True)
            template = ' {}  -  CPU: {:6.2f} %   MEM: {:6.2f} %   SWAP: {:6.2f} %\n'
            self.write(
                template.format(
                    '            System',
                    psutil.cpu_percent(),
                    psutil.virtual_memory().percent,
                    psutil.swap_memory().percent
                )
            )
            for name, psproc in self._session.stats_processes.items():
                with psproc.oneshot():
                    cpu = psproc.cpu_percent()
                    mem = psproc.memory_percent('vms')
                    swap = psproc.memory_percent('swap')
                    self.write(template.format(name, cpu, mem, swap))

    def _get_progress_information_message(self):
        msg = TerminalReporter._get_progress_information_message(self)
        if self.verbosity <= 0:
            return msg
        if self.config.getoption('--sys-stats') is False:
            return msg
        if self.verbosity == 1:
            msg = ' [CPU:{}%] [MEM:{}%]{}'.format(psutil.cpu_percent(),
                                                  psutil.virtual_memory().percent,
                                                  msg)
        return msg


def pytest_sessionstart(session):
    session.stats_processes = OrderedDict((
        ('    Test Suite Run', psutil.Process(os.getpid())),
    ))


def pytest_addoption(parser):
    '''
    register argparse-style options and ini-style config values.
    '''
    output_options_group = parser.getgroup('Output Options')
    output_options_group.addoption(
        '--sys-stats',
        default=False,
        action='store_true',
        help='Print System CPU and MEM statistics after each test execution.'
    )


@pytest.mark.trylast
def pytest_configure(config):
    '''
    called after command line options have been parsed
    and all plugins and initial conftest files been loaded.
    '''
    # Register our terminal reporter
    if not getattr(config, 'slaveinput', None):
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        salt_reporter = SaltTerminalReporter(standard_reporter.config)

        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(salt_reporter, 'terminalreporter')
