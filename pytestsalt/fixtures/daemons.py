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
import logging

# Import salt libs
import salt.master
import salt.minion
import salt.log.setup
import salt.utils.process as process

# Import 3rd-party libs
import pytest

log = logging.getLogger(__name__)


@pytest.yield_fixture(scope='session')
def _process_manager():
    '''
    Yields a salt process manager
    '''
    # Initialize Salt's multiprocessing logging queue
    salt.log.setup.setup_multiprocessing_logging_listener()

    # Initialize the process manager
    manager = process.ProcessManager(name='Pytest-Salt-ProcessManager')

    # Yield the manager instance
    yield manager

    # Start the manager
    manager.run()


@pytest.yield_fixture(scope='session')
def process_manager(_process_manager):
    '''
    Returns the salt process manager from _process_manager.

    We need these two functions to properly shutdown the process manager
    '''
    yield _process_manager

    log.warning('stop process manager')
    salt.log.setup.shutdown_multiprocessing_logging_listener()
    _process_manager.kill_children()


@pytest.fixture(scope='session')
def salt_master(process_manager, master_config, minion_config):
    '''
    Returns a running salt-master
    '''
    master_process = process_manager.add_process(
        SaltMaster,
        args=(master_config, minion_config)
    )
    try:
        master_process.wait_until_running(timeout=5)
    except salt.minion.SaltDaemonNotRunning as exc:
        pytest.skip(str(exc))
    log.info('The pytest salt-master is running and accepting connections')
    return master_process


@pytest.fixture(scope='session')
@pytest.mark.usefixtures('salt-master')
def salt_minion(process_manager, minion_config):
    '''
    Returns a running salt-minion
    '''
    minion_process = process_manager.add_process(
        SaltMaster,
        args=(minion_config,)
    )
    try:
        minion_process.wait_until_running(timeout=5)
    except salt.minion.SaltDaemonNotRunning as exc:
        pytest.skip(str(exc))
    log.info('The pytest salt-minion is running and accepting commands')
    return minion_process


class SaltMinion(process.MultiprocessingProcess):
    '''
    Multiprocessing process for running a salt-minion
    '''
    def __init__(self, minion_opts):
        super(SaltMinion, self).__init__()
        self.minion = salt.minion.Minion(minion_opts)

    def wait_until_running(self, timeout=None):
        '''
        Block waiting until we can confirm that the minion is up and running
        and connected to a master
        '''
        self.minion.sync_connect_master(timeout=timeout)
        # Let's issue a test.ping to make sure the minion's transport stream
        # attribute is set, which will avoid a hanging test session termination
        # because of the following exception:
        #   Exception AttributeError: "'NoneType' object has no attribute 'zmqstream'" in
        #       <bound method Minion.__del__ of <salt.minion.Minion object at 0x7f2c41bf6390>> ignored
        self.minion.functions.test.ping()

    def run(self):
        self.minion.tune_in()


class SaltMaster(SaltMinion):
    '''
    Multiprocessing process for running a salt-master
    '''
    def __init__(self, master_opts, minion_opts):
        super(SaltMaster, self).__init__(minion_opts)
        self.master = salt.master.Master(master_opts)

    def run(self):
        self.master.start()
