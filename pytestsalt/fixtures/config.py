# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures.config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    pytest salt configuration related fixtures
'''
# pylint: disable=redefined-outer-name

# Import python libs
from __future__ import absolute_import, print_function
import os
import pwd
import logging

# Import 3rd-party libs
import pytest

# Import salt libs
import salt.config
import salt.utils
import salt.utils.dictupdate as dictupdate
import salt.utils.verify as salt_verify
import salt.serializers.yaml as yamlserialize

log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def running_username():
    return pwd.getpwuid(os.getuid()).pw_name


@pytest.fixture(scope='session')
def master_config_file(conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return conf_dir.join('master').realpath().strpath


@pytest.fixture(scope='session')
def minion_config_file(conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return conf_dir.join('minion').realpath().strpath


@pytest.fixture(scope='session')
def cloud_config_file(conf_dir):
    '''
    Returns the path to the salt cloud configuration file
    '''
    return conf_dir.join('cloud').realpath().strpath


@pytest.fixture(scope='session')
def master_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt master
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def minion_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt minion
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def cli_master_config_file(cli_conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    print(888, cli_conf_dir.join('master').realpath().strpath)
    return cli_conf_dir.join('master').realpath().strpath


@pytest.fixture(scope='session')
def cli_minion_config_file(cli_conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return cli_conf_dir.join('minion').realpath().strpath


@pytest.fixture(scope='session')
def cli_cloud_config_file(cli_conf_dir):
    '''
    Returns the path to the salt cloud configuration file
    '''
    return cli_conf_dir.join('cloud').realpath().strpath


@pytest.fixture(scope='session')
def cli_master_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt master
    configuration options.

    It will be applied over the loaded default options
    '''


@pytest.fixture(scope='session')
def cli_minion_config_overrides():
    '''
    This fixture should be implemented to overwrite default salt minion
    configuration options.

    It will be applied over the loaded default options
    '''


def _master_config(tempdir,
                   config_file,
                   publish_port,
                   return_port,
                   config_overrides,
                   running_username):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    default_options = {
        'root_dir': tempdir.strpath,
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
        'pillar_opts': True,
        'peer': {
            '.*': [
                'test.*'
            ]
        },
        'log_file': 'logs/master',
        'key_logfile': 'logs/key',
        'token_dir': 'tokens',
        'token_file': tempdir.join('ksfjhdgiuebfgnkefvsikhfjdgvkjahcsidk').strpath,
        'file_buffer_size': 8192,
        'user': running_username,
        'log_fmt_console': "[%(levelname)-8s][%(name)-5s:%(lineno)-4d] %(message)s"
        #'log_fmt_logfile': '%(asctime)s,%(msecs)03.0f [%(name)-5s:%(lineno)-4d][%(levelname)-8s] %(message)s'
    }
    if config_overrides:
        # Merge in the default options with the master_config_overrides
        dictupdate.update(default_options, config_overrides, merge_lists=True)

    log.warning('WRITING TO %s', config_file)

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


@pytest.fixture(scope='session')
def master_config(tempdir,
                  master_config_file,
                  master_publish_port,
                  master_return_port,
                  master_config_overrides,
                  running_username):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    return _master_config(tempdir,
                          master_config_file,
                          master_publish_port,
                          master_return_port,
                          master_config_overrides,
                          running_username)


@pytest.fixture(scope='session')
def cli_master_config(tempdir,
                      cli_master_config_file,
                      cli_master_publish_port,
                      cli_master_return_port,
                      cli_master_config_overrides,
                      running_username):
    '''
    This fixture will return the salt master configuration options after being
    overridden with any options passed from ``master_config_overrides``
    '''
    return _master_config(tempdir,
                          cli_master_config_file,
                          cli_master_publish_port,
                          cli_master_return_port,
                          cli_master_config_overrides,
                          running_username)


def _minion_config(tempdir,
                   config_file,
                   return_port,
                   config_overrides,
                   running_username):
    '''
    This fixture will return the salt master configuration options after being
    overrided with any options passed from ``master_config_overrides``
    '''
    default_options = {
        'root_dir': tempdir.strpath,
        'master': 'localhost',
        'master_port': return_port,
        'id': 'minion',
        'pidfile': 'run/minion.pid',
        'pki_dir': 'pki',
        'cachedir': 'cache',
        'sock_dir': '.salt-unix',
        'log_file': 'logs/minion',
        'loop_interval': 0.05,
        'open_mode': True,
        'user': running_username,
        #'multiprocessing': False,
        'log_fmt_console': "[%(levelname)-8s][%(name)-5s:%(lineno)-4d] %(message)s"
    }
    if config_overrides:
        # Merge in the default options with the minion_config_overrides
        dictupdate.update(default_options, config_overrides, merge_lists=True)

    log.warning('WRITING TO %s', config_file)
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


@pytest.fixture(scope='session')
def minion_config(tempdir,
                  minion_config_file,
                  master_return_port,
                  minion_config_overrides,
                  running_username):
    '''
    This fixture will return the salt master configuration options after being
    overrided with any options passed from ``master_config_overrides``
    '''
    return _minion_config(tempdir,
                          minion_config_file,
                          master_return_port,
                          minion_config_overrides,
                          running_username)


@pytest.fixture(scope='session')
def cli_minion_config(tempdir,
                      cli_minion_config_file,
                      cli_master_return_port,
                      cli_minion_config_overrides,
                      running_username):
    '''
    This fixture will return the salt master configuration options after being
    overrided with any options passed from ``master_config_overrides``
    '''
    return _minion_config(tempdir,
                          cli_minion_config_file,
                          cli_master_return_port,
                          cli_minion_config_overrides,
                          running_username)
