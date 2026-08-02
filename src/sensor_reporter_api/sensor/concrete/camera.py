from sensor_reporter_api.api.registry import SensorStatus
from sensor_reporter_api.sensor.basic import SpecialSensor, StreamError
import cv2
import numpy as np

class Camera(SpecialSensor):
    # === abstract overwrite to decode binary images ===
    def _decode_binary(self, img_binary: bytes):
        img = cv2.imdecode(
            np.frombuffer(img_binary, np.uint8),
            cv2.IMREAD_COLOR
        )
        return img

    async def _send_acknowledge_configure(self, settings: dict, timeout: float = 5.0):
        """
        Sends a configuration to the camera sensor when not streaming.
        Here await is sent from phone, config applied and acknowledged.
        This is such that the camera is ready to capture or stream only after the configuration is actually applied.
        Because there is a latency between sending the configuration and the camera actually applying it, this method waits for the camera to be ready before returning.
        """
        await self._send_configure(settings=settings)
        await self._wait_for_status(SensorStatus.AWAIT, timeout=timeout)
        await self._send_acknowledge()
        await self._wait_for_status(SensorStatus.READY, timeout=timeout)

    async def _send_configure_routing(self, settings: dict, timeout: float = 5.0):
        """
        Routes a sent configuration to the according confguration method to apply a certain protocol
        depending on the current state of the camera sensor (_is_streaming).
        """
        if self._is_streaming:
            await self._send_configure(settings=settings)
        else:
            await self._send_acknowledge_configure(settings=settings, timeout=timeout)

    async def start_stream(self):
        await self._send_stream_start()

    async def stop_stream(self):
        await self._send_stream_stop()

    async def _send_capture(self):
        await self._send_action("capture")

    async def capture(self):
        """
        Captures a single image from the camera sensor.
        """
        if self._is_streaming:
            raise StreamError(f"Cannot capture while streaming.")
        await self._send_capture()

    async def set_zoom(self, zoom: float):
        await self._send_configure_routing({"zoom": zoom})

    async def set_focus(self, focus: dict):
        await self._send_configure_routing({"focus": focus})

    async def set_exposure(self, exposure: int):
        await self._send_configure_routing({"exposure": exposure})

    async def set_torch(self, torch: bool):
        await self._send_configure_routing({"torch": torch})

    async def set_flash(self, flash: bool):
        await self._send_configure_routing({"flash": flash})

    async def set_back_lense(self):
        await self._send_configure_routing({"lens": "back"})

    async def set_front_lense(self):
        await self._send_configure_routing({"lens": "front"})

    async def set_resolution(self, width: int, height: int):
        await self._send_configure_routing({"resolution": f"{width}x{height}"})

    async def set_aspect_ratio(self, denominator: int, numerator: int):
        await self._send_configure_routing({"aspectRatio": f"{numerator}:{denominator}"})
