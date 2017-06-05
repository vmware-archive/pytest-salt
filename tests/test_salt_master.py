# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    test_salt_master.py
    ~~~~~~~~~~~~~~~~~~~

    Test the pytest salt plugin salt master
'''

# Import python libs
from __future__ import absolute_import


def test_salt_master_running(salt_master):
    assert salt_master.is_alive()
