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
import time
import sys
import json
import socket
import logging
import multiprocessing
from collections import namedtuple

# Import 3rd-party libs
import salt.ext.six as six
import pytest
from tornado import gen
from tornado import ioloop
from tornado import concurrent
from tornado.process import Subprocess
from concurrent.futures import ThreadPoolExecutor

# Import salt libs
import salt.utils.vt as vt
from salt.utils.process import SignalHandlingMultiprocessingProcess

log = logging.getLogger(__name__)


def cli_bin_dir(config):
    '''
    Return the path to the CLI script directory to use
    '''
    path = config.getoption('cli_bin_dir')
    if path is not None:
        # We were passed --cli-bin-dir as a CLI option
        return path

    # The path was not passed as a CLI option
    path = config.getini('cli_bin_dir')
    if path is not None:
        # We were passed cli_bin_dir as a INI option
        return path

    # Default to the directory of the current python executable
    return os.path.dirname(sys.executable)


def get_threadpool_executors(config):
    '''
    Return the number of threads the ThreadPoolExecutor should use
    '''
    executors = config.getoption('thread_executors')
    if executors is not None:
        return executors

    executors = config.getini('thread_executors')
    if executors is not None:
        try:
            return int(executors)
        except ValueError:
            pass

    return 4


@pytest.fixture(scope='session')
def pytestsalt_executor(request):
    '''
    Return a session scoped ThreadPoolExecutor
    '''
    return ThreadPoolExecutor(
        max_workers=get_threadpool_executors(request.config))


@pytest.yield_fixture
def salt_master_prep():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-master and after ending it.
    '''
    # Prep routines for the salt master go here

    # Start the salt-master
    yield

    # Clean routines for the salt master go here


@pytest.yield_fixture
def salt_master(request,
                conf_dir,
                master_id,
                master_config,
                salt_master_prep,  # pylint: disable=unused-argument
                io_loop,
                pytestsalt_executor):
    '''
    Returns a running salt-master
    '''
    log.info('Starting pytest salt-master(%s)', master_id)
    master_process = SaltMaster(master_config,
                                conf_dir.strpath,
                                cli_bin_dir(request.config),
                                io_loop,
                                pytestsalt_executor)
    master_process.start()
    if master_process.is_alive():
        try:
            connectable = master_process.wait_until_running(timeout=10)
            if connectable is False:
                master_process.terminate()
                pytest.xfail('The pytest salt-master({0}) has failed to start'.format(master_id))
        except Exception as exc:  # pylint: disable=broad-except
            master_process.terminate()
            pytest.xfail(str(exc))
        log.info('The pytest salt-master(%s) is running and accepting connections', master_id)
        yield master_process
    else:
        master_process.terminate()
        pytest.xfail('The pytest salt-master({0}) has failed to start'.format(master_id))
    log.info('Stopping pytest salt-master(%s)', master_id)
    master_process.terminate()
    log.info('Pytest salt-master(%s) stopped', master_id)


@pytest.yield_fixture
def salt_minion_prep():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-minion and after ending it.
    '''
    # Prep routines for the salt minion go here

    # Start the salt-minion
    yield

    # Clean routines for the salt minion go here


@pytest.yield_fixture
def salt_minion(salt_master,
                minion_id,
                minion_config,
                salt_minion_prep):  # pylint: disable=unused-argument
    '''
    Returns a running salt-minion
    '''
    log.info('Starting pytest salt-minion(%s)', minion_id)
    minion_process = SaltMinion(minion_config,
                                salt_master.config_dir,
                                salt_master.bin_dir_path,
                                salt_master.io_loop,
                                salt_master.executor)
    minion_process.start()
    if minion_process.is_alive():
        try:
            connectable = minion_process.wait_until_running(timeout=10)
            if connectable is False:
                minion_process.terminate()
                pytest.xfail('The pytest salt-minion({0}) has failed to start'.format(minion_id))
        except Exception as exc:  # pylint: disable=broad-except
            minion_process.terminate()
            pytest.xfail(str(exc))
        log.info('The pytest salt-minion(%s) is running and accepting commands', minion_id)
        yield minion_process
    else:
        minion_process.terminate()
        pytest.xfail('The pytest salt-minion({0}) has failed to start'.format(minion_id))
    log.info('Stopping pytest salt-minion(%s)', minion_id)
    minion_process.terminate()
    log.info('pytest salt-minion(%s) stopped', minion_id)


@pytest.yield_fixture
def salt_call_prep():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-call and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_call(salt_minion, salt_call_prep):  # pylint: disable=unused-argument
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(salt_minion.config,
                         salt_minion.config_dir,
                         salt_minion.bin_dir_path,
                         salt_minion.io_loop,
                         salt_minion.executor)
    yield salt_call


@pytest.yield_fixture
def salt_key_prep():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-key and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_key(salt_master, salt_key_prep):  # pylint: disable=unused-argument
    '''
    Returns a salt_key fixture
    '''
    salt_key = SaltKey(salt_master.config,
                       salt_master.config_dir,
                       salt_master.bin_dir_path,
                       salt_master.io_loop,
                       salt_master.executor)
    yield salt_key


@pytest.yield_fixture
def salt_run_prep():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-run and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_run(salt_master, salt_run_prep):  # pylint: disable=unused-argument
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(salt_master.config,
                       salt_master.config_dir,
                       salt_master.bin_dir_path,
                       salt_master.io_loop,
                       salt_master.executor)
    yield salt_run


class SaltScriptBase(object):
    '''
    Base class for Salt CLI scripts
    '''

    cli_script_name = None

    def __init__(self,
                 config,
                 config_dir,
                 bin_dir_path,
                 io_loop=None,
                 executor=None):  # pylint: disable=too-many-arguments
        self.config = config
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self._io_loop = io_loop
        self._executor = executor

    @property
    def io_loop(self):
        '''
        Return an IOLoop
        '''
        if self._io_loop is None:
            self._io_loop = ioloop.IOLoop.current()
        return self._io_loop

    @property
    def executor(self):
        '''
        Return a ThreadPoolExecutor
        '''
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=4)
        return self._executor

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

    def __init__(self, *args, **kwargs):
        super(SaltDaemonScriptBase, self).__init__(*args, **kwargs)
        self._running = multiprocessing.Event()
        self._connectable = multiprocessing.Event()
        self._process = None

    def is_alive(self):
        '''
        Returns true if the process is alive
        '''
        return self._running.is_set()

    def get_check_ports(self):  # pylint: disable=no-self-use
        '''
        Return a list of ports to check against to ensure the daemon is running
        '''
        return []

    def start(self):
        '''
        Start the daemon subprocess
        '''
        self._process = SignalHandlingMultiprocessingProcess(
            target=self._start, args=(self._running,))
        self._process.start()
        self._running.set()
        return True

    def _start(self, running_event):
        '''
        The actual, coroutine aware, start method
        '''
        log.info('Starting pytest %s DAEMON', self.__class__.__name__)
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
        ] + self.get_script_args()
        log.info('Running \'%s\' from %s...', ' '.join(proc_args), self.__class__.__name__)

        terminal = vt.Terminal(proc_args,
                               stream_stdout=False,
                               log_stdout=True,
                               #log_stdout_level='warning',
                               stream_stderr=False,
                               log_stderr=True,
                               #log_stderr_level='warning'
                               )
        self.pid = terminal.pid

        while running_event.is_set() and terminal.has_unread_data:
            # We're not actually interessed in processing the output, just consume it
            terminal.recv()
            time.sleep(0.125)

        # Let's close the terminal now that we're done with it
        terminal.close(kill=True)
        self.exitcode = terminal.exitstatus

    def terminate(self):
        '''
        Terminate the started daemon
        '''
        self._running.clear()
        self._connectable.clear()
        self._process.terminate()

    def wait_until_running(self, timeout=None):
        '''
        Blocking call to wait for the daemon to start listening
        '''
        if self._connectable.is_set():
            return True
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
        while self._running.is_set():
            if not check_ports:
                self._connectable.set()
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
        raise gen.Return(self._connectable.is_set())


class SaltCliScriptBase(SaltScriptBase):
    '''
    Base class which runs Salt's non daemon CLI scripts
    '''

    DEFAULT_TIMEOUT = 5
    ShellResult = namedtuple('Result', ('exitcode', 'stdout', 'stderr', 'json'))

    def run_sync(self, *args, **kwargs):
        '''
        Run the given command synchronously
        '''
        timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        try:
            return self.io_loop.run_sync(lambda: self._run_script(*args, **kwargs), timeout=timeout)
        except ioloop.TimeoutError as exc:
            pytest.xfail(
                'Failed to run {0} args: {1!r}; kwargs: {2!r}; Error: {3}'.format(
                    self.cli_script_name, args, kwargs, exc
                )
            )

    @gen.coroutine
    def run(self, *args, **kwargs):
        '''
        Run the given command asynchronously
        '''
        try:
            result = yield self._run_script(*args, **kwargs)
            raise gen.Return(result)
        except gen.TimeoutError as exc:
            pytest.xfail(
                'Failed to run {0} args: {1!r}; kwargs: {2!r}; Error: {3}'.format(
                    self.cli_script_name, args, kwargs, exc
                )
            )

    #@concurrent.run_on_executor
    @gen.coroutine
    def _run_script(self, *args, **kwargs):
        '''
        This method just calls the actual run script method and chains the post
        processing of it.
        '''
        timeout_expire = time.time() + kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
            '--out', 'json'
        ] + self.get_script_args() + list(args)
        terminal = vt.Terminal(proc_args,
                               stream_stdout=False,
                               log_stdout=True,
                               #log_stdout_level='warning',
                               stream_stderr=False,
                               log_stderr=True,
                               #log_stderr_level='warning'
                               )

        # Consume the output
        stdout = ''
        stderr = ''
        timedout = False
        while terminal.has_unread_data:
            try:
                out, err = terminal.recv()
            except IOError:
                out = err = ''
            if out:
                stdout += out
            if err:
                stderr += err
            if timeout_expire < time.time():
                timedout = True
                break
            yield gen.sleep(0.001)
            #time.sleep(0.025)

        # Let's close the terminal now that we're done with it
        terminal.close(kill=True)
        if timedout:
            raise gen.TimeoutError('Timmed out!')
        exitcode = terminal.exitstatus
        try:
            json_out = json.loads(stdout)
        except ValueError:
            json_out = None
        raise gen.Return(self.ShellResult(exitcode, stdout, stderr, json_out))
        return self.ShellResult(exitcode, stdout, stderr, json_out)


class SaltCall(SaltCliScriptBase):
    '''
    Class which runs salt-call commands
    '''

    cli_script_name = 'salt-call'

    def get_script_args(self):
        return ['--retcode-passthrough']


class SaltKey(SaltCliScriptBase):
    '''
    Class which runs salt-key commands
    '''

    cli_script_name = 'salt-key'


class SaltRun(SaltCliScriptBase):
    '''
    Class which runs salt-run commands
    '''

    cli_script_name = 'salt-run'


class SaltMinion(SaltDaemonScriptBase):
    '''
    Class which runs the salt-minion daemon
    '''

    cli_script_name = 'salt-minion'

    def get_script_args(self):
        return ['--disable-keepalive', '-l', 'quiet']

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

    def get_script_args(self):
        return ['-l', 'quiet']


def pytest_addoption(parser):
    '''
    Add pytest salt plugin daemons related options
    '''
    saltparser = parser.getgroup('Salt Plugin Options')
    saltparser.addoption(
        '--thread-executors',
        default=None,
        type=int,
        help='Number of threads to assign to the ThreadPoolExecutor. Defaults to 4.')
    saltparser.addoption(
        '--cli-bin-dir',
        default=None,
        help=('Path to the bin directory where the salt daemon\'s scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )
    parser.addini(
        'thread_executors',
        default=None,
        help='Number of threads to assign to the ThreadPoolExecutor. Defaults to 4.')
    parser.addini(
        'cli_bin_dir',
        default=None,
        help=('Path to the bin directory where the salt daemon\'s scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )
