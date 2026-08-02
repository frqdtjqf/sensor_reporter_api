from sensor_reporter_api.api import (
    ChannelManager,

    # === STATUS ===
    SensorStatus,
    ServerDataTypes
)
from sensor_reporter_api.src.sensor_reporter_api.debug_tools import Logger
import websockets

import json
from collections import defaultdict
from typing import Any, Callable, Awaitable
from enum import Enum
import asyncio

Callback = Callable[[Any], Awaitable[None]]

"""
Source of truth for the callback stack to define a unique callback for each handler.
Changing should not break any code included in the framework.
Overheading code using the callback stack will break and needs to be adjusted, if it is not also defined on the basis of this class.
"""
class SensorEvents(str, Enum):
    NUMERIC = "numeric"
    METADATA = "data"
    STATUS = "status"
    BINARY = "binary"

"""
Names the channels. Only used in context of this class and can be changes without problems.
"""
class APIChannelNames(str, Enum):
    STATUS = "status"
    DATA = "data"

"""
Thrown when the status of a sensor blocks a specific action.
"""
class StatusError(RuntimeError):
    pass

class Sensor:
    """
    Serves an abstract base class for connections to a specific sensor via listening to a websocket.
    Needs the uri to listen to and the sensor id to either specify the channel or subscribe to a sensor.
    Used for mapping the streamed data to a specific sensor.

    Defines most needed functionalities, but is still an abstract class. Child classes will have to define at least start() and stop() if they are purely numeric.
    If the sensor can either send or receive binary data, the decoder/encoder for binaryes have to be implemented additionally according to their usecase.
    
    Input:
        server_base: <IP>:<PORT>
        ch_extension: enxtension to specific channel from server_base (ex.: /sensors/numeric)
        sensor_id: id of the sensor delivered by android application

    Public (only these functions should be available outside this class):
        - properties    -> allows to receive deeper information if needed. For example the status of the sensor or the status of the connection.
        - on()          -> allows to define a custom callback on received data
        - start()       -> establishes connection
        - stop()        -> stops connection

    Abstract (these functions should be overwritten if the sensor needs them):
        - _encode_binary()
        - _decode_binary()
    """
    def __init__(self, server_base: str, ch_extension: str, capabilities: dict, logger: Logger = None):
        self.uri = f"ws://{server_base}{ch_extension}"
        self.sensor_id = capabilities.get("id")
        self.capabilities = capabilities
        self.logger = logger

        self._data_channel = ChannelManager(self.uri, APIChannelNames.DATA, self._handler, listen_only=False)
        self._status_channel = ChannelManager(self.uri+"/status", APIChannelNames.STATUS, self._handler, listen_only=True)

        self._status = None
        self._status_condition = asyncio.Condition()

        self._pending_metadata = None
        self._intent_connection = False
        self._listeners = None
        self._msg_callbacks = defaultdict(list)

        self._lock = asyncio.Lock()

        self._handlers = {
            ServerDataTypes.METADATA: self._handle_metadata,
            ServerDataTypes.NUMERIC: self._handle_numeric
        }

    # =========== PROPERTIES =========
    # === status ===
    @property
    def is_ready(self):
        return self._status is SensorStatus.READY

    @property
    def is_busy(self):
        return self._status is SensorStatus.BUSY

    @property
    def is_await(self):
        return self._status is SensorStatus.AWAIT
    
    @property
    def is_error(self):
        return self._status is SensorStatus.ERROR

    # === connection ===
    @property
    def is_live(self):
        return (
            self._data_channel.connected
            and self._status_channel.connected
        )
    # =========== LOGGING =========
    def _log(self, message: str):
        """
        Logs a message according to the logger settings. If no logger is set, nothing will be logged.
        """
        if self.logger:
            self.logger.debug(f"Sensor {self.sensor_id}: {message}")

    # =========== CALLBACKS FOR MESSAGES =========
    def on(self, event: SensorEvents, callback: Callback):
        """
        Maps a given SensorEvent to a given callback function and stores them in self._msg_callbacks.
        Allows each handler to perform a function defined outside ot this class and work with the sensordata.
        This is the API to use the data of each sensor. Data can be used however wanted and does not have any influence on the sensor operations.
        on() callbacks should be defined or changed, while the sensor connection is stopped. Otherwise this may lead to an unwanted handling of data.
        """
        self._msg_callbacks[event].append(callback)

    async def _perform_callback(self, event: SensorEvents, data):
        """
        Takes defined callback function for the asked event and executes it.
        """
        for callback in self._msg_callbacks[event]:
            await callback(data)

    # =========== INCOMING MESSAGES =======
    # === receiver ===
    async def _handler(self, channel: str, message):
        """
        Entry Point for incoming messages.
        Every incoming message over every connected channel (and in case of purely numeric sensors also only the subscribed messages)
        is received here and gets routed to the handler for status channel and data channel.
        """
        self._log(f"Received message on channel {channel}: {message}")
        if isinstance(message, bytes):
            if self._pending_metadata is None:
                return  # Ignore binary messages if no metadata is pending
            await self._handle_binary(message)
            return

        data = self._decode_json(message)

        if channel == APIChannelNames.STATUS:
            await self._handle_status(data)

        elif channel == APIChannelNames.DATA:
            await self._handle_data(data)

        else:
            raise TypeError("Received message type is not supported")

    async def _handle_data(self, data):
        """
        Defines the handling of all data received over the "data" channel is processed.
        Maps specific handlers for each receivable type via self._handlers.
        """
        msg_type = data.get("type")

        handler = self._handlers.get(msg_type)

        if handler is None:
            raise RuntimeError(
                f"Unknown data type {msg_type}"
            )

        await handler(data)

    async def _handle_status(self, data):
        """
        Defines how received status is handled.
        Receives a decoded message sent over "status" channel and updates class property self.status.
        {
            "type": "status",
            "state": "...",
            "sensorId": "...",
            "timestamp": ...,
            "message": "<optional message>"
        }
        @properties are defined for each status to check for a specific status more comfortable.

        CALLBACK ON:
        {
            "state": "...",
            "timestamp": "...",
            "message": "..",
        }
        Parsed message of the originaly sent status including only relevant data and removed all data only used in protocol.
        Outside code should not be bothered with communication protocol.
        """
        if data.get("type") != ServerDataTypes.STATUS:
            raise ValueError(f"Missguided message. Status handler received: {data}")
        sent_state = data.get("state")
        if sent_state is None:
            raise ValueError(f"Received faulty status message without a state: {data}")
        try:
            new_status = SensorStatus(sent_state)
        except ValueError:
            raise ValueError(
                f"Unknown status: {sent_state}"
            )
        if new_status is SensorStatus.ERROR:
            raise StatusError(f"Sensor {self.sensor_id} is in error state. Message: {data.get('message')}")
        
        refined_values = ["state", "timestamp", "message"]
        refined_status = {}
        for key, value in data.items():
            if key in refined_values:
                refined_status[key] = value

        async with self._status_condition:
            self._status = new_status
            self._status_condition.notify_all()
        
        await self._perform_callback(
            SensorEvents.STATUS,
            refined_status
        )

    async def _handle_numeric(self, data):
        """
        Defines how received numerics are handled.
        Is implemented in this parent class, since its the same for all sensors.

        Expected:
        {
            "type": "numeric",
            "sensorId": "...",
            "values": []
        }

        Filters out any messages that do not contain the sensorId of the sensor represented by this class.

        CALLBACK ON:
        [
         ...
        ]
        List of whatever values the sensor was sending. Interpretation is open to the user.
        All protocol definitions are removed for callback.
        """

        if data.get("type") != ServerDataTypes.NUMERIC:
            raise ValueError(f"Unexpected numeric message: {data}")

        if data.get("sensorId") != self.sensor_id:
            return

        values = data.get("values")
        if values is None:
            raise ValueError(f"Numeric message has no values: {data}")

        await self._perform_callback(
            SensorEvents.NUMERIC,
            values
        )

    async def _handle_metadata(self, data):
        """
        Defines how received metadata are handled. Overwrite this in a child to define behaviour.
        Call super()._handle_metadata() at the end to perform callback.

        CALLBACK ON:
        Metadata may look different for every type of sensor.
        on() callback should be used with care, metadata is already mapped to the respective binary received after in _handle_binary().
        Only reason to use callback is for handling only the metadata in scenarios that require maximum speed connection.
        For this case, the option still exists, but for normal applications use the on() for _handle_binary() to parse decoded binary and metadata together.
        """
        refined_metadata = {}
        for key, value in data.items():
            if key == "dataType":
                continue
            refined_metadata[key] = value

        if data.get("dataType"):
            self._pending_metadata = refined_metadata
        else:
            raise ValueError(f"Metadata does not include a dataType. Protocol broken. {data}")

        await self._perform_callback(
            SensorEvents.METADATA,
            refined_metadata
        )

    async def _handle_binary(self, data):
        """
        Defines how received binarys are handled. Overwrite this in a child to define behaviour.
        Call super()._handle_binary(data) at the end to perform callback.

        CALLBACK ON:
        {
            "metadata": <pending refined metadata received beforehand (JSON)>,
            "data": <decoded binary data>
        }
        """
        decoded_bin = self._decode_binary(data)
        metadata = self._pending_metadata
        self._pending_metadata = None

        await self._perform_callback(
            SensorEvents.BINARY,
            {
                "metadata": metadata,
                "data": decoded_bin
            }
        )
    
    # === decoder ===
    def _decode_json(self, message) -> dict:
        """
        Decodes JSON messages.
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON message")
        return data

    def _decode_binary(self, message):
        """
        Decodes BINARY messages.
        """
        raise NotImplementedError("Function not implemented")

    # =========== OUTGOING MESSAGES ================
    # === sender ===
    async def _send_json(self, payload: dict) -> str:
        """
        Takes a dict, converts it to a string and sends it.
        """
        self._log(f"Sending JSON: {payload}")
        await self._data_channel.send(self._encode_json(payload))

    async def _send_binary(self, payload: Any):
        """
        Takes any values, converts them into bytes and sends them.
        """
        self._log(f"Sending BINARY: {payload}", verbose=True)
        await self._data_channel.send(self._encode_binary(payload))

    # === encoder ===
    def _encode_json(self, data: dict):
        """
        Encodes a dict into a string to send via connection.
        """
        return json.dumps(data)
    
    def _encode_binary(self, data: Any):
        """
        Encodes data to bytes.
        """
        raise NotImplementedError("Function not implemented")

    # =========== WAIT FOR STATUS ===========
    async def _wait_for_status(self, target_status: SensorStatus, timeout: float = 5.0):
        """
        Waits for a specific status to be received over the status channel.
        Raises TimeoutError if the status is not received within the given timeout.
        """
        if self._status is target_status:
            return

        async with self._status_condition:
            try:
                await asyncio.wait_for(self._status_condition.wait_for(lambda: self._status is target_status), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout waiting for status {target_status}. Current status: {self._status}")
    
    # =========== HANDLE SERVER CONNECTION ===========
    # === START/STOP conenction to android sensor ===
    async def start(self):
        """
        Connects relevant channels. Use super().start() when overwriting this in a child as first step.
        Also start listeners to these channels.
        """
        self._intent_connection = True
        await self._data_channel.connect()
        await self._status_channel.connect()
        await self._create_listeners()

    async def stop(self):
        """
        Disconnects relevant channels. Use super().stop() when overwriting this in a child as last step.
        Also stops active listeners.
        """
        self._intent_connection = False
        await self._cleanup_listeners()
        await self._data_channel.disconnect()
        await self._status_channel.disconnect()

    # === creates/cleans active listeners of this class ===
    async def _cleanup_listeners(self):
        for li in self._listeners:
            li.cancel()
        await asyncio.gather(*self._listeners, return_exceptions=True)
        self._listeners.clear()

    async def _create_listeners(self):
        self._listeners = [
            asyncio.create_task(self._data_channel.listen()),
            asyncio.create_task(self._status_channel.listen())
        ]

        