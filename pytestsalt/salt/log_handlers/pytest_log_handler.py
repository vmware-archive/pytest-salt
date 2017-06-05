# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: Copyright 2016 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    pytestsalt.salt.log_handlers.pytest_log_handler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Salt External Logging Handler
'''

# Import python libs
from __future__ import absolute_import
import os
import socket
import threading
import logging
from multiprocessing import Queue

# Import 3rd-party libs
import msgpack

# Import Salt libs
import salt.log.setup

__virtualname__ = 'pytest_log_handler'

log = logging.getLogger(__name__)


def __virtual__():
    if 'pytest_log_port' not in __opts__:
        return False, "'pytest_log_port' not in options"
    return True


def setup_handlers():
    # One million log messages is more than enough to queue.
    # Above that value, if `process_queue` can't process fast enough,
    # start dropping. This will contain a memory leak in case `process_queue`
    # can't process fast enough of in case it can't deliver the log records at all.
    queue_size = 10000000
    queue = Queue(queue_size)
    handler = salt.log.setup.QueueHandler(queue)
    handler.setLevel(1)
    pytest_log_prefix = os.environ.get('PYTEST_LOG_PREFIX') or __opts__['pytest_log_prefix']
    process_queue_thread = threading.Thread(target=process_queue,
                                            args=(__opts__['pytest_log_port'],
                                                  pytest_log_prefix,
                                                  queue))
    process_queue_thread.daemon = True
    process_queue_thread.start()
    return handler


def process_queue(port, prefix, queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', port))
    while True:
        try:
            record = queue.get()
            if record is None:
                # A sentinel to stop processing the queue
                break
            # Just send every log. Filtering will happen on the main process
            # logging handlers
            record_dict = record.__dict__
            record_dict['msg'] = prefix + record_dict['msg']
            sock.sendall(msgpack.dumps(record_dict, encoding='utf-8'))
        except (IOError, EOFError, KeyboardInterrupt, SystemExit):
            break
        except Exception as exc:  # pylint: disable=broad-except
            log.warning(
                'An exception occurred in the pytest salt logging '
                'queue thread: %s',
                exc,
                exc_info_on_loglevel=logging.DEBUG
            )
