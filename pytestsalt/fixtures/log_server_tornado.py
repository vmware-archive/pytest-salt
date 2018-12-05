# -*- coding: utf-8 -*-
'''
    pytestsalt.fixtures.log_server_tornado
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tornado Log Server Fixture
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging
import threading

# Import 3rd-party libs
import msgpack
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

log = logging.getLogger(__name__)


class LogServer(TCPServer):

    @gen.coroutine
    def handle_stream(self, stream, address):
        unpacker = msgpack.Unpacker(raw=False)
        while True:
            try:
                wire_bytes = yield stream.read_bytes(1024, partial=True)
                if not wire_bytes:
                    break
                try:
                    unpacker.feed(wire_bytes)
                except msgpack.exceptions.BufferFull:
                    # Start over loosing some data?!
                    unpacker = msgpack.Unpacker(raw=False)
                    unpacker.feed(wire_bytes)
                for record_dict in unpacker:
                    record = logging.makeLogRecord(record_dict)
                    logger = logging.getLogger(record.name)
                    logger.handle(record)
            except (EOFError, KeyboardInterrupt, SystemExit, StreamClosedError):
                break
            except Exception as exc:  # pylint: disable=broad-except
                log.exception(exc)


def log_server_tornado(log_server_port):
    '''
    Starts a log server.
    '''

    def process_logs(port):
        server = LogServer()
        server.listen(port, address='localhost')
        try:
            IOLoop.current().start()
        except KeyboardInterrupt:
            pass

        server.stop()

    process_queue_thread = threading.Thread(target=process_logs, args=(log_server_port,))
    process_queue_thread.daemon = True
    process_queue_thread.start()
