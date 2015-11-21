# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    test_salt_master.py
    ~~~~~~~~~~~~~~~~~~~

    Test the pytest salt plugin salt master
'''

# Import python libs
from __future__ import absolute_import

# Import pytest libs
import pytest


@pytest.mark.function
@pytest.mark.daemon
def test_salt_master_running(salt_master):
    assert salt_master.is_alive()


@pytest.mark.function
@pytest.mark.daemon
def test_salt_master_running_2(salt_master):
    '''
    Assert that the second function scoped master also runs ok
    '''
    assert salt_master.is_alive()


@pytest.mark.function
@pytest.mark.cli
def test_cli_salt_master_running(cli_salt_master):
    assert cli_salt_master.is_alive()


@pytest.mark.session
@pytest.mark.daemon
def test_session_salt_master_running(session_salt_master):
    assert session_salt_master.is_alive()


@pytest.mark.session
@pytest.mark.cli
def test_session_cli_salt_master_running(session_cli_salt_master):
    assert session_cli_salt_master.is_alive()
