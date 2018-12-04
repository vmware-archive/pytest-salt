# -*- coding: utf-8 -*-
'''
pytestsalt.salt.log_handlers.pytest_log_handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Salt External Logging Handler
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import os
import socket
import threading
import logging
from multiprocessing import Queue

# Import 3rd-party libs
import msgpack

# Import Salt libs
import salt.log.setup
try:
    import salt.utils.stringutils
    to_unicode = salt.utils.stringutils.to_unicode
except ImportError:
    import salt.utils
    to_unicode = salt.utils.to_unicode

__virtualname__ = 'pytest_log_handler'

log = logging.getLogger(__name__)


def __virtual__():
    if 'pytest_log_port' not in __opts__:
        return False, "'pytest_log_port' not in options"
    return True


def setup_handlers():
    host_addr = __opts__.get('pytest_log_host')
    if not host_addr:
        import subprocess
        if __opts__['pytest_windows_guest'] is True:
            proc = subprocess.Popen('ipconfig', stdout=subprocess.PIPE)
            for line in proc.stdout.read().strip().encode(__salt_system_encoding__).splitlines():
                if 'Default Gateway' in line:
                    parts = line.split()
                    host_addr = parts[-1]
                    break
        else:
            proc = subprocess.Popen(
                "netstat -rn | grep -E '^0.0.0.0|default' | awk '{ print $2 }'",
                shell=True, stdout=subprocess.PIPE
            )
            host_addr = proc.stdout.read().strip().encode(__salt_system_encoding__)
    host_port = __opts__['pytest_log_port']
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host_addr, host_port))
    except socket.error as exc:
        # Don't even bother if we can't connect
        log.warning('Cannot connect back to log server: %s', exc)
        return
    finally:
        sock.close()

    # One million log messages is more than enough to queue.
    # Above that value, if `process_queue` can't process fast enough,
    # start dropping. This will contain a memory leak in case `process_queue`
    # can't process fast enough of in case it can't deliver the log records at all.
    queue_size = 10000000
    queue = Queue(queue_size)
    handler = salt.log.setup.QueueHandler(queue)
    level = salt.log.setup.LOG_LEVELS[(__opts__.get('pytest_log_level') or 'error').lower()]
    handler.setLevel(level)
    pytest_log_prefix = os.environ.get('PYTEST_LOG_PREFIX') or __opts__['pytest_log_prefix']
    process_queue_thread = threading.Thread(target=process_queue,
                                            args=(host_addr,
                                                  host_port,
                                                  pytest_log_prefix,
                                                  queue))
    process_queue_thread.daemon = True
    process_queue_thread.start()
    return handler


def process_queue(host, port, prefix, queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except socket.error:
        sock.close()
        return

    log.warning('Sending log records to Remote log server')
    while True:
        try:
            record = queue.get()
            if record is None:
                # A sentinel to stop processing the queue
                break
            # Just send every log. Filtering will happen on the main process
            # logging handlers
            record_dict = record.__dict__
            record_dict['msg'] = '[{}] {}'.format(to_unicode(prefix), to_unicode(record_dict['msg']))
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
