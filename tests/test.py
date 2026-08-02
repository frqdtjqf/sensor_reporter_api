from sensor_reporter_api.src.sensor_reporter_api import Phone, SensorEvents
import asyncio

IP = "localhost"
PORT = 8080

import matplotlib.pyplot as plt
from collections import deque

plt.ion()

history = 200

x = deque(maxlen=history)
y = deque(maxlen=history)
z = deque(maxlen=history)

fig, ax = plt.subplots()

line_x, = ax.plot([], [], label="x")
line_y, = ax.plot([], [], label="y")
line_z, = ax.plot([], [], label="z")

ax.legend()
ax.set_xlim(0, history)
ax.set_ylim(-20, 20)      # ggf. anpassen


async def on_msg(values):
    x.append(values[0])
    y.append(values[1])
    z.append(values[2])

    xs = range(len(x))

    line_x.set_data(xs, x)
    line_y.set_data(xs, y)
    line_z.set_data(xs, z)

    ax.relim()
    ax.autoscale_view(scalex=False)

    fig.canvas.draw()
    fig.canvas.flush_events()

async def main():
    samsung = Phone(IP, PORT)
    await samsung.connect()

    sensors = samsung.get_available_sensor_ids()

    acc = samsung.get_sensor("hw_1_lsm6dsl_accelerometer")

    acc.on(
        SensorEvents.NUMERIC,
        on_msg
    )
    await acc.start()

    await asyncio.Event().wait()


if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nAbgebrochen.")