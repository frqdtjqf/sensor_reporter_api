from sensor_reporter_api.src.sensor_reporter_api import Phone, SensorEvents, Logger
import asyncio

IP = "localhost"
PORT = 8080


import cv2

async def on_msg(msg):
    image = msg["data"]

    cv2.imshow(
        "camera_main",
        image
    )

    cv2.waitKey(1)

async def on_capture(msg):
    image = msg["data"]

    cv2.imshow(
        "camera_main_capture",
        image
    )

    cv2.waitKey(1)



async def main():

    logger = Logger("test_cam", verbose=True)

    samsung = Phone(IP, PORT, logger)
    await samsung.connect()

    cam = samsung.get_sensor("camera_main")

    cam.on(
        SensorEvents.BINARY,
        on_msg
    )
    print(cam)
    await cam.start()

    await cam.set_torch(True)

    await cam.start_stream()

    await asyncio.sleep(5)

    await cam.set_torch(False)

    await asyncio.sleep(5)

    await cam.set_zoom(2.0)

    await asyncio.sleep(5)

    await cam.set_zoom(1.0)

    await asyncio.sleep(5)

    await cam.stop_stream()

    await cam.capture()

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAbgebrochen.")