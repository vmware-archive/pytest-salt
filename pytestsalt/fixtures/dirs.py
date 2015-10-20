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
import os
import shutil
import logging
import tempfile

# Import 3rd-party libs
import pytest


log = logging.getLogger(__name__)

if os.uname()[0] == 'Darwin':
    SYS_TMP_DIR = '/tmp'
else:
    SYS_TMP_DIR = os.environ.get('TMPDIR', tempfile.gettempdir())

PYTESTSALT_TESTS_TEMPDIR = os.path.join(SYS_TMP_DIR, 'pytest-salt-tmp')


@pytest.yield_fixture(scope='session')
def tests_tempdir(request):
    '''
    Yield a known temporary directory which can be left untouched at the
    end of the test suite execution for debugging puroses
    '''
    tests_tempdir_path = request.config.getoption('--tests-temp-dir')

    # The tests tempdir is always wiped on start if it exists
    if os.path.exists(tests_tempdir_path):
        log.debug('Removing stale salt tests temporary directory: %s', tests_tempdir_path)
        shutil.rmtree(tests_tempdir_path)

    # Recreate the directory
    os.makedirs(tests_tempdir_path)
    yield tests_tempdir_path

    # Teardown code
    if request.config.getoption('--no-clean') is True:
        log.debug('The salt tests temporary directory is left untouched')
    else:
        log.debug('Removing the salt tests temporary directory')
        shutil.rmtree(tests_tempdir_path)


@pytest.fixture(scope='session')
def conf_dir(tests_tempdir):
    '''
    Fixture which returns the salt configuration directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(tests_tempdir, 'conf')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def master_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt master configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(conf_dir, 'master.d')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def minion_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt minion configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(conf_dir, 'minion.d')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def cloud_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt-cloud configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(conf_dir, 'cloud.conf.d')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def cloud_profiles_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt-cloud profiles configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(conf_dir, 'cloud.profiles.d')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def cloud_providers_config_includes_dir(conf_dir):
    '''
    Fixture which returns the salt-cloud providers configuration includes directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(conf_dir, 'cloud.providers.d')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def integration_files_dir(tests_tempdir):
    '''
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(tests_tempdir, 'integration-files')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def state_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(integration_files_dir, 'state-tree')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def pillar_tree_root_dir(integration_files_dir):
    '''
    Fixture which returns the salt pillar tree root directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(integration_files_dir, 'pillar-tree')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def base_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(state_tree_root_dir, 'base')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def prod_env_state_tree_root_dir(state_tree_root_dir):
    '''
    Fixture which returns the salt prod environment state tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(state_tree_root_dir, 'prod')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def base_env_pillar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt base environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(pillar_tree_root_dir, 'base')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


@pytest.fixture(scope='session')
def prod_env_pilar_tree_root_dir(pillar_tree_root_dir):
    '''
    Fixture which returns the salt prod environment pillar tree directory path.
    Creates the directory if it does not yet exist.
    '''
    dirpath = os.path.join(pillar_tree_root_dir, 'prod')
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


def pytest_addoption(parser):
    '''
    Add pytest salt plugin dirs related options
    '''
    saltparser = parser.getgroup('Salt Plugin Options')
    saltparser.addoption(
        '--tests-temp-dir',
        default=PYTESTSALT_TESTS_TEMPDIR,
        help=('Temporary directory which will be used as a root for all '
              'of salt required directories, runtime generated configuration, '
              'state tree, etc... Default: \'{0}\' ATTENTION: If the provided '
              'path exists when starting the tests suite, THE PATH WILL BE '
              'WIPED!!! '.format(PYTESTSALT_TESTS_TEMPDIR))
    )
    saltparser.addoption(
        '--no-clean',
        default=False,
        action='store_true',
        help='Don\'t remove the pytest salt temporary directory.'
    )
