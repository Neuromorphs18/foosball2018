#
# use nano_neurons code on arduino
#
import serial
import nengo
import struct
import timeit

ser = None
last_write_time = None

def on_start(sim):
    global ser
    ser = serial.Serial('/dev/cu.usbserial-AI03K35Q', 9600)
    ser.isOpen()

def ard_output(t,x):
    global last_write_time
    cur_time = timeit.default_timer()
    if last_write_time is None or cur_time > (last_write_time+.01):
        x = int(x*255) # max 255 pwm
        dir = 0
        if x<0:
            x = -x
            dir = 1
        a = struct.pack('BB', x, dir)
        ser.write(str(a))
        last_write_time = cur_time

model = nengo.Network()
with model:
    stim = nengo.Node([0])
    ens = nengo.Ensemble(100, 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)
    nengo.Connection(stim, ens, synapse=None)
    nengo.Connection(ens, motor, synapse = 0.01)
