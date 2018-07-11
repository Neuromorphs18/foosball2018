#
#
import nengo
import time
import timeit
import sys
sys.path.insert(0, '../table_api')
import sensiball

class TableInOut(object):
    def __init__(self):
        self.nengo_position = 0
        #self.now = timeit.default_timer()
        
    def handle_positions(self, positions):
        # map to -1,1
        # print(positions)
        self.nengo_position = 2*(float(positions[0])/float(positions[1]))-1

        #tmp_now = timeit.default_timer()
        #print(tmp_now-self.now)
        #self.now = tmp_now 

    def __call__(self, t):
        return self.nengo_position

table_inout = TableInOut()

table = None
table_dict = {}
def on_start(sim):
    global table
    table = sensiball.Table('/dev/cu.usbmodem1411')
    table_dict[table] = None
    table.add_handler(table_inout)

def on_close(sim):
    for key in table_dict:
        key.close()

def ard_output(t,x):
    x = int(x * 255)
    table.set_speeds((x, 0, 0, 0, 0, 0, 0, 0))
    time.sleep(.001)

model = nengo.Network()
with model:
    desired = nengo.Node([0])
    derror = nengo.Ensemble(n_neurons=64,dimensions=1)
    error = nengo.Ensemble(n_neurons=64,dimensions=1)
    PD = nengo.Ensemble(n_neurons=64,dimensions = 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)

    position = nengo.Node(table_inout, size_in=0, size_out=1)

    nengo.Connection(desired, error, transform=1, synapse=0.005)
    nengo.Connection(position, error, transform=-1, synapse=0.005)
    nengo.Connection(error, derror, transform=1, synapse=0.005)
    nengo.Connection(error, derror, transform=-1, synapse=0.01)
    nengo.Connection(error, PD, transform=.8, synapse=0.005)

    nengo.Connection(PD, motor, synapse = 0.01)
    nengo.Connection(derror, PD, transform = 3., synapse = 0.005)

    derror_vis = nengo.Node(None, size_in=2)
    nengo.Connection(error, derror_vis[0], synapse=None)
    nengo.Connection(derror, derror_vis[1], synapse=None)
    
