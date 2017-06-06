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


def test_salt_minion_running(salt_minion):
    assert salt_minion.is_alive()
