import nengo
import time
import timeit
import sys
sys.path.insert(0, '../table_api')
import sensiball


class Handler(object):
    def handle_positions(self, positions):
        ratio = round(float(positions[0]) / float(positions[1]) * 100)
        if ratio > 100:
            ratio = 100
        elif ratio < 0:
            ratio = 0
        sys.stdout.write('\r' + '-' * (100 - ratio) + '0' + '-' * ratio)

handler = Handler()

table = None
def on_start(sim):
    global table
    table = sensiball.Table(device='/dev/cu.usbmodem1411')
    time.sleep(5)    
    table.add_handler(handler)
    print('calibtrating...')
    table.calibrate()

def speed_setter(t):
    if t % 1 < .5:
        table.set_speeds((60, 0, 0, 0, 0, 0, 0, 0))
        time.sleep(0.001)
    else:
        table.set_speeds((-60, 0, 0, 0, 0, 0, 0, 0))
        time.sleep(0.001)

model = nengo.Network()
with model:
    set_speeds = nengo.Node(speed_setter, size_in=0, size_out=0)