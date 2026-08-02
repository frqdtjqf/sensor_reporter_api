# Sensor Reporter - Python API

## Prerequisites

To use this library, you need the **Sensor Reporter App** installed on your Android device.

1. **Download:** Get the latest APK from the [Android App Repository](https://github.com/frqdtjqf/sensor_reporter/releases).
2. **Setup:** Ensure both your PC and Android device are on the same Wi-Fi network.

This Project provides a python api package to communicate with the sensor reporter android app.

It is able to read sensor data of all Hardware Sensors and provides them via a websocket for the user to read. They are neatly wrapped in a NumericSensor class which handles communication protocols and provides an interface to get the sensor data.

Additionally communication with the microphone, gps, audio player and camera is made possible by spezialized versions of classes.

## 1. Phone
This is the main class of this project. It builds up the communication with the phone and initializes all available sensor classes.

| Function name | Input | Output | Functionality |
| --- | --- | --- | --- |
| connect | - | - | gets information from dicovery channel; fills in sensor and device information; initializes sensor classes |
| get_sensor | sensorId as string | sensor class instance | - |
| get_device_info | - | returns the device part of the discovery dict | - |
| get_available_sensor_ids | - | returns a list of all sensorIds the phone provides | - |
| start_sensor | - | sensorId as string | starts the sensor instance related to the sensorId |
| stop_sensor | - | sensorId as string | stops the sensor instance related to the sensorId |
| stop_all | - | - | stops all sensor instances of this phone |

### 1.1 Numeric Sensors

### 1.2 Spezialized Sensors

#### 1.2.1 Camera

#### 1.2.2 GPS

#### 1.2.3 Microphone

#### 1.2.4 Audioplayer