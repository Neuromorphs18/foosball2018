#
#
import nengo
import time
import timeit
import sys
sys.path.insert(0, '../table_api')
import sensiball
import redis
import numpy as np

class TableInOut(object):
    def __init__(self):
        self.nengo_position = 0
        #self.now = timeit.default_timer()
        
    def handle_positions(self, positions):
        # map to -1,1
        # print(positions)
        if positions[0][1] != 0:
            self.nengo_position = 2*(float(positions[0][0])/float(positions[0][1]))-1

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
    table = sensiball.Sensiball()
    table.open('/dev/cu.usbmodem1421', 115200)
    table.add_handler(table_inout)
    time.sleep(2)
    table.send_calibrate()
    table_dict[table] = None 

def on_close(sim):
    for key in table_dict:
        key.send_halt()

now = timeit.default_timer()
def ard_output(t,x):
    global now
    if timeit.default_timer() > now + 0.1 :
        x = int(x * 255)
        table.send_speeds((x, 0, 0, 0, 0, 0, 0, 0))
        now = timeit.default_timer()

db = redis.StrictRedis("10.162.177.1")
db.set('pos', '0;0')
db.set('vel', '0;0')

'''def get_pos(t):
    pos = db.get('pos').decode('utf-8').split(';')
    scale -1,1; flip
    return [float(e) for e in pos]'''

def get_pos(t):
    pos = db.get('pos').decode('utf-8').split(';')
    # print("pos", pos)
    y = float(pos[1])
    y = 2 * (y - 45) / 55 - 1
    if y > 1: y = 1
    if y < -1: y = -1
    return y

'''def get_vel(t):
    vel = db.get('vel').decode('utf-8').split(';')
    scale -1,1; flip
    return [float(e) for e in vel]'''

#load weights for prediction network
dec = np.load('prediction_decoder_2Rows.npz')
dec = dec['dec3']

model = nengo.Network()
with model:

    '''# Prediction neurons
    redis_pos = nengo.Node(get_pos, size_out=2) 
    redis_vel = nengo.Node(get_vel, size_out=2)

    desired = nengo.Node(None, size_in=2)

    ens = nengo.Ensemble(n_neurons=2000, dimensions=4, 
                        neuron_type=nengo.LIFRate(), 
                        radius=2, seed=1, label="prediction")

    nengo.Connection(redis_pos, ens[0:2])
    nengo.Connection(redis_vel, ens[2:4])
    nengo.Connection(ens.neurons, desired, transform=dec, synapse=None)

    #goalie = desired[0]
    #defenders = desired[1]'''

    # PD Control
    desired = nengo.Node(get_pos, size_out=1)
    #desired = nengo.Node([0])
    
    derror = nengo.Ensemble(n_neurons=64,dimensions=1)
    error = nengo.Ensemble(n_neurons=64,dimensions=1)
    PD = nengo.Ensemble(n_neurons=64,dimensions = 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)

    position = nengo.Node(table_inout, size_in=0, size_out=1)

    nengo.Connection(desired, error, transform=-1, synapse=0.005)
    nengo.Connection(position, error, transform=-1, synapse=0.005)
    nengo.Connection(error, derror, transform=1, synapse=0.005)
    nengo.Connection(error, derror, transform=-1, synapse=0.01)
    nengo.Connection(error, PD, transform=.7, synapse=0.005)

    nengo.Connection(PD, motor, synapse = 0.01)
    nengo.Connection(derror, PD, transform = 3., synapse = 0.005)

    deriv_vis = nengo.Node(None, size_in=2, label="error")
    nengo.Connection(error, deriv_vis[0], synapse=None)
    nengo.Connection(derror, deriv_vis[1], synapse=None)

    # Learning
    adaptive = nengo.Ensemble(400, dimensions=2)
    nengo.Connection(position, adaptive[0], transform=1000, synapse=None)
    nengo.Connection(position, adaptive[0], transform=-1000, synapse=0)
    nengo.Connection(position, adaptive[1])
    adapt_vis = nengo.Node(None, size_in=1)
    learn_conn = nengo.Connection(adaptive, adapt_vis, function=lambda x: 0, synapse=None)
    learn_conn.learning_rule_type = nengo.PES(learning_rate=1e-6)
    nengo.Connection(adapt_vis, motor, synapse=None)
    nengo.Connection(PD, learn_conn.learning_rule, transform=-1)
    
    
    