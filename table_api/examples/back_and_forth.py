import sys
sys.path.insert(0, '..')
from sensiball import Sensiball
import time

row = 0

def handle_positions(positions):
    print(positions)
    if positions[row][1] != 0:
        ratio = round(float(positions[row][0]) / float(positions[row][1]) * 100)
        if ratio > 100:
            ratio = 100
        elif ratio < 0:
            ratio = 0
        sys.stdout.write('\r' + '-' * (100 - ratio) + '|' + '-' * ratio)

sb = Sensiball()
sb.open('/dev/tty.usbmodemFA131', 115200)
sb.add_handler(handle_positions)

time.sleep(2)
sb.send_calibrate()
speeds = [0] * 8
while True:
    speeds[row * 2] = 60
    sb.send_speeds(speeds)
    time.sleep(1)
    speeds[row * 2] = -60
    sb.send_speeds(speeds)
    time.sleep(1)
