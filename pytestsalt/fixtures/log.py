# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2016 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.fixtures.log
    ~~~~~~~~~~~~~~~~~~~~~~~

    Log server fixture which creates a server that receives log records
    from external process to log them in the current process
'''

# Import python libs
from __future__ import absolute_import
import threading
import logging
try:
    import SocketServer as socketserver
except ImportError:
    import socketserver

# Import pytest libs
import pytest

# Import 3rd-party libs
import msgpack

log = logging.getLogger(__name__)


@pytest.yield_fixture(scope='session')
def log_server(salt_log_port):
    '''
    Returns a log server fixture.

    This is an autouse fixture so no need to depend on it
    '''
    server = ThreadedSocketServer(('localhost', salt_log_port), SocketServerRequestHandler)
    server_process = threading.Thread(target=server.serve_forever)
    server_process.daemon = True
    server_process.start()
    yield server
    server.server_close()
    server.shutdown()


class ThreadingMixIn(socketserver.ThreadingMixIn):
    daemon_threads = True


class ThreadedSocketServer(ThreadingMixIn, socketserver.TCPServer):

    def server_activate(self):
        self.shutting_down = threading.Event()
        socketserver.TCPServer.server_activate(self)
        #super(ThreadedSocketServer, self).server_activate()

    def server_close(self):
        self.shutting_down.set()
        socketserver.TCPServer.server_close(self)
        #super(ThreadedSocketServer, self).server_close()


class SocketServerRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        unpacker = msgpack.Unpacker(encoding='utf-8')
        while not self.server.shutting_down.is_set():
            try:
                wire_bytes = self.request.recv(1024)
                if not wire_bytes:
                    break
                unpacker.feed(wire_bytes)
                for record_dict in unpacker:
                    record = logging.makeLogRecord(record_dict)
                    logger = logging.getLogger(record.name)
                    logger.handle(record)
            except (EOFError, KeyboardInterrupt, SystemExit):
                break
            except Exception as exc:  # pylint: disable=broad-except
                log.exception(exc)
