# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    test_salt_minion.py
    ~~~~~~~~~~~~~~~~~~~

    Test the pytest salt plugin salt minion
'''

# Import python libs
from __future__ import absolute_import


def test_ping(cli_salt_call):
    assert cli_salt_call.run('test.ping', timeout=10) is True


def test_sync(cli_salt_call):
    assert cli_salt_call.run('saltutil.sync_all', timeout=10) is True
