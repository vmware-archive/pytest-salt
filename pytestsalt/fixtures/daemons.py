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
import signal
import socket
import logging
import subprocess
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
                conf_dir,
                master_id,
                master_config,
                io_loop):
    '''
    Returns a running salt-master
    '''
    log.warning('Starting pytest salt-master(%s)', master_id)
    master_process = SaltMaster(master_config,
                                conf_dir.strpath,
                                request.config.getoption('--cli-bin-dir'),
                                request.config.getoption('-v'),
                                io_loop)
    master_process.start()
    if master_process.is_alive():
        try:
            connectable = master_process.wait_until_running(timeout=10)
            if connectable is False:
                master_process.terminate()
                pytest.skip('The pytest salt-master({0}) has failed to start'.format(master_id))
        except Exception as exc:  # pylint: disable=broad-except
            master_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest salt-master(%s) is running and accepting connections', master_id)
        yield master_process
    else:
        master_process.terminate()
        pytest.skip('The pytest salt-master({0}) has failed to start'.format(master_id))
    log.warning('Stopping pytest salt-master(%s)', master_id)
    master_process.terminate()
    log.warning('Pytest salt-master(%s) stopped', master_id)


@pytest.yield_fixture
def salt_minion(salt_master, minion_id, minion_config):
    '''
    Returns a running salt-minion
    '''
    log.warning('Starting pytest salt-minion(%s)', minion_id)
    minion_process = SaltMinion(minion_config,
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
                pytest.skip('The pytest salt-minion({0}) has failed to start'.format(minion_id))
        except Exception as exc:  # pylint: disable=broad-except
            minion_process.terminate()
            pytest.skip(str(exc))
        log.warning('The pytest salt-minion(%s) is running and accepting commands', minion_id)
        yield minion_process
    else:
        minion_process.terminate()
        pytest.skip('The pytest salt-minion({0}) has failed to start'.format(minion_id))
    log.warning('Stopping pytest salt-minion(%s)', minion_id)
    minion_process.terminate()
    log.warning('pytest salt-minion(%s) stopped', minion_id)


@pytest.yield_fixture
def salt_call(salt_minion):
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(salt_minion.config,
                         salt_minion.config_dir,
                         salt_minion.bin_dir_path,
                         salt_minion.verbosity,
                         salt_minion.io_loop)
    yield salt_call


@pytest.yield_fixture
def salt_key(salt_master):
    '''
    Returns a salt_key fixture
    '''
    salt_key = SaltKey(salt_master.config,
                       salt_master.config_dir,
                       salt_master.bin_dir_path,
                       salt_master.verbosity,
                       salt_master.io_loop)
    yield salt_key


@pytest.yield_fixture
def salt_run(salt_master):
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(salt_master.config,
                       salt_master.config_dir,
                       salt_master.bin_dir_path,
                       salt_master.verbosity,
                       salt_master.io_loop)
    yield salt_run


class SaltScriptBase(object):
    '''
    Base class for Salt CLI scripts
    '''

    cli_script_name = None

    ShellResult = namedtuple('Result', ('exitcode', 'stdout', 'stderr'))

    def __init__(self, config, config_dir, bin_dir_path, verbosity, io_loop=None):  # pylint: disable=too-many-arguments
        self.config = config
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.verbosity = verbosity
        self._io_loop = io_loop

    @property
    def io_loop(self):
        '''
        The io_loop instance. If not passed, one is instantiated
        '''
        if self._io_loop is None:
            self._io_loop = ioloop.IOLoop.instance()
            self._io_loop.start()
        return self._io_loop

    def get_script_path(self, script_name):
        '''
        Returns the path to the script to run
        '''
        return os.path.join(self.bin_dir_path, script_name)

    def get_script_args(self):  # pylint: disable=no-self-use
        '''
        Returns any additional arguments to pass to the CLI script
        '''
        return []


class SaltDaemonScriptBase(SaltScriptBase):
    '''
    Base class for Salt Daemon CLI scripts
    '''

    cli_script_name = None
    proc = None
    pid = None
    stdout = None
    stderr = None
    exitcode = None
    _running = False

    def is_alive(self):
        '''
        Returns true if the process is alive
        '''
        return self._running

    def get_check_ports(self):  # pylint: disable=no-self-use
        '''
        Return a list of ports to check against to ensure the daemon is running
        '''
        return []

    def start(self):
        '''
        Start the daemon subprocess
        '''
        return self.io_loop.run_sync(self._start)

    @gen.coroutine
    def _start(self):
        '''
        The actual, coroutine aware, start method
        '''
        log.warning('Starting pytest %s DAEMON', self.__class__.__name__)
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

        self.proc = Subprocess(' '.join(proc_args), close_fds=True, shell=True)
        self.pid = self.proc.proc.pid

        # Let's make the start() call wait a little for the process to
        # bootstrap without blocking the IOLoop
        yield gen.sleep(0.25)

        @gen.coroutine
        def set_exitcode(future):
            '''
            Set the exitcode in the class instance to the exitcode of the stopped subprocess
            '''
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
        '''
        Terminate the started daemon
        '''
        if self.proc is not None:
            def _inner_terminate():
                '''
                The actual terminate method
                '''
                self.proc.proc.send_signal(signal.SIGTERM)
                try:
                    self.proc.proc.terminate()
                except Exception:  # pylint: disable=broad-except
                    pass
                try:
                    self.proc.proc.communicate()
                except Exception:  # pylint: disable=broad-except
                    pass
                self.proc = None
            self.io_loop.run_sync(_inner_terminate)

    def wait_until_running(self, timeout=None):
        '''
        Blocking call to wait for the daemon to start listening
        '''
        try:
            return self.io_loop.run_sync(self._wait_until_running, timeout=timeout)
        except ioloop.TimeoutError:
            return False

    @gen.coroutine
    def _wait_until_running(self):
        '''
        The actual, coroutine aware, call to wait for the daemon to start listening
        '''
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


class SaltCliScriptBase(SaltScriptBase):
    '''
    Base class which runs Salt's non daemon CLI scripts
    '''

    DEFAULT_TIMEOUT = 5
    SCRIPT_NAME = None

    def run_sync(self, *args, **kwargs):
        '''
        Run the given command synchronously
        '''
        timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        try:
            return self.io_loop.run_sync(lambda: self._run_script_pre(*args, **kwargs), timeout=timeout)
        except ioloop.TimeoutError as exc:
            pytest.skip(
                'Failed to run {0} args: {1!r}; kwargs: {2!r}; Error: {3}'.format(
                    self.SCRIPT_NAME, args, kwargs, exc
                )
            )

    @gen.coroutine
    def run(self, *args, **kwargs):
        '''
        Run the given command asynchronously
        '''
        timeout = self.io_loop.time() + kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        try:
            result = yield gen.with_timeout(timeout, self._run_script_pre(*args, **kwargs))
            raise gen.Return(result)
        except gen.TimeoutError as exc:
            pytest.skip(
                'Failed to run args: {0!r}; kwargs: {1!r}; Error: {2}'.format(
                    args, kwargs, exc
                )
            )

    @gen.coroutine
    def _run_script_pre(self, *args, **kwargs):
        '''
        This method just calls the actual run script method and chains the post
        processing of it.
        '''
        timeout = kwargs.pop('timeout', 5)
        raw_output = kwargs.pop('raw_output', False)
        proc = yield self._run_script(*args, **kwargs)
        result = yield self._run_script_post(proc, timeout, raw_output)
        raise gen.Return(result)

    @gen.coroutine
    def _run_script(self, *args, **kwargs):
        '''
        This method can be overridden by subclasses and it should return
        the process instantiated.
        '''
        proc_args = [
            self.get_script_path(self.SCRIPT_NAME),
            '-c',
            self.config_dir,
            '-l', get_log_level_name(self.verbosity),
            '--out', 'json'
        ] + self.get_script_args() + list(args)
        log.warn('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)
        Subprocess.initialize(self.io_loop)
        proc = Subprocess(
            proc_args,
            stdout=Subprocess.STREAM,
            stderr=Subprocess.STREAM,
        )
        raise gen.Return(proc)

    @gen.coroutine
    def _run_script_post(self, proc, timeout, raw_output):
        '''
        This method takes care of waiting for the process to finish or cancel
        it in case the timeout is exceded.
        It will also return a ShellResult in the end
        '''
        def terminate_proc():
            '''
            Terminate the process in case a pytest.skip was issued or the process
            did not exit correctly
            '''
            proc.proc.send_signal(signal.SIGTERM)
            try:
                proc.proc.terminate()
            except Exception:  # pylint: disable=broad-except
                pass
            try:
                proc.proc.communicate()
            except Exception:  # pylint: disable=broad-except
                pass
        # Make sure that, if the timeout occurrs, the process will be properly shut down
        terminate_timeout = self.io_loop.add_timeout(self.io_loop.time() + timeout,
                                                     terminate_proc)

        # Let's wait for the process to exit
        exitcode = yield proc.wait_for_exit(raise_error=False)

        # If the process exited, remove the terminate_timeout
        self.io_loop.remove_timeout(terminate_timeout)

        # Process output
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


class SaltCall(SaltCliScriptBase):
    '''
    Class which runs salt-call commands
    '''

    SCRIPT_NAME = 'salt-call'

    def get_script_args(self):
        return [
            '--retcode-passthrough',
        ]


class SaltKey(SaltCliScriptBase):
    '''
    Class which runs salt-key commands
    '''

    SCRIPT_NAME = 'salt-key'


class SaltRun(SaltCliScriptBase):
    '''
    Class which runs salt-run commands
    '''

    SCRIPT_NAME = 'salt-run'


class SaltMinion(SaltDaemonScriptBase):
    '''
    Class which runs the salt-minion daemon
    '''

    cli_script_name = 'salt-minion'

    def get_script_args(self):
        return ['--disable-keepalive']

    def get_check_ports(self):
        return set([self.config['pytest_port']])


class SaltMaster(SaltDaemonScriptBase):
    '''
    Class which runs the salt-minion daemon
    '''

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
