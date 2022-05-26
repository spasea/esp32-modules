import ulogger as logging
import network

LOGGER = logging.getLogger(__name__)


class Station:
    def __init__(self, ssid=None, password=None, single_string=''):
        self.station = ''
        self.is_lamp_blinking = False
        self.single_string = single_string
        self.password = password
        self.ssid = ssid

        self.get_connection()

    def find(self):
        station = network.WLAN(network.STA_IF)
        station.active(True)
        stations = station.scan()
        stations_dict = {}

        for station_item in stations:
            stations_dict[station_item[0].decode()] = ''

        config_stations = self.single_string.split('____')
        station_to_connect = ''

        for config_station in config_stations:
            if station_to_connect != '':
                break

            [ssid, _] = config_station.split('__')

            if ssid not in stations_dict:
                continue

            station_to_connect = config_station

        if station_to_connect == '':
            raise Exception('No available station')

        [ssid, password] = station_to_connect.split('__')

        self.password = password
        self.ssid = ssid

        self.connect()

    def connect(self):
        station = network.WLAN(network.STA_IF)

        self.station = station

        if not station.isconnected():
            station.active(True)
            station.connect(self.ssid, self.password)

            while not station.isconnected():
                pass

    def get_connection(self):
        if self.single_string != '':
            try:
                self.find()
            except Exception as e:
                LOGGER.error(e)

            return

        try:
            self.connect()
        except Exception as e:
            LOGGER.error(e)

    async def check_connection(self):
        if self.station.isconnected():
            return

        self.get_connection()
