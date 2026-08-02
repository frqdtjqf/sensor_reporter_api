from sensor_reporter_api.sensor import SensorFactory
import websockets
import json

class SensorNotFound(RuntimeError):
    pass

class DiscoveryError(RuntimeError):
    pass

class Phone:
    """
    Represents one Android device.
    Handles discovery and creates sensor instances.

    Public:
        - connect()                     -> retrieves information from discovery and fills in sensor and device information
        - get_sensor()                  -> returns instance of a sensor
        - get_device_info()             -> returns device info dictionary
        - get_available_sensor_ids()    -> returns a list of all available sensor_Id
        - start_sensor()                -> starts a sensor
        - stop_sensor()                 -> stops a sensor
        - stop_all()                    -> stops all sensors
    """

    def __init__(self, ip: str, port: int = 8080, logger=None):
        self._server_base = f"{ip}:{port}"
        self._discovery_channel = f"ws://{self._server_base}/discovery"

        self._device = {}
        self._sensors = {}
        self._logger = logger

    async def connect(self):
        await self._update_device_discovery()

    # =========== HELPER ==========================
    def get_sensor(self, sensor_id: str):
        """
        Returns the sensor instance for a given id.
        """
        sensor = self._sensors.get(sensor_id)
        if sensor is None:
            raise SensorNotFound(f"The requestet sensor does not exist on this phone: {sensor_id}")

        return sensor

    # =========== DISCOVERY MANAGEMENT =============
    async def _get_discovery(self):
        """
        Opens discovery channel, collecting the sent JSON.
        Connection is closed by android app automatically.
        """
        async with websockets.connect(self._discovery_channel) as ws:
            discovery = json.loads(await ws.recv())
        return discovery

    async def _update_device_discovery(self):
        """
        Retrives device information via discovery.
        Updates class internal parameters based on discovery.
        Recognizes faulty discovery protocol.
        """
        discovery = await self._get_discovery()
        device = discovery.get("device")
        sensor_dict = discovery.get("sensors")
        if device is None or sensor_dict is None:
            raise DiscoveryError(f"Received faulty data from discovery channel: {discovery}")

        self._device = device

        for sensor in sensor_dict:
            instance = SensorFactory.create(
                self._server_base,
                sensor,
                self._logger
            )

            if instance is not None:
                self._sensors[instance.sensor_id] = instance


    # =========== INFORMATION FUNCTION =============
    def get_device_info(self):
        return self._device

    def get_available_sensor_ids(self):
        return self._sensors.keys()

    # =========== START/STOP FUNCTIONS =============
    async def start_sensor(self, sensor_id):
        """
        Starts the sensor for a given id.
        """
        sensor = self.get_sensor(sensor_id)
        sensor.start()

    async def stop_sensor(self, sensor_id):
        """
        Stops the sensor for a given id.
        """
        sensor = self.get_sensor(sensor_id)
        sensor.stop()

    async def stop_all(self):
        """
        Stops all sensors.
        """
        for id in self.sensors.keys():
            await self.stop_sensor(id)