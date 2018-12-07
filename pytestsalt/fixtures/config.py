# -*- coding: utf-8 -*-
'''
pytestsalt.fixtures.config
~~~~~~~~~~~~~~~~~~~~~~~~~~

pytest salt configuration related fixtures
'''
# pylint: disable=redefined-outer-name,too-many-arguments,too-many-locals

# Import python libs
from __future__ import absolute_import, print_function
import os
import sys
import copy
import pprint
import logging
import subprocess

# Import 3rd-party libs
import pytest

IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    import win32api  # pylint: disable=import-error
else:
    import pwd

try:
    import shutil
    COLUMNS = shutil.get_terminal_size((80, 20)).columns
except AttributeError:
    from pytestsalt.ext.console import getTerminalSize
    COLUMNS, _ = getTerminalSize()

DEFAULT_MOM_ID = 'pytest-salt-mom'
DEFAULT_MASTER_ID = 'pytest-salt-master'
DEFAULT_MINION_ID = 'pytest-salt-minion'
DEFAULT_SYNDIC_ID = 'pytest-salt-syndic'
DEFAULT_SECONDARY_MINION_ID = 'pytest-salt-sec-minion'
DEFAULT_SESSION_MOM_ID = 'pytest-session-salt-mom'
DEFAULT_SESSION_MASTER_ID = 'pytest-session-salt-master'
DEFAULT_SESSION_MINION_ID = 'pytest-session-salt-minion'
DEFAULT_SESSION_SYNDIC_ID = 'pytest-session-salt-syndic'
DEFAULT_SESSION_SECONDARY_MINION_ID = 'pytest-session-salt-sec-minion'

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
    saltparser.addoption(
        '--salt-fail-hard',
        default=None,
        action='store_true',
        help=('If a salt daemon fails to start, the test is marked as XFailed. '
              'If this flag is passed, then a test failure is raised instead of XFail.')
    )
    parser.addini(
        'cli_bin_dir',
        default=None,
        help=('Path to the bin directory where the salt CLI scripts can be '
              'found. Defaults to the directory name of the python executable '
              'running py.test')
    )
    parser.addini(
        'salt_fail_hard',
        default=None,
        type='bool',
        help=('If a salt daemon fails to start, the test is marked as XFailed. '
              'If this flag is set, then a test failure is raised instead of XFail.')
    )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, startdir):
    '''
    return a string to be displayed as header info for terminal reporting.
    '''
    # Store a reference to where the base directory of the project is
    config.startdir = startdir


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
        return os.path.expanduser(path)

    # The path was not passed as a CLI option
    path = request.config.getini('cli_bin_dir')
    if path:
        # We were passed cli_bin_dir as a INI option
        return os.path.expanduser(path)

    return cli_bin_dir


@pytest.fixture(scope='session')
def salt_fail_hard(request):
    '''
    Return the salt fail hard value
    '''
    return False


@pytest.fixture(scope='session')
def _salt_fail_hard(request, salt_fail_hard):
    '''
    Return the salt fail hard value
    '''
    fail_hard = request.config.getoption('salt_fail_hard')
    if fail_hard is not None:
        # We were passed --salt-fail-hard as a CLI option
        return fail_hard

    # The salt fail hard was not passed as a CLI option
    fail_hard = request.config.getini('salt_fail_hard')
    if fail_hard != []:
        # We were passed salt_fail_hard as a INI option
        return fail_hard

    return salt_fail_hard


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
def salt_master_of_masters_id_counter():
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
def salt_syndic_id_counter():
    '''
    Fixture which return a number to include in the syndic ID.
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
def cli_proxy_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-proxy'


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


@pytest.fixture(scope='session')
def cli_ssh_script_name():
    '''
    Return the CLI script basename
    '''
    return 'salt-ssh'


@pytest.fixture
def master_of_masters_id(salt_master_of_masters_id_counter):
    '''
    Returns the master of masters id
    '''
    return DEFAULT_MOM_ID + '-{}'.format(salt_master_of_masters_id_counter())


@pytest.fixture
def master_id(salt_master_id_counter):
    '''
    Returns the master id
    '''
    return DEFAULT_MASTER_ID + '-{}'.format(salt_master_id_counter())


@pytest.fixture
def minion_id(salt_minion_id_counter):
    '''
    Returns the minion id
    '''
    return DEFAULT_MINION_ID + '-{}'.format(salt_minion_id_counter())


@pytest.fixture
def secondary_minion_id(salt_minion_id_counter):
    '''
    Returns the secondary minion id
    '''
    return DEFAULT_SECONDARY_MINION_ID + '-{}'.format(salt_minion_id_counter())


@pytest.fixture
def syndic_id(salt_syndic_id_counter):
    '''
    Returns the syndic id
    '''
    return DEFAULT_SYNDIC_ID + '-{}'.format(salt_syndic_id_counter())


@pytest.fixture(scope='session')
def session_master_of_masters_id(salt_master_of_masters_id_counter):
    '''
    Returns the master of masters id
    '''
    return DEFAULT_SESSION_MOM_ID + '-{}'.format(salt_master_of_masters_id_counter())


@pytest.fixture(scope='session')
def session_master_id(salt_master_id_counter):
    '''
    Returns the session scoped master id
    '''
    return DEFAULT_SESSION_MASTER_ID + '-{}'.format(salt_master_id_counter())


@pytest.fixture(scope='session')
def session_minion_id(salt_minion_id_counter):
    '''
    Returns the session scoped minion id
    '''
    return DEFAULT_SESSION_MINION_ID + '-{}'.format(salt_minion_id_counter())


@pytest.fixture(scope='session')
def session_secondary_minion_id(salt_minion_id_counter):
    '''
    Returns the session scoped secondary minion id
    '''
    return DEFAULT_SESSION_SECONDARY_MINION_ID + '-{}'.format(salt_minion_id_counter())


@pytest.fixture(scope='session')
def session_syndic_id(salt_syndic_id_counter):
    '''
    Returns the session scoped syndic id
    '''
    return DEFAULT_SESSION_SYNDIC_ID + '-{}'.format(salt_syndic_id_counter())


@pytest.fixture
def master_config_file(conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return conf_dir.join('master').realpath().strpath


@pytest.fixture
def master_of_masters_config_file(master_of_masters_conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return master_of_masters_conf_dir.join('master').realpath().strpath


@pytest.fixture
def minion_config_file(conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return conf_dir.join('minion').realpath().strpath


@pytest.fixture
def secondary_minion_config_file(secondary_conf_dir):
    '''
    Returns the path to the salt secondary minion configuration file
    '''
    return secondary_conf_dir.join('minion').realpath().strpath


@pytest.fixture
def proxy_config_file(conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return conf_dir.join('proxy').realpath().strpath


@pytest.fixture
def master_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt master
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture
def master_of_masters_config_overrides():
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


@pytest.fixture
def secondary_minion_config_overrides():
    '''
    This fixture should be implemented to overwrite default secondary salt minion
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture
def syndic_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt syndic
    minion configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def session_master_config_file(session_conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return session_conf_dir.join('master').realpath().strpath


@pytest.fixture(scope='session')
def session_master_of_masters_config_file(session_master_of_masters_conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return session_master_of_masters_conf_dir.join('master').realpath().strpath


@pytest.fixture(scope='session')
def session_minion_config_file(session_conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return session_conf_dir.join('minion').realpath().strpath


@pytest.fixture(scope='session')
def session_secondary_minion_config_file(session_secondary_conf_dir):
    '''
    Returns the path to the salt secondary minion configuration file
    '''
    return session_secondary_conf_dir.join('minion').realpath().strpath


@pytest.fixture(scope='session')
def session_master_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt master
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def session_master_of_masters_config_overrides():
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


@pytest.fixture(scope='session')
def session_secondary_minion_config_overrides():
    '''
    This fixture should be implemented to overwrite default secondary salt minion
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def session_syndic_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt syndic
    minion configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture
def master_log_prefix(master_id):
    return 'salt-master/{}'.format(master_id)


@pytest.fixture(scope='session')
def session_master_log_prefix(session_master_id):
    return 'salt-master/{}'.format(session_master_id)


@pytest.fixture
def master_of_masters_log_prefix(master_of_masters_id):
    return 'salt-master/{}'.format(master_of_masters_id)


@pytest.fixture(scope='session')
def session_master_of_masters_log_prefix(session_master_of_masters_id):
    return 'salt-master/{}'.format(session_master_of_masters_id)


@pytest.fixture
def minion_log_prefix(minion_id):
    return 'salt-minion/{}'.format(minion_id)


@pytest.fixture(scope='session')
def session_minion_log_prefix(session_minion_id):
    return 'salt-minion/{}'.format(session_minion_id)


@pytest.fixture
def proxy_log_prefix(minion_id):
    return 'salt-proxy/{}'.format(minion_id)


@pytest.fixture(scope='session')
def session_proxy_log_prefix(session_minion_id):
    return 'salt-proxy/{}'.format(session_minion_id)


@pytest.fixture
def secondary_minion_log_prefix(secondary_minion_id):
    return 'salt-minion/{}'.format(secondary_minion_id)


@pytest.fixture(scope='session')
def session_secondary_minion_log_prefix(session_secondary_minion_id):
    return 'salt-minion/{}'.format(session_secondary_minion_id)


@pytest.fixture
def syndic_log_prefix(syndic_id):
    return 'salt-syndic/{}'.format(syndic_id)


@pytest.fixture(scope='session')
def session_syndic_log_prefix(session_syndic_id):
    return 'salt-syndic/{}'.format(session_syndic_id)


@pytest.fixture
def salt_log_prefix(minion_id):
    return 'salt/{}'.format(minion_id)


@pytest.fixture(scope='session')
def session_salt_log_prefix(session_minion_id):
    return 'salt/{}'.format(session_minion_id)


@pytest.fixture
def salt_call_log_prefix(master_id):
    return 'salt-call/{}'.format(master_id)


@pytest.fixture(scope='session')
def session_salt_call_log_prefix(session_master_id):
    return 'salt-call/{}'.format(session_master_id)


@pytest.fixture
def salt_key_log_prefix(master_id):
    return 'salt-key/{}'.format(master_id)


@pytest.fixture(scope='session')
def session_salt_key_log_prefix(session_master_id):
    return 'salt-key/{}'.format(session_master_id)


@pytest.fixture
def salt_run_log_prefix(master_id):
    return 'salt-run/{}'.format(master_id)


@pytest.fixture(scope='session')
def session_salt_run_log_prefix(session_master_id):
    return 'salt-run/{}'.format(session_master_id)


def apply_master_config(default_options,
                        root_dir,
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
                        log_server_port,
                        log_server_level,
                        engines_dir,
                        log_handlers_dir,
                        master_log_prefix,
                        tcp_master_pub_port,
                        tcp_master_pull_port,
                        tcp_master_publish_pull,
                        tcp_master_workers,
                        direct_overrides=None):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    import pytestsalt.utils.compat as compat
    import salt.config
    import salt.utils
    import salt.utils.dictupdate as dictupdate
    import salt.utils.verify as salt_verify
    import salt.utils.yaml as yamlserialize
    _default_options = {
        'id': master_id,
        'interface': '127.0.0.1',
        'root_dir': root_dir.strpath,
        'publish_port': publish_port,
        'ret_port': return_port,
        'tcp_master_pub_port': tcp_master_pub_port,
        'tcp_master_pull_port': tcp_master_pull_port,
        'tcp_master_publish_pull': tcp_master_publish_pull,
        'tcp_master_workers': tcp_master_workers,
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
        'log_file': 'logs/master.log',
        'log_level_logfile': 'debug',
        'key_logfile': 'logs/key.log',
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
    for varname in ('sock_dir',):
        # These are settings which are tested against and provided by Salt's test suite, so,
        # let's not override them if provided
        if varname in default_options:
            _default_options.pop(varname)
    # Merge in the initial default options with the internal _default_options
    dictupdate.update(default_options, _default_options, merge_lists=True)

    if config_overrides:
        # Merge in the default options with the master_config_overrides
        dictupdate.update(default_options, config_overrides, merge_lists=True)

    default_options.setdefault('engines', [])
    if 'pytest' not in default_options['engines']:
        default_options['engines'].append('pytest')

    if 'engines_dirs' not in default_options:
        default_options['engines_dirs'] = []

    default_options['engines_dirs'].insert(0, engines_dir)
    default_options['pytest_engine_port'] = engine_port

    if 'log_handlers_dirs' not in default_options:
        default_options['log_handlers_dirs'] = []
    default_options['log_handlers_dirs'].insert(0, log_handlers_dir)

    default_options['pytest_log_host'] = 'localhost'
    default_options['pytest_log_port'] = log_server_port
    default_options['pytest_log_level'] = log_server_level
    default_options['pytest_log_prefix'] = master_log_prefix

    if direct_overrides is not None:
        # We've been passed some direct override configuration.
        # Apply it!
        dictupdate.update(default_options, direct_overrides, merge_lists=True)

    log.info('Writing to configuration file %s. Configuration:\n%s',
             config_file,
             pprint.pformat(default_options))

    # Write down the computed configuration into the config file
    with compat.fopen(config_file, 'w') as wfh:
        yamlserialize.safe_dump(default_options, wfh, default_flow_style=False)

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

    try:
        salt_verify.verify_env(  # pylint: disable=unexpected-keyword-arg
            verify_env_entries,
            running_username,
            sensitive_dirs=[options['pki_dir']]
        )
    except TypeError:
        salt_verify.verify_env(
            verify_env_entries,
            running_username,
            pki_dir=options['pki_dir']
        )
    return options


@pytest.fixture
def master_default_options():
    return {}


@pytest.fixture
def master_config(root_dir,
                  master_default_options,
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
                  log_server_port,
                  log_server_level,
                  engines_dir,
                  log_handlers_dir,
                  master_log_prefix,
                  master_tcp_master_pub_port,
                  master_tcp_master_pull_port,
                  master_tcp_master_publish_pull,
                  master_tcp_master_workers):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    return apply_master_config(master_default_options,
                               root_dir,
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
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               master_log_prefix,
                               master_tcp_master_pub_port,
                               master_tcp_master_pull_port,
                               master_tcp_master_publish_pull,
                               master_tcp_master_workers)


@pytest.fixture(scope='session')
def session_master_default_options():
    return {}


@pytest.fixture(scope='session')
def session_master_config(session_root_dir,
                          session_master_default_options,
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
                          log_server_port,
                          log_server_level,
                          engines_dir,
                          log_handlers_dir,
                          session_master_log_prefix,
                          session_master_tcp_master_pub_port,
                          session_master_tcp_master_pull_port,
                          session_master_tcp_master_publish_pull,
                          session_master_tcp_master_workers):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``session_master_config_overrides``
    '''
    return apply_master_config(session_master_default_options,
                               session_root_dir,
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
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               session_master_log_prefix,
                               session_master_tcp_master_pub_port,
                               session_master_tcp_master_pull_port,
                               session_master_tcp_master_publish_pull,
                               session_master_tcp_master_workers)


@pytest.fixture(scope='session')
def master_of_masters_default_options():
    return {}


@pytest.fixture
def master_of_masters_config(master_of_masters_root_dir,
                             master_of_masters_config_file,
                             master_of_masters_default_options,
                             master_of_masters_publish_port,
                             master_of_masters_return_port,
                             master_of_masters_engine_port,
                             master_of_masters_config_overrides,
                             master_of_masters_id,
                             master_of_masters_base_env_state_tree_root_dir,
                             master_of_masters_prod_env_state_tree_root_dir,
                             master_of_masters_base_env_pillar_tree_root_dir,
                             master_of_masters_prod_env_pillar_tree_root_dir,
                             running_username,
                             log_server_port,
                             log_server_level,
                             engines_dir,
                             log_handlers_dir,
                             master_of_masters_log_prefix,
                             master_of_masters_master_tcp_master_pub_port,
                             master_of_masters_master_tcp_master_pull_port,
                             master_of_masters_master_tcp_master_publish_pull,
                             master_of_masters_master_tcp_master_workers):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    direct_overrides = {
        'order_masters': True,
    }
    return apply_master_config(master_of_masters_default_options,
                               master_of_masters_root_dir,
                               master_of_masters_config_file,
                               master_of_masters_publish_port,
                               master_of_masters_return_port,
                               master_of_masters_engine_port,
                               master_of_masters_config_overrides,
                               master_of_masters_id,
                               [master_of_masters_base_env_state_tree_root_dir.strpath],
                               [master_of_masters_prod_env_state_tree_root_dir.strpath],
                               [master_of_masters_base_env_pillar_tree_root_dir.strpath],
                               [master_of_masters_prod_env_pillar_tree_root_dir.strpath],
                               running_username,
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               master_of_masters_log_prefix,
                               master_of_masters_master_tcp_master_pub_port,
                               master_of_masters_master_tcp_master_pull_port,
                               master_of_masters_master_tcp_master_publish_pull,
                               master_of_masters_master_tcp_master_workers,
                               direct_overrides=direct_overrides)


@pytest.fixture(scope='session')
def session_master_of_masters_default_options():
    return {}


@pytest.fixture(scope='session')
def session_master_of_masters_config(session_master_of_masters_root_dir,
                                     session_master_of_masters_config_file,
                                     session_master_of_masters_publish_port,
                                     session_master_of_masters_return_port,
                                     session_master_of_masters_engine_port,
                                     session_master_of_masters_default_options,
                                     session_master_of_masters_config_overrides,
                                     session_master_of_masters_id,
                                     session_base_env_state_tree_root_dir,
                                     session_prod_env_state_tree_root_dir,
                                     session_base_env_pillar_tree_root_dir,
                                     session_prod_env_pillar_tree_root_dir,
                                     running_username,
                                     log_server_port,
                                     log_server_level,
                                     engines_dir,
                                     log_handlers_dir,
                                     session_master_of_masters_log_prefix,
                                     session_master_of_masters_master_tcp_master_pub_port,
                                     session_master_of_masters_master_tcp_master_pull_port,
                                     session_master_of_masters_master_tcp_master_publish_pull,
                                     session_master_of_masters_master_tcp_master_workers):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``session_master_config_overrides``
    '''
    direct_overrides = {
        'order_masters': True,
    }
    return apply_master_config(session_master_of_masters_default_options,
                               session_master_of_masters_root_dir,
                               session_master_of_masters_config_file,
                               session_master_of_masters_publish_port,
                               session_master_of_masters_return_port,
                               session_master_of_masters_engine_port,
                               session_master_of_masters_config_overrides,
                               session_master_of_masters_id,
                               [session_base_env_state_tree_root_dir.strpath],
                               [session_prod_env_state_tree_root_dir.strpath],
                               [session_base_env_pillar_tree_root_dir.strpath],
                               [session_prod_env_pillar_tree_root_dir.strpath],
                               running_username,
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               session_master_of_masters_log_prefix,
                               session_master_of_masters_master_tcp_master_pub_port,
                               session_master_of_masters_master_tcp_master_pull_port,
                               session_master_of_masters_master_tcp_master_publish_pull,
                               session_master_of_masters_master_tcp_master_workers,
                               direct_overrides=direct_overrides)


def apply_minion_config(default_options,
                        root_dir,
                        config_file,
                        return_port,
                        engine_port,
                        config_overrides,
                        minion_id,
                        running_username,
                        log_server_port,
                        log_server_level,
                        engines_dir,
                        log_handlers_dir,
                        minion_log_prefix,
                        tcp_pub_port,
                        tcp_pull_port,
                        direct_overrides=None):
    '''
    This fixture will return the salt minion configuration options after being
    overridden with any options passed from ``config_overrides``
    '''
    import pytestsalt.utils.compat as compat
    import salt.config
    import salt.utils
    import salt.utils.dictupdate as dictupdate
    import salt.utils.verify as salt_verify
    import salt.utils.yaml as yamlserialize
    _default_options = {
        'root_dir': root_dir.strpath,
        'interface': '127.0.0.1',
        'master': '127.0.0.1',
        'master_port': return_port,
        'tcp_pub_port': tcp_pub_port,
        'tcp_pull_port': tcp_pull_port,
        'id': minion_id,
        'pidfile': 'run/minion.pid',
        'pki_dir': 'pki',
        'cachedir': 'cache',
        'sock_dir': '.salt-unix',
        'log_file': 'logs/minion.log',
        'log_level_logfile': 'debug',
        'loop_interval': 0.05,
        'open_mode': True,
        'user': running_username,
        #'multiprocessing': False,
        'log_fmt_console': "[%(levelname)-8s][%(name)-5s:%(lineno)-4d] %(message)s",
        'log_fmt_logfile': "[%(asctime)s,%(msecs)03.0f][%(name)-5s:%(lineno)-4d][%(levelname)-8s] %(message)s",
        'hash_type': 'sha256'
    }
    for varname in ('sock_dir',):
        # These are settings which are tested against and provided by Salt's test suite, so,
        # let's not override them if provided
        if varname in default_options:
            _default_options.pop(varname)
    # Merge in the initial default options with the internal _default_options
    dictupdate.update(default_options, _default_options, merge_lists=True)

    if config_overrides:
        # Merge in the default options with the minion_config_overrides
        dictupdate.update(default_options, config_overrides, merge_lists=True)

    #default_options.setdefault('engines', [])
    #if 'pytest' not in default_options['engines']:
    #    default_options['engines'].append('pytest')

    #if 'engines_dirs' not in default_options:
    #    default_options['engines_dirs'] = []

    #default_options['engines_dirs'].insert(0, engines_dir)
    #default_options['pytest_engine_port'] = engine_port

    if 'log_handlers_dirs' not in default_options:
        default_options['log_handlers_dirs'] = []
    default_options['log_handlers_dirs'].insert(0, log_handlers_dir)

    default_options['pytest_log_host'] = 'localhost'
    default_options['pytest_log_port'] = log_server_port
    default_options['pytest_log_level'] = log_server_level
    default_options['pytest_log_prefix'] = minion_log_prefix

    if direct_overrides is not None:
        # We've been passed some direct override configuration.
        # Apply it!
        dictupdate.update(default_options, direct_overrides, merge_lists=True)

    log.info('Writing to configuration file %s. Configuration:\n%s',
             config_file,
             pprint.pformat(default_options))

    # Write down the computed configuration into the config file
    with compat.fopen(config_file, 'w') as wfh:
        yamlserialize.safe_dump(default_options, wfh, default_flow_style=False)

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
    try:
        # Salt > v2017.7.x
        salt_verify.verify_env(  # pylint: disable=unexpected-keyword-arg
            verify_env_entries,
            running_username,
            sensitive_dirs=[options['pki_dir']]
        )
    except TypeError:
        # Salt <= v2017.7.x
        salt_verify.verify_env(
            verify_env_entries,
            running_username,
            pki_dir=options['pki_dir']
        )
    return options


@pytest.fixture
def minion_default_options():
    return {}


@pytest.fixture
def minion_config(root_dir,
                  minion_config_file,
                  master_return_port,
                  minion_engine_port,
                  minion_default_options,
                  minion_config_overrides,
                  minion_id,
                  running_username,
                  log_server_port,
                  log_server_level,
                  engines_dir,
                  log_handlers_dir,
                  minion_log_prefix,
                  minion_tcp_pub_port,
                  minion_tcp_pull_port):
    '''
    This fixture will return the salt minion configuration options after being
    overrided with any options passed from ``minion_config_overrides``
    '''
    return apply_minion_config(minion_default_options,
                               root_dir,
                               minion_config_file,
                               master_return_port,
                               minion_engine_port,
                               minion_config_overrides,
                               minion_id,
                               running_username,
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               minion_log_prefix,
                               minion_tcp_pub_port,
                               minion_tcp_pull_port)


@pytest.fixture(scope='session')
def session_minion_default_options():
    return {}


@pytest.fixture(scope='session')
def session_minion_config(session_root_dir,
                          session_minion_config_file,
                          session_master_return_port,
                          session_minion_engine_port,
                          session_minion_default_options,
                          session_minion_config_overrides,
                          session_minion_id,
                          running_username,
                          log_server_port,
                          log_server_level,
                          engines_dir,
                          log_handlers_dir,
                          session_minion_log_prefix,
                          session_minion_tcp_pub_port,
                          session_minion_tcp_pull_port):
    '''
    This fixture will return the session salt minion configuration options after being
    overrided with any options passed from ``session_minion_config_overrides``
    '''
    return apply_minion_config(session_minion_default_options,
                               session_root_dir,
                               session_minion_config_file,
                               session_master_return_port,
                               session_minion_engine_port,
                               session_minion_config_overrides,
                               session_minion_id,
                               running_username,
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               session_minion_log_prefix,
                               session_minion_tcp_pub_port,
                               session_minion_tcp_pull_port)


@pytest.fixture
def secondary_minion_default_options():
    return {}


@pytest.fixture
def secondary_minion_config(secondary_root_dir,
                            secondary_minion_config_file,
                            master_return_port,
                            secondary_minion_engine_port,
                            secondary_minion_default_options,
                            secondary_minion_config_overrides,
                            secondary_minion_id,
                            running_username,
                            log_server_port,
                            log_server_level,
                            engines_dir,
                            log_handlers_dir,
                            secondary_minion_log_prefix,
                            secondary_minion_tcp_pub_port,
                            secondary_minion_tcp_pull_port):
    '''
    This fixture will return the secondary salt minion configuration options after being
    overrided with any options passed from ``secondary_minion_config_overrides``
    '''
    return apply_minion_config(secondary_minion_default_options,
                               secondary_root_dir,
                               secondary_minion_config_file,
                               master_return_port,
                               secondary_minion_engine_port,
                               secondary_minion_config_overrides,
                               secondary_minion_id,
                               running_username,
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               secondary_minion_log_prefix,
                               secondary_minion_tcp_pub_port,
                               secondary_minion_tcp_pull_port)


@pytest.fixture(scope='session')
def session_secondary_minion_default_options():
    return {}


@pytest.fixture(scope='session')
def session_secondary_minion_config(session_secondary_root_dir,
                                    session_secondary_minion_config_file,
                                    session_master_return_port,
                                    session_secondary_minion_engine_port,
                                    session_secondary_minion_default_options,
                                    session_secondary_minion_config_overrides,
                                    session_secondary_minion_id,
                                    running_username,
                                    log_server_port,
                                    log_server_level,
                                    engines_dir,
                                    log_handlers_dir,
                                    session_secondary_minion_log_prefix,
                                    session_secondary_minion_tcp_pub_port,
                                    session_secondary_minion_tcp_pull_port):
    '''
    This fixture will return the session salt minion configuration options after being
    overrided with any options passed from ``session_secondary_minion_config_overrides``
    '''
    return apply_minion_config(session_secondary_minion_default_options,
                               session_secondary_root_dir,
                               session_secondary_minion_config_file,
                               session_master_return_port,
                               session_secondary_minion_engine_port,
                               session_secondary_minion_config_overrides,
                               session_secondary_minion_id,
                               running_username,
                               log_server_port,
                               log_server_level,
                               engines_dir,
                               log_handlers_dir,
                               session_secondary_minion_log_prefix,
                               session_secondary_minion_tcp_pub_port,
                               session_secondary_minion_tcp_pull_port)


def apply_syndic_config(syndic_default_options,
                        master_config_file,
                        syndic_conf_dir,
                        syndic_engine_port,
                        syndic_config_overrides,
                        running_username,
                        log_server_port,
                        log_server_level,
                        syndic_log_prefix,
                        syndic_id,
                        engines_dir,
                        log_handlers_dir,
                        root_dir):
    '''
    This fixture will return the salt syndic configuration options after being
    overridden with any options passed from ``config_overrides``
    '''
    import pytestsalt.utils.compat as compat
    import salt.config
    import salt.utils
    import salt.utils.dictupdate as dictupdate
    import salt.utils.verify as salt_verify
    import salt.utils.yaml as yamlserialize

    with compat.fopen(master_config_file) as rfh:
        master_config = yamlserialize.safe_load(rfh.read())

    master_overrides = {
        'syndic_master': 'localhost',
        'syndic_master_port': master_config['ret_port'],
        'syndic_pidfile': 'run/salt-syndic.pid',
        'syndic_user': running_username,
        'syndic_log_file': 'logs/syndic.log',
    }
    if syndic_default_options:
        # Override pytest salt overrides with any value comming in from syndic_default_options
        master_overrides.update(syndic_default_options)

    dictupdate.update(master_config, master_overrides, merge_lists=True)

    syndic_master_config_file = syndic_conf_dir.join('master').realpath().strpath

    # Write down the master computed configuration into the config file
    log.info('Writing to configuration file %s. Configuration:\n%s',
              syndic_master_config_file,
              pprint.pformat(master_config))
    with compat.fopen(syndic_master_config_file, 'w') as wfh:
        yamlserialize.safe_dump(master_config, wfh, default_flow_style=False)

    syndic_config_file = syndic_conf_dir.join('minion').realpath().strpath
    direct_overrides = copy.deepcopy(master_overrides)
    direct_overrides.update({
        'id': syndic_id,
    })

    apply_minion_config(syndic_default_options,
                        root_dir,
                        syndic_config_file,
                        master_config['ret_port'],  # master_return_port
                        syndic_engine_port,
                        syndic_config_overrides,
                        syndic_id,
                        running_username,
                        log_server_port,
                        log_server_level,
                        engines_dir,
                        log_handlers_dir,
                        syndic_log_prefix,
                        None,  # minion_tcp_pub_port,
                        None,  # minion_tcp_pull_port,
                        direct_overrides=direct_overrides)

    return salt.config.syndic_config(syndic_master_config_file, syndic_config_file)


@pytest.fixture
def syndic_default_options():
    return {}


@pytest.fixture
def syndic_config(master_config,
                  master_config_file,
                  syndic_conf_dir,
                  syndic_engine_port,
                  syndic_default_options,
                  syndic_config_overrides,
                  running_username,
                  log_server_port,
                  log_server_level,
                  syndic_log_prefix,
                  syndic_id,
                  engines_dir,
                  log_handlers_dir,
                  root_dir):
    '''
    This fixture will return the salt syndic configuration options after being
    overridden with any options passed from ``syndic_config_overrides``
    '''
    return apply_syndic_config(syndic_default_options,
                               master_config_file,
                               syndic_conf_dir,
                               syndic_engine_port,
                               syndic_config_overrides,
                               running_username,
                               log_server_port,
                               log_server_level,
                               syndic_log_prefix,
                               syndic_id,
                               engines_dir,
                               log_handlers_dir,
                               root_dir)


@pytest.fixture(scope='session')
def session_syndic_default_options():
    return {}


@pytest.fixture(scope='session')
def session_syndic_config(session_master_config_file,
                          session_syndic_conf_dir,
                          session_syndic_engine_port,
                          session_syndic_default_options,
                          session_syndic_config_overrides,
                          running_username,
                          log_server_port,
                          log_server_level,
                          session_syndic_log_prefix,
                          session_syndic_id,
                          engines_dir,
                          log_handlers_dir,
                          session_root_dir):
    '''
    This fixture will return the salt syndic configuration options after being
    overridden with any options passed from ``syndic_config_overrides``
    '''
    return apply_syndic_config(session_syndic_default_options,
                               session_master_config_file,
                               session_syndic_conf_dir,
                               session_syndic_engine_port,
                               session_syndic_config_overrides,
                               running_username,
                               log_server_port,
                               log_server_level,
                               session_syndic_log_prefix,
                               session_syndic_id,
                               engines_dir,
                               log_handlers_dir,
                               session_root_dir)


@pytest.fixture
def salt_ssh_log_prefix(sshd_port):
    return 'salt-ssh/{}'.format(sshd_port)


@pytest.fixture(scope='session')
def session_salt_ssh_log_prefix(session_sshd_port):
    return 'salt-ssh/{}'.format(session_sshd_port)


@pytest.fixture
def ssh_client_key(ssh_config_dir):
    '''
    The ssh client key
    '''
    return _generate_ssh_key(ssh_config_dir.join('test_key').realpath().strpath)


@pytest.fixture(scope='session')
def session_ssh_client_key(session_ssh_config_dir):
    '''
    The ssh client key
    '''
    return _generate_ssh_key(session_ssh_config_dir.join('test_key').realpath().strpath)


def _sshd_config_lines(sshd_port):
    '''
    Return a list of lines which will make the sshd_config file
    '''
    return [
        'Port {}'.format(sshd_port),
        'ListenAddress 127.0.0.1',
        'Protocol 2',
        'UsePrivilegeSeparation yes',
        '# Turn strict modes off so that we can operate in /tmp',
        'StrictModes no',
        '# Lifetime and size of ephemeral version 1 server key',
        'KeyRegenerationInterval 3600',
        'ServerKeyBits 1024',
        '# Logging',
        'SyslogFacility AUTH',
        'LogLevel INFO',
        '# Authentication:',
        'LoginGraceTime 120',
        'PermitRootLogin without-password',
        'StrictModes yes',
        'RSAAuthentication yes',
        'PubkeyAuthentication yes',
        '#AuthorizedKeysFile	%h/.ssh/authorized_keys',
        '#AuthorizedKeysFile	key_test.pub',
        '# Don\'t read the user\'s ~/.rhosts and ~/.shosts files',
        'IgnoreRhosts yes',
        '# For this to work you will also need host keys in /etc/ssh_known_hosts',
        'RhostsRSAAuthentication no',
        '# similar for protocol version 2',
        'HostbasedAuthentication no',
        '#IgnoreUserKnownHosts yes',
        '# To enable empty passwords, change to yes (NOT RECOMMENDED)',
        'PermitEmptyPasswords no',
        '# Change to yes to enable challenge-response passwords (beware issues with',
        '# some PAM modules and threads)',
        'ChallengeResponseAuthentication no',
        '# Change to no to disable tunnelled clear text passwords',
        'PasswordAuthentication no',
        'X11Forwarding no',
        'X11DisplayOffset 10',
        'PrintMotd no',
        'PrintLastLog yes',
        'TCPKeepAlive yes',
        '#UseLogin no',
        'AcceptEnv LANG LC_*',
        'Subsystem sftp /usr/lib/openssh/sftp-server',
        '#UsePAM yes',
    ]


@pytest.fixture
def sshd_config_lines(sshd_port):
    '''
    Return a list of lines which will make the sshd_config file
    '''
    return _sshd_config_lines(sshd_port)


@pytest.fixture(scope='session')
def session_sshd_config_lines(session_sshd_port):
    '''
    Return a list of lines which will make the sshd_config file
    '''
    return _sshd_config_lines(session_sshd_port)


@pytest.fixture
def write_sshd_config(sshd_config_dir, sshd_config_lines, ssh_client_key):
    '''
    This fixture will write the necessary configuration to run an SSHD server to be used in tests
    '''
    return _write_sshd_config(sshd_config_dir, sshd_config_lines, ssh_client_key)


@pytest.fixture(scope='session')
def session_write_sshd_config(session_sshd_config_dir, session_sshd_config_lines, session_ssh_client_key):
    '''
    This fixture will write the necessary configuration to run an SSHD server to be used in tests
    '''
    return _write_sshd_config(session_sshd_config_dir, session_sshd_config_lines, session_ssh_client_key)


@pytest.fixture
def _write_sshd_config(sshd_config_dir, sshd_config_lines, ssh_client_key):
    '''
    This fixture will write the necessary configuration to run an SSHD server to be used in tests
    '''
    import salt.utils
    import pytestsalt.utils.compat as compat
    sshd = salt.utils.which('sshd')

    if not sshd:
        pytest.skip('"sshd" not found.')

    # Generate server key
    server_key_dir = sshd_config_dir.realpath().strpath
    server_dsa_key_file = os.path.join(server_key_dir, 'ssh_host_dsa_key')
    server_ecdsa_key_file = os.path.join(server_key_dir, 'ssh_host_ecdsa_key')
    server_ed25519_key_file = os.path.join(server_key_dir, 'ssh_host_ed25519_key')

    _generate_ssh_key(server_dsa_key_file, 'dsa', 1024)
    _generate_ssh_key(server_ecdsa_key_file, 'ecdsa', 521)
    _generate_ssh_key(server_ed25519_key_file, 'ed25519', 521)

    sshd_config = sshd_config_lines[:]
    sshd_config.append('AuthorizedKeysFile {}.pub'.format(ssh_client_key))
    sshd_config.append('HostKey {}'.format(server_dsa_key_file))
    sshd_config.append('HostKey {}'.format(server_ecdsa_key_file))
    sshd_config.append('HostKey {}'.format(server_ed25519_key_file))

    with compat.fopen(sshd_config_dir.join('sshd_config').realpath().strpath, 'w') as wfh:
        wfh.write('\n'.join(sshd_config))


@pytest.fixture
def sshd_server_log_prefix(sshd_port):
    '''
    The log prefix to use for the sshd server fixture
    '''
    return 'sshd-server/{}'.format(sshd_port)


@pytest.fixture(scope='session')
def session_sshd_server_log_prefix(session_sshd_port):
    '''
    The log prefix to use for the sshd server fixture
    '''
    return 'session-sshd-server/{}'.format(session_sshd_port)


def _generate_ssh_key(key_path, key_type='ecdsa', key_size=521):
    '''
    Generate an SSH key
    '''
    import salt.utils
    log.debug('Generating ssh key(type: %s; size: %d; path: %s;)', key_type, key_size, key_path)
    keygen = salt.utils.which('ssh-keygen')
    if not keygen:
        pytest.skip('"ssh-keygen" not found')

    keygen_process = subprocess.Popen(
        [
            keygen,
            '-t', key_type,
            '-b', str(key_size),
            '-C', '"$(whoami)@$(hostname)-$(date -I)"',
            '-f', os.path.basename(key_path),
            '-P', ''
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        cwd=os.path.dirname(key_path)
    )
    _, keygen_err = keygen_process.communicate()
    if keygen_err:
        pytest.skip(
            'ssh-keygen had errors generating {}({}:{}): {}'.format(
                os.path.basename(key_path),
                key_type,
                key_size,
                keygen_err
            )
        )
    return key_path


@pytest.fixture
def roster_config_file(conf_dir):
    '''
    Returns the path to the salt-ssh roster configuration file
    '''
    return conf_dir.join('roster').realpath().strpath


@pytest.fixture(scope='session')
def session_roster_config_file(session_conf_dir):
    '''
    Returns the path to the salt-ssh roster configuration file
    '''
    return session_conf_dir.join('roster').realpath().strpath


@pytest.fixture
def roster_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt-ssh roster
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def session_roster_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt-ssh roster
    configuration options.

    It will be applied over the loaded default options
    '''


def _roster_config(config_file, config, config_overrides):
    import pytestsalt.utils.compat as compat
    import salt.utils.yaml as yamlserialize
    if config_overrides:
        config.update(config_overrides)

    with compat.fopen(config_file, 'w') as wfh:
        yamlserialize.safe_dump(config, wfh, default_flow_style=False)
    return config


@pytest.fixture
def roster_config(roster_config_file,
                  roster_config_overrides,
                  running_username,
                  ssh_client_key,
                  master_config,
                  sshd_port):
    config = {
        'localhost': {
            'host': '127.0.0.1',
            'port': sshd_port,
            'user': running_username,
            'priv': ssh_client_key
        }
    }
    return _roster_config(roster_config_file, config, roster_config_overrides)


@pytest.fixture(scope='session')
def session_roster_config(session_roster_config_file,
                          session_roster_config_overrides,
                          running_username,
                          session_ssh_client_key,
                          session_sshd_port,
                          session_master_config):
    config = {
        'localhost': {
            'host': '127.0.0.1',
            'port': session_sshd_port,
            'user': running_username,
            'priv': session_ssh_client_key
        }
    }
    return _roster_config(session_roster_config_file, config, session_roster_config_overrides)


@pytest.mark.trylast
def pytest_configure(config):
    pytest.helpers.utils.register(apply_master_config)
    pytest.helpers.utils.register(apply_minion_config)
    pytest.helpers.utils.register(apply_syndic_config)
