import websockets
from typing import Optional, Any, Callable, Awaitable

MessageCallback = Callable[[Any], Awaitable[None]]

class ChannelStateError(RuntimeError):
    pass

class SupportError(RuntimeError):
    pass

class ChannelManager:
    def __init__(self, uri: str, name: str, msg_callback: MessageCallback, listen_only: bool = False):
        self.uri = uri
        self.msg_callback = msg_callback
        self.name = name

        self.listen_only = listen_only
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def connect(self):
        """
        Starts connection.
        """
        if self._ws:
            return False

        try:
            ws = await websockets.connect(self.uri)
            self._running = True
            self._ws = ws
            return True
        except Exception as e:
            self._ws = None
            raise ConnectionError(f"Error connecting to channel: {e}")
        
    async def disconnect(self):
        """
        Stops connection.
        """
        if not self._ws:
            return False

        try:
            ws = self._ws
            self._ws = None
            await ws.close()
            return True
        except Exception as e:
            raise ConnectionError(f"Error disconnection from channel: {e}")

    async def send(self, data: Any):
        """
        Sends any type of data.
        """
        if self.listen_only:
            raise SupportError(f"Channel is set to listen only, no commands can be sent.")
        if not self._ws:
            raise ConnectionError(f"Not connected to {self.uri}")
        await self._ws.send(data)

    async def listen(self):
        """
        Processes incoming data from channel.
        """
        if not self._ws:
            raise ConnectionError(f"Not connected to {self.uri}")

        try:
            async for message in self._ws:
                await self.msg_callback(self.name, message)

        except ConnectionError as e:
            self.disconnect()
            raise ConnectionError(f"Connection closed: {e}")