from foosball_standalone import *
import nengo

foosball = Foosball()
foosball.add_player(Player(x=50, 
                           ys=[foosball.height/3], 
                           max_y=foosball.height/3,
                           color="blue", goal_left=False))
foosball.add_player(Player(x=150, 
                           ys=[0, foosball.height/2], 
                           max_y=foosball.height/2,
                           color="blue", goal_left=False))
foosball.add_player(Player(x=350, 
                           ys=np.linspace(0, foosball.height-foosball.height/3+25, 5), 
                           max_y=foosball.height/3-25,
                           color="blue", goal_left=False))
foosball.add_player(Player(x=550, 
                           ys=np.linspace(0, foosball.height-foosball.height/3-25, 3), 
                           max_y=foosball.height/3+25,
                           color="blue", goal_left=False))
                           
                           
foosball.add_player(Player(x=750, 
                           ys=[foosball.height/3], 
                           max_y=foosball.height/3,
                           color="yellow", goal_left=True))
foosball.add_player(Player(x=800-150, 
                           ys=[0, foosball.height/2], 
                           max_y=foosball.height/2,
                           color="yellow", goal_left=True))
foosball.add_player(Player(x=800-350, 
                           ys=np.linspace(0, foosball.height-foosball.height/3+25, 5), 
                           max_y=foosball.height/3-25,
                           color="yellow", goal_left=True))
foosball.add_player(Player(x=800-550, 
                           ys=np.linspace(0, foosball.height-foosball.height/3-25, 3), 
                           max_y=foosball.height/3+25,
                           color="yellow", goal_left=True))



def foosball_node(t, x):
    foosball.step(0.001, slide=x)
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


