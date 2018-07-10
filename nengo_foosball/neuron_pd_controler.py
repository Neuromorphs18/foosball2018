#
# use nano_neurons code on arduino
# reset motor, wait for callibration to stop; refresh nengo
# hit play (serial should connect after a bit)
#
import nengo
import time
import sys
sys.path.insert(0, '../table_api')
import sensiball

class Input(object):
    def __init__(self):
        self.nengo_position = 0
    
    def handle_positions(self, positions):
        # map to -1,1
        print(positions)
        # handle i2c errors: 2**15-1
        self.nengo_postion = 2*positions[0]/positions[1]-1
        
    def __call__(self, t):
        return self.nengo_position

pos_input = Input()

table = None
def on_start(sim):
    global table
    table = sensiball.Table('/dev/cu.usbmodem1421')
    time.sleep(5)
    table.add_handlers(pos_input)

def on_close(sim):
    table.close()

def ard_output(t,x):
    x = int(x * 255)
    if x > 255:
        x = 255
    elif x < -255:
        x = -255
    table.set_speeds((x, 0, 0, 0, 0, 0, 0, 0))

model = nengo.Network()
with model:
    stim = nengo.Node([0])
    #ens = nengo.Ensemble(100, 1)
    slow = nengo.Ensemble(n_neurons=64,dimensions=1)
    derror = nengo.Ensemble(n_neurons=64,dimensions=1)
    error = nengo.Ensemble(n_neurons=64,dimensions=1)
    PD = nengo.Ensemble(n_neurons=64,dimensions = 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)

    position = nengo.Node(pos_input, size_in=0, size_out=1)
    # fwdmodel = nengo.Ensemble(n_neurons=64,dimensions=1)
    # nengo.Connection(fwdmodel, fwdmodel, transform=1, synapse=0.1)

    nengo.Connection(stim, error, transform=1, synapse=0.005)
    nengo.Connection(position, error, transform=-1, synapse=0.005)
    nengo.Connection(error, slow, transform=1, synapse=0.1)
    nengo.Connection(error, derror, transform=1, synapse=0.005)
    nengo.Connection(slow, derror, transform=-0.8,synapse=0.005)
    nengo.Connection(derror, PD, transform=0.7, synapse=0.005)
    nengo.Connection(error, PD, transform=1.0, synapse=0.005)

    nengo.Connection(PD, motor, synapse = 0.01)
    # nengo.Connection(PD, fwdmodel, transform=1.0,synapse=0.1)
