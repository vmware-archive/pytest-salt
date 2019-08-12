# -*- coding: utf-8 -*-
'''
    pytestsalt.fixtures.stats
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test session process stats fixtures
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import os
import sys
from collections import OrderedDict

# Import 3rd-party libs
import psutil

# Import pytest libs
import pytest
from _pytest.terminal import TerminalReporter

IS_WINDOWS = sys.platform.startswith('win')


class SaltTerminalReporter(TerminalReporter):
    def __init__(self, config):
        TerminalReporter.__init__(self, config)
        self._session = None
        self._show_sys_stats = config.getoption('--sys-stats') is True
        self._sys_stats_no_children = config.getoption('--sys-stats-no-children') is True

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

        if self._show_sys_stats is False:
            return

        if self.verbosity > 1:
            self.ensure_newline()
            self.section('Processes Statistics', sep='-', bold=True)
            left_padding = len(max(['System'] + list(self._session.stats_processes), key=len))
            template = '  ...{dots}  {name}  -'
            if not IS_WINDOWS:
                template += '  SWAP: {swap:6.2f} %   CPU: {cpu:6.2f} %'
            else:
                template += '  CPU: {cpu:6.2f} %'
            template += '   MEM: {mem:6.2f} %\n'
            stats = {
                'name': 'System',
                'dots': '.' * (left_padding - len('System')),
                'cpu': psutil.cpu_percent(),
                'mem': psutil.virtual_memory().percent
            }
            if not IS_WINDOWS:
                stats['swap'] = psutil.swap_memory().percent
            self.write(template.format(**stats))

            template = '  ...{dots}  {name}  -'
            if not IS_WINDOWS:
                template += '  SWAP: {swap:6.2f} %   CPU: {cpu:6.2f} %'
            else:
                template += '  CPU: {cpu:6.2f} %'
            children_template = template + '   MEM: {mem:6.2f} %   MEM SUM: {c_mem} %   CHILD PROCS: {c_count}\n'
            no_children_template = template + '   MEM: {mem:6.2f} %\n'

            for name, psproc in self._session.stats_processes.items():
                template = no_children_template
                dots = '.' * (left_padding - len(name))
                try:
                    with psproc.oneshot():
                        stats = {
                            'name': name,
                            'dots': dots,
                            'cpu': psproc.cpu_percent(),
                            'mem': psproc.memory_percent('vms')
                        }
                        if self._sys_stats_no_children is False:
                            children = psproc.children(recursive=True)
                            if children:
                                template = children_template
                                stats['c_count'] = 0
                                c_mem = stats['mem']
                                for child in children:
                                    try:
                                        c_mem += child.memory_percent('vms')
                                        stats['c_count'] += 1
                                    except psutil.NoSuchProcess:
                                        continue
                                if stats['c_count']:
                                    stats['c_mem'] = '{:6.2f}'.format(c_mem)
                                else:
                                    template = no_children_template
                        if not IS_WINDOWS:
                            stats['swap'] = psproc.memory_percent('swap')
                        self.write(template.format(**stats))
                except psutil.NoSuchProcess:
                    continue

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
        ('Test Suite Run', psutil.Process(os.getpid())),
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
    output_options_group.addoption(
        '--sys-stats-no-children',
        default=False,
        action='store_true',
        help='Don\'t include child processes memory statistics.'
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
