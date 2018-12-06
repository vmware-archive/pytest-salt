# -*- coding: utf-8 -*-
'''
pytestsalt.engines.pytest_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple salt engine which will setup a socket to accept connections allowing us to know
when a daemon is up and running
'''

# Import python libs
from __future__ import absolute_import, print_function
import sys
import errno
import socket
import logging

# Import salt libs
import salt.utils.event
try:
    import salt.utils.asynchronous
    HAS_SALT_ASYNC = True
except ImportError:
    HAS_SALT_ASYNC = False

# Import 3rd-party libs
from tornado import gen
from tornado import ioloop
from tornado import iostream
from tornado import netutil

log = logging.getLogger(__name__)

__virtualname__ = 'pytest'


def __virtual__():
    return 'pytest_engine_port' in __opts__  # pylint: disable=undefined-variable


def start():
    pytest_engine = PyTestEngine(__opts__)  # pylint: disable=undefined-variable
    pytest_engine.start()


class PyTestEngine(object):
    def __init__(self, opts):
        self.opts = opts
        self.id = opts['id']
        self.role = opts['__role']
        self.sock_dir = opts['sock_dir']
        self.port = int(opts['pytest_engine_port'])
        self.tcp_server_sock = None

    def start(self):
        self.io_loop = ioloop.IOLoop()
        self.io_loop.make_current()
        self.io_loop.add_callback(self._start)
        self.io_loop.start()

    @gen.coroutine
    def _start(self):
        log.info('Starting Pytest Engine(role=%s, id=%s) on port %s', self.role, self.id, self.port)

        self.tcp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server_sock.setblocking(0)
        # bind the socket to localhost on the config provided port
        self.tcp_server_sock.bind(('localhost', self.port))
        # become a server socket
        self.tcp_server_sock.listen(5)
        if HAS_SALT_ASYNC:
            with salt.utils.asynchronous.current_ioloop(self.io_loop):
                netutil.add_accept_handler(self.tcp_server_sock, self.handle_connection)
        else:
            netutil.add_accept_handler(self.tcp_server_sock, self.handle_connection)

        if self.role == 'master':
            yield self.fire_master_started_event()
        else:
            yield self.listen_to_minion_connected_event()

    def handle_connection(self, connection, address):
        log.warning('Accepted connection from %s. Role: %s  ID: %s', address, self.role, self.id)
        # We just need to know that the daemon running the engine is alive...
        try:
            connection.shutdown(socket.SHUT_RDWR)  # pylint: disable=no-member
            connection.close()
        except socket.error as exc:
            if not sys.platform.startswith('darwin'):
                raise
            try:
                if exc.errno != errno.ENOTCONN:
                    raise
            except AttributeError:
                # This is not macOS !?
                pass

    @gen.coroutine
    def listen_to_minion_connected_event(self):
        start_event_match = 'salt/{}/{}/start'.format(self.role, self.id)
        log.info('Listening for salt-%s connected event. Tag: %s', self.role, start_event_match)
        event_bus = salt.utils.event.get_master_event(self.opts, self.sock_dir, listen=True)
        event_bus.subscribe(start_event_match)
        while True:
            event = event_bus.get_event(full=True, no_block=True)
            if event is not None and event['tag'] == start_event_match:
                log.info('Got salt-%s connected event: %s', self.role, event)
                break
            yield gen.sleep(0.25)

    @gen.coroutine
    def fire_master_started_event(self):
        master_start_event_tag = 'salt/master/{}/start'.format(self.id)
        log.info('Firing salt-%s started event. Tag: %s', self.role, master_start_event_tag)
        event_bus = salt.utils.event.get_master_event(self.opts, self.sock_dir, listen=False)
        load = {'id': self.id, 'tag': master_start_event_tag, 'data': {}}
        # 30 seconds should be more than enough to fire these events every second in order
        # for pytest-salt to pickup that the master is running
        timeout = 30
        while True:
            timeout -= 1
            try:
                event_bus.fire_event(load, master_start_event_tag, timeout=500)
                if timeout <= 0:
                    break
                yield gen.sleep(1)
            except iostream.StreamClosedError:
                break
