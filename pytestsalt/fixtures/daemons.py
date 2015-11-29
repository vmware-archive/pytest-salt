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
import socket
import logging
import subprocess


# Import salt libs
import salt.master
import salt.minion
import salt.log.setup
from salt.exceptions import TimedProcTimeoutError
import salt.utils.timed_subprocess as timed_subprocess
from salt.utils.process import SignalHandlingMultiprocessingProcess

# Import 3rd-party libs
import pytest

log = logging.getLogger(__name__)

HANDLED_LEVELS = {
    2: 'warning',       # logging.WARN,    # -v
    3: 'info',          # logging.INFO,    # -vv
    4: 'debug',         # logging.DEBUG,   # -vvv
    5: 'trace',         # logging.TRACE,   # -vvvv
    6: 'garbage'        # logging.GARBAGE  # -vvvvv
}


def get_log_level_name(verbosity):
    '''
    Return the CLI logging level name based on pytest verbosity
    '''
    return HANDLED_LEVELS.get(verbosity,
                              HANDLED_LEVELS.get(verbosity > 6 and 6 or 2))


@pytest.yield_fixture(scope='session')
def mp_logging_setup():
    '''
    Returns the salt process manager from _process_manager.

    We need these two functions to properly shutdown the process manager
    '''
    log.warning('starting multiprocessing logging')
    salt.log.setup.setup_multiprocessing_logging_listener()
    log.warning('multiprocessing logging started')
    yield
    log.warning('stopping multiprocessing logging')
    salt.log.setup.shutdown_multiprocessing_logging()
    salt.log.setup.shutdown_multiprocessing_logging_listener()
    log.warning('multiprocessing logging stopped')


@pytest.yield_fixture
def salt_master(request,
                mp_logging_setup,
                cli_conf_dir,
                cli_master_config):
    '''
    Returns a running salt-master
    '''
    log.warning('Starting CLI salt-master')
    master_process = SaltCliMaster(cli_master_config,
                                   cli_conf_dir.strpath,
                                   request.config.getoption('--cli-bin-dir'),
                                   request.config.getoption('-v'))
    master_process.start()
    # Allow the subprocess to start
    time.sleep(0.5)
    if master_process.is_alive():
        try:
            retcode = master_process.wait_until_running(timeout=10)
            if not retcode:
                os.kill(master_process.pid, signal.SIGTERM)
                master_process.join()
                master_process.terminate()
                pytest.skip('The pytest salt-master has failed to start')
        except TimedProcTimeoutError as exc:
            os.kill(master_process.pid, signal.SIGTERM)
            master_process.join()
            master_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest CLI salt-master is running and accepting connections')
        yield master_process
    else:
        #os.kill(master_process.pid, signal.SIGTERM)
        master_process.join()
        master_process.terminate()
        pytest.skip('The pytest salt-master has failed to start')
    log.warning('Stopping CLI salt-master')
    try:
        os.kill(master_process.pid, signal.SIGTERM)
    except OSError:
        pass
    master_process.join()
    master_process.terminate()
    log.warning('CLI salt-master stopped')


@pytest.yield_fixture
def salt_minion(salt_master, cli_minion_config):
    '''
    Returns a running salt-minion
    '''
    log.warning('Starting CLI salt-minion')
    minion_process = SaltCliMinion(cli_minion_config,
                                   cli_salt_master.config_dir,
                                   cli_salt_master.bin_dir_path,
                                   cli_salt_master.verbosity)
    minion_process.start()
    # Allow the subprocess to start
    time.sleep(0.5)
    if minion_process.is_alive():
        try:
            retcode = minion_process.wait_until_running(timeout=5)
            if not retcode:
                os.kill(minion_process.pid, signal.SIGTERM)
                minion_process.join()
                minion_process.terminate()
                pytest.skip('The pytest salt-minion has failed to start')
        except TimedProcTimeoutError as exc:
            os.kill(minion_process.pid, signal.SIGTERM)
            minion_process.join()
            minion_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest CLI salt-minion is running and accepting commands')
        yield minion_process
    else:
        #os.kill(minion_process.pid, signal.SIGTERM)
        minion_process.join()
        minion_process.terminate()
        pytest.skip('The pytest salt-minion has failed to start')
    log.warning('Stopping CLI salt-minion')
    os.kill(minion_process.pid, signal.SIGTERM)
    minion_process.join()
    minion_process.terminate()
    log.warning('CLI salt-minion stopped')


@pytest.yield_fixture
def salt_call(salt_minion):
    salt_call = SaltCliCall(salt_minion.config,
                            salt_minion.config_dir,
                            salt_minion.bin_dir_path,
                            salt_minion.verbosity)
    yield salt_call


class SaltCliScriptBase(object):

    cli_script_name = None

    def __init__(self, config, config_dir, bin_dir_path, verbosity):
        self.config = config
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.verbosity = verbosity

    def get_script_path(self, script_name):
        return os.path.join(self.bin_dir_path, script_name)

    def get_script_args(self):
        return []


class SaltCliMPScriptBase(SaltCliScriptBase, SignalHandlingMultiprocessingProcess):

    cli_script_name = None

    def __init__(self, config, config_dir, bin_dir_path, verbosity):
        SaltCliScriptBase.__init__(
            self,
            config,
            config_dir,
            bin_dir_path,
            verbosity)
        SignalHandlingMultiprocessingProcess.__init__(
            self,
            log_queue=salt.log.setup.get_multiprocessing_logging_queue())

    def get_check_ports(self):
        return []

    def run(self):
        log.warning('Starting %s CLI DAEMON', self.__class__.__name__)
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
            '-l', get_log_level_name(self.verbosity)
        ] + self.get_script_args()
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        proc = subprocess.Popen(
            proc_args,
        )
        proc.communicate()

    def wait_until_running(self, timeout=None):
        if timeout is not None:
            until = time.time() + timeout
        check_ports = self.get_check_ports()
        connectable = False
        while True:
            if not check_ports:
                connectable = True
                break
            if time.time() >= until:
                break
            for port in set(check_ports):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn = sock.connect_ex(('localhost', port))
                if conn == 0:
                    check_ports.remove(port)
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                del sock
            time.sleep(0.125)
        return connectable


class SaltCliCall(SaltCliScriptBase):

    def run(self, *args, **kwargs):
        return self._salt_call(*args, **kwargs)

    def _salt_call(self, *args, **kwargs):
        timeout = kwargs.pop('timeout', 5)
        proc_args = [
            self.get_script_path('salt-call'),
            '-c',
            self.config_dir,
            '--retcode-passthrough',
            '-l', get_log_level_name(self.verbosity),
        ] + list(args)
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        proc = timed_subprocess.TimedProc(
            proc_args,
            #with_communicate=True
        )
        try:
            log.warning('salt-call finished. retcode: %s', proc.process.returncode)
            return proc.process.returncode == 0
        except TimedProcTimeoutError:
            log.warning('Timed out!!!')
            return False


class SaltCliMinion(SaltCliMPScriptBase):

    cli_script_name = 'salt-minion'

    def get_script_args(self):
        return ['--disable-keepalive']

    def get_check_ports(self):
        return set([self.config['pytest_port']])


class SaltCliMaster(SaltCliMPScriptBase):

    cli_script_name = 'salt-master'

    def get_check_ports(self):
        return set([self.config['ret_port'],
                    self.config['publish_port'],
                    self.config['pytest_port']])


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
