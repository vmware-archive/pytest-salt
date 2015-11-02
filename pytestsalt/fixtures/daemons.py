# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures.daemons
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Salt daemons fixtures
'''
# pylint: disable=redefined-outer-name

# Import python libs
from __future__ import absolute_import, print_function
import os
import sys
import time
import signal
import logging
import functools
import subprocess

# Import salt libs
import salt.master
import salt.minion
import salt.log.setup
import salt.utils.process as process
import salt.utils.timed_subprocess as timed_subprocess
from salt.exceptions import SaltDaemonNotRunning, TimedProcTimeoutError

# Import 3rd-party libs
import pytest

log = logging.getLogger(__name__)


@pytest.yield_fixture(scope='session')
def _process_manager():
    '''
    Yields a salt process manager
    '''
    # Initialize Salt's multiprocessing logging queue
    salt.log.setup.setup_multiprocessing_logging_listener()

    # Initialize the process manager
    manager = process.ProcessManager(name='Pytest-Salt-ProcessManager')

    # Yield the manager instance
    yield manager

    # Start the manager
    manager.run()


@pytest.yield_fixture(scope='session')
def process_manager(_process_manager):
    '''
    Returns the salt process manager from _process_manager.

    We need these two functions to properly shutdown the process manager
    '''
    yield _process_manager

    log.warning('stop process manager')
    _process_manager.stop_restarting()
    _process_manager.send_signal_to_processes(signal.SIGTERM)
    _process_manager.kill_children()
    salt.log.setup.shutdown_multiprocessing_logging()
    salt.log.setup.shutdown_multiprocessing_logging_listener()


@pytest.fixture(scope='session')
def salt_master(process_manager, master_config, minion_config):
    '''
    Returns a running salt-master
    '''
    master_process = process_manager.add_process(
        SaltMaster,
        args=(master_config, minion_config)
    )
    try:
        master_process.wait_until_running(timeout=5)
    except SaltDaemonNotRunning as exc:
        pytest.skip(str(exc))
    log.info('The pytest salt-master is running and accepting connections')
    return master_process


@pytest.fixture(scope='session')
def salt_minion(process_manager, minion_config, salt_master):
    '''
    Returns a running salt-minion
    '''
    minion_process = process_manager.add_process(
        SaltMinion,
        args=(minion_config,)
    )
    try:
        minion_process.wait_until_running(timeout=5)
    except SaltDaemonNotRunning as exc:
        pytest.skip(str(exc))
    log.info('The pytest salt-minion is running and accepting commands')
    return minion_process


@pytest.yield_fixture(scope='session')
def cli_salt_master(request, process_manager, cli_conf_dir, cli_master_config, cli_minion_config):
    '''
    Returns a running salt-master
    '''
    master_process = process_manager.add_process(
        SaltCliMaster,
        args=(cli_conf_dir, request.config.getoption('--cli-bin-dir'),
              cli_master_config['pidfile'], cli_minion_config['pidfile'])
    )

    # Allow the subprocess to start
    time.sleep(1)
    if master_process.is_alive():
        try:
            master_process.wait_until_running(timeout=10)
        except TimedProcTimeoutError as exc:
            pytest.skip(str(exc))
            del process_manager._process_map[master_process.pid]
        log.info('The pytest salt-master is running and accepting connections')
        yield master_process
    else:
        pytest.skip('The pytest salt-master has failed to start')


@pytest.fixture(scope='session')
def cli_salt_minion(request, process_manager, cli_conf_dir, cli_salt_master, cli_minion_config):
    '''
    Returns a running salt-minion
    '''
    minion_process = process_manager.add_process(
        SaltCliMinion,
        args=(cli_conf_dir, request.config.getoption('--cli-bin-dir'))
    )
    # Allow the subprocess to start
    time.sleep(0.5)
    if minion_process.is_alive():
        try:
            minion_process.wait_until_running(timeout=5)
        except TimedProcTimeoutError as exc:
            del process_manager._process_map[minion_process.pid]
            pytest.skip(str(exc))
        log.info('The pytest salt-minion is running and accepting commands')
        return minion_process
    log.info('The pytest salt-minion has failed to start')


class SaltMinion(process.MultiprocessingProcess):
    '''
    Multiprocessing process for running a salt-minion
    '''
    def __init__(self, minion_opts):
        super(SaltMinion, self).__init__()
        self.minion = salt.minion.Minion(minion_opts)

    def wait_until_running(self, timeout=None):
        '''
        Block waiting until we can confirm that the minion is up and running
        and connected to a master
        '''
        self.minion.sync_connect_master(timeout=timeout)
        # Let's issue a test.ping to make sure the minion's transport stream
        # attribute is set, which will avoid a hanging test session termination
        # because of the following exception:
        #   Exception AttributeError: "'NoneType' object has no attribute 'zmqstream'" in
        #       <bound method Minion.__del__ of <salt.minion.Minion object at 0x7f2c41bf6390>> ignored
        self.minion.functions.test.ping()

    def run(self):
        self.minion.tune_in()


class SaltMaster(SaltMinion):
    '''
    Multiprocessing process for running a salt-master
    '''
    def __init__(self, master_opts, minion_opts):
        super(SaltMaster, self).__init__(minion_opts)
        self.master = salt.master.Master(master_opts)

    def run(self):
        self.master.start()


class SaltCliScriptBase(process.MultiprocessingProcess):

    cli_script_name = None

    def __init__(self, config_dir, bin_dir_path, script_pidfile):
        super(SaltCliScriptBase, self).__init__()
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.script_pidfile = script_pidfile
        self.proc = None

    def get_script_path(self, scrip_name):
        return os.path.join(self.bin_dir_path, scrip_name)

    def _on_signal(self, pid, signum, sigframe):
        # escalate the signal
        os.kill(pid, signum)

    def run(self):
        import signal
        log.warning('Starting %s CLI DAEMON', self.__class__.__name__)
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
            '-l', 'quiet'
        ]
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        proc = subprocess.Popen(
            proc_args,
            #stdout=timed_subprocess.subprocess.PIPE,
            #stderr=timed_subprocess.subprocess.PIPE,
        )
        signal.signal(signal.SIGINT, functools.partial(self._on_signal, proc.pid))
        signal.signal(signal.SIGTERM, functools.partial(self._on_signal, proc.pid))
        proc.communicate()


class SaltCliMinion(SaltCliScriptBase):

    cli_script_name = 'salt-minion'

    def wait_until_running(self, timeout=None):
        proc_args = [
            self.get_script_path('salt-call'),
            '-c',
            self.config_dir,
            '--retcode-passthrough',
            '-l', 'quiet',
            '--out', 'quiet',
            'test.ping'
        ]
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        proc = timed_subprocess.TimedProc(
            proc_args,
            #stdout=timed_subprocess.subprocess.PIPE,
            #stderr=timed_subprocess.subprocess.PIPE,
            with_communicate=True
        )
        proc.wait(timeout)
        log.warning('salt-call finished. retcode: %s', proc.process.returncode)


class SaltCliMaster(SaltCliMinion):

    cli_script_name = 'salt-master'

    def __init__(self, config_dir, bin_dir_path, script_pidfile, minion_pidfile):
        super(SaltCliMaster, self).__init__(config_dir, bin_dir_path, script_pidfile)
        self.minion_pidile = minion_pidfile

    def wait_until_running(self, timeout=None):
        proc_args = [
            self.get_script_path('salt-minion'),
            '-c',
            self.config_dir,
            '--disable-keepalive',
            #'-l',
            #'error'
        ]
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        minion_subprocess = subprocess.Popen(
            proc_args,
            #stdout=timed_subprocess.subprocess.PIPE,
            #stderr=timed_subprocess.subprocess.PIPE,
            #close_fds=True
        )
        # Let's let the minion start
        time.sleep(2)
        try:
            super(SaltCliMaster, self).wait_until_running(timeout=timeout)
            log.warning('Terminating minion after successful salt-call')
            os.kill(minion_subprocess.pid, signal.SIGTERM)
            minion_subprocess.terminate()
        except TimedProcTimeoutError:
            log.warning('Terminating minion after failed salt-call')
            os.kill(minion_subprocess.pid, signal.SIGTERM)
            minion_subprocess.terminate()
            raise
        except Exception as exc:
            log.exception(exc)


def pytest_addoption(parser):
    '''
    Add pytest salt plugin daemons related options
    '''
    saltparser = parser.getgroup('Salt Plugin Options')
    saltparser.addoption(
        '--cli-bin-dir',
        default=os.path.dirname(sys.executable),
        help=('Path to the bin directory where the salt daemon\'s scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )
