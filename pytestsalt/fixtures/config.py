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

# Import 3rd-party libs
import pytest

# Import salt libs
import salt.config
import salt.utils
import salt.utils.dictupdate as dictupdate
import salt.utils.verify as salt_verify
import salt.serializers.yaml as yamlserialize

# Import pytestsalt libs
from pytestsalt.fixtures.dirs import SYS_TMP_DIR


@pytest.fixture(scope='session')
def running_username():
    return pwd.getpwuid(os.getuid()).pw_name


@pytest.fixture(scope='session')
def master_config_file(conf_dir):
    '''
    Returns the path to the salt master configuration file
    '''
    return os.path.join(conf_dir, 'master')


@pytest.fixture(scope='session')
def minion_config_file(conf_dir):
    '''
    Returns the path to the salt minion configuration file
    '''
    return os.path.join(conf_dir, 'minion')


@pytest.fixture(scope='session')
def cloud_config_file(conf_dir):
    '''
    Returns the path to the salt cloud configuration file
    '''
    return os.path.join(conf_dir, 'cloud')


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
def master_config(tests_tempdir,
                  master_config_file,
                  master_publish_port,
                  master_return_port,
                  master_config_overrides,
                  running_username):
    '''
    This fixture will return the salt master configuration options after being
    overrided with any options passed from ``master_config_overrides``
    '''
    default_options = {
        'root_dir': tests_tempdir,
        'publish_port': master_publish_port,
        'ret_port': master_return_port,
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
        'token_file': os.path.join(SYS_TMP_DIR, 'ksfjhdgiuebfgnkefvsikhfjdgvkjahcsidk'),
        'file_buffer_size': 8192,
        'user': running_username
    }
    if master_config_overrides:
        # Merge in the default options with the master_config_overrides
        dictupdate.update(default_options, master_config_overrides, merge_lists=True)

    # Write down the computed configuration into the config file
    with salt.utils.fopen(master_config_file, 'w') as wfh:
        wfh.write(yamlserialize.serialize(default_options))

    # Make sure to load the config file as a salt-master starting from CLI
    options = salt.config.master_config(master_config_file)

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
def minion_config(tests_tempdir,
                  minion_config_file,
                  master_return_port,
                  minion_config_overrides,
                  running_username):
    '''
    This fixture will return the salt master configuration options after being
    overrided with any options passed from ``master_config_overrides``
    '''
    default_options = {
        'root_dir': tests_tempdir,
        'master': 'localhost',
        'master_port': master_return_port,
        'id': 'minion',
        'pidfile': 'run/minion.pid',
        'pki_dir': 'pki',
        'cachedir': 'cache',
        'sock_dir': '.salt-unix',
        'log_file': 'logs/minion',
        'loop_interval': 0.05,
        'open_mode': True,
        'user': running_username
    }
    if minion_config_overrides:
        # Merge in the default options with the minion_config_overrides
        dictupdate.update(default_options, minion_config_overrides, merge_lists=True)

    # Write down the computed configuration into the config file
    with salt.utils.fopen(minion_config_file, 'w') as wfh:
        wfh.write(yamlserialize.serialize(default_options))

    # Make sure to load the config file as a salt-master starting from CLI
    options = salt.config.minion_config(minion_config_file)

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
