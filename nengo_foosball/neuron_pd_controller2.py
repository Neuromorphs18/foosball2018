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
    table = sensiball.Table('/dev/cu.usbmodem1421')
    table_dict[table] = None
    time.sleep(5)
    table.calibrate()
    time.sleep(5)
    table.add_handler(table_inout)

def on_close(sim):
    for key in table_dict:
        key.close()

now = timeit.default_timer()
def ard_output(t,x):
    global now
    global table
    if timeit.default_timer() > now + 0.01:
        x = int(x * 255)
        if x > 255:
            x = 255
        elif x < -255:
            x = -255
        table.set_speeds((x, 0, 0, 0, 0, 0, 0, 0))
        now = timeit.default_timer()

model = nengo.Network()
with model:
    stim = nengo.Node([0])
    #ens = nengo.Ensemble(100, 1)
    #slow = nengo.Ensemble(n_neurons=64,dimensions=1)
    derror = nengo.Ensemble(n_neurons=64,dimensions=1)
    error = nengo.Ensemble(n_neurons=64,dimensions=1)
    PD = nengo.Ensemble(n_neurons=64,dimensions = 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)

    position = nengo.Node(table_inout, size_in=0, size_out=1)
    # fwdmodel = nengo.Ensemble(n_neurons=64,dimensions=1)
    # nengo.Connection(fwdmodel, fwdmodel, transform=1, synapse=0.1)

    nengo.Connection(stim, error, transform=1, synapse=0.005)
    nengo.Connection(position, error, transform=-1, synapse=0.005)
    #nengo.Connection(error, slow, transform=1, synapse=0.1)
    nengo.Connection(error, derror, transform=1, synapse=0.005)
    nengo.Connection(error, derror, transform=-1, synapse=0.1)
    #nengo.Connection(slow, derror, transform=-0.8,synapse=0.005)
    #nengo.Connection(derror, PD, transform=0.7, synapse=0.005)
    nengo.Connection(error, PD, transform=.3, synapse=0.005)

    nengo.Connection(PD, motor, synapse = 0.01)
    # nengo.Connection(PD, fwdmodel, transform=1.0,synapse=0.1)
