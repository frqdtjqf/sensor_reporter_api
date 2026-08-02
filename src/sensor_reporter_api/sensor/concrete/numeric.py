from sensor_reporter_api.sensor.basic import Sensor

class NumericSensor(Sensor):
    """
    Implementation to listen to all numeric sensors.
    Inherits from the total basic Sensor class and is the simplest form of an actual sensor.
    Uses a subscribe function to identify the relevant data from a stream including data from all numeric sensors.
    Receives no BINARY data, only JSON receiver implemented.
    """
    def __init__(self, server_base, capabilities, logger=None):
        super().__init__(
            server_base=server_base,
            ch_extension="/sensors/numeric",
            capabilities=capabilities,
            logger=logger
        )

    async def _subscribe(self):
        await self._send_json({
            "action": "subscribe",
            "id": self.sensor_id
        })

    async def _unsubscribe(self):
        await self._send_json({
            "action": "unsubscribe",
            "id": self.sensor_id
        })
        
    async def start(self):
        await super().start()
        await self._subscribe()

    async def stop(self):
        await self._unsubscribe()
        await super().stop()