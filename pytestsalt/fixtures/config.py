# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures.config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    pytest salt configuration related fixtures
'''
# pylint: disable=redefined-outer-name,too-many-arguments,too-many-locals

# Import python libs
from __future__ import absolute_import, print_function
import os
import pwd
import sys
import logging

# Import 3rd-party libs
import pytest

# Import salt libs
import salt.config
import salt.utils
import salt.utils.dictupdate as dictupdate
import salt.utils.verify as salt_verify
import salt.serializers.yaml as yamlserialize

# Import pytest salt libs
import pytestsalt.salt.engines
import pytestsalt.salt.log_handlers

IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    import win32api

DEFAULT_MASTER_ID = 'pytest-salt-master'
DEFAULT_MINION_ID = 'pytest-salt-minion'
DEFAULT_SESSION_MASTER_ID = 'pytest-session-salt-master'
DEFAULT_SESSION_MINION_ID = 'pytest-session-salt-minion'

log = logging.getLogger(__name__)


class Counter(object):  # pylint: disable=too-few-public-methods
    '''
    Simple counter class which increases count on every call to it's instance
    '''
    def __init__(self):
        self.counter = 0

    def __call__(self):
        try:
            return self.counter
        finally:
            self.counter += 1


def pytest_addoption(parser):
    '''
    Add pytest salt plugin daemons related options
    '''
    saltparser = parser.getgroup('Salt Plugin Options')
    saltparser.addoption(
        '--cli-bin-dir',
        default=None,
        help=('Path to the bin directory where the salt CLI scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )
    parser.addini(
        'cli_bin_dir',
        default=None,
        help=('Path to the bin directory where the salt CLI scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )


#@pytest.hookimpl(trylast=True)
#def pytest_report_header(config, _cli_bin_dir):
#    '''
#    return a string to be displayed as header info for terminal reporting.
#    '''
#    return 'pytest-salt CLI binaries directory: {0}'.format(_cli_bin_dir)


@pytest.fixture(scope='session')
def python_executable_path():
    '''
    return the python executable path
    '''
    return sys.executable


@pytest.fixture(scope='session')
def cli_bin_dir(request, python_executable_path):
    '''
    Return the path to the CLI script directory to use
    '''
    # Default to the directory of the current python executable
    return os.path.dirname(python_executable_path)


@pytest.fixture(scope='session')
def _cli_bin_dir(request, cli_bin_dir):
    '''
    Return the path to the CLI script directory to use
    '''
    path = request.config.getoption('cli_bin_dir')
    if path is not None:
        # We were passed --cli-bin-dir as a CLI option
        return path

    # The path was not passed as a CLI option
    path = request.config.getini('cli_bin_dir')
    if path:
        # We were passed cli_bin_dir as a INI option
        return path

    return _cli_bin_dir


@pytest.fixture(scope='session')
def running_username():
    '''
    Returns the current username
    '''
    if IS_WINDOWS:
        return win32api.GetUserName()
    return pwd.getpwuid(os.getuid()).pw_name


@pytest.fixture(scope='session')
def salt_master_id_counter():
    '''
    Fixture which return a number to include in the master ID.
    Every call to this fixture increases the counter.
    '''
    return Counter()


@pytest.fixture(scope='session')
def salt_minion_id_counter():
    '''
    Fixture which return a number to include in the minion ID.
    Every call to this fixture increases the counter.
    '''
    return Counter()


@pytest.fixture(scope='session')
def cli_master_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-master'


@pytest.fixture(scope='session')
def cli_minion_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-minion'


@pytest.fixture(scope='session')
def cli_salt_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt'


@pytest.fixture(scope='session')
def cli_run_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-run'


@pytest.fixture(scope='session')
def cli_key_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-key'


@pytest.fixture(scope='session')
def cli_call_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-call'


@pytest.fixture(scope='session')
def cli_syndic_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-syndic'


@pytest.fixture
def master_id(salt_master_id_counter):
    '''
    Returns the master id
    '''
    return DEFAULT_MASTER_ID + '-{0}'.format(salt_master_id_counter())


@pytest.fixture
def minion_id(salt_minion_id_counter):
    '''
    Returns the minion id
    '''
    return DEFAULT_MINION_ID + '-{0}'.format(salt_minion_id_counter())


@pytest.fixture(scope='session')
def session_master_id(salt_master_id_counter):
    '''
    Returns the session scope master id
    '''
    return DEFAULT_SESSION_MASTER_ID + '-{0}'.format(salt_master_id_counter())


@pytest.fixture(scope='session')
def session_minion_id(salt_minion_id_counter):
    '''
    Returns the session scope minion id
    '''
    return DEFAULT_SESSION_MINION_ID + '-{0}'.format(salt_minion_id_counter())


@pytest.fixture
def master_config_file(conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return conf_dir.join('master').realpath().strpath


@pytest.fixture
def minion_config_file(conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return conf_dir.join('minion').realpath().strpath


@pytest.fixture
def master_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt master
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture
def minion_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt minion
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def session_master_config_file(session_conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return session_conf_dir.join('master').realpath().strpath


@pytest.fixture(scope='session')
def session_minion_config_file(session_conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return session_conf_dir.join('minion').realpath().strpath


@pytest.fixture(scope='session')
def session_master_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt master
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def session_minion_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt minion
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture
def master_log_prefix(master_id):
    return 'salt-master/{0}'.format(master_id)


@pytest.fixture
def minion_log_prefix(minion_id):
    return 'salt-minion/{0}'.format(minion_id)


@pytest.fixture
def salt_log_prefix(minion_id):
    return 'salt/{0}'.format(minion_id)


@pytest.fixture
def salt_call_log_prefix(master_id):
    return 'salt-call/{0}'.format(master_id)


@pytest.fixture
def salt_key_log_prefix(master_id):
    return 'salt-key/{0}'.format(master_id)


@pytest.fixture
def salt_run_log_prefix(master_id):
    return 'salt-run/{0}'.format(master_id)


def _master_config(root_dir,
                   config_file,
                   publish_port,
                   return_port,
                   engine_port,
                   config_overrides,
                   master_id,
                   base_env_state_tree_root_dirs,
                   prod_env_state_tree_root_dirs,
                   base_env_pillar_tree_root_dirs,
                   prod_env_pillar_tree_root_dirs,
                   running_username,
                   salt_log_port,
                   master_log_prefix):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    default_options = {
        'id': master_id,
        'root_dir': root_dir.strpath,
        'publish_port': publish_port,
        'ret_port': return_port,
        'worker_threads': 3,
        'pidfile': 'run/master.pid',
        'pki_dir': 'pki',
        'cachedir': 'cache',
        'timeout': 3,
        'sock_dir': '.salt-unix',
        'open_mode': True,
        'syndic_master': 'localhost',
        'fileserver_list_cache_time': 0,
        'fileserver_backend': ['roots'],
        'pillar_opts': False,
        'peer': {
            '.*': [
                'test.*'
            ]
        },
        'log_file': 'logs/master',
        'log_level_logfile': 'debug',
        'key_logfile': 'logs/key',
        'token_dir': 'tokens',
        'token_file': root_dir.join('ksfjhdgiuebfgnkefvsikhfjdgvkjahcsidk').strpath,
        'file_buffer_size': 8192,
        'user': running_username,
        'log_fmt_console': "[%(levelname)-8s][%(name)-5s:%(lineno)-4d] %(message)s",
        'log_fmt_logfile': "[%(asctime)s,%(msecs)03.0f][%(name)-5s:%(lineno)-4d][%(levelname)-8s] %(message)s",
        'file_roots': {
            'base': base_env_state_tree_root_dirs,
            'prod': prod_env_state_tree_root_dirs,
        },
        'pillar_roots': {
            'base': base_env_pillar_tree_root_dirs,
            'prod': prod_env_pillar_tree_root_dirs,
        },
        'hash_type': 'sha256'
    }
    if config_overrides:
        # Merge in the default options with the master_config_overrides
        dictupdate.update(default_options, config_overrides, merge_lists=True)

    default_options.setdefault('engines', [])
    if 'pytest' not in default_options['engines']:
        default_options['engines'].append('pytest')

    if 'engines_dirs' not in default_options:
        default_options['engines_dirs'] = []

    default_options['engines_dirs'].insert(0, os.path.dirname(pytestsalt.salt.engines.__file__))
    default_options['pytest_port'] = engine_port

    if 'log_handlers_dirs' not in default_options:
        default_options['log_handlers_dirs'] = []
    default_options['log_handlers_dirs'].insert(0, os.path.dirname(pytestsalt.salt.log_handlers.__file__))

    default_options['pytest_log_port'] = salt_log_port
    default_options['pytest_log_prefix'] = '[{0}] '.format(master_log_prefix)

    log.info('Writing configuration file to %s', config_file)

    # Write down the computed configuration into the config file
    with salt.utils.fopen(config_file, 'w') as wfh:
        wfh.write(yamlserialize.serialize(default_options))

    # Make sure to load the config file as a salt-master starting from CLI
    options = salt.config.master_config(config_file)

    # verify env to make sure all required directories are created and have the
    # right permissions
    verify_env_entries = [
        os.path.join(options['pki_dir'], 'minions'),
        os.path.join(options['pki_dir'], 'minions_pre'),
        os.path.join(options['pki_dir'], 'minions_rejected'),
        os.path.join(options['pki_dir'], 'accepted'),
        os.path.join(options['pki_dir'], 'rejected'),
        os.path.join(options['pki_dir'], 'pending'),
        os.path.dirname(options['log_file']),
        options['token_dir'],
        #options['extension_modules'],
        options['sock_dir'],
    ]
    verify_env_entries += base_env_state_tree_root_dirs
    verify_env_entries += prod_env_state_tree_root_dirs
    verify_env_entries += base_env_pillar_tree_root_dirs
    verify_env_entries += prod_env_pillar_tree_root_dirs

    if default_options.get('transport', None) == 'raet':
        verify_env_entries.extend([
            os.path.join(options['cachedir'], 'raet'),
        ])
    else:
        verify_env_entries.extend([
            os.path.join(options['cachedir'], 'jobs'),
        ])

    salt_verify.verify_env(
        verify_env_entries,
        running_username,
        pki_dir=options['pki_dir']
    )
    return options


@pytest.fixture
def master_config(root_dir,
                  master_config_file,
                  master_publish_port,
                  master_return_port,
                  master_engine_port,
                  master_config_overrides,
                  master_id,
                  base_env_state_tree_root_dir,
                  prod_env_state_tree_root_dir,
                  base_env_pillar_tree_root_dir,
                  prod_env_pillar_tree_root_dir,
                  running_username,
                  salt_log_port,
                  master_log_prefix):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    return _master_config(root_dir,
                          master_config_file,
                          master_publish_port,
                          master_return_port,
                          master_engine_port,
                          master_config_overrides,
                          master_id,
                          [base_env_state_tree_root_dir.strpath],
                          [prod_env_state_tree_root_dir.strpath],
                          [base_env_pillar_tree_root_dir.strpath],
                          [prod_env_pillar_tree_root_dir.strpath],
                          running_username,
                          salt_log_port,
                          master_log_prefix)


@pytest.fixture(scope='session')
def session_master_config(session_root_dir,
                          session_master_config_file,
                          session_master_publish_port,
                          session_master_return_port,
                          session_master_engine_port,
                          session_master_config_overrides,
                          session_master_id,
                          session_base_env_state_tree_root_dir,
                          session_prod_env_state_tree_root_dir,
                          session_base_env_pillar_tree_root_dir,
                          session_prod_env_pillar_tree_root_dir,
                          running_username,
                          salt_log_port):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``session_master_config_overrides``
    '''
    return _master_config(session_root_dir,
                          session_master_config_file,
                          session_master_publish_port,
                          session_master_return_port,
                          session_master_engine_port,
                          session_master_config_overrides,
                          session_master_id,
                          [session_base_env_state_tree_root_dir.strpath],
                          [session_prod_env_state_tree_root_dir.strpath],
                          [session_base_env_pillar_tree_root_dir.strpath],
                          [session_prod_env_pillar_tree_root_dir.strpath],
                          running_username,
                          salt_log_port)


def _minion_config(root_dir,
                   config_file,
                   return_port,
                   engine_port,
                   config_overrides,
                   minion_id,
                   running_username,
                   salt_log_port,
                   minion_log_prefix):
    '''
    This fixture will return the salt minion configuration options after being
    overridden with any options passed from ``config_overrides``
    '''
    default_options = {
        'root_dir': root_dir.strpath,
        'master': 'localhost',
        'master_port': return_port,
        'id': minion_id,
        'pidfile': 'run/minion.pid',
        'pki_dir': 'pki',
        'cachedir': 'cache',
        'sock_dir': '.salt-unix',
        'log_file': 'logs/minion',
        'log_level_logfile': 'debug',
        'loop_interval': 0.05,
        'open_mode': True,
        'user': running_username,
        #'multiprocessing': False,
        'log_fmt_console': "[%(levelname)-8s][%(name)-5s:%(lineno)-4d] %(message)s",
        'log_fmt_logfile': "[%(asctime)s,%(msecs)03.0f][%(name)-5s:%(lineno)-4d][%(levelname)-8s] %(message)s",
        'hash_type': 'sha256'
    }
    if config_overrides:
        # Merge in the default options with the minion_config_overrides
        dictupdate.update(default_options, config_overrides, merge_lists=True)

    default_options.setdefault('engines', [])
    if 'pytest' not in default_options['engines']:
        default_options['engines'].append('pytest')

    if 'engines_dirs' not in default_options:
        default_options['engines_dirs'] = []

    default_options['engines_dirs'].insert(0, os.path.dirname(pytestsalt.salt.engines.__file__))
    default_options['pytest_port'] = engine_port

    if 'log_handlers_dirs' not in default_options:
        default_options['log_handlers_dirs'] = []
    default_options['log_handlers_dirs'].insert(0, os.path.dirname(pytestsalt.salt.log_handlers.__file__))

    default_options['pytest_log_port'] = salt_log_port
    default_options['pytest_log_prefix'] = '[{0}] '.format(minion_log_prefix)

    log.info('Writing configuration file to %s', config_file)

    # Write down the computed configuration into the config file
    with salt.utils.fopen(config_file, 'w') as wfh:
        wfh.write(yamlserialize.serialize(default_options))

    # Make sure to load the config file as a salt-master starting from CLI
    options = salt.config.minion_config(config_file)

    # verify env to make sure all required directories are created and have the
    # right permissions
    verify_env_entries = [
        os.path.join(options['pki_dir'], 'minions'),
        os.path.join(options['pki_dir'], 'minions_pre'),
        os.path.join(options['pki_dir'], 'minions_rejected'),
        os.path.join(options['pki_dir'], 'accepted'),
        os.path.join(options['pki_dir'], 'rejected'),
        os.path.join(options['pki_dir'], 'pending'),
        os.path.dirname(options['log_file']),
        os.path.join(options['cachedir'], 'proc'),
        #options['extension_modules'],
        options['sock_dir'],
    ]
    salt_verify.verify_env(
        verify_env_entries,
        running_username,
        pki_dir=options['pki_dir']
    )
    return options


@pytest.fixture
def minion_config(root_dir,
                  minion_config_file,
                  master_return_port,
                  minion_engine_port,
                  minion_config_overrides,
                  minion_id,
                  running_username,
                  salt_log_port,
                  minion_log_prefix):
    '''
    This fixture will return the salt minion configuration options after being
    overrided with any options passed from ``minion_config_overrides``
    '''
    return _minion_config(root_dir,
                          minion_config_file,
                          master_return_port,
                          minion_engine_port,
                          minion_config_overrides,
                          minion_id,
                          running_username,
                          salt_log_port,
                          minion_log_prefix)


@pytest.fixture(scope='session')
def session_minion_config(session_root_dir,
                          session_minion_config_file,
                          session_master_return_port,
                          session_minion_engine_port,
                          session_minion_config_overrides,
                          session_minion_id,
                          running_username,
                          salt_log_port):
    '''
    This fixture will return the session salt minion configuration options after being
    overrided with any options passed from ``session_minion_config_overrides``
    '''
    return _minion_config(session_root_dir,
                          session_minion_config_file,
                          session_master_return_port,
                          session_minion_engine_port,
                          session_minion_config_overrides,
                          session_minion_id,
                          running_username,
                          salt_log_port)
