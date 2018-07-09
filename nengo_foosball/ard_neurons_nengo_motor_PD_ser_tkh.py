#
# use nano_neurons code on arduino
# reset motor, wait for callibration to stop; refresh nengo
# hit play (serial should connect after a bit)
#
import serial
import nengo
import struct
import timeit
import time

ser = None
last_write_time = None

def on_start(sim):
    global ser
    ser = serial.Serial('COM8', 9600)
    if ser.isOpen()==True:
        print ('opened serial port')
    time.sleep(15)

def on_pause (sim):
    a = struct.pack('BB', 0, 0)
    ser.write(a)
        
def ard_output(t,x):
    global last_write_time
    cur_time = timeit.default_timer()
    if last_write_time is None or cur_time > (last_write_time+.01):
        x = int(x*255) # max 255 pwm
        dir = 0
        if x<0:
            x = -x
            dir = 1
        if x > 255:
            x = 255
        #print (a)
        a = struct.pack('BB', x, dir)
        ser.write(a)
        last_write_time = cur_time 
        

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
    
    nengo.Connection(PD, motor, synapse = None)
    nengo.Connection(PD, fwdmodel, transform=1.0,synapse=0.1)