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
import logging

# Import 3rd-party libs
import pytest

pytest_plugins = ('tempdir', 'logging')

log = logging.getLogger(__name__)


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
    tests_confdir = config._tempdir.join('conf').strpath
    tests_cli_confdir = config._tempdir.join('conf-cli').strpath
    return [
        'pytest salt dirs:',
        '      salt config dir: {0}'.format(tests_confdir),
        '  salt cli config dir: {0}'.format(tests_cli_confdir)
    ]


@pytest.fixture(scope='session')
def conf_dir(tempdir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = tempdir.join('conf')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def cli_conf_dir(tempdir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = tempdir.join('conf-cli')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def master_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('master.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def minion_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('minion.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def cloud_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt-cloud configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('cloud.conf.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def cloud_profiles_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt-cloud profiles configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('cloud.profiles.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def cloud_providers_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt-cloud providers configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = conf_dir.join('cloud.providers.d')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def integration_files_dir(tempdir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = tempdir.join('integration-files')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def state_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = integration_files_dir.join('state-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def pillar_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = integration_files_dir.join('pillar-tree')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def base_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = state_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def prod_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = state_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def base_env_pillar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = pillar_tree_root_dir.join('base')
    dirpath.ensure(dir=True)
    return dirpath.realpath()


@pytest.fixture(scope='session')
def prod_env_pilar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = pillar_tree_root_dir.join('prod')
    dirpath.ensure(dir=True)
    return dirpath.realpath()
