import sensiball
import time
import sys

table = sensiball.Table(device='/dev/cu.usbmodemFA131')

class Handler(object):
    def __init__(self):
        self.speed = 0

    def handle_positions(self, positions):
        ratio = round(float(positions[0]) / float(positions[1]) * 100)
        if ratio > 100:
            ratio = 100
        elif ratio < 0:
            ratio = 0
        sys.stdout.write('\r' + '-' * (100 - ratio) + '█' + '-' * ratio)
        table.set_speeds((self.speed, 0, 0, 0, 0, 0, 0, 0))

handler = Handler()
table.add_handler(handler)

while True:
    handler.speed = 60
    time.sleep(1)
    handler.speed = -60
    time.sleep(1)
