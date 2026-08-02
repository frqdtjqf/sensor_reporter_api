from sensor_reporter_api.sensor.basic import SpecialSensor
import numpy as np

class Microphone(SpecialSensor):

    def _decode_binary(self, message: bytes):
        metadata = self._pending_metadata

        format = metadata.get("format")
        rate = metadata.get("sampleRate")
        channels = metadata.get("channels")
        if rate is None or channels is None or format is None:
            raise ValueError(f"Metadata is not complete. Audio cant be reconstructed: {metadata}")

        if self._byte_type == "pcm_s16le":
            samples = np.frombuffer(
                message,
                dtype="<i2"
            )
        else:
            raise ValueError(f"Unsupported audio format: {self._byte_type}")

        if channels > 1:
            samples  = samples.reshape(-1, channels)

        return samples