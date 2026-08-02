from .base import Sensor, StatusError

class StreamError(RuntimeError):
    pass

class SpecialSensor(Sensor):
    """
    Serves an abstract base class for connections to a specific sensor via listening to a websocket.
    Extends the Sensor class for sensors with a dedicated status and data channel that is not shared with others.

    Child classes do not need to subscribe to sensor data and can blindly take any input from their respective channels.
    """
    def __init__(self, server_base, capabilities, logger=None):
        super().__init__(
            server_base=server_base,
            ch_extension=f"/sensor/{capabilities.get('id')}",
            capabilities=capabilities,
            logger=logger
        )
        self._is_streaming = False

    def _encode_binary(self, data):
        return data if isinstance(data, (bytes, bytearray)) else b""

    # === send action ===
    async def _send_action(self, action: str, **payload):
        await self._send_json({
            "action": action,
            **payload
        })

    # === acknowledge action ===
    async def _send_acknowledge(self):
        """
        Sends Acknowledgement at data channel.
        """
        await self._send_action("acknowledge")

    # === enable/disable stream ===
    async def _send_stream_action(self, value: bool):
        """
        Sends a stream action.
        """
        self._is_streaming = value
        await self._send_action("stream", enable=value)

    async def _send_stream_start(self):
        """
        Sends action to start stream.
        """
        if self._is_streaming:
            raise StreamError(f"Stream is already running.")
        if self.is_await or self.is_error:
            raise StatusError(f"Status: {self._status} does not allow to start streaming.")
        await self._send_stream_action(True)

    async def _send_stream_stop(self):
        """
        Sends action to stop stream.
        """
        await self._send_stream_action(False)

    # === send settings configuration ===
    async def _send_configure(self, settings: dict):
        """
        Sends a configuration dictionary.
        """
        if self.is_await or self.is_error:
            raise StatusError(f"Status: {self._status} does not allow to send a configuration.")
        await self._send_action("configure", settings=settings)