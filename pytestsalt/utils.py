# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.utils
    ~~~~~~~~~~~~~~~~

    Some pytest fixtures used in pytest-salt
'''

# Import Python libs
from __future__ import absolute_import
import socket


def get_unused_localhost_port():
    '''
    Return a random unused port on localhost
    '''
    usock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    usock.bind(('127.0.0.1', 0))
    port = usock.getsockname()[1]
    usock.close()
    return port


#class
