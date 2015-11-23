# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures.dirs
    ~~~~~~~~~~~~~~~~~~~~~~~~

    pytest salt directories related fixtures
'''
# pylint: disable=redefined-outer-name

# Import Python libs
from __future__ import absolute_import
import random
import logging

# Import 3rd-party libs
import pytest

pytest_plugins = ('tempdir', 'catchlog')

log = logging.getLogger(__name__)

ROOT_DIR = 'root'
CLI_ROOT_DIR = 'cli-root'
SESSION_ROOT_DIR = 'session-root'
SESSION_CLI_ROOT_DIR = 'session-cli-root'


def pytest_tempdir_basename():
    '''
    An alternate way to define the predictable temporary directory.
    By default returns ``None`` and get's the basename either from the INI file or
    from the CLI passed option
    '''
    return 'pytest-salt-tmp'


def pytest_report_header(config):
    '''
    return a string to be displayed as header info for terminal reporting.
    '''
    tests_rootdir = config._tempdir.join(ROOT_DIR).strpath
    tests_session_rootdir = config._tempdir.join(SESSION_ROOT_DIR).strpath
    tests_cli_rootdir = config._tempdir.join(CLI_ROOT_DIR).strpath
    tests_session_cli_rootdir = config._tempdir.join(SESSION_CLI_ROOT_DIR).strpath
    return [
        'pytest salt root dirs:',
        '        function scope root dir: {0}'.format(tests_rootdir),
        '  function scope cli config dir: {0}'.format(tests_cli_rootdir),
        '       session scope config dir: {0}'.format(tests_session_rootdir),
        '   session scope cli config dir: {0}'.format(tests_session_cli_rootdir)
    ]


@pytest.fixture
def root_dir(tempdir):
    dirpath = tempdir.join('root-{0}'.format(random.randint(0, 50000)))
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_root_dir(tempdir):
    dirpath = tempdir.join('cli-root-{0}'.format(random.randint(0, 50000)))
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_root_dir(tempdir):
    dirpath = tempdir.join('session-root-{0}'.format(random.randint(0, 50000)))
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_root_dir(tempdir):
    dirpath = tempdir.join('session-cli-root-{0}'.format(random.randint(0, 50000)))
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def conf_dir(root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = root_dir.join('conf')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_conf_dir(cli_root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_root_dir.join('conf')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def master_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('master.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def minion_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('minion.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_master_config_includes_dir(cli_conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_conf_dir.join('master.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_minion_config_includes_dir(cli_conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_conf_dir.join('minion.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def integration_files_dir(root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = root_dir.join('integration-files')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_integration_files_dir(cli_root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_root_dir.join('integration-files')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def state_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = integration_files_dir.join('state-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def pillar_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = integration_files_dir.join('pillar-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def base_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = state_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def prod_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = state_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def base_env_pillar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = pillar_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def prod_env_pillar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = pillar_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_state_tree_root_dir(cli_integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_integration_files_dir.join('state-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_pillar_tree_root_dir(cli_integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_integration_files_dir.join('pillar-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_base_env_state_tree_root_dir(cli_state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_state_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_prod_env_state_tree_root_dir(cli_state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_state_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_base_env_pillar_tree_root_dir(cli_pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_pillar_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture
def cli_prod_env_pillar_tree_root_dir(cli_pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = cli_pillar_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_conf_dir(session_root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_root_dir.join('conf')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_conf_dir(session_cli_root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_root_dir.join('conf')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_master_config_includes_dir(session_conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_conf_dir.join('master.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_minion_config_includes_dir(session_conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_conf_dir.join('minion.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_master_config_includes_dir(session_cli_conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_conf_dir.join('master.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_minion_config_includes_dir(session_cli_conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_conf_dir.join('minion.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_integration_files_dir(session_root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_root_dir.join('integration-files')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_integration_files_dir(session_cli_root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_root_dir.join('integration-files')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_state_tree_root_dir(session_integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_integration_files_dir.join('state-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_pillar_tree_root_dir(session_integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_integration_files_dir.join('pillar-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_base_env_state_tree_root_dir(session_state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_state_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_prod_env_state_tree_root_dir(session_state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_state_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_base_env_pillar_tree_root_dir(session_pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_pillar_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_prod_env_pillar_tree_root_dir(session_pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_pillar_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_state_tree_root_dir(session_cli_integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_integration_files_dir.join('state-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_pillar_tree_root_dir(session_cli_integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_integration_files_dir.join('pillar-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_base_env_state_tree_root_dir(session_cli_state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_state_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_prod_env_state_tree_root_dir(session_cli_state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_state_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_base_env_pillar_tree_root_dir(session_cli_pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_pillar_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def session_cli_prod_env_pillar_tree_root_dir(session_cli_pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = session_cli_pillar_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()
