# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2015-2018 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.utils
    ~~~~~~~~~~~~~~~~

    Some pytest fixtures used in pytest-salt
'''

# Import Python libs
from __future__ import absolute_import
import os
import re
import sys
import json
import time
import errno
import atexit
import signal
import socket
import logging
import subprocess
import threading
from operator import itemgetter
from collections import namedtuple

# Import 3rd party libs
import pytest
import psutil
try:
    import setproctitle
    HAS_SETPROCTITLE = True
except ImportError:
    HAS_SETPROCTITLE = False

log = logging.getLogger(__name__)

if sys.platform.startswith('win'):
    SIGINT = SIGTERM = signal.CTRL_BREAK_EVENT  # pylint: disable=no-member
else:
    SIGINT = signal.SIGINT
    SIGTERM = signal.SIGTERM


def set_proc_title(title):
    if HAS_SETPROCTITLE is False:
        return
    setproctitle.setproctitle('[{0}] - {1}'.format(title, setproctitle.getproctitle()))


def get_unused_localhost_port():
    '''
    Return a random unused port on localhost
    '''
    usock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    usock.bind(('127.0.0.1', 0))
    port = usock.getsockname()[1]
    usock.close()
    return port


def collect_child_processes(pid):
    '''
    Try to collect any started child processes of the provided pid
    '''
    # Let's get the child processes of the started subprocess
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
    except psutil.NoSuchProcess:
        children = []
    return children


def _terminate_process_list(process_list, kill=False, slow_stop=False):
    for process in process_list[:]:  # Iterate over copy of the list
        if not psutil.pid_exists(process.pid):
            process_list.remove(process)
            continue
        try:
            if not kill and process.status() == psutil.STATUS_ZOMBIE:
                # Zombie processes will exit once child processes also exit
                continue
            try:
                cmdline = process.cmdline()
            except psutil.AccessDenied:
                # OSX is more restrictive about the above information
                cmdline = None
            if not cmdline:
                cmdline = process.as_dict()
            if kill:
                log.info('Killing process(%s): %s', process.pid, cmdline)
                process.kill()
            else:
                log.info('Terminating process(%s): %s', process.pid, cmdline)
                try:
                    if slow_stop:
                        # Allow coverage data to be written down to disk
                        process.send_signal(SIGTERM)
                        try:
                            process.wait(2)
                        except psutil.TimeoutExpired:
                            if psutil.pid_exists(process.pid):
                                continue
                    else:
                        process.terminate()
                except OSError as exc:
                    if exc.errno not in (errno.ESRCH, errno.EACCES):
                        raise
            if not psutil.pid_exists(process.pid):
                process_list.remove(process)
        except psutil.NoSuchProcess:
            process_list.remove(process)


def terminate_process_list(process_list, kill=False, slow_stop=False):

    def on_process_terminated(proc):
        log.info('Process %s terminated with exit code: %s', getattr(proc, '_cmdline', proc), proc.returncode)

    # Try to terminate processes with the provided kill and slow_stop parameters
    log.info('Terminating process list. 1st step. kill: %s, slow stop: %s', kill, slow_stop)

    # Cache the cmdline since that will be inaccessible once the process is terminated
    for proc in process_list:
        try:
            cmdline = proc.cmdline()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # OSX is more restrictive about the above information
            cmdline = None
        if not cmdline:
            try:
                cmdline = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cmdline = '<could not be retrived; dead process: {0}>'.format(proc)
        proc._cmdline = cmdline
    _terminate_process_list(process_list, kill=kill, slow_stop=slow_stop)
    psutil.wait_procs(process_list, timeout=15, callback=on_process_terminated)

    if process_list:
        # If there's still processes to be terminated, retry and kill them if slow_stop is False
        log.info('Terminating process list. 2nd step. kill: %s, slow stop: %s', slow_stop is False, slow_stop)
        _terminate_process_list(process_list, kill=slow_stop is False, slow_stop=slow_stop)
        psutil.wait_procs(process_list, timeout=10, callback=on_process_terminated)

    if process_list:
        # If there's still processes to be terminated, just kill them, no slow stopping now
        log.info('Terminating process list. 3rd step. kill: True, slow stop: False')
        _terminate_process_list(process_list, kill=True, slow_stop=False)
        psutil.wait_procs(process_list, timeout=5, callback=on_process_terminated)

    if process_list:
        # In there's still processes to be terminated, log a warning about it
        log.warning('Some processes failed to properly terminate: %s', process_list)


def terminate_child_processes(pid=None, children=None, kill=False, slow_stop=False):
    '''
    Try to terminate/kill any started child processes of the provided pid
    '''
    if pid:
        if not children:
            # Let's get the child processes of the started subprocess
            children = collect_child_processes(pid)
        else:
            # Let's collect children again since there might be new ones
            children.extend(collect_child_processes(pid))

    if children:
        terminate_process_list(children, kill=slow_stop is False, slow_stop=slow_stop)


def terminate_process(pid=None, process=None, children=None, kill_children=False, slow_stop=False):
    '''
    Try to terminate/kill the started processe
    '''
    children = children or []
    process_list = []
    # Always kill children if kill the parent process.
    kill_children = True if slow_stop is False else kill_children

    if pid and not process:
        try:
            process = psutil.Process(pid)
            process_list.append(process)
        except psutil.NoSuchProcess:
            # Process is already gone
            process = None

    if kill_children:
        if process:
            if not children:
                children = collect_child_processes(process.pid)
            else:
                # Let's collect children again since there might be new ones
                children.extend(collect_child_processes(pid))
        if children:
            process_list.extend(children)

    if process_list:
        if process:
            log.info('Stopping process %s and respective children: %s', process, children)
        else:
            log.info('Terminating process list: %s', process_list)
        terminate_process_list(process_list, kill=slow_stop is False, slow_stop=slow_stop)


def start_daemon(request,
                 daemon_name=None,
                 daemon_id=None,
                 daemon_log_prefix=None,
                 daemon_cli_script_name=None,
                 daemon_config=None,
                 daemon_config_dir=None,
                 daemon_class=None,
                 bin_dir_path=None,
                 fail_hard=False,
                 start_timeout=10,
                 slow_stop=False,
                 environ=None,
                 cwd=None,
                 **kwargs):
    '''
    Returns a running salt daemon
    '''
    if fail_hard:
        fail_method = pytest.fail
    else:
        fail_method = pytest.xfail
    log.info('[%s] Starting pytest %s(%s)', daemon_name, daemon_log_prefix, daemon_id)
    attempts = 0
    process = None
    while attempts <= 3:  # pylint: disable=too-many-nested-blocks
        attempts += 1
        process = daemon_class(request,
                               daemon_config,
                               daemon_config_dir,
                               bin_dir_path,
                               daemon_log_prefix,
                               cli_script_name=daemon_cli_script_name,
                               slow_stop=slow_stop,
                               environ=environ,
                               cwd=cwd,
                               **kwargs)
        process.start()
        if process.is_alive():
            try:
                connectable = process.wait_until_running(timeout=start_timeout)
                if connectable is False:
                    connectable = process.wait_until_running(timeout=start_timeout/2)
                    if connectable is False:
                        process.terminate()
                        if attempts >= 3:
                            fail_method(
                                'The pytest {0}({1}) has failed to confirm running status '
                                'after {2} attempts'.format(daemon_name, daemon_id, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s] %s', daemon_log_prefix, exc, exc_info=True)
                terminate_process(process.pid, kill_children=True, slow_stop=slow_stop)
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
                terminate_process(process.pid, kill_children=True, slow_stop=slow_stop)
                log.info('[%s] pytest %s(%s) stopped', daemon_log_prefix, daemon_name, daemon_id)

            request.addfinalizer(stop_daemon)
            return process
        else:
            terminate_process(process.pid, kill_children=True, slow_stop=slow_stop)
            continue
    else:   # pylint: disable=useless-else-on-loop
            # Wrong, we have a return, its not useless
        if process is not None:
            terminate_process(process.pid, kill_children=True, slow_stop=slow_stop)
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
                 cli_script_name=None,
                 slow_stop=False,
                 environ=None,
                 cwd=None):
        self.request = request
        self.config = config
        if not isinstance(config_dir, str):
            config_dir = config_dir.realpath().strpath
        self.config_dir = config_dir
        self.bin_dir_path = bin_dir_path
        self.log_prefix = log_prefix
        if cli_script_name is None:
            raise RuntimeError('Please provide a value for the cli_script_name keyword argument')
        self.cli_script_name = cli_script_name
        if self.cli_display_name is None:
            self.cli_display_name = '{0}({1})'.format(self.__class__.__name__,
                                                      self.cli_script_name)
        self.slow_stop = slow_stop
        self.environ = environ or os.environ.copy()
        self.cwd = cwd or os.getcwd()
        self._terminal = self._children = None

    def get_script_path(self, script_name):
        '''
        Returns the path to the script to run
        '''
        script_path =  os.path.join(self.bin_dir_path, script_name)
        if not os.path.exists(script_path):
            pytest.fail('The CLI script {!r} does not exist'.format(script_path))
        return script_path

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

    def init_terminal(self, cmdline, **kwargs):
        '''
        Instantiate a terminal with the passed cmdline and kwargs and return it.

        Additionaly, it sets a reference to it in self._terminal and also collects
        an initial listing of child processes which will be used when terminating the
        terminal
        '''
        # Late import
        import salt.utils.nb_popen as nb_popen
        self._terminal = nb_popen.NonBlockingPopen(cmdline, **kwargs)
        self._children = collect_child_processes(self._terminal.pid)
        atexit.register(self.terminate)
        return self._terminal

    def terminate(self):
        '''
        Terminate the started daemon
        '''
        if self._terminal is None:
            return
        # Lets log and kill any child processes which salt left behind
        if self._terminal.stdout:
            self._terminal.stdout.close()
        if self._terminal.stderr:
            self._terminal.stderr.close()
        terminate_process(pid=self._terminal.pid,
                          children=self._children,
                          kill_children=True,
                          slow_stop=self.slow_stop)


class SaltDaemonScriptBase(SaltScriptBase):
    '''
    Base class for Salt Daemon CLI scripts
    '''

    def __init__(self, *args, **kwargs):
        self._process_cli_output_in_thread = kwargs.pop('process_cli_output_in_thread', True)
        super(SaltDaemonScriptBase, self).__init__(*args, **kwargs)
        self._running = threading.Event()
        self._connectable = threading.Event()

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

    def get_check_events(self):  # pylint: disable=no-self-use
        '''
        Return a list of event tags to check against to ensure the daemon is running
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

    def get_salt_run_event_listener(self):
        try:
            cli_script_name = self.request.getfixturevalue('cli_run_script_name')
        except AttributeError:
            cli_script_name = self.request.getfuncargvalue('cli_run_script_name')

        return SaltRunEventListener(self.request,
                                    self.config,
                                    self.config_dir,
                                    self.bin_dir_path,
                                    self.log_prefix,
                                    cli_script_name=cli_script_name)

    def start(self):
        '''
        Start the daemon subprocess
        '''
        # Late import
        log.info('[%s][%s] Starting DAEMON in CWD: %s', self.log_prefix, self.cli_display_name, self.cwd)
        proc_args = [
            self.get_script_path(self.cli_script_name)
        ] + self.get_base_script_args() + self.get_script_args()

        if sys.platform.startswith('win'):
            # Windows needs the python executable to come first
            proc_args.insert(0, sys.executable)

        log.info('[%s][%s] Running \'%s\'...', self.log_prefix, self.cli_display_name, ' '.join(proc_args))

        self.init_terminal(proc_args, env=self.environ, cwd=self.cwd)
        self._running.set()
        if self._process_cli_output_in_thread:
            process_output_thread = threading.Thread(target=self._process_output_in_thread)
            process_output_thread.daemon = True
            process_output_thread.start()
        return True

    def _process_output_in_thread(self):
        '''
        The actual, coroutine aware, start method
        '''
        try:
            while self._running.is_set() and self._terminal.poll() is None:
                # We're not actually interested in processing the output, just consume it
                if self._terminal.stdout is not None:
                    self._terminal.recv()
                if self._terminal.stderr is not None:
                    self._terminal.recv_err()
                time.sleep(0.125)
                if self._terminal.poll() is not None:
                    self._running.clear()
        except (SystemExit, KeyboardInterrupt):
            self._running.clear()
        finally:
            if self._terminal.stdout:
                self._terminal.stdout.close()
            if self._terminal.stderr:
                self._terminal.stderr.close()

    @property
    def pid(self):
        terminal = getattr(self, '_terminal', None)
        if not terminal:
            return
        return terminal.pid

    def terminate(self):
        '''
        Terminate the started daemon
        '''
        # Let's get the child processes of the started subprocess
        self._running.clear()
        self._connectable.clear()
        time.sleep(0.0125)
        super(SaltDaemonScriptBase, self).terminate()

    def wait_until_running(self, timeout=None):
        '''
        Blocking call to wait for the daemon to start listening
        '''
        # Late import
        import salt.ext.six as six
        if self._connectable.is_set():
            return True

        expire = time.time() + timeout
        check_ports = self.get_check_ports()
        if check_ports:
            log.debug(
                '[%s][%s] Checking the following ports to assure running status: %s',
                self.log_prefix,
                self.cli_display_name,
                check_ports
            )
        check_events = self.get_check_events()
        if check_events:
            log.debug(
                '[%s][%s] Checking the following event tags to assure running status: %s',
                self.log_prefix,
                self.cli_display_name,
                check_events
            )
        log.debug('Wait until running expire: %s  Timeout: %s  Current Time: %s', expire, timeout, time.time())
        event_listener = self.get_salt_run_event_listener()
        try:
            while True:
                if self._running.is_set() is False:
                    # No longer running, break
                    log.warning('No longer running!')
                    break

                if time.time() > expire:
                    # Timeout, break
                    log.debug('Expired at %s(was set to %s)', time.time(), expire)
                    break

                if not check_ports and not check_events:
                    self._connectable.set()
                    break

                if check_events:
                    result = event_listener.run(check_events, timeout=timeout - 0.5)
                    if result.exitcode == 0:
                        for tag in result.json['matched']:
                            check_events.remove(tag)

                for port in set(check_ports):
                    if isinstance(port, int):
                        log.debug('[%s][%s] Checking connectable status on port: %s',
                                  self.log_prefix,
                                  self.cli_display_name,
                                  port)
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        conn = sock.connect_ex(('localhost', port))
                        try:
                            if conn == 0:
                                log.debug('[%s][%s] Port %s is connectable!',
                                          self.log_prefix,
                                          self.cli_display_name,
                                          port)
                                check_ports.remove(port)
                                sock.shutdown(socket.SHUT_RDWR)
                        except socket.error:
                            continue
                        finally:
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
        except KeyboardInterrupt:
            return self._connectable.is_set()
        finally:
            event_listener.terminate()
        if self._connectable.is_set():
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

    def __init__(self, *args, **kwargs):
        self.default_timeout = kwargs.pop('default_timeout', self.DEFAULT_TIMEOUT)
        super(SaltCliScriptBase, self).__init__(*args, **kwargs)

    def get_base_script_args(self):
        return SaltScriptBase.get_base_script_args(self) + ['--out=json']

    def get_minion_tgt(self, **kwargs):
        return kwargs.pop('minion_tgt', None)

    def run(self, *args, **kwargs):
        '''
        Run the given command synchronously
        '''
        # Late import
        import salt.ext.six as six
        timeout = kwargs.get('timeout', self.default_timeout)
        if 'fail_hard' in kwargs:
            # Explicit fail_hard passed
            fail_hard = kwargs.pop('fail_hard')
        else:
            # Get the value of the _salt_fail_hard fixture
            try:
                fail_hard = self.request.getfixturevalue('_salt_fail_hard')
            except AttributeError:
                fail_hard = self.request.getfuncargvalue('_salt_fail_hard')
        if fail_hard is True:
            fail_method = pytest.fail
        else:
            fail_method = pytest.xfail
        log.info('The fail hard setting for %s is: %s', self.cli_script_name, fail_hard)
        minion_tgt = self.get_minion_tgt(**kwargs)
        timeout_expire = time.time() + kwargs.pop('timeout', self.default_timeout)
        environ = self.environ.copy()
        environ['PYTEST_LOG_PREFIX'] = '[{0}] '.format(self.log_prefix)
        environ['PYTHONUNBUFFERED'] = '1'
        proc_args = [
            self.get_script_path(self.cli_script_name)
        ] + self.get_base_script_args() + self.get_script_args()

        if sys.platform.startswith('win'):
            # Windows needs the python executable to come first
            proc_args.insert(0, sys.executable)

        if minion_tgt is not None:
            proc_args.append(minion_tgt)
        proc_args.extend(list(args))
        for key in kwargs:
            proc_args.append('{0}={1}'.format(key, kwargs[key]))

        log.info('[%s][%s] Running \'%s\' in CWD: %s ...',
                 self.log_prefix, self.cli_display_name, ' '.join(proc_args), self.cwd)

        terminal = self.init_terminal(proc_args,
                                      cwd=self.cwd,
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
                    self.terminate()
                    fail_method(
                        '[{0}][{1}] Failed to run: args: {2!r}; kwargs: {3!r}; Error: {4}'.format(
                            self.log_prefix,
                            self.cli_display_name,
                            args,
                            kwargs,
                            '[{0}][{1}] Timed out after {2} seconds!'.format(self.log_prefix,
                                                                             self.cli_display_name,
                                                                             timeout)
                        )
                    )
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            self.terminate()

        if six.PY3:
            # pylint: disable=undefined-variable
            stdout = stdout.decode(__salt_system_encoding__)
            stderr = stderr.decode(__salt_system_encoding__)
            # pylint: enable=undefined-variable

        exitcode = terminal.returncode
        stdout, stderr, json_out = self.process_output(minion_tgt, stdout, stderr, cli_cmd=proc_args)
        return ShellResult(exitcode, stdout, stderr, json_out)

    def process_output(self, tgt, stdout, stderr, cli_cmd=None):
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


class SaltRunEventListener(SaltCliScriptBase):
    '''
    Class which runs 'salt-run state.event *' to match agaist a provided set of event tags
    '''

    EVENT_MATCH_RE = re.compile(r'^(?P<tag>[\w/-]+)(?:[\s]+)(?P<data>[\S\W]+)$')

    def get_base_script_args(self):
        return SaltScriptBase.get_base_script_args(self)

    def get_script_args(self):  # pylint: disable=no-self-use
        '''
        Returns any additional arguments to pass to the CLI script
        '''
        return ['state.event']

    def run(self, tags=(), timeout=10):  # pylint: disable=arguments-differ
        '''
        Run the given command synchronously
        '''
        # Late import
        import salt.ext.six as six
        exitcode = 0
        timeout_expire = time.time() + timeout
        environ = self.environ.copy()
        environ['PYTEST_LOG_PREFIX'] = '[{0}][EventListen] '.format(self.log_prefix)
        environ['PYTHONUNBUFFERED'] = '1'
        proc_args = [
            self.get_script_path(self.cli_script_name)
        ] + self.get_base_script_args() + self.get_script_args()

        if sys.platform.startswith('win'):
            # Windows needs the python executable to come first
            proc_args.insert(0, sys.executable)

        log.info('[%s][%s] Running \'%s\' in CWD: %s...',
                 self.log_prefix, self.cli_display_name, ' '.join(proc_args), self.cwd)

        to_match_events = set(tags)
        matched_events = {}

        terminal = self.init_terminal(proc_args,
                                      cwd=self.cwd,
                                      env=environ,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

        # Consume the output
        stdout = six.b('')
        stderr = six.b('')

        process_output = six.b('')
        events_processed = 0
        try:
            while True:
                if terminal.stdout is not None:
                    try:
                        out = terminal.recv(4096)
                    except IOError:
                        out = six.b('')
                    if out:
                        stdout += out
                        process_output += out
                if terminal.stderr is not None:
                    try:
                        err = terminal.recv_err(4096)
                    except IOError:
                        err = ''
                    if err:
                        stderr += err
                if out is None and err is None:
                    if to_match_events:
                        exitcode = 1
                    log.warning('[%s][%s] Premature exit?! Failed to find all of the required event tags. '
                                'Total events processed: %s',
                                self.log_prefix,
                                self.cli_display_name,
                                events_processed)
                    break

                if process_output:
                    lines = process_output.split(b'}\n')
                    if lines[-1] != b'':
                        process_output = lines.pop()
                    else:
                        process_output = six.b('')
                        lines.pop()
                    for line in lines:
                        match = self.EVENT_MATCH_RE.match(line.decode(__salt_system_encoding__))  # pylint: disable=undefined-variable
                        if match:
                            events_processed += 1
                            tag, data = match.groups()
                            if tag in to_match_events:
                                matched_events[tag] = json.loads(data + '}')
                                to_match_events.remove(tag)

                    log.info('[%s][%s] Events processed so far: %d',
                             self.log_prefix,
                             self.cli_display_name,
                             events_processed)

                if not to_match_events:
                    log.debug('[%s][%s] ALL EVENT TAGS FOUND!!!', self.log_prefix, self.cli_display_name)
                    break

                if timeout_expire < time.time():
                    log.warning('[%s][%s] Failed to find all of the required event tags. Total events processed: %s',
                                self.log_prefix,
                                self.cli_display_name,
                                events_processed)
                    exitcode = 1
                    break
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            self.terminate()

        if six.PY3:
            # pylint: disable=undefined-variable
            stdout = stdout.decode(__salt_system_encoding__)
            stderr = stderr.decode(__salt_system_encoding__)
            # pylint: enable=undefined-variable

        json_out = {
            'matched': matched_events,
            'unmatched': to_match_events
        }
        return ShellResult(exitcode, stdout, stderr, json_out)


@pytest.mark.trylast
def pytest_configure(config):
    pytest.helpers.utils.register(get_unused_localhost_port)
