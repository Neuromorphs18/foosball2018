import nengo
import redis
import numpy as np 

db = redis.StrictRedis("10.162.177.1")
db.set('pos', '0;0')
db.set('vel', '0;0')

def get_pos(t):
    pos = db.get('pos').decode('utf-8').split(';')
    return [float(e) for e in pos]

def get_vel(t):
    vel = db.get('vel').decode('utf-8').split(';')
    return [float(e) for e in vel]

dec = np.load('prediction_decoder.npz')
dec = dec['dec']

model = nengo.Network()
with model:
    redis_pos = nengo.Node(get_pos, size_out=2) 
    redis_vel = nengo.Node(get_vel, size_out=2) 
    pos = nengo.Ensemble(n_neurons=100, dimensions=2)
    vel = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(redis_pos, pos, transform=1/240, synapse=None)
    nengo.Connection(redis_vel, vel, transform=1/200, synapse=None)
    
    def goalie_prediction(t,x):
        pass
    f = nengo.Node(None, size_in=51)
    
    ens = nengo.Ensemble(n_neurons=2000, dimensions=4, neuron_type=nengo.LIFRate(), radius=2, seed=1)
    conn = nengo.Connection(ens.neurons, f, transform=dec, synapse=None)
    nengo.Connection(pos, ens[0:2])
    nengo.Connection(vel, ens[2:4])
