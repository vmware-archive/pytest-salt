# -*- coding: utf-8 -*-
'''
    pytestsalt.fixtures.log_server_asyncio
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    AsyncIO Log Server Fixture
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import errno
import asyncio
import logging
import threading

# Import 3rd-party libs
import msgpack

log = logging.getLogger(__name__)


def log_server_asyncio(log_server_port):
    '''
    Starts a log server.
    '''
    async def read_child_processes_log_records(reader, writer):
        unpacker = msgpack.Unpacker(raw=False)
        while True:
            try:
                wire_bytes = await reader.read(1024)
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
            except (EOFError, KeyboardInterrupt, SystemExit):
                break
            except Exception as exc:  # pylint: disable=broad-except
                log.exception(exc)

    def process_logs(port):
        loop = asyncio.new_event_loop()
        try:
            coro = asyncio.start_server(read_child_processes_log_records, host='localhost', port=port, loop=loop)
            server = loop.run_until_complete(coro)
        except OSError as err:
            if err.errno != errno.EADDRNOTAVAIL:
                # If not address not available, in case localhost cannot be resolved
                raise
            coro = asyncio.start_server(read_child_processes_log_records, host='127.0.0.1', port=port, loop=loop)
            server = loop.run_until_complete(coro)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

    process_queue_thread = threading.Thread(target=process_logs, args=(log_server_port,))
    process_queue_thread.daemon = True
    process_queue_thread.start()
