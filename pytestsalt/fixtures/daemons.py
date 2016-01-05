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
    0: 'critical',      # logging.CRITICAL  # -v
    1: 'error',         # logging.ERROR     # -vv
    2: 'warning',       # logging.WARN,     # -vvv
    3: 'info',          # logging.INFO,     # -vvvv
    4: 'debug',         # logging.DEBUG,    # -vvvvv
    5: 'trace',         # logging.TRACE,    # -vvvvvv
    6: 'garbage'        # logging.GARBAGE   # -vvvvvvv
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
                cli_master_config,
                io_loop):
    '''
    Returns a running salt-master
    '''
    log.warning('Starting CLI salt-master')
    master_process = SaltCliMaster(cli_master_config,
                                   cli_conf_dir.strpath,
                                   request.config.getoption('--cli-bin-dir'),
                                   request.config.getoption('-v'),
                                   io_loop)
    master_process.start()
    if master_process.is_alive():
        try:
            connectable = master_process.wait_until_running(timeout=10)
            if connectable is False:
                master_process.terminate()
                pytest.skip('The pytest salt-master has failed to start')
        except Exception as exc:  # pylint: disable=broad-except
            master_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest CLI salt-master is running and accepting connections')
        yield master_process
    else:
        master_process.terminate()
        pytest.skip('The pytest salt-master has failed to start')
    log.warning('Stopping CLI salt-master')
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
                                   salt_master.verbosity,
                                   salt_master.io_loop)
    minion_process.start()
    if minion_process.is_alive():
        try:
            connectable = minion_process.wait_until_running(timeout=5)
            if connectable is False:
                minion_process.terminate()
                pytest.skip('The pytest salt-minion has failed to start')
        except Exception as exc:  # pylint: disable=broad-except
            minion_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest CLI salt-minion is running and accepting commands')
        yield minion_process
    else:
        minion_process.terminate()
        pytest.skip('The pytest salt-minion has failed to start')
    log.warning('Stopping CLI salt-minion')
    minion_process.terminate()
    log.warning('CLI salt-minion stopped')


@pytest.yield_fixture
def salt_call(salt_minion):
    salt_call = SaltCliCall(salt_minion.config,
                            salt_minion.config_dir,
                            salt_minion.bin_dir_path,
                            salt_minion.verbosity,
                            salt_minion.io_loop)
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
            self._io_loop.start()
        return self._io_loop

    def get_script_path(self, script_name):
        return os.path.join(self.bin_dir_path, script_name)

    def get_script_args(self):
        return []


class SaltCliDaemonScriptBase(SaltCliScriptBase):

    cli_script_name = None
    proc = None
    pid = None
    stdout = None
    stderr = None
    exitcode = None
    _running = False

    def is_alive(self):
        return self._running

    def get_check_ports(self):
        return []

    def start(self):
        return self.io_loop.run_sync(self._start)

    @gen.coroutine
    def _start(self):
        log.warning('Starting %s CLI DAEMON', self.__class__.__name__)
        self._running = True
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
            '-l', get_log_level_name(self.verbosity)
        ] + self.get_script_args()
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)

        # Allow the IOLoop to do something else
        yield gen.sleep(0.125)
        Subprocess.initialize(self.io_loop)

        self.proc = Subprocess(proc_args)
        self.pid = self.proc.proc.pid

        # Let's make the start() call wait a little for the process to
        # bootstrap without blocking the IOLoop
        yield gen.sleep(0.25)

        @gen.coroutine
        def set_exitcode(future):
            self.exitcode = future.result()
            self._running = False
            # Allow the IOLoop to do something else
            yield gen.moment
            Subprocess.uninitialize()

        self.io_loop.add_future(
            self.proc.wait_for_exit(raise_error=False),
            set_exitcode
        )

    def terminate(self):
        if self.proc is not None:
            def _inner_terminate():
                os.kill(self.pid, signal.SIGTERM)
                try:
                    self.proc.proc.terminate()
                except Exception:
                    pass

                def kill_it_if_hung(signum, frame):
                    log.warning('%s has hung while exiting. Killing it!', self.__class__.__name__)
                    try:
                        os.kill(self.pid, signal.SIGKILL)
                    except Exception:
                        pass

                signal.signal(signal.SIGALRM, kill_it_if_hung)
                signal.alarm(5)
                try:
                    self.proc.proc.communicate()
                except Exception:
                    pass
                # If we reached this far it means that the process didn't hung while exiting. Disable the alarm.
                signal.alarm(0)
                self.proc = None
            self.io_loop.run_sync(_inner_terminate)

    def wait_until_running(self, timeout=None):
        try:
            return self.io_loop.run_sync(self._wait_until_running, timeout=timeout)
        except ioloop.TimeoutError:
            return False

    @gen.coroutine
    def _wait_until_running(self):
        check_ports = self.get_check_ports()
        connectable = False
        while True:
            if not check_ports:
                connectable = True
                break
            for port in set(check_ports):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn = sock.connect_ex(('localhost', port))
                if conn == 0:
                    check_ports.remove(port)
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                del sock
            yield gen.sleep(0.125)
        raise gen.Return(connectable)


class SaltCliCall(SaltCliScriptBase):

    def run_sync(self, *args, **kwargs):
        timeout = kwargs.pop('timeout', 5)
        try:
            return self.io_loop.run_sync(lambda: self._salt_call(*args, **kwargs), timeout=timeout)
        except ioloop.TimeoutError as exc:
            pytest.skip(
                'Failed to run args: {0!r}; kwargs: {1!r}; Error: {2}'.format(
                    args, kwargs, exc
                )
            )

    @gen.coroutine
    def run(self, *args, **kwargs):
        timeout = self.io_loop.time() + kwargs.pop('timeout', 5)
        try:
            result = yield gen.with_timeout(timeout, self._salt_call(*args, **kwargs))
            raise gen.Return(result)
        except gen.TimeoutError as exc:
            pytest.skip(
                'Failed to run args: {0!r}; kwargs: {1!r}; Error: {2}'.format(
                    args, kwargs, exc
                )
            )

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
        # Allow the IOLoop to do something else
        yield gen.moment
        Subprocess.uninitialize()
        raise gen.Return(
            self.ShellResult(exitcode, stdout, stderr)
        )


class SaltCliMinion(SaltCliDaemonScriptBase):

    cli_script_name = 'salt-minion'

    def get_script_args(self):
        return ['--disable-keepalive']

    def get_check_ports(self):
        return set([self.config['pytest_port']])


class SaltCliMaster(SaltCliDaemonScriptBase):

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
