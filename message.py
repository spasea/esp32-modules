from usocketio.transport import SocketIO
import machine


class Events:
    def __init__(self, room_id: str = None, sensor_id: str = None):
        self.sensor_id = sensor_id
        self.room_id = room_id

        assert self.sensor_id is not None or self.room_id is not None, 'Invalid initial params'

    def base(self) -> str:
        return ':'.join([self.room_id, self.sensor_id])

    def server_state(self) -> str:
        return ':'.join([self.base(), 'server_state'])

    def server_reboot(self) -> str:
        return ':'.join([self.base(), 'server_reboot'])

    def client_state(self) -> str:
        return ':'.join([self.base(), 'client_state'])

    def server_load_state(self) -> str:
        return ':'.join([self.base(), 'server_load_state'])

    def server_change(self) -> str:
        return ':'.join([self.base(), 'server_change'])

    def state(self) -> str:
        return ':'.join([self.base(), 'state'])

    def custom(self, event) -> str:
        return ':'.join([self.base(), event])


class BaseSensor:
    def __init__(self, event_instance: Events, socketio: SocketIO, get_state, load_state):
        self.socketio = socketio
        self.event_instance = event_instance
        self.get_state = get_state
        self.load_state = load_state

    def reboot(self):
        self.socketio.emit(self.event_instance.client_state(), self.get_state())

        machine.reset()

    def post_state(self):
        self.socketio.emit(self.event_instance.state(), self.get_state())

    def add_events(self):
        self.socketio.emit('join', self.event_instance.base())

        @self.socketio.on(self.event_instance.server_reboot())
        def handle(msg):
            self.reboot()

        @self.socketio.on(self.event_instance.server_state())
        def handle(msg):
            self.post_state()

        @self.socketio.on(self.event_instance.server_load_state())
        def handle(payload):
            self.load_state(payload)

        @self.socketio.at_interval(5)
        async def handle():
            self.socketio.emit(self.event_instance.state(), self.get_state())
