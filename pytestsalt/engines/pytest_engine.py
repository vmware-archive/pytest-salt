# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2015 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.engines.pytest_engine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple salt engine which will setup a socket to accept connections allowing us to know
    when a daemon is up and running
'''

# Import python libs
from __future__ import absolute_import
import socket
import logging

# Import 3rd-party libs
from tornado import ioloop
from tornado import netutil

log = logging.getLogger(__name__)

__virtualname__ = 'pytest'


def __virtual__():
    return 'pytest_port' in __opts__  # pylint: disable=undefined-variable


def start():
    io_loop = ioloop.IOLoop.instance()
    pytest_engine = PyTestEngine(__opts__, io_loop)  # pylint: disable=undefined-variable
    io_loop.add_callback(pytest_engine.start)
    io_loop.start()


class PyTestEngine(object):
    def __init__(self, opts, io_loop):
        self.opts = opts
        self.io_loop = io_loop
        self.sock = None

    def start(self):
        port = int(self.opts['pytest_port'])
        log.warning('Starting Pytest Engine(role=%s) on port %s', self.opts['__role'], port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        # bind the socket to localhost on the config provided port
        self.sock.bind(('localhost', port))
        # become a server socket
        self.sock.listen(5)
        netutil.add_accept_handler(
            self.sock,
            self.handle_connection,
            io_loop=self.io_loop,
        )

    def handle_connection(self, connection, address):
        log.warning('Accepted connection from %s. Role: %s', address, self.opts['__role'])
        # We just need to know that the daemon running the engine is alive...
        connection.shutdown(socket.SHUT_RDWR)  # pylint: disable=no-member
        connection.close()
