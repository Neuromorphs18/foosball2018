#
# use nano_neurons code on arduino
# reset motor, wait for callibration to stop
# hit play (serial should connect after a bit)
# Run gui with nengo -b nengo_board

import nengo
from nengo_board.networks import RemotePESEnsembleNetwork
import serial
import struct
import timeit
import time

ser = None
last_write_time = None

def on_start(sim):
    global ser
    ser = serial.Serial('/dev/cu.usbserial-AI03K35Q', 9600)
    ser.isOpen()
    time.sleep(2)

def on_pause(sim):
        a = struct.pack('BB', 0, 0)
        ser.write(a)

def ard_output(t,x):
    global last_write_time
    cur_time = timeit.default_timer()
    if last_write_time is None or cur_time > (last_write_time+.01):
        x = int(x*255) # max 255 pwm
        if x > 255: x = 255
        dir = 0
        if x<0:
            x = -x
            dir = 1
        a = struct.pack('BB', x, dir)
        ser.write(a)
        last_write_time = cur_time

model = nengo.Network()
with model:
    stim = nengo.Node([0])
    ens = RemotePESEnsembleNetwork(
        'de1', input_dimensions=1, input_synapse=None,
        learn_rate=0, n_neurons=100, label='ensemble',
        ens_args={'neuron_type': nengo.neurons.SpikingRectifiedLinear()})
    motor = nengo.Node(ard_output, size_in=1, size_out=0)
    nengo.Connection(stim, ens.input, synapse=None)
    nengo.Connection(ens.output, motor, synapse = 0.01)
    
    

