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

def listener(positions):
    pass

def on_start(sim):
    table = sensiball.Table('/dev/???')
    time.sleep(5)
    table.add_listener(listener)

def ard_output(t,x):
    x = int(x * 255)
    if x > 255:
        x = 255
    elif x < -255:
        x = -255
    sensiball.set_speeds((x, 0, 0, 0, 0, 0, 0, 0))

model = nengo.Network()
with model:
    stim = nengo.Node([0])
    #ens = nengo.Ensemble(100, 1)
    slow = nengo.Ensemble(n_neurons=64,dimensions=1)
    derror = nengo.Ensemble(n_neurons=64,dimensions=1)
    error = nengo.Ensemble(n_neurons=64,dimensions=1)
    PD = nengo.Ensemble(n_neurons=64,dimensions = 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)

    fwdmodel = nengo.Ensemble(n_neurons=64,dimensions=1)
    nengo.Connection(fwdmodel, fwdmodel, transform=1, synapse=0.1)

    nengo.Connection(stim, error, transform=1, synapse=0.005)
    nengo.Connection(fwdmodel,error,transform=-1,synapse=0.005)
    nengo.Connection(error,slow,transform=1,synapse=0.1)
    nengo.Connection(error,derror,transform=1,synapse=0.005)
    nengo.Connection(slow,derror,transform=-0.8,synapse=0.005)
    nengo.Connection(derror, PD,transform=0.7,synapse=0.005)
    nengo.Connection(error,PD,transform=1.0,synapse=0.005)

    nengo.Connection(PD, motor, synapse = 0.01)
    nengo.Connection(PD, fwdmodel, transform=1.0,synapse=0.1)
