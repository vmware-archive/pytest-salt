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

# Import 3rd-party libs
import pytest


@pytest.mark.usefixtures('salt_master')
def test_salt_master_running(process_manager):
    assert process_manager
