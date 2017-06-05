# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    test_salt_minion.py
    ~~~~~~~~~~~~~~~~~~~

    Test the pytest salt plugin salt minion
'''

# Import python libs
from __future__ import absolute_import


# Import pytest libs
import pytest


def test_ping(salt_call):
    assert salt_call.run_sync('test.ping', timeout=10).exitcode == 0


@pytest.mark.gen_test
def test_ping_async(salt_call):
    result = yield salt_call.run('test.ping', timeout=10)
    assert result.exitcode == 0


def test_sync(salt_call):
    assert salt_call.run_sync('saltutil.sync_all', timeout=10).exitcode == 0


@pytest.mark.gen_test
def test_sync_async(salt_call):
    result = yield salt_call.run('saltutil.sync_all', timeout=10)
    assert result.exitcode == 0
