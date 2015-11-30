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
import json
import time
import errno
import signal
import socket
import logging
import functools
import subprocess
import multiprocessing
from collections import namedtuple

# Import 3rd-party libs
import salt.ext.six as six
import pytest
from tornado import gen
from tornado import ioloop
from tornado.process import Subprocess

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


@pytest.yield_fixture
def salt_master(request,
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
        except Exception as exc:  # pylint: disable=broad-except
            try:
                os.kill(master_process.pid, signal.SIGTERM)
            except OSError as osexc:
                if osexc.errno != errno.ESRCH:
                    # No such process
                    raise
            master_process.join()
            master_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest CLI salt-master is running and accepting connections')
        yield master_process
    else:
        master_process.terminate()
        pytest.skip('The pytest salt-master has failed to start')
    log.warning('Stopping CLI salt-master')
    try:
        os.kill(master_process.pid, signal.SIGTERM)
    except OSError as exc:
        if exc.errno != errno.ESRCH:
            # No such process
            raise
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
                                   salt_master.config_dir,
                                   salt_master.bin_dir_path,
                                   salt_master.verbosity)
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
        except Exception as exc:  # pylint: disable=broad-except
            try:
                os.kill(minion_process.pid, signal.SIGTERM)
            except OSError as osexc:
                if osexc.errno != errno.ESRCH:
                    # No such process
                    raise
            minion_process.join()
            minion_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest CLI salt-minion is running and accepting commands')
        yield minion_process
    else:
        minion_process.terminate()
        pytest.skip('The pytest salt-minion has failed to start')
    log.warning('Stopping CLI salt-minion')
    try:
        os.kill(minion_process.pid, signal.SIGTERM)
    except OSError as exc:
        if exc.errno != errno.ESRCH:
            # No such process
            raise
    minion_process.join()
    minion_process.terminate()
    log.warning('CLI salt-minion stopped')


@pytest.yield_fixture
def salt_call(salt_minion, io_loop):
    salt_call = SaltCliCall(salt_minion.config,
                            salt_minion.config_dir,
                            salt_minion.bin_dir_path,
                            salt_minion.verbosity,
                            io_loop)
    yield salt_call


class SaltCliScriptBase(object):

    cli_script_name = None

    ShellResult = namedtuple('Result', ('exitcode', 'stdout', 'stderr'))

    def __init__(self, config, config_dir, bin_dir_path, verbosity, io_loop=None):
        self.config = config
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.verbosity = verbosity
        self._io_loop = io_loop

    @property
    def io_loop(self):
        if self._io_loop is None:
            self._io_loop = ioloop.IOLoop.instance()
        return self._io_loop

    def get_script_path(self, script_name):
        return os.path.join(self.bin_dir_path, script_name)

    def get_script_args(self):
        return []


class SaltCliMPScriptBase(SaltCliScriptBase, multiprocessing.Process):

    cli_script_name = None

    def __init__(self, config, config_dir, bin_dir_path, verbosity):
        SaltCliScriptBase.__init__(self, config, config_dir, bin_dir_path, verbosity)
        multiprocessing.Process.__init__(self)

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
        signal.signal(signal.SIGINT, functools.partial(self._on_signal, proc.pid))
        signal.signal(signal.SIGTERM, functools.partial(self._on_signal, proc.pid))
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

    def _on_signal(self, pid, signum, sigframe):
        log.warning('%s CLI DAEMON received signal: %s', self.__class__.__name__, signum)
        # escalate the signal
        os.kill(pid, signum)


class SaltCliCall(SaltCliScriptBase):

    def run(self, *args, **kwargs):
        timeout = kwargs.pop('timeout', 5)
        return self.io_loop.run_sync(lambda: self._salt_call(*args, **kwargs), timeout=timeout)

    @gen.coroutine
    def _salt_call(self, *args, **kwargs):
        raw_output = kwargs.pop('raw_output', False)
        proc_args = [
            self.get_script_path('salt-call'),
            '-c',
            self.config_dir,
            '--retcode-passthrough',
            '-l', get_log_level_name(self.verbosity),
            '--out', 'json'
        ] + list(args)
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        Subprocess.initialize(self.io_loop)
        proc = Subprocess(
            proc_args,
            stdout=Subprocess.STREAM,
            stderr=Subprocess.STREAM,
        )
        exitcode = yield proc.wait_for_exit(raise_error=False)
        stdout = yield proc.stdout.read_until_close()
        if six.PY3:
            stdout = stdout.decode(__salt_system_encoding__)  # pylint: disable=undefined-variable
        if raw_output is False:
            stdout = json.loads(stdout)
        stderr = yield proc.stderr.read_until_close()
        if six.PY3:
            stderr = stderr.decode(__salt_system_encoding__)  # pylint: disable=undefined-variable
        Subprocess.uninitialize()
        raise gen.Return(
            self.ShellResult(exitcode, stdout, stderr)
        )


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
