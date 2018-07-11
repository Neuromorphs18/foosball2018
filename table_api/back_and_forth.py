import sensiball
import time
import sys

class Handler(object):
    def handle_positions(self, positions):
        ratio = round(float(positions[0]) / float(positions[1]) * 100)
        if ratio > 100:
            ratio = 100
        elif ratio < 0:
            ratio = 0
        sys.stdout.write('\r' + '-' * (100 - ratio) + '█' + '-' * ratio)

handler = Handler()
table = sensiball.Table(device='/dev/cu.usbmodem1421')
table.add_handler(handler)

while True:
    for i in range(0, 1):
        table.set_speeds((60, 0, 0, 0, 0, 0, 0, 0))
        time.sleep(0.001)
    for i in range(0, 1):
        table.set_speeds((-60, 0, 0, 0, 0, 0, 0, 0))
        time.sleep(0.001)
