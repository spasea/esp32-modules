"""
Micropython Socket.IO client.
"""

import ulogger as LOGGER
import ure as re
import ujson as json
import usocket as socket
from ucollections import namedtuple

from .protocol import *
from .transport import SocketIO

URL_RE = re.compile(r'http(s|)://([A-Za-z0-9\-\.]+)(?:\:([0-9]+))?(/.+)?')
URI = namedtuple('URI', ('hostname', 'port', 'path'))


def urlparse(uri):
    """Parse http:// URLs"""
    match = URL_RE.match(uri)
    if match:
        return URI(match.group(2), int(match.group(3)), match.group(4))


def _connect_http(hostname, port, path):
    """Stage 1 do the HTTP connection to get our SID"""
    try:
        sock = socket.socket()
        addr = socket.getaddrinfo(hostname, port)
        LOGGER.debug('Host: %s:%s' % (hostname, port))
        sock.connect(addr[0][-1])

        def send_header(val, args):
            if __debug__:
                LOGGER.debug(str(val) % (args))

            sock.write(val % args + '\r\n')

        send_header(b'GET %s HTTP/1.1', path)
        send_header(b'Host: %s:%s', (hostname, port))
        send_header(b'%s', '')

        header = sock.readline()[:-2]
        assert header == b'HTTP/1.1 200 OK', header

        length = None

        while header:
            header = sock.readline()[:-2]
            if not header:
                break

            header, value = header.split(b': ')
            header = header.lower()
            if header == b'content-type':
                LOGGER.debug('Value: %s' % value)
            elif header == b'content-length':
                length = int(value)

        assert length

        LOGGER.debug('Len: %s' % length)

        data = sock.read(length)
        return decode_payload(data)

    finally:
        sock.close()


def connect(uri):
    """Connect to a socket IO server."""
    uri = urlparse(uri)

    assert uri

    path = uri.path or '/' + 'socket.io/?EIO=3'

    # Start a HTTP connection, which will give us an SID to use to upgrade
    # the websockets connection
    packets = _connect_http(uri.hostname, uri.port, path + '&transport=polling')
    # The first packet should open the connection,
    # following packets might be initialisation messages for us
    packet_type, params = next(packets)

    assert packet_type == PACKET_OPEN
    params = json.loads(params)
    LOGGER.debug("Websocket parameters = %s" % params)

    assert 'websocket' in params['upgrades']

    sid = params['sid']
    path += '&sid={}'.format(sid)

    if __debug__:
        LOGGER.debug("Connecting to websocket SID %s" % sid)

    # Start a websocket and send a probe on it
    ws_uri = 'ws://{hostname}:{port}{path}&EIO=3&transport=websocket'.format(
        hostname=uri.hostname,
        port=uri.port,
        path=path)

    socketio = SocketIO(ws_uri, **params)

    # handle rest of the packets once we're in the main loop
    @socketio.on('connection')
    def on_connect(data):
        pass

    @socketio.on('alert')
    def handler(data):
        LOGGER.warn('Alert: %s' % data)

    socketio._send_packet(PACKET_PING, 'probe')

    # We should receive an answer to our probe
    packet = socketio._recv()
    assert packet == (PACKET_PONG, 'probe'), packet

    # Upgrade the connection
    socketio._send_packet(PACKET_UPGRADE)
    packet_upgrade = socketio._recv()

    assert packet_upgrade == (PACKET_MESSAGE, '0'), packet_upgrade

    return socketio
