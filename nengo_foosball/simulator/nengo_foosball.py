import nengo
import numpy as np
from environment import Foosball
import pickle
import os

foosball = Foosball()
state = foosball.get_state()

def foosball_node(t, x):
    foosball.update(0.01, x)    
    foosball_node._nengo_html_ = foosball.svg()

model = nengo.Network()

with model:
    control = nengo.Node(np.zeros(2*len(foosball.players)))

    f = nengo.Node(foosball_node, size_in=len(foosball.players)*2)
    nengo.Connection(control, f, transform=-1000)
        
    try:
        import nengo_xbox
        xbox = nengo_xbox.Xbox()
        nengo.Connection(xbox.axis[[0,1,2,3]], f[:4], transform=-1000)
    except ImportError:
        pass