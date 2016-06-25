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
import errno
import atexit
import signal
import socket
import logging
import subprocess
import multiprocessing
from collections import namedtuple

# Import 3rd-party libs
try:
    import ujson as json
except ImportError:
    # Use the standard library, slower, json module
    import json
import salt.ext.six as six
import pytest
import psutil
from tornado import gen
from tornado import ioloop
from tornado import concurrent
from tornado.process import Subprocess

# Import salt libs
#import salt
import salt.utils.nb_popen as nb_popen
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
    if path:
        # We were passed cli_bin_dir as a INI option
        return path

    # Default to the directory of the current python executable
    return os.path.dirname(sys.executable)


def close_terminal(terminal):
    '''
    Close a terminal
    '''
    # Let's begin the shutdown routines
    if terminal.poll() is None:
        try:
            terminal.send_signal(signal.SIGKILL)
        except OSError as exc:
            if exc.errno not in (errno.ESRCH, errno.EACCES):
                raise
        timeout = 5
        while timeout > 0:
            if terminal.poll() is not None:
                break
            timeout -= 0.0125
            time.sleep(0.0125)
    if terminal.poll() is None:
        try:
            terminal.kill()
        except OSError as exc:
            if exc.errno not in (errno.ESRCH, errno.EACCES):
                raise
    # Let's close the terminal now that we're done with it
    try:
        terminal.terminate()
    except OSError as exc:
        if exc.errno not in (errno.ESRCH, errno.EACCES):
            raise
    terminal.communicate()


def terminate_child_processes(pid):
    '''
    Try to terminate/kill any started child processes of the provided pid
    '''
    # Let's get the child processes of the started subprocess
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
    except psutil.NoSuchProcess:
        children = []

    # Lets log and kill any child processes which salt left behind
    for child in children[:]:
        try:
            cmdline = child.cmdline()
            log.info('Salt left behind a child process. Process cmdline: %s', cmdline)
            child.send_signal(signal.SIGKILL)
            try:
                child.wait(timeout=5)
            except psutil.TimeoutExpired:
                child.kill()
            log.info('Process terminated. Process cmdline: %s', cmdline)
        except psutil.NoSuchProcess:
            children.remove(child)
    if children:
        psutil.wait_procs(children, timeout=5)


@pytest.yield_fixture
def salt_master_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-master and after ending it.
    '''
    # Prep routines go here

    # Start the salt-master
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_master_after_start(salt_master):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-master and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_master(request,
                conf_dir,
                master_id,
                master_config,
                salt_master_before_start,  # pylint: disable=unused-argument
                io_loop,
                log_server,
                master_log_prefix):
    '''
    Returns a running salt-master
    '''
    log.info('[%s] Starting pytest salt-master(%s)', master_log_prefix, master_id)
    attempts = 0
    while attempts <= 3:
        attempts += 1
        master_process = SaltMaster(master_config,
                                    conf_dir.strpath,
                                    cli_bin_dir(request.config),
                                    master_log_prefix,
                                    io_loop)
        master_process.start()
        if master_process.is_alive():
            try:
                connectable = master_process.wait_until_running(timeout=10)
                if connectable is False:
                    connectable = master_process.wait_until_running(timeout=5)
                    if connectable is False:
                        master_process.terminate()
                        if attempts >= 3:
                            pytest.xfail(
                                'The pytest salt-master({0}) has failed to confirm running status '
                                'after {1} attempts'.format(master_id, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s]: %s', master_log_prefix, exc, exc_info=True)
                master_process.terminate()
                if attempts >= 3:
                    pytest.xfail(str(exc))
                continue
            log.info(
                '[%s] The pytest salt-master(%s) is running and accepting connections '
                'after %d attempts',
                master_log_prefix,
                master_id,
                attempts
            )
            yield master_process
            break
        else:
            master_process.terminate()
            continue
    else:
        pytest.xfail(
            'The pytest salt-master({0}) has failed to start after {1} attempts'.format(
                master_id, attempts-1
            )
        )
    log.info('[%s] Stopping pytest salt-master(%s)', master_log_prefix, master_id)
    master_process.terminate()
    log.info('[%s] Pytest salt-master(%s) stopped', master_log_prefix, master_id)


@pytest.fixture(scope='session')
def salt_version(request):
    proc = subprocess.Popen(
        [
            '{0}/salt-master'.format(cli_bin_dir(request.config)),
            '--version'
        ],
        stdout=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    version = stdout.split()[1]
    if six.PY3:
        version = version.decode('utf-8')
    return version


@pytest.yield_fixture
def salt_minion_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-minion and after ending it.
    '''
    # Prep routines go here

    # Start the salt-minion
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_minion_after_start(salt_minion):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-minion and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_minion(salt_master,
                minion_id,
                minion_config,
                salt_minion_before_start,  # pylint: disable=unused-argument
                minion_log_prefix,
                salt_run,
                log_server):  # pylint: disable=unused-argument
    '''
    Returns a running salt-minion
    '''
    log.info('[%s] Starting pytest salt-minion(%s)', minion_log_prefix, minion_id)
    attempts = 0
    while attempts <= 3:  # pylint: disable=too-many-nested-blocks
        attempts += 1
        minion_process = SaltMinion(minion_config,
                                    salt_master.config_dir,
                                    salt_master.bin_dir_path,
                                    minion_log_prefix,
                                    salt_master.io_loop,
                                    salt_run=salt_run)
        minion_process.start()
        if minion_process.is_alive():
            try:
                connectable = minion_process.wait_until_running(timeout=10)
                if connectable is False:
                    connectable = minion_process.wait_until_running(timeout=5)
                    if connectable is False:
                        minion_process.terminate()
                        if attempts >= 3:
                            pytest.xfail(
                                'The pytest salt-minion({0}) has failed to confirm '
                                'running status after {1} attempts'.format(minion_id, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s] %s', minion_log_prefix, exc, exc_info=True)
                minion_process.terminate()
                if attempts >= 3:
                    pytest.xfail(str(exc))
                continue
            log.info(
                '[%s] The pytest salt-minion(%s) is running and accepting commands '
                'after %d attempts',
                minion_log_prefix,
                minion_id,
                attempts
            )
            yield minion_process
            break
        else:
            minion_process.terminate()
            continue
    else:
        pytest.xfail(
            'The pytest salt-minion({0}) has failed to start after {1} attempts'.format(
                minion_id,
                attempts-1
            )
        )
    log.info('[%s] Stopping pytest salt-minion(%s)', minion_log_prefix, minion_id)
    minion_process.terminate()
    log.info('[%s] pytest salt-minion(%s) stopped', minion_log_prefix, minion_id)


@pytest.yield_fixture
def salt_before_start():
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
def salt_after_start(salt):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt CLI script and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt(salt_minion,
        salt_before_start,
        log_server,
        salt_log_prefix):  # pylint: disable=unused-argument
    '''
    Returns a salt fixture
    '''
    salt = Salt(salt_minion.config,
                salt_minion.config_dir,
                salt_minion.bin_dir_path,
                salt_log_prefix,
                salt_minion.io_loop)
    yield salt


@pytest.yield_fixture
def salt_call_before_start():
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
def salt_call_after_start(salt_call):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-call and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_call(salt_minion,
              salt_call_before_start,
              salt_call_log_prefix,
              log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(salt_minion.config,
                         salt_minion.config_dir,
                         salt_minion.bin_dir_path,
                         salt_call_log_prefix,
                         salt_minion.io_loop)
    yield salt_call


@pytest.yield_fixture
def salt_key_before_start():
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
def salt_key_after_start(salt_key):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-key and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_key(salt_master,
             salt_key_before_start,
             salt_key_log_prefix,
             log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_key fixture
    '''
    salt_key = SaltKey(salt_master.config,
                       salt_master.config_dir,
                       salt_master.bin_dir_path,
                       salt_key_log_prefix,
                       salt_master.io_loop)
    yield salt_key


@pytest.yield_fixture
def salt_run_before_start():
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
def salt_run_after_start(salt_run):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-run and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_run(salt_master,
             salt_run_before_start,
             salt_run_log_prefix,
             log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(salt_master.config,
                       salt_master.config_dir,
                       salt_master.bin_dir_path,
                       salt_run_log_prefix,
                       salt_master.io_loop)
    yield salt_run


class SaltScriptBase(object):
    '''
    Base class for Salt CLI scripts
    '''

    cli_script_name = None
    cli_display_name = None

    def __init__(self,
                 config,
                 config_dir,
                 bin_dir_path,
                 log_prefix,
                 io_loop=None,
                 salt_run=None):
        self.config = config
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.log_prefix = log_prefix
        self._io_loop = io_loop
        self.salt_run = salt_run
        if self.cli_display_name is None:
            self.cli_display_name = '{0}({1})'.format(self.__class__.__name__,
                                                      self.cli_script_name)

    @property
    def io_loop(self):
        '''
        Return an IOLoop
        '''
        if self._io_loop is None:
            self._io_loop = ioloop.IOLoop.current()
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
        self._running.set()
        self._process.start()
        atexit.register(terminate_child_processes, self._process.pid)
        return True

    def _start(self, running_event):
        '''
        The actual, coroutine aware, start method
        '''
        log.info('[%s][%s] Starting DAEMON', self.log_prefix, self.cli_display_name)
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
        ] + self.get_script_args()
        log.info('[%s][%s] Running \'%s\'...',
                 self.log_prefix,
                 self.cli_display_name,
                 ' '.join(proc_args))

        terminal = nb_popen.NonBlockingPopen(proc_args)
        atexit.register(close_terminal, terminal)

        try:
            while running_event.is_set() and terminal.poll() is None:
                # We're not actually interested in processing the output, just consume it
                if terminal.stdout is not None:
                    terminal.recv()
                if terminal.stderr is not None:
                    terminal.recv_err()
                time.sleep(0.125)
        except (SystemExit, KeyboardInterrupt):
            pass

        close_terminal(terminal)

    def terminate(self):
        '''
        Terminate the started daemon
        '''
        # Let's get the child processes of the started subprocess
        try:
            parent = psutil.Process(self._process.pid)
            children = parent.children(recursive=True)
        except psutil.NoSuchProcess:
            children = []

        self._running.clear()
        self._connectable.clear()
        time.sleep(0.0125)
        self._process.terminate()

        # Lets log and kill any child processes which salt left behind
        for child in children[:]:
            try:
                cmdline = child.cmdline()
                log.info('[%s][%s] Salt left behind a child process. Process cmdline: %s',
                         self.log_prefix,
                         self.cli_display_name,
                         cmdline)
                child.send_signal(signal.SIGKILL)
                try:
                    child.wait(timeout=5)
                except psutil.TimeoutExpired:
                    child.kill()
                log.info('[%s][%s] Process terminated. Process cmdline: %s',
                         self.log_prefix,
                         self.cli_display_name,
                         cmdline)
            except psutil.NoSuchProcess:
                children.remove(child)
        if children:
            psutil.wait_procs(children, timeout=5)

    def wait_until_running(self, timeout=None):
        '''
        Blocking call to wait for the daemon to start listening
        '''
        if self._connectable.is_set():
            return True
        try:
            return self.io_loop.run_sync(self._wait_until_running, timeout=timeout+1)
        except ioloop.TimeoutError:
            return False

    @gen.coroutine
    def _wait_until_running(self):
        '''
        The actual, coroutine aware, call to wait for the daemon to start listening
        '''
        yield gen.sleep(1)
        check_ports = self.get_check_ports()
        log.debug(
            '[%s][%s] Checking the following ports to assure running status: %s',
            self.log_prefix,
            self.cli_display_name,
            check_ports
        )
        while self._running.is_set():
            if not check_ports:
                self._connectable.set()
                break
            for port in set(check_ports):
                if isinstance(port, int):
                    log.debug('[%s][%s] Checking connectable status on port: %s',
                              self.log_prefix,
                              self.cli_display_name,
                              port)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn = sock.connect_ex(('localhost', port))
                    if conn == 0:
                        log.debug('[%s][%s] Port %s is connectable!',
                                  self.log_prefix,
                                  self.cli_display_name,
                                  port)
                        check_ports.remove(port)
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
                    del sock
                elif isinstance(port, six.string_types):
                    if not self.salt_run:
                        raise RuntimeError(
                            'We can\'t check to ID\'s without an instance of salt-run as self.salt_run'
                        )
                    minions_joined = yield self.salt_run.run('manage.joined')
                    if minions_joined.exitcode == 0:
                        if minions_joined.json and port in minions_joined.json:
                            check_ports.remove(port)
                        elif not minions_joined.json:
                            log.debug('salt-run manage.join did not return any valid JSON: %s', minions_joined)
            yield gen.sleep(0.5)
        # A final sleep to allow the ioloop to do other things
        yield gen.sleep(0.125)
        log.debug('[%s][%s] All ports checked. Running!', self.log_prefix, self.cli_display_name)
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
                '[{0}][{1}] Failed to run: args: {2!r}; kwargs: {3!r}; Error: {4}'.format(
                    self.log_prefix,
                    self.cli_display_name,
                    args,
                    kwargs,
                    exc
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
                '[{0}][{1}] Failed to run: args: {2!r}; kwargs: {3!r}; Error: {4}'.format(
                    self.log_prefix,
                    self.cli_display_name,
                    args,
                    kwargs,
                    exc
                )
            )

    @gen.coroutine
    def _run_script(self, *args, **kwargs):
        '''
        This method just calls the actual run script method and chains the post
        processing of it.
        '''
        timeout_expire = time.time() + kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        environ = os.environ.copy()
        environ['PYTEST_LOG_PREFIX'] = '[{0}] '.format(self.log_prefix)
        proc_args = [
            self.get_script_path(self.cli_script_name),
            '-c',
            self.config_dir,
            '--out', 'json'
        ] + self.get_script_args() + list(args)

        log.info('[%s][%s] Running \'%s\'...',
                 self.log_prefix,
                 self.cli_display_name,
                 ' '.join(proc_args))

        terminal = nb_popen.NonBlockingPopen(proc_args,
                                             env=environ,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        # Consume the output
        stdout = six.b('')
        stderr = six.b('')
        timedout = False

        try:
            while True:
                # We're not actually interested in processing the output, just consume it
                if terminal.stdout is not None:
                    try:
                        out = terminal.recv(4096)
                    except IOError:
                        out = six.b('')
                    if out:
                        stdout += out
                if terminal.stderr is not None:
                    try:
                        err = terminal.recv_err(4096)
                    except IOError:
                        err = ''
                    if err:
                        stderr += err
                if out is None and err is None:
                    break
                if timeout_expire < time.time():
                    timedout = True
                    break
                yield gen.sleep(0.001)
        except (SystemExit, KeyboardInterrupt):
            pass

        close_terminal(terminal)

        if timedout:
            raise gen.TimeoutError(
                '[{0}][{1}] Timed out after {2} seconds!'.format(
                    self.log_prefix,
                    self.cli_display_name,
                    kwargs.get('timeout', self.DEFAULT_TIMEOUT)
                )
            )

        if six.PY3:
            # pylint: disable=undefined-variable
            stdout = stdout.decode(__salt_system_encoding__)
            stderr = stderr.decode(__salt_system_encoding__)
            # pylint: enable=undefined-variable

        exitcode = terminal.returncode
        try:
            json_out = json.loads(stdout)
        except ValueError:
            log.debug('[%s][%s] Failed to load JSON from the following output:\n%r',
                      self.log_prefix,
                      self.cli_display_name,
                      stdout)
            json_out = None
        yield gen.sleep(0.125)
        raise gen.Return(self.ShellResult(exitcode, stdout, stderr, json_out))


class Salt(SaltCliScriptBase):
    '''
    Class which runs salt-call commands
    '''

    cli_script_name = 'salt'


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
        return set([self.config['id'], self.config['pytest_port']])


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
        '--cli-bin-dir',
        default=None,
        help=('Path to the bin directory where the salt daemon\'s scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )
    parser.addini(
        'cli_bin_dir',
        default=None,
        help=('Path to the bin directory where the salt daemon\'s scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    '''
    Fixtures injection based on markers
    '''
    for fixture in ('salt_master', 'salt_minion', 'salt_call', 'salt', 'salt_key', 'salt_run'):
        if fixture in item.fixturenames:
            after_start_fixture = '{0}_after_start'.format(fixture)
            if after_start_fixture not in item.fixturenames:
                item.fixturenames.append(after_start_fixture)


def pytest_report_header(config):
    '''
    return a string to be displayed as header info for terminal reporting.
    '''
    return 'pytest-salt CLI binaries directory: {0}'.format(cli_bin_dir(config))
