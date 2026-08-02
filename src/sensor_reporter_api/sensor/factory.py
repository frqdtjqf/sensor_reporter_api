from .concrete import (
    NumericSensor,
    Microphone,
    Camera,
    AudioPlayer,
    GPS
)

class SensorFactory:
    """
    Organises a register for all sensors. Sensors like camera, microphone, ... are mapped to their respective class type.
    Every sensor that is not registered is classified as a NumericSensor and only supports one sided datastreams from the server over a shared channel.
    Creates the appropriate Sensor implementation for a discovered sensor and returns it.
    """

    _SENSOR_TYPES = {
        "audio_mic": Microphone,
        "camera_main": Camera,
        "audio_output": AudioPlayer,
        "gps_main": GPS
    }

    @classmethod
    def create(cls, server_base: str, sensor_discovery: dict, logger=None):
        sensor_id = sensor_discovery.get("id")
        if sensor_id is None:
            raise ValueError(f"Sensor has no sensor_Id: {sensor_discovery}")
        
        sensor_cls = cls._SENSOR_TYPES.get(sensor_id)
        if sensor_cls is None:
            sensor_cls = NumericSensor

        return sensor_cls(
            server_base=server_base,
            capabilities=sensor_discovery,
            logger=logger
        )
