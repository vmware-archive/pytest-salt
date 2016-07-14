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
from operator import itemgetter
from collections import namedtuple

# Import 3rd-party libs
try:
    import ujson as json
except ImportError:
    # Use the standard library, slower, json module
    import json
import pytest
import psutil
from tornado import gen
from tornado import ioloop

# Import salt libs
#import salt
import salt.ext.six as six
import salt.utils as salt_utils
import salt.utils.nb_popen as nb_popen
from salt.utils.process import SignalHandlingMultiprocessingProcess

pytest_plugins = ['tornado']

log = logging.getLogger(__name__)


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


@pytest.yield_fixture(scope='session')
def session_io_loop():
    '''
    Create an instance of the `tornado.ioloop.IOLoop` for a test run session.
    '''
    io_loop = ioloop.IOLoop()
    io_loop.make_current()

    yield io_loop

    io_loop.clear_current()
    if not ioloop.IOLoop.initialized() or io_loop is not ioloop.IOLoop.instance():
        io_loop.close(all_fds=True)


@pytest.fixture(scope='session')
def salt_version(_cli_bin_dir, cli_master_script_name, python_executable_path):
    '''
    Return the salt version for the CLI install
    '''
    args = [
        os.path.join(_cli_bin_dir, cli_master_script_name),
        '--version'
    ]
    if sys.platform.startswith('win'):
        # We always need to prefix the call arguments with the python executable on windows
        args.insert(0, python_executable_path)

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    version = stdout.split()[1]
    if six.PY3:
        version = version.decode('utf-8')
    return version


def start_daemon(request,
                 daemon_name=None,
                 daemon_id=None,
                 daemon_log_prefix=None,
                 daemon_cli_script_name=None,
                 daemon_config=None,
                 daemon_config_dir=None,
                 daemon_class=None,
                 bin_dir_path=None,
                 io_loop=None):
    '''
    Returns a running salt daemon
    '''
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
                            pytest.xfail(
                                'The pytest {0}({1}) has failed to confirm running status '
                                'after {2} attempts'.format(daemon_name, daemon_id, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s] %s', daemon_log_prefix, exc, exc_info=True)
                process.terminate()
                if attempts >= 3:
                    pytest.xfail(str(exc))
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
        pytest.xfail(
            'The pytest {0}({1}) has failed to start after {2} attempts'.format(
                daemon_name,
                daemon_id,
                attempts-1
            )
        )


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


@pytest.fixture
def salt_master(request,
                conf_dir,
                master_id,
                master_config,
                salt_master_before_start,  # pylint: disable=unused-argument
                io_loop,
                log_server,  # pylint: disable=unused-argument
                master_log_prefix,
                cli_master_script_name,
                _cli_bin_dir):
    '''
    Returns a running salt-master
    '''
    return start_daemon(request,
                        daemon_name='salt-master',
                        daemon_id=master_id,
                        daemon_log_prefix=master_log_prefix,
                        daemon_cli_script_name=cli_master_script_name,
                        daemon_config=master_config,
                        daemon_config_dir=conf_dir,
                        daemon_class=SaltMaster,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=io_loop)


@pytest.yield_fixture(scope='session')
def session_salt_master_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-master and after ending it.
    '''
    # Prep routines go here

    # Start the salt-master
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_master_after_start(session_salt_master):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-master and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture(scope='session')
def session_salt_master(request,
                        session_conf_dir,
                        session_master_id,
                        session_master_config,
                        session_salt_master_before_start,  # pylint: disable=unused-argument
                        session_io_loop,
                        log_server,  # pylint: disable=unused-argument
                        session_master_log_prefix,
                        cli_master_script_name,
                        _cli_bin_dir):
    '''
    Returns a running salt-master
    '''
    return start_daemon(request,
                        daemon_name='salt-master',
                        daemon_id=session_master_id,
                        daemon_log_prefix=session_master_log_prefix,
                        daemon_cli_script_name=cli_master_script_name,
                        daemon_config=session_master_config,
                        daemon_config_dir=session_conf_dir,
                        daemon_class=SaltMaster,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=session_io_loop)


@pytest.yield_fixture
def salt_master_of_masters_before_start():
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
def salt_master_of_masters_after_start(salt_master_of_masters):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-master and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture
def salt_master_of_masters(request,
                           master_of_masters_conf_dir,
                           master_of_masters_id,
                           master_of_masters_config,
                           salt_master_of_masters_before_start,  # pylint: disable=unused-argument
                           io_loop,
                           log_server,  # pylint: disable=unused-argument
                           master_of_masters_log_prefix,
                           cli_master_script_name,
                           _cli_bin_dir):
    '''
    Returns a running salt-master
    '''
    return start_daemon(request,
                        daemon_name='salt-master',
                        daemon_id=master_of_masters_id,
                        daemon_log_prefix=master_of_masters_log_prefix,
                        daemon_cli_script_name=cli_master_script_name,
                        daemon_config=master_of_masters_config,
                        daemon_config_dir=master_of_masters_conf_dir,
                        daemon_class=SaltMaster,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=io_loop)


@pytest.yield_fixture(scope='session')
def session_salt_master_of_masters_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-master and after ending it.
    '''
    # Prep routines go here

    # Start the salt-master
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_master_of_masters_after_start(session_salt_master_of_masters):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-master and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture(scope='session')
def session_salt_master_of_masters(request,
                                   session_master_of_masters_conf_dir,
                                   session_master_of_masters_id,
                                   session_master_of_masters_config,
                                   session_salt_master_of_masters_before_start,  # pylint: disable=unused-argument
                                   session_io_loop,
                                   log_server,  # pylint: disable=unused-argument
                                   session_master_of_masters_log_prefix,
                                   cli_master_script_name,
                                   _cli_bin_dir):
    '''
    Returns a running salt-master
    '''
    return start_daemon(request,
                        daemon_name='salt-master',
                        daemon_id=session_master_of_masters_id,
                        daemon_log_prefix=session_master_of_masters_log_prefix,
                        daemon_cli_script_name=cli_master_script_name,
                        daemon_config=session_master_of_masters_config,
                        daemon_config_dir=session_master_of_masters_conf_dir,
                        daemon_class=SaltMaster,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=session_io_loop)


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


@pytest.fixture
def salt_minion(request,
                salt_master,
                minion_id,
                minion_config,
                salt_minion_before_start,  # pylint: disable=unused-argument
                minion_log_prefix,
                cli_minion_script_name,
                log_server,
                io_loop,
                _cli_bin_dir,
                conf_dir):  # pylint: disable=unused-argument
    '''
    Returns a running salt-minion
    '''
    return start_daemon(request,
                        daemon_name='salt-minion',
                        daemon_id=minion_id,
                        daemon_log_prefix=minion_log_prefix,
                        daemon_cli_script_name=cli_minion_script_name,
                        daemon_config=minion_config,
                        daemon_config_dir=conf_dir,
                        daemon_class=SaltMinion,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=io_loop)


@pytest.yield_fixture(scope='session')
def session_salt_minion_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-minion and after ending it.
    '''
    # Prep routines go here

    # Start the salt-minion
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_minion_after_start(session_salt_minion):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-minion and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture(scope='session')
def session_salt_minion(request,
                        session_salt_master,
                        session_minion_id,
                        session_minion_config,
                        session_salt_minion_before_start,  # pylint: disable=unused-argument
                        session_minion_log_prefix,
                        cli_minion_script_name,
                        log_server,
                        _cli_bin_dir,
                        session_conf_dir,
                        session_io_loop):  # pylint: disable=unused-argument
    '''
    Returns a running salt-minion
    '''
    return start_daemon(request,
                        daemon_name='salt-minion',
                        daemon_id=session_minion_id,
                        daemon_log_prefix=session_minion_log_prefix,
                        daemon_cli_script_name=cli_minion_script_name,
                        daemon_config=session_minion_config,
                        daemon_config_dir=session_conf_dir,
                        daemon_class=SaltMinion,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=session_io_loop)


@pytest.yield_fixture
def secondary_salt_minion_before_start():
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
def secondary_salt_minion_after_start(secondary_salt_minion):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-minion and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture
def secondary_salt_minion(request,
                          salt_master,
                          secondary_minion_id,
                          secondary_minion_config,
                          secondary_salt_minion_before_start,  # pylint: disable=unused-argument
                          secondary_minion_log_prefix,
                          cli_minion_script_name,
                          log_server,
                          io_loop,
                          _cli_bin_dir,
                          secondary_conf_dir):  # pylint: disable=unused-argument
    '''
    Returns a running salt-minion
    '''
    return start_daemon(request,
                        daemon_name='salt-minion',
                        daemon_id=secondary_minion_id,
                        daemon_log_prefix=secondary_minion_log_prefix,
                        daemon_cli_script_name=cli_minion_script_name,
                        daemon_config=secondary_minion_config,
                        daemon_config_dir=secondary_conf_dir,
                        daemon_class=SaltMinion,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=io_loop)


@pytest.yield_fixture(scope='session')
def session_secondary_salt_minion_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-minion and after ending it.
    '''
    # Prep routines go here

    # Start the salt-minion
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_secondary_salt_minion_after_start(session_secondary_salt_minion):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-minion and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture(scope='session')
def session_secondary_salt_minion(request,
                                  session_salt_master,
                                  session_secondary_minion_id,
                                  session_secondary_minion_config,
                                  session_secondary_salt_minion_before_start,  # pylint: disable=unused-argument
                                  session_secondary_minion_log_prefix,
                                  cli_minion_script_name,
                                  log_server,
                                  _cli_bin_dir,
                                  session_secondary_conf_dir,
                                  session_io_loop):  # pylint: disable=unused-argument
    '''
    Returns a running salt-minion
    '''
    return start_daemon(request,
                        daemon_name='salt-minion',
                        daemon_id=session_secondary_minion_id,
                        daemon_log_prefix=session_secondary_minion_log_prefix,
                        daemon_cli_script_name=cli_minion_script_name,
                        daemon_config=session_secondary_minion_config,
                        daemon_config_dir=session_secondary_conf_dir,
                        daemon_class=SaltMinion,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=session_io_loop)


@pytest.yield_fixture
def salt_syndic_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-syndic and after ending it.
    '''
    # Prep routines go here

    # Start the daemon
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_syndic_after_start(salt_syndic):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-master and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture
def salt_syndic(request,
                syndic_conf_dir,
                syndic_id,
                syndic_config,
                salt_syndic_before_start,  # pylint: disable=unused-argument
                io_loop,
                log_server,  # pylint: disable=unused-argument
                syndic_log_prefix,
                cli_syndic_script_name,
                _cli_bin_dir):
    '''
    Returns a running salt-syndic
    '''
    return start_daemon(request,
                        daemon_name='salt-syndic',
                        daemon_id=syndic_id,
                        daemon_log_prefix=syndic_log_prefix,
                        daemon_cli_script_name=cli_syndic_script_name,
                        daemon_config=syndic_config,
                        daemon_config_dir=syndic_conf_dir,
                        daemon_class=SaltSyndic,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=io_loop)


@pytest.yield_fixture(scope='session')
def session_salt_syndic_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-syndic and after ending it.
    '''
    # Prep routines go here

    # Start the daemon
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_syndic_after_start(session_salt_syndic):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-master and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture(scope='session')
def session_salt_syndic(request,
                        session_syndic_conf_dir,
                        session_syndic_id,
                        session_syndic_config,
                        session_salt_syndic_before_start,  # pylint: disable=unused-argument
                        session_io_loop,
                        log_server,  # pylint: disable=unused-argument
                        session_syndic_log_prefix,
                        cli_syndic_script_name,
                        _cli_bin_dir):
    '''
    Returns a running salt-syndic
    '''
    return start_daemon(request,
                        daemon_name='salt-syndic',
                        daemon_id=session_syndic_id,
                        daemon_log_prefix=session_syndic_log_prefix,
                        daemon_cli_script_name=cli_syndic_script_name,
                        daemon_config=session_syndic_config,
                        daemon_config_dir=session_syndic_conf_dir,
                        daemon_class=SaltSyndic,
                        bin_dir_path=_cli_bin_dir,
                        io_loop=session_io_loop)


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
def salt(request,
         salt_minion,
         minion_config,
         _cli_bin_dir,
         io_loop,
         conf_dir,
         cli_salt_script_name,
         salt_before_start,  # pylint: disable=unused-argument
         log_server,         # pylint: disable=unused-argument
         salt_log_prefix):   # pylint: disable=unused-argument
    '''
    Returns a salt fixture
    '''
    salt = Salt(request,
                minion_config,
                conf_dir,
                _cli_bin_dir,
                salt_log_prefix,
                io_loop,
                cli_script_name=cli_salt_script_name)
    yield salt


@pytest.yield_fixture(scope='session')
def session_salt_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-call and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_after_start(session_salt):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt CLI script and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt(request,
                 session_salt_minion,
                 session_minion_config,
                 _cli_bin_dir,
                 session_io_loop,
                 session_conf_dir,
                 cli_salt_script_name,
                 session_salt_before_start,  # pylint: disable=unused-argument
                 log_server,         # pylint: disable=unused-argument
                 session_salt_log_prefix):   # pylint: disable=unused-argument
    '''
    Returns a salt fixture
    '''
    salt = Salt(request,
                session_minion_config,
                session_conf_dir,
                _cli_bin_dir,
                session_salt_log_prefix,
                session_io_loop,
                cli_script_name=cli_salt_script_name)
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
def salt_call(request,
              salt_minion,
              salt_call_before_start,
              salt_call_log_prefix,
              cli_call_script_name,
              minion_config,
              conf_dir,
              _cli_bin_dir,
              io_loop,
              log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(request,
                         minion_config,
                         conf_dir,
                         _cli_bin_dir,
                         salt_call_log_prefix,
                         io_loop,
                         cli_script_name=cli_call_script_name)
    yield salt_call


@pytest.yield_fixture(scope='session')
def session_salt_call_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-call and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_call_after_start(session_salt_call):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-call and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_call(request,
                      session_salt_minion,
                      session_salt_call_before_start,
                      session_salt_call_log_prefix,
                      cli_call_script_name,
                      session_minion_config,
                      session_conf_dir,
                      _cli_bin_dir,
                      session_io_loop,
                      log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(request,
                         session_minion_config,
                         session_conf_dir,
                         _cli_bin_dir,
                         session_salt_call_log_prefix,
                         session_io_loop,
                         cli_script_name=cli_call_script_name)
    yield salt_call


@pytest.yield_fixture
def salt_key_before_start():
    '''
    this fixture should be overridden if you need to do
    some preparation work before running salt-key and
    clean up after ending it.
    '''
    # prep routines go here

    # run!
    yield

    # clean routines go here


@pytest.yield_fixture
def salt_key_after_start(salt_key):
    '''
    this fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-key and before ending it.
    '''
    # prep routines go here

    # resume test execution
    yield

    # clean routines go here


@pytest.yield_fixture
def salt_key(request,
             salt_master,
             salt_key_before_start,
             salt_key_log_prefix,
             cli_key_script_name,
             master_config,
             conf_dir,
             io_loop,
             _cli_bin_dir,
             log_server):  # pylint: disable=unused-argument
    '''
    returns a salt_key fixture
    '''
    salt_key = SaltKey(request,
                       master_config,
                       conf_dir,
                       _cli_bin_dir,
                       salt_key_log_prefix,
                       io_loop,
                       cli_script_name=cli_key_script_name)
    yield salt_key


@pytest.yield_fixture(scope='session')
def session_salt_key_before_start():
    '''
    this fixture should be overridden if you need to do
    some preparation work before running salt-key and
    clean up after ending it.
    '''
    # prep routines go here

    # run!
    yield

    # clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_key_after_start(session_salt_key):
    '''
    this fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-key and before ending it.
    '''
    # prep routines go here

    # resume test execution
    yield

    # clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_key(request,
                     session_salt_master,
                     session_salt_key_before_start,
                     session_salt_key_log_prefix,
                     cli_key_script_name,
                     session_master_config,
                     session_conf_dir,
                     session_io_loop,
                     _cli_bin_dir,
                     log_server):  # pylint: disable=unused-argument
    '''
    returns a salt_key fixture
    '''
    salt_key = SaltKey(request,
                       session_master_config,
                       session_conf_dir,
                       _cli_bin_dir,
                       session_salt_key_log_prefix,
                       session_io_loop,
                       cli_script_name=cli_key_script_name)
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
def salt_run(request,
             salt_master,
             salt_run_before_start,  # pylint: disable=unused-argument
             salt_run_log_prefix,
             cli_run_script_name,
             conf_dir,
             io_loop,
             master_config,
             _cli_bin_dir,
             log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(request,
                       master_config,
                       conf_dir,
                       _cli_bin_dir,
                       salt_run_log_prefix,
                       io_loop,
                       cli_script_name=cli_run_script_name)
    yield salt_run


@pytest.yield_fixture(scope='session')
def session_salt_run_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-run and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_run_after_start(session_salt_run):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-run and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_run(request,
                     session_salt_master,
                     session_salt_run_before_start,  # pylint: disable=unused-argument
                     session_salt_run_log_prefix,
                     cli_run_script_name,
                     session_conf_dir,
                     session_io_loop,
                     session_master_config,
                     _cli_bin_dir,
                     log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(request,
                       session_master_config,
                       session_conf_dir,
                       _cli_bin_dir,
                       session_salt_run_log_prefix,
                       session_io_loop,
                       cli_script_name=cli_run_script_name)
    yield salt_run


@pytest.yield_fixture
def salt_ssh_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-ssh and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_ssh_after_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-ssh and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_ssh(request,
             sshd_server,
             conf_dir,
             io_loop,
             salt_ssh_before_start,  # pylint: disable=unused-argument
             salt_ssh_log_prefix,
             _cli_bin_dir,
             cli_ssh_script_name,
             roster_config,
             log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_ssh fixture
    '''
    salt_ssh = SaltSSH(request,
                       roster_config,
                       conf_dir,
                       _cli_bin_dir,
                       salt_ssh_log_prefix,
                       io_loop,
                       cli_script_name=cli_ssh_script_name)
    yield salt_ssh


@pytest.yield_fixture(scope='session')
def session_salt_ssh_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation work before running salt-ssh and
    clean up after ending it.
    '''
    # Prep routines go here

    # Run!
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_ssh_after_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-ssh and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_ssh(request,
                     session_sshd_server,
                     session_conf_dir,
                     session_io_loop,
                     session_salt_ssh_before_start,  # pylint: disable=unused-argument
                     session_salt_ssh_log_prefix,
                     _cli_bin_dir,
                     cli_ssh_script_name,
                     session_roster_config,
                     log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_ssh fixture
    '''
    salt_ssh = SaltSSH(request,
                       session_roster_config,
                       session_conf_dir,
                       _cli_bin_dir,
                       session_salt_ssh_log_prefix,
                       session_io_loop,
                       cli_script_name=cli_ssh_script_name)
    yield salt_ssh


@pytest.yield_fixture
def sshd_server_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the sshd server and after ending it.
    '''
    # Prep routines go here

    # Start the sshd server
    yield

    # Clean routines go here


@pytest.yield_fixture
def sshd_server_after_start(sshd_server):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the sshd server and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture
def sshd_server(request,
                io_loop,
                write_sshd_config,  # pylint: disable=unused-argument
                sshd_server_before_start,  # pylint: disable=unused-argument
                sshd_server_log_prefix,
                sshd_port,
                sshd_config_dir,
                log_server):  # pylint: disable=unused-argument
    '''
    Returns a running sshd server
    '''
    log.info('[%s] Starting pytest sshd server at port %s', sshd_server_log_prefix, sshd_port)
    attempts = 0
    while attempts <= 3:  # pylint: disable=too-many-nested-blocks
        attempts += 1
        process = SSHD(request,
                       {'port': sshd_port},
                       sshd_config_dir,
                       None,  # bin_dir_path,
                       sshd_server_log_prefix,
                       io_loop,
                       cli_script_name='sshd')
        process.start()
        if process.is_alive():
            try:
                connectable = process.wait_until_running(timeout=10)
                if connectable is False:
                    connectable = process.wait_until_running(timeout=5)
                    if connectable is False:
                        process.terminate()
                        if attempts >= 3:
                            pytest.xfail(
                                'The pytest sshd server({0}) has failed to confirm '
                                'running status after {1} attempts'.format(sshd_port, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s] %s', sshd_server_log_prefix, exc, exc_info=True)
                process.terminate()
                if attempts >= 3:
                    pytest.xfail(str(exc))
                continue
            log.info(
                '[%s] The pytest sshd server(%s) is running and accepting commands '
                'after %d attempts',
                sshd_server_log_prefix,
                sshd_port,
                attempts
            )
            yield process
            break
        else:
            process.terminate()
            continue
    else:
        pytest.xfail(
            'The pytest sshd server({0}) has failed to start after {1} attempts'.format(
                sshd_port,
                attempts-1
            )
        )
    log.info('[%s] Stopping pytest sshd server(%s)', sshd_server_log_prefix, sshd_port)
    process.terminate()
    log.info('[%s] pytest sshd server(%s) stopped', sshd_server_log_prefix, sshd_port)


@pytest.yield_fixture(scope='session')
def session_sshd_server_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the sshd server and after ending it.
    '''
    # Prep routines go here

    # Start the sshd server
    yield

    # Clean routines go here


@pytest.yield_fixture
def session_sshd_server_after_start(sshd_server):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the sshd server and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_sshd_server(request,
                        session_io_loop,
                        session_write_sshd_config,  # pylint: disable=unused-argument
                        session_sshd_server_before_start,  # pylint: disable=unused-argument
                        session_sshd_server_log_prefix,
                        session_sshd_port,
                        session_sshd_config_dir,
                        log_server):  # pylint: disable=unused-argument
    '''
    Returns a running sshd server
    '''
    log.info('[%s] Starting pytest sshd server at port %s', session_sshd_server_log_prefix, session_sshd_port)
    attempts = 0
    while attempts <= 3:  # pylint: disable=too-many-nested-blocks
        attempts += 1
        process = SSHD(request,
                       {'port': session_sshd_port},
                       session_sshd_config_dir,
                       None,  # bin_dir_path,
                       session_sshd_server_log_prefix,
                       session_io_loop,
                       cli_script_name='sshd')
        process.start()
        if process.is_alive():
            try:
                connectable = process.wait_until_running(timeout=10)
                if connectable is False:
                    connectable = process.wait_until_running(timeout=5)
                    if connectable is False:
                        process.terminate()
                        if attempts >= 3:
                            pytest.xfail(
                                'The pytest sshd server({0}) has failed to confirm '
                                'running status after {1} attempts'.format(session_sshd_port, attempts))
                        continue
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('[%s] %s', session_sshd_server_log_prefix, exc, exc_info=True)
                process.terminate()
                if attempts >= 3:
                    pytest.xfail(str(exc))
                continue
            log.info(
                '[%s] The pytest sshd server(%s) is running and accepting commands '
                'after %d attempts',
                session_sshd_server_log_prefix,
                session_sshd_port,
                attempts
            )
            yield process
            break
        else:
            process.terminate()
            continue
    else:
        pytest.xfail(
            'The pytest sshd server({0}) has failed to start after {1} attempts'.format(
                session_sshd_port,
                attempts-1
            )
        )
    log.info('[%s] Stopping pytest sshd server(%s)', session_sshd_server_log_prefix, session_sshd_port)
    process.terminate()
    log.info('[%s] pytest sshd server(%s) stopped', session_sshd_server_log_prefix, session_sshd_port)


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

    @property
    def io_loop(self):
        '''
        Return an IOLoop
        '''
        return ioloop.IOLoop.current()

    def get_script_path(self, script_name):
        '''
        Returns the path to the script to run
        '''
        return os.path.join(self.bin_dir_path, script_name)

    def get_base_script_args(self):  # pylint: disable=no-self-use
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
        yield gen.moment
        #yield gen.sleep(1)
        check_ports = self.get_check_ports()
        log.debug(
            '[%s][%s] Checking the following ports to assure running status: %s',
            self.log_prefix,
            self.cli_display_name,
            check_ports
        )
        while self._running.is_set():
            yield gen.moment
            if not check_ports:
                self._connectable.set()
                break
            for port in set(check_ports):
                yield gen.moment
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
                    minions_joined = yield salt_run.run('manage.joined')
                    if minions_joined.exitcode == 0:
                        if minions_joined.json and port in minions_joined.json:
                            check_ports.remove(port)
                            log.warning('Removed ID %r  Still left: %r', port, check_ports)
                        elif minions_joined.json is None:
                            log.debug('salt-run manage.join did not return any valid JSON: %s', minions_joined)
            #yield gen.moment
            yield gen.sleep(0.5)
        # A final sleep to allow the ioloop to do other things
        yield gen.moment
        #yield gen.sleep(0.125)
        log.debug('[%s][%s] All ports checked. Running!', self.log_prefix, self.cli_display_name)
        raise gen.Return(self._connectable.is_set())


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

    def get_minion_tgt(self, **kwargs):
        return kwargs.pop('minion_tgt', None)

    @gen.coroutine
    def _run_script(self, *args, **kwargs):
        '''
        This method just calls the actual run script method and chains the post
        processing of it.
        '''
        minion_tgt = self.get_minion_tgt(**kwargs)
        timeout_expire = self.io_loop.time() + kwargs.pop('timeout', self.DEFAULT_TIMEOUT)
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
        timedout = False

        try:
            while True:
                yield gen.moment
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
                if timeout_expire < self.io_loop.time():
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
        stdout, stderr, json_out = self.process_output(minion_tgt, stdout, stderr)
        yield gen.moment
        #yield gen.sleep(0.125)
        raise gen.Return(ShellResult(exitcode, stdout, stderr, json_out))

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


class Salt(SaltCliScriptBase):
    '''
    Class which runs salt-call commands
    '''

    def get_minion_tgt(self, **kwargs):
        return kwargs.pop('minion_tgt', self.config['id'])

    def process_output(self, tgt, stdout, stderr):
        if 'No minions matched the target. No command was sent, no jid was assigned.\n' in stdout:
            stdout = stdout.split('\n', 1)[1:][0]
        stdout, stderr, json_out = SaltCliScriptBase.process_output(self, tgt, stdout, stderr)
        if json_out:
            return stdout, stderr, json_out[tgt]
        return stdout, stderr, json_out


class SaltCall(SaltCliScriptBase):
    '''
    Class which runs salt-call commands
    '''

    def get_script_args(self):
        return ['--retcode-passthrough']


class SaltKey(SaltCliScriptBase):
    '''
    Class which runs salt-key commands
    '''


class SaltRun(SaltCliScriptBase):
    '''
    Class which runs salt-run commands
    '''

    def process_output(self, tgt, stdout, stderr):
        if 'No minions matched the target. No command was sent, no jid was assigned.\n' in stdout:
            stdout = stdout.split('\n', 1)[1:][0]
        stdout, stderr, json_out = SaltCliScriptBase.process_output(self, tgt, stdout, stderr)
        return stdout, stderr, json_out


class SaltSSH(SaltCliScriptBase):
    '''
    Class which runs salt-ssh commands
    '''

    def get_script_args(self):
        return [
            '-l', 'trace',
            '-w',
            '--rand-thin-dir',
            '--roster-file={0}'.format(os.path.join(self.config_dir, 'roster')),
            '--ignore-host-keys',
        ]

    def get_minion_tgt(self, **kwargs):
        return 'localhost'

    def process_output(self, tgt, stdout, stderr):
        stdout, stderr, json_out = SaltCliScriptBase.process_output(self, tgt, stdout, stderr)
        if json_out:
            return stdout, stderr, json_out[tgt]
        return stdout, stderr, json_out


class SaltMinion(SaltDaemonScriptBase):
    '''
    Class which runs the salt-minion daemon
    '''

    def get_script_args(self):
        return ['--disable-keepalive', '-l', 'quiet']

    def get_check_ports(self):
        return set([self.config['id'], self.config['pytest_port']])


class SaltMaster(SaltDaemonScriptBase):
    '''
    Class which runs the salt-master daemon
    '''

    def get_check_ports(self):
        return set([self.config['ret_port'],
                    self.config['publish_port'],
                    self.config['pytest_port']])

    def get_script_args(self):
        return ['-l', 'quiet']


class SaltSyndic(SaltDaemonScriptBase):
    '''
    Class which runs the salt-syndic daemon
    '''

    def get_check_ports(self):
        return set([self.config['pytest_port']])

    def get_script_args(self):
        return ['-l', 'quiet']


class SSHD(SaltDaemonScriptBase):
    '''
    Class which runs an sshd daemon
    '''

    def get_script_path(self, script_name):
        '''
        Returns the path to the script to run
        '''
        sshd = salt_utils.which(self.cli_script_name)
        if not sshd:
            pytest.skip('"sshd" not found')
        return sshd

    def get_base_script_args(self):
        return ['-D', '-f', os.path.join(self.config_dir, 'sshd_config')]

    def get_check_ports(self):
        return [self.config['port']]


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
