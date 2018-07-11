#
# works with nano_rotate_nengo arduino code
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
        x = int(x*127) # max 127 pwm
        a = struct.pack('b', x)
        ser.write(str(a))
        last_write_time = cur_time

model = nengo.Network()
with model:
    ard = nengo.Node([0])
    output = nengo.Node(ard_output, size_in=1, size_out=0)
    nengo.Connection(ard, output, synapse=None)
