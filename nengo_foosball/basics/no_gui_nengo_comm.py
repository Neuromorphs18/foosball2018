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
        sys.stdout.write('\r' + '-' * (100 - ratio) + '█' + '-' * ratio)

handler = Handler()

table = sensiball.Table(device='/dev/cu.usbmodem1421')
table.add_handler(handler)
'''def on_start(sim):
    global table
    table = sensiball.Table(device='/dev/cu.usbmodem1421')
    table.add_handler(handler)'''

def speed_setter(t):
    if t % .002 < .001:
        table.set_speeds((60, 0, 0, 0, 0, 0, 0, 0))
        time.sleep(0.001)
    else:
        table.set_speeds((-60, 0, 0, 0, 0, 0, 0, 0))
        time.sleep(0.001)

model = nengo.Network()
with model:
    set_speeds = nengo.Node(speed_setter)

with nengo.Simulator(model) as sim:
    sim.run(10.0)