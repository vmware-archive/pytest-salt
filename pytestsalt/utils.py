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
import multiprocessing
import logging
try:
    import SocketServer as socketserver
except ImportError:
    import socketserver
import msgpack

log = logging.getLogger(__name__)


def get_unused_localhost_port():
    '''
    Return a random unused port on localhost
    '''
    usock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    usock.bind(('127.0.0.1', 0))
    port = usock.getsockname()[1]
    usock.close()
    return port



def get_pytest_log_server(port):
    return ThreadedSocketServer(('localhost', port), SocketServerRequestHandler)


class ThreadedSocketServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class SocketServerRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        unpacker = msgpack.Unpacker(encoding='utf-8')
        while True:
            try:
                wire_bytes = self.request.recv(1024)
                if not wire_bytes:
                    break
                unpacker.feed(wire_bytes)
                for record_dict in unpacker:
                    record = logging.makeLogRecord(record_dict)
                    logger = logging.getLogger(record.name)
                    logger.handle(record)
            except Exception as exc:
                log.exception(exc)
