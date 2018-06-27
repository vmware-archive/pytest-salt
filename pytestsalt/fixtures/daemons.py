# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2015 by the SaltStack Team, see AUTHORS for more details.
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
import logging
import subprocess

# Import 3rd-party libs
import pytest

from pytestsalt.utils import SaltCliScriptBase, SaltDaemonScriptBase, start_daemon

log = logging.getLogger(__name__)


@pytest.fixture
def salt_cli_default_timeout():
    '''
    Default timeout for CLI tools
    '''


@pytest.fixture(scope='session')
def salt_version(_cli_bin_dir, cli_master_script_name, python_executable_path):
    '''
    Return the salt version for the CLI install
    '''
    try:
        import salt.ext.six as six
    except ImportError:
        import six
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
                log_server,  # pylint: disable=unused-argument
                master_log_prefix,
                cli_master_script_name,
                _cli_bin_dir,
                _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                        log_server,  # pylint: disable=unused-argument
                        session_master_log_prefix,
                        cli_master_script_name,
                        _cli_bin_dir,
                        _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                           log_server,  # pylint: disable=unused-argument
                           master_of_masters_log_prefix,
                           cli_master_script_name,
                           _cli_bin_dir,
                           _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                                   log_server,  # pylint: disable=unused-argument
                                   session_master_of_masters_log_prefix,
                                   cli_master_script_name,
                                   _cli_bin_dir,
                                   _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                _cli_bin_dir,
                _salt_fail_hard,
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                        _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                          _cli_bin_dir,
                          _salt_fail_hard,
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                                  _salt_fail_hard,
                                  session_secondary_conf_dir):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                log_server,  # pylint: disable=unused-argument
                syndic_log_prefix,
                cli_syndic_script_name,
                _cli_bin_dir,
                _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
                        log_server,  # pylint: disable=unused-argument
                        session_syndic_log_prefix,
                        cli_syndic_script_name,
                        _cli_bin_dir,
                        _salt_fail_hard):
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
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


@pytest.yield_fixture
def salt_proxy_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-proxy and after ending it.
    '''
    # Prep routines go here

    # Start the salt-proxy
    yield

    # Clean routines go here


@pytest.yield_fixture
def salt_proxy_after_start(salt_proxy):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-proxy and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture
def salt_proxy(request,
               salt_master,
               proxy_id,
               proxy_config,
               salt_proxy_before_start,  # pylint: disable=unused-argument
               proxy_log_prefix,
               cli_proxy_script_name,
               log_server,
               _cli_bin_dir,
               _salt_fail_hard,
               conf_dir):  # pylint: disable=unused-argument
    '''
    Returns a running salt-proxy
    '''
    return start_daemon(request,
                        daemon_name='salt-proxy',
                        daemon_id=proxy_id,
                        daemon_log_prefix=proxy_log_prefix,
                        daemon_cli_script_name=cli_proxy_script_name,
                        daemon_config=proxy_config,
                        daemon_config_dir=conf_dir,
                        daemon_class=SaltProxy,
                        bin_dir_path=_cli_bin_dir,
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


@pytest.yield_fixture(scope='session')
def session_salt_proxy_before_start():
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work before starting
    the salt-minion and after ending it.
    '''
    # Prep routines go here

    # Start the salt-proxy
    yield

    # Clean routines go here


@pytest.yield_fixture(scope='session')
def session_salt_proxy_after_start(session_salt_proxy):
    '''
    This fixture should be overridden if you need to do
    some preparation and clean up work after starting
    the salt-proxy and before ending it.
    '''
    # Prep routines go here

    # Resume test execution
    yield

    # Clean routines go here


@pytest.fixture(scope='session')
def session_salt_proxy(request,
                       session_salt_master,
                       session_proxy_id,
                       session_proxy_config,
                       session_salt_proxy_before_start,  # pylint: disable=unused-argument
                       session_proxy_log_prefix,
                       cli_minion_script_name,
                       log_server,
                       _cli_bin_dir,
                       session_conf_dir,
                       _salt_fail_hard):
    '''
    Returns a running salt-proxy
    '''
    return start_daemon(request,
                        daemon_name='salt-proxy',
                        daemon_id=session_proxy_id,
                        daemon_log_prefix=session_proxy_log_prefix,
                        daemon_cli_script_name=cli_proxy_script_name,
                        daemon_config=session_proxy_config,
                        daemon_config_dir=session_conf_dir,
                        daemon_class=SaltProxy,
                        bin_dir_path=_cli_bin_dir,
                        fail_hard=_salt_fail_hard,
                        start_timeout=30)


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
         conf_dir,
         cli_salt_script_name,
         salt_cli_default_timeout,
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
                cli_script_name=cli_salt_script_name,
                default_timeout=salt_cli_default_timeout)
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
                 session_conf_dir,
                 cli_salt_script_name,
                 salt_cli_default_timeout,
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
                cli_script_name=cli_salt_script_name,
                default_timeout=salt_cli_default_timeout)
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
              salt_cli_default_timeout,
              log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(request,
                         minion_config,
                         conf_dir,
                         _cli_bin_dir,
                         salt_call_log_prefix,
                         cli_script_name=cli_call_script_name,
                         default_timeout=salt_cli_default_timeout)
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
                      salt_cli_default_timeout,
                      log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_call fixture
    '''
    salt_call = SaltCall(request,
                         session_minion_config,
                         session_conf_dir,
                         _cli_bin_dir,
                         session_salt_call_log_prefix,
                         cli_script_name=cli_call_script_name,
                         default_timeout=salt_cli_default_timeout)
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
             _cli_bin_dir,
             salt_cli_default_timeout,
             log_server):  # pylint: disable=unused-argument
    '''
    returns a salt_key fixture
    '''
    salt_key = SaltKey(request,
                       master_config,
                       conf_dir,
                       _cli_bin_dir,
                       salt_key_log_prefix,
                       cli_script_name=cli_key_script_name,
                       default_timeout=salt_cli_default_timeout)
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
                     _cli_bin_dir,
                     salt_cli_default_timeout,
                     log_server):  # pylint: disable=unused-argument
    '''
    returns a salt_key fixture
    '''
    salt_key = SaltKey(request,
                       session_master_config,
                       session_conf_dir,
                       _cli_bin_dir,
                       session_salt_key_log_prefix,
                       cli_script_name=cli_key_script_name,
                       default_timeout=salt_cli_default_timeout)
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
             master_config,
             _cli_bin_dir,
             salt_cli_default_timeout,
             log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(request,
                       master_config,
                       conf_dir,
                       _cli_bin_dir,
                       salt_run_log_prefix,
                       cli_script_name=cli_run_script_name,
                       default_timeout=salt_cli_default_timeout)
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
                     session_master_config,
                     _cli_bin_dir,
                     salt_cli_default_timeout,
                     log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_run fixture
    '''
    salt_run = SaltRun(request,
                       session_master_config,
                       session_conf_dir,
                       _cli_bin_dir,
                       session_salt_run_log_prefix,
                       cli_script_name=cli_run_script_name,
                       default_timeout=salt_cli_default_timeout)
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
             salt_ssh_before_start,  # pylint: disable=unused-argument
             salt_ssh_log_prefix,
             _cli_bin_dir,
             cli_ssh_script_name,
             roster_config,
             salt_cli_default_timeout,
             log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_ssh fixture
    '''
    salt_ssh = SaltSSH(request,
                       roster_config,
                       conf_dir,
                       _cli_bin_dir,
                       salt_ssh_log_prefix,
                       cli_script_name=cli_ssh_script_name,
                       default_timeout=salt_cli_default_timeout)
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
                     session_salt_ssh_before_start,  # pylint: disable=unused-argument
                     session_salt_ssh_log_prefix,
                     _cli_bin_dir,
                     cli_ssh_script_name,
                     session_roster_config,
                     salt_cli_default_timeout,
                     log_server):  # pylint: disable=unused-argument
    '''
    Returns a salt_ssh fixture
    '''
    salt_ssh = SaltSSH(request,
                       session_roster_config,
                       session_conf_dir,
                       _cli_bin_dir,
                       session_salt_ssh_log_prefix,
                       cli_script_name=cli_ssh_script_name,
                       default_timeout=salt_cli_default_timeout)
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
                write_sshd_config,  # pylint: disable=unused-argument
                sshd_server_before_start,  # pylint: disable=unused-argument
                sshd_server_log_prefix,
                sshd_port,
                sshd_config_dir,
                sshd_priv_dir,
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
                        session_write_sshd_config,  # pylint: disable=unused-argument
                        session_sshd_server_before_start,  # pylint: disable=unused-argument
                        session_sshd_server_log_prefix,
                        session_sshd_port,
                        session_sshd_config_dir,
                        session_sshd_priv_dir,
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


class Salt(SaltCliScriptBase):
    '''
    Class which runs salt-call commands
    '''

    def get_minion_tgt(self, **kwargs):
        return kwargs.pop('minion_tgt', self.config['id'])

    def process_output(self, tgt, stdout, stderr, cli_cmd):
        if 'No minions matched the target. No command was sent, no jid was assigned.\n' in stdout:
            stdout = stdout.split('\n', 1)[1:][0]
        old_stdout = None
        if '--show-jid' in cli_cmd and stdout.startswith('jid: '):
            old_stdout = stdout
            stdout = stdout.split('\n', 1)[-1].strip()
        stdout, stderr, json_out = SaltCliScriptBase.process_output(self, tgt, stdout, stderr, cli_cmd)
        if old_stdout is not None:
            stdout = old_stdout
        if json_out:
            if not isinstance(json_out, dict):
                # A string was most likely loaded, not what we want.
                return stdout, stderr, None
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

    def process_output(self, tgt, stdout, stderr, cli_cmd):
        if 'No minions matched the target. No command was sent, no jid was assigned.\n' in stdout:
            stdout = stdout.split('\n', 1)[1:][0]
        stdout, stderr, json_out = SaltCliScriptBase.process_output(self, tgt, stdout, stderr, cli_cmd)
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

    def process_output(self, tgt, stdout, stderr, cli_cmd):
        stdout, stderr, json_out = SaltCliScriptBase.process_output(self, tgt, stdout, stderr, cli_cmd)
        if json_out:
            return stdout, stderr, json_out[tgt]
        return stdout, stderr, json_out


class SaltMinion(SaltDaemonScriptBase):
    '''
    Class which runs the salt-minion daemon
    '''

    def get_script_args(self):
        script_args = ['-l', 'quiet']
        if sys.platform.startswith('win') is False:
            script_args.append('--disable-keepalive')
        return script_args

    def get_check_events(self):
        if sys.platform.startswith('win'):
            return super(SaltMinion, self).get_check_events()
        return set(['salt/{0}/{1}/start'.format(self.config['__role'], self.config['id'])])

    def get_check_ports(self):
        if sys.platform.startswith('win'):
            return set([self.config['tcp_pub_port'],
                        self.config['tcp_pull_port']])
        return super(SaltMinion, self).get_check_ports()


class SaltProxy(SaltDaemonScriptBase):
    '''
    Class which runs the salt-proxy daemon
    '''

    def get_script_args(self):
        script_args = ['-l', 'quiet']

        script_args.extend(['--proxyid', self.config['id']])
        if sys.platform.startswith('win') is False:
            script_args.append('--disable-keepalive')
        return script_args

    def get_check_events(self):
        if sys.platform.startswith('win'):
            return super(SaltProxy, self).get_check_events()
        return set(['salt/{0}/{1}/start'.format(self.config['__role'], self.config['id'])])

    def get_check_ports(self):
        if sys.platform.startswith('win'):
            return set([self.config['tcp_pub_port'],
                        self.config['tcp_pull_port']])
        return super(SaltProxy, self).get_check_ports()


class SaltMaster(SaltDaemonScriptBase):
    '''
    Class which runs the salt-master daemon
    '''

    def get_script_args(self):
        return ['-l', 'quiet']

    def get_check_events(self):
        if sys.platform.startswith('win'):
            return super(SaltMaster, self).get_check_events()
        return set(['salt/{0}/{1}/start'.format(self.config['__role'], self.config['id'])])

    def get_check_ports(self):
        if sys.platform.startswith('win'):
            return set([self.config['ret_port'],
                        self.config['publish_port']])
        return super(SaltMaster, self).get_check_ports()


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
        import salt.utils
        sshd = salt.utils.which(self.cli_script_name)
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
