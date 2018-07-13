#
#
import nengo
import time
import timeit
import sys
sys.path.insert(0, '../table_api')
import sensiball
import redis

class TableInOut(object):
    def __init__(self):
        self.nengo_position = 0
        #self.now = timeit.default_timer()
        
    def handle_positions(self, positions):
        # map to -1,1
        #print(positions[0][1])
        print(positions)
        if positions[0][1] != 0:
            self.nengo_position = 2*(float(positions[0][0])/float(positions[0][1]))-1
            #print("selfpos handle" , self.nengo_position)
        #tmp_now = timeit.default_timer()
        #print(tmp_now-self.now)
        #self.now = tmp_now 

    def __call__(self, t):
        print(self.nengo_position)
        return self.nengo_position

table_inout = TableInOut()

table = None
table_dict = {}
def on_start(sim):
    global table
    table = sensiball.Sensiball()
    table.open('/dev/ttyACM1', 115200)
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
    
    #time.sleep(0.1)

db = redis.StrictRedis("localhost")
db.set('pos', '0;0')

def get_pos(t):
    pos = db.get('pos').decode('utf-8').split(';')
    print("pod", pos)
    y = float(pos[1])
    y = 2 * (y - 45) / 55 - 1
    if y > 1: y = 1
    if y < -1: y = -1
    return y

model = nengo.Network()
with model:
    # PD Control
    desired = nengo.Node(get_pos, size_out=1)
    #desired = nengo.Node([0])
    derror = nengo.Ensemble(n_neurons=64,dimensions=1)
    error = nengo.Ensemble(n_neurons=64,dimensions=1)
    PD = nengo.Ensemble(n_neurons=64,dimensions = 1)
    motor = nengo.Node(ard_output, size_in=1, size_out=0)

    position = nengo.Node(table_inout, size_in=0, size_out=1)

    #nengo.Connection(desired, error, transform=-1/90, synapse=0.005)
    nengo.Connection(desired, error, transform=-1, synapse=0.005)
    nengo.Connection(position, error, transform=-1, synapse=0.005)
    nengo.Connection(error, derror, transform=1, synapse=0.005)
    nengo.Connection(error, derror, transform=-1, synapse=0.01)
    nengo.Connection(error, PD, transform=.7, synapse=0.005)

    nengo.Connection(PD, motor, synapse = 0.01)
    nengo.Connection(derror, PD, transform = 3, synapse = 0.005)

    deriv_vis = nengo.Node(None, size_in=2)
    nengo.Connection(error, deriv_vis[0], synapse=None)
    nengo.Connection(derror, deriv_vis[1], synapse=None)

    # Learning
    adaptive = nengo.Ensemble(100, dimensions=2)
    nengo.Connection(position, adaptive[0], transform=1000, synapse=None)
    nengo.Connection(position, adaptive[0], transform=-1000, synapse=0)
    nengo.Connection(position, adaptive[1])
    adapt_vis = nengo.Node(None, size_in=1)
    learn_conn = nengo.Connection(adaptive, adapt_vis, function=lambda x: 0, synapse=None)
    learn_conn.learning_rule_type = nengo.PES(learning_rate=1e-6)
    nengo.Connection(adapt_vis, motor, synapse=None)
    nengo.Connection(PD, learn_conn.learning_rule, transform=-1)
    
    
    
