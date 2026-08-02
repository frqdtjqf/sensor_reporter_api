from sensor_reporter_api.sensor.basic import SpecialSensor, StatusError
import numpy as np
import asyncio

class AudioPlayer(SpecialSensor):
    def __init__(self, server_base, capabilities, logger=None):
        super().__init__(server_base, capabilities, logger)
        self._recommended_sample_rate = capabilities.get("recommended_buffer_size", 4096)

    def _encode_binary(self, data):
        if isinstance(data, np.ndarray):
            samples = np.clip(data, -1.0, 1.0)
            samples_int16 = (samples * 32767).astype(np.int16)
            return samples_int16.tobytes()
        return super()._encode_binary(data)

    # === send audio data ===
    async def _send_metadata(self, metadata: dict):
        """
        Sends metadata at data channel.
        """
        await self._send_json(metadata)

    async def _send_signal(self, signal: np.ndarray):
        raw_bytes = self._encode_binary(signal)
        chunk_size = int(self._recommended_sample_rate)

        for i in range(0, len(raw_bytes), chunk_size):
            chunk = raw_bytes[i:i + chunk_size]

            metadata = {
                "type": "data",
                "dataType": "audio",
                "size": len(chunk),
                "sampleRate": self._recommended_sample_rate,
                "channels": 1,
                "format": "pcm_s16le"
            }
            await self._send_stream_chunk(chunk, metadata)
            asyncio.sleep(0)

    async def _send_stream_chunk(self, signal: np.ndarray, metadata: dict):
        if not self.is_ready:
            raise StatusError(f"Audio player is not ready. Status: {self._status}")

        encoded_signal = self._encode_binary(signal)
        if encoded_signal is None:
            raise ValueError(f"Failed to encode audio signal: {signal}")
        
        await self._send_json(metadata)
        await self._send_binary(encoded_signal)
            
    # === play audio ===
    async def _send_play_tone(self, tone: str, duration: int):
        if not self.is_ready:
            raise StatusError(f"Audio player is not ready. Status: {self._status}")
        await self._send_action("play_beep", type=tone, duration=duration)

    async def _send_url(self, url: str):
        if not self.is_ready:
            raise StatusError(f"Audio player is not ready. Status: {self._status}")
        await self._send_action("play_url", url=url)

    # === predefined settings ===
    async def set_volume(self, volume: float):
        if not self.is_ready:
            raise StatusError(f"Audio player is not ready. Status: {self._status}")
        await self._send_configure({"volume": volume})

    # === public sender methods ===
    async def stream_audio(self, signal: np.ndarray):
        """
        Streams audio data to the audio player.
        """
        if not self.is_ready:
            raise StatusError(f"Audio player is not ready. Status: {self._status}")

        await self._send_stream_start()
        await self._send_signal(signal)
        await self._send_stream_stop()

    async def play_tone(self, tone: str, duration: int):
        """
        Plays a predefined tone for a specified duration.
        """
        await self._send_play_tone(tone, duration)

    async def play_url(self, url: str):
        """
        Plays audio from a specified URL.
        """
        await self._send_url(url)