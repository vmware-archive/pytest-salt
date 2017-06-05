# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures.dirs
    ~~~~~~~~~~~~~~~~~~~~~~~~

    pytest salt directories related fixtures
'''
# pylint: disable=redefined-outer-name

# Import Python libs
from __future__ import absolute_import
import logging

# Import 3rd-party libs
import pytest

pytest_plugins = ('tempdir', 'catchlog')  # pylint: disable=invalid-name

log = logging.getLogger(__name__)

ROOT_DIR = 'root'
MOM_ROOT_DIR = 'mom-root'
SECONDARY_ROOT_DIR = 'secondary-root'
SESSION_ROOT_DIR = 'session-root'
SESSION_MOM_ROOT_DIR = 'session-mom-root'
SESSION_SECONDARY_ROOT_DIR = 'session-secondary-root'


@pytest.fixture
def root_dir(tempdir):
    '''
    Return the function scoped salt root dir
    '''
    return tempdir.mkdir(ROOT_DIR)


@pytest.fixture(scope='session')
def session_root_dir(tempdir):
    '''
    Return the session scoped salt root dir
    '''
    return tempdir.mkdir(SESSION_ROOT_DIR)


@pytest.fixture
def master_of_masters_root_dir(tempdir):
    '''
    Return the function scoped salt master of masters root dir
    '''
    return tempdir.mkdir(MOM_ROOT_DIR)


@pytest.fixture(scope='session')
def session_master_of_masters_root_dir(tempdir):
    '''
    Return the session scoped salt master of masters root dir
    '''
    return tempdir.mkdir(SESSION_MOM_ROOT_DIR)


@pytest.fixture
def secondary_root_dir(tempdir):
    '''
    Return the function scoped salt secondary root dir
    '''
    return tempdir.mkdir(SECONDARY_ROOT_DIR)


@pytest.fixture(scope='session')
def session_secondary_root_dir(tempdir):
    '''
    Return the session scoped salt secondary root dir
    '''
    return tempdir.mkdir(SESSION_SECONDARY_ROOT_DIR)


@pytest.fixture
def conf_dir(root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = root_dir.join('conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_conf_dir(session_root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_root_dir.join('conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_conf_dir(master_of_masters_conf_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_root_dir.join('conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_conf_dir(session_master_of_masters_root_dir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_root_dir.join('conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def secondary_conf_dir(secondary_root_dir):
    '''
    Fixture which returns the salt secondary configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = secondary_root_dir.join('conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_secondary_conf_dir(session_secondary_root_dir):
    '''
    Fixture which returns the salt secondary configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_secondary_root_dir.join('conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def syndic_conf_dir(root_dir):
    '''
    Fixture which returns the salt syndic configuration directory path.
    Creates the directory if it does not yet exist.

    Even though the salt syndic will read from both the master and minion
    configuration files, we'll store copies on this directory for complete
    separation, ie, to don't include syndic config options in either of the
    master and minion configuration files.
    '''
    dirname = root_dir.join('syndic-conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_syndic_conf_dir(session_root_dir):
    '''
    Fixture which returns the salt syndic configuration directory path.
    Creates the directory if it does not yet exist.

    Even though the salt syndic will read from both the master and minion
    configuration files, we'll store copies on this directory for complete
    separation, ie, to don't include syndic config options in either of the
    master and minion configuration files.
    '''
    dirname = session_root_dir.join('syndic-conf')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = conf_dir.join('master.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_config_includes_dir(session_conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_conf_dir.join('master.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_config_includes_dir(master_of_masters_conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_conf_dir.join('master.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_config_includes_dir(session_master_of_masters_conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_conf_dir.join('master.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def minion_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = conf_dir.join('minion.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_minion_config_includes_dir(session_conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_conf_dir.join('minion.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def secondary_minion_config_includes_dir(secondary_conf_dir):
    '''
    Fixture which returns the salt secondary minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = secondary_conf_dir.join('minion.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_secondary_minion_config_includes_dir(session_secondary_conf_dir):
    '''
    Fixture which returns the salt secondary minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_secondary_conf_dir.join('minion.d')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def integration_files_dir(root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = root_dir.join('integration-files')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def state_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = integration_files_dir.join('state-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def pillar_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = integration_files_dir.join('pillar-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def base_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = state_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def prod_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = state_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def base_env_pillar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = pillar_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def prod_env_pillar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = pillar_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_integration_files_dir(master_of_masters_root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_root_dir.join('integration-files')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_state_tree_root_dir(master_of_masters_integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_integration_files_dir.join('state-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_pillar_tree_root_dir(master_of_masters_integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_integration_files_dir.join('pillar-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_base_env_state_tree_root_dir(master_of_masters_state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_state_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_prod_env_state_tree_root_dir(master_of_masters_state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_state_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_base_env_pillar_tree_root_dir(master_of_masters_pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_pillar_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def master_of_masters_prod_env_pillar_tree_root_dir(master_of_masters_pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = master_of_masters_pillar_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_integration_files_dir(session_root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_root_dir.join('integration-files')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_state_tree_root_dir(session_integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_integration_files_dir.join('state-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_pillar_tree_root_dir(session_integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_integration_files_dir.join('pillar-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_base_env_state_tree_root_dir(session_state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_state_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_prod_env_state_tree_root_dir(session_state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_state_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_base_env_pillar_tree_root_dir(session_pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_pillar_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_prod_env_pillar_tree_root_dir(session_pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_pillar_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_integration_files_dir(session_master_of_masters_root_dir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_root_dir.join('integration-files')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_state_tree_root_dir(session_master_of_masters_integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_integration_files_dir.join('state-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_pillar_tree_root_dir(session_master_of_masters_integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_integration_files_dir.join('pillar-tree')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_base_env_state_tree_root_dir(session_master_of_masters_state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_state_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_prod_env_state_tree_root_dir(session_master_of_masters_state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_state_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_base_env_pillar_tree_root_dir(session_master_of_masters_pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_master_of_masters_pillar_tree_root_dir.join('base')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture(scope='session')
def session_master_of_masters_prod_env_pillar_tree_root_dir(session_master_of_masters_pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirname = session_pillar_tree_root_dir.join('prod')
    dirname.ensure(dir=True)
    return dirname


@pytest.fixture
def sshd_config_dir(tempdir):
    '''
    Return the path to a configuration directory for the sshd server
    '''
    config_dir = tempdir.join('sshd')
    config_dir.ensure(dir=True)
    return config_dir


@pytest.fixture(scope='session')
def session_sshd_config_dir(tempdir):
    '''
    Return the path to a configuration directory for a session scoped sshd server
    '''
    config_dir = tempdir.join('session-sshd')
    config_dir.ensure(dir=True)
    return config_dir


@pytest.fixture
def ssh_config_dir(tempdir):
    '''
    Return the path to a configuration directory for the ssh client
    '''
    config_dir = tempdir.join('ssh-client')
    config_dir.ensure(dir=True)
    return config_dir


@pytest.fixture(scope='session')
def session_ssh_config_dir(tempdir):
    '''
    Return the path to a configuration directory for a session scoped ssh client
    '''
    config_dir = tempdir.join('session-ssh-client')
    config_dir.ensure(dir=True)
    return config_dir
