from enum import Enum

# ==============================
# Defines how python api names and maps them to the android names
# ==============================
"""
Hardwired to the stati send over the status channel by the android application.
Changing these WILL break the code since the android app does not know about this and will still send its hardwired stati.
The sensor class will then not be able to detect the stati of the sensor correctly, rendering the status channel useless.

Numeric sensors might still work, since they dont use the status as much. Camera and other specialized sensor managers won't work.
"""
class SensorStatus(str, Enum):
    READY = "ready"
    BUSY = "busy"
    AWAIT = "await"
    ERROR = "error"

"""
Defines which types of data the android application can send, excluding binary.
Each message looks like this:
{
    "type": <ServerDataType>,
    "...": ...
}
"type" here is what ServerDataTypes refers to.
    - "data" is sent before any binary is sent, since the binary itself does not have any JSON wrapping defining its properties.
        It is mostly sent as a respose to a specific action.
    - "numeric" refers to the data sent by a numeric sensor over the main /sensors channel or by GPS over its own channel.
        Includes a "values" field that consists of the data from the sensor. Is sent in respose to the "subscribe" action and streamed until unsubscribe.
    - "status" is sent exclusivly via the specific status channel of the respective sensor.
        Includes a "state" field which refers to the status of the sensor as it is described in "SensorStatus" class above.
"""
class ServerDataTypes(str, Enum):
    NUMERIC = "numeric"
    METADATA = "data"
    STATUS = "status"
# ==============================