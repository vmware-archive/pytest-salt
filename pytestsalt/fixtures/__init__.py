# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures
    ~~~~~~~~~~~~~~~~~~~

    pytest salt fixtures
'''

# Import python libs
from __future__ import absolute_import

# Import 3rd-party libs
import pytest
import tornado.ioloop


@pytest.yield_fixture
def salt_io_loop():
    '''
    Create an instance of the `tornado.ioloop.IOLoop` for each test case.
    '''
    io_loop = tornado.ioloop.IOLoop()
    io_loop.make_current()
    yield io_loop
    io_loop.clear_current()
    if not tornado.ioloop.IOLoop.initialized() or io_loop is not tornado.ioloop.IOLoop.instance():
        io_loop.close(all_fds=True)


@pytest.yield_fixture(scope='session')
def session_salt_io_loop():
    '''
    Create an instance of the `tornado.ioloop.IOLoop` for each test case.
    '''
    io_loop = tornado.ioloop.IOLoop()
    io_loop.make_current()
    yield io_loop
    io_loop.clear_current()
    if not tornado.ioloop.IOLoop.initialized() or io_loop is not tornado.ioloop.IOLoop.instance():
        io_loop.close(all_fds=True)
