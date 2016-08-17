# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.utils
    ~~~~~~~~~~~~~~~~

    Some pytest fixtures used in pytest-salt
'''

# Import Python libs
from __future__ import absolute_import
import os
import json
import time
import errno
import atexit
import signal
import socket
import logging
import subprocess
import multiprocessing
from operator import itemgetter
from collections import namedtuple

# Import 3rd party libs
import pytest
import psutil
import salt.ext.six as six

# Import salt libs
import salt.utils.nb_popen as nb_popen
from salt.utils.process import SignalHandlingMultiprocessingProcess

pytest_plugins = ['helpers_namespace']

log = logging.getLogger(__name__)


def get_unused_localhost_port():
    '''
    Return a random unused port on localhost
    '''
    usock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    usock.bind(('127.0.0.1', 0))
    port = usock.getsockname()[1]
    usock.close()
    return port


def close_terminal(terminal):
    '''
    Close a terminal
    '''
    # Let's begin the shutdown routines
    if terminal.poll() is None:
        terminate_child_processes(terminal.pid)
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


def start_daemon(request,
                 daemon_name=None,
                 daemon_id=None,
                 daemon_log_prefix=None,
                 daemon_cli_script_name=None,
                 daemon_config=None,
                 daemon_config_dir=None,
                 daemon_class=None,
                 bin_dir_path=None,
                 io_loop=None,
                 fail_hard=False):
    '''
    Returns a running salt daemon
    '''
    if fail_hard:
        fail_method = pytest.fail
    else:
        fail_method = pytest.xfail
    log.info('[%s] Starting pytest %s(%s)', daemon_name, daemon_log_prefix, daemon_id)
    attempts = 0
    while attempts <= 3:  # pylint: disable=too-many-nested-blocks
        attempts += 1
        process = daemon_class(request,
                               daemon_config,
                               daemon_config_dir,
                               bin_dir_path,
                               daemon_log_prefix,
                               io_loop,
                               cli_script_name=daemon_cli_script_name)
        process.start()
        if process.is_alive():
            try:
                connectable = process.wait_until_running(timeout=10)
                if connectable is False:
                    connectable = process.wait_until_running(timeout=5)
                    if connectable is False:
                        process.terminate()
                        if attempts >= 3:
                            fail_method(
                                'The pytest {0}({1}) has failed to confirm running status '
                                'after {2} attempts'.format(daemon_name, daemon_id, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s] %s', daemon_log_prefix, exc, exc_info=True)
                process.terminate()
                if attempts >= 3:
                    fail_method(str(exc))
                continue
            log.info(
                '[%s] The pytest %s(%s) is running and accepting commands '
                'after %d attempts',
                daemon_log_prefix,
                daemon_name,
                daemon_id,
                attempts
            )

            def stop_daemon():
                log.info('[%s] Stopping pytest %s(%s)', daemon_log_prefix, daemon_name, daemon_id)
                process.terminate()
                log.info('[%s] pytest %s(%s) stopped', daemon_log_prefix, daemon_name, daemon_id)

            request.addfinalizer(stop_daemon)
            return process
        else:
            process.terminate()
            continue
    else:
        fail_method(
            'The pytest {0}({1}) has failed to start after {2} attempts'.format(
                daemon_name,
                daemon_id,
                attempts-1
            )
        )


class SaltScriptBase(object):
    '''
    Base class for Salt CLI scripts
    '''

    cli_display_name = None

    def __init__(self,
                 request,
                 config,
                 config_dir,
                 bin_dir_path,
                 log_prefix,
                 io_loop=None,
                 cli_script_name=None):
        self.request = request
        self.config = config
        if not isinstance(config_dir, str):
            config_dir = config_dir.realpath().strpath
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.log_prefix = log_prefix
        self._io_loop = io_loop
        if cli_script_name is None:
            raise RuntimeError('Please provide a value for the cli_script_name keyword argument')
        self.cli_script_name = cli_script_name
        if self.cli_display_name is None:
            self.cli_display_name = '{0}({1})'.format(self.__class__.__name__,
                                                      self.cli_script_name)

    def get_script_path(self, script_name):
        '''
        Returns the path to the script to run
        '''
        return os.path.join(self.bin_dir_path, script_name)

    def get_base_script_args(self):
        '''
        Returns any additional arguments to pass to the CLI script
        '''
        return ['-c', self.config_dir]

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

    def get_salt_run_fixture(self):
        if self.request.scope == 'session':
            try:
                return self.request.getfixturevalue('session_salt_run')
            except AttributeError:
                return self.request.getfuncargvalue('session_salt_run')
        try:
            return self.request.getfixturevalue('salt_run')
        except AttributeError:
            return self.request.getfuncargvalue('salt_run')

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
            self.get_script_path(self.cli_script_name)
        ] + self.get_base_script_args() + self.get_script_args()
        log.info('[%s][%s] Running \'%s\'...',
                 self.log_prefix,
                 self.cli_display_name,
                 ' '.join(proc_args))

        environ = os.environ.copy()
        terminal = nb_popen.NonBlockingPopen(proc_args, env=environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            self._running.clear()

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

        expire = time.time() + timeout
        check_ports = self.get_check_ports()
        log.debug(
            '[%s][%s] Checking the following ports to assure running status: %s',
            self.log_prefix,
            self.cli_display_name,
            check_ports
        )
        log.debug('Expire: %s  Timeout: %s  Current Time: %s', expire, timeout, time.time())
        while True:
            if self._running.is_set() is False:
                # No longer running, break
                break
            if time.time() > expire:
                # Timeout, break
                break
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
                    salt_run = self.get_salt_run_fixture()
                    minions_joined = salt_run.run('manage.joined')
                    if minions_joined.exitcode == 0:
                        if minions_joined.json and port in minions_joined.json:
                            check_ports.remove(port)
                            log.warning('Removed ID %r  Still left: %r', port, check_ports)
                        elif minions_joined.json is None:
                            log.debug('salt-run manage.join did not return any valid JSON: %s', minions_joined)
            time.sleep(0.5)
        log.debug('[%s][%s] All ports checked. Running!', self.log_prefix, self.cli_display_name)
        return self._connectable.is_set()


class ShellResult(namedtuple('Result', ('exitcode', 'stdout', 'stderr', 'json'))):
    '''
    This class serves the purpose of having a common result class which will hold the
    data from the bigret backend(despite the backend being used).

    This will allow filtering by access permissions and/or object ownership.

    '''
    __slots__ = ()

    def __new__(cls, exitcode, stdout, stderr, json):
        return super(ShellResult, cls).__new__(cls, exitcode, stdout, stderr, json)

    # These are copied from the namedtuple verbose output in order to quiet down PyLint
    exitcode = property(itemgetter(0), doc='Alias for field number 0')
    stdout = property(itemgetter(1), doc='Alias for field number 1')
    stderr = property(itemgetter(2), doc='Alias for field number 2')
    json = property(itemgetter(3), doc='Alias for field number 3')

    def __eq__(self, other):
        '''
        Allow comparison against the parsed JSON or the output
        '''
        if self.json:
            return self.json == other
        return self.stdout == other


class SaltCliScriptBase(SaltScriptBase):
    '''
    Base class which runs Salt's non daemon CLI scripts
    '''

    DEFAULT_TIMEOUT = 25

    def get_base_script_args(self):
        return SaltScriptBase.get_base_script_args(self) + ['--out=json']

    def get_minion_tgt(self, **kwargs):
        return kwargs.pop('minion_tgt', None)

    def run(self, *args, **kwargs):
        '''
        Run the given command synchronously
        '''
        timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        if kwargs.pop('fail_hard', False):
            fail_method = pytest.fail
        else:
            fail_method = pytest.xfail
        minion_tgt = self.get_minion_tgt(**kwargs)
        timeout_expire = time.time() + kwargs.pop('timeout', self.DEFAULT_TIMEOUT)
        environ = os.environ.copy()
        environ['PYTEST_LOG_PREFIX'] = '[{0}] '.format(self.log_prefix)
        proc_args = [
            self.get_script_path(self.cli_script_name)
        ] + self.get_base_script_args() + self.get_script_args()
        if minion_tgt is not None:
            proc_args.append(minion_tgt)
        proc_args.extend(list(args))
        for key in kwargs:
            proc_args.append('{0}={1}'.format(key, kwargs[key]))

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
                    fail_method(
                        '[{0}][{1}] Failed to run: args: {2!r}; kwargs: {3!r}; Error: {4}'.format(
                            self.log_prefix,
                            self.cli_display_name,
                            args,
                            kwargs,
                            '[{0}][{1}] Timed out after {2} seconds!'.format(
                                self.log_prefix,
                                self.cli_display_name,
                                kwargs.get('timeout', self.DEFAULT_TIMEOUT)
                            )
                        )
                    )
        except (SystemExit, KeyboardInterrupt):
            pass

        close_terminal(terminal)

        if six.PY3:
            # pylint: disable=undefined-variable
            stdout = stdout.decode(__salt_system_encoding__)
            stderr = stderr.decode(__salt_system_encoding__)
            # pylint: enable=undefined-variable

        exitcode = terminal.returncode
        stdout, stderr, json_out = self.process_output(minion_tgt, stdout, stderr)
        return ShellResult(exitcode, stdout, stderr, json_out)

    def process_output(self, tgt, stdout, stderr):
        if stdout:
            try:
                json_out = json.loads(stdout)
            except ValueError:
                log.debug('[%s][%s] Failed to load JSON from the following output:\n%r',
                          self.log_prefix,
                          self.cli_display_name,
                          stdout)
                json_out = None
        else:
            json_out = None
        return stdout, stderr, json_out


@pytest.mark.trylast
def pytest_configure(config):
    pytest.helpers.utils.register(get_unused_localhost_port)
