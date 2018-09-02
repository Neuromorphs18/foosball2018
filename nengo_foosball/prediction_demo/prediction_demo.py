import nengo
import numpy as np

class Player(object):
    def __init__(self, x, ys, max_y, color, goal_left):
        self.x = x
        self.ys = ys
        self.max_y = max_y
        self.offset = max_y / 2
        self.radius = 12
        self.max_radius = 30
        self.color = color
        self.rotate_offset = 0
        self.goal_left = goal_left
        self.kick_deg = 40
        self.velocity = 0
        
    def slide(self, dt, velocity):
        self.offset = np.clip(self.offset + velocity*dt, 0, self.max_y)
    
    def rotate(self, dt, velocity):
        self.velocity = velocity 
        self.rotate_offset = (self.rotate_offset + self.velocity*dt) % 360
        self.rot_off = self.rotate_offset 
        if (self.rotate_offset > 90 and self.rotate_offset < 180) or (
            self.rotate_offset > 270):
                self.rot_off = 90 - self.rotate_offset
        
    def collide(self, x, y):
        for player_y in self.ys:
            if self.rotate_offset < self.kick_deg or self.rotate_offset > 270 - self.kick_deg:
                delta_x = x - self.x
                delta_y = y - (player_y + self.offset)
                dist = np.sqrt(delta_x**2 + delta_y**2)
                if dist < self.radius:
                    return delta_x, delta_y
        return 0, 0
        
    def __rx(self):
        return self.radius + (self.rot_off % 90)/90 * (self.max_radius - self.radius)
      
    def __cx_off(self):
        return (self.rot_off % 90)/90 * 20 * (int(self.rotate_offset > 180)*2 - 1)
        
    def __opacity(self):
        if self.goal_left and self.rotate_offset > 0 and self.rotate_offset <= 180:
            return 0.5 
        elif not(self.goal_left) and self.rotate_offset > 180:
            return 0.5
        return 1 
        
    def svg(self):
        line_width=5
        
        players = ['<ellipse cx="{x}" cy="{y}" ry="{radius}" rx="{angle}" fill="{color}" fill-opacity="{opacity}"/>'.format(
            x=self.x - self.__cx_off(), y=yy+self.offset, radius=self.radius, angle=self.__rx(), color=self.color, opacity=self.__opacity()) for yy in self.ys]
        
        return '''
        <rect x="{x0}" y="0" width="{line_width}" height="{height}" fill="silver"/>
        {players}
        
        '''.format(x0=self.x-line_width/2, players=''.join(players), line_width=line_width, height=self.table.height)

class Foosball(object):
    def __init__(self, ball_noise=0, seed=None):
        self.width = 800
        self.height = 400
        self.ball_radius = 12
        self.ball_noise = ball_noise
        self.rng = np.random.RandomState()
        
        self.score = np.zeros(2)
        self.reset_ball()
        
        self.players = []
        
    def add_player(self, player):
        player.table = self
        self.players.append(player)
        
    def reset_ball(self):
        self.ball_pos = np.array([self.width/2, self.height/2]).astype(float)
        #self.ball_vel = np.array([-1000, 0])
        self.ball_vel = self.rng.uniform(-1000, 1000, 2).astype(float)
        self.ball_vel[1]*=0.5
        
    def step(self, dt, slide):
        if self.ball_noise is not None:
            self.ball_vel += self.rng.normal(loc=0, scale=self.ball_noise, size=2)
            
        self.ball_pos += self.ball_vel*dt  
        
        #if self.ball_pos[0]-self.ball_radius < 0 and self.height/3 < self.ball_pos[1] < 2*self.height/3:
        #    self.score[0] += 1
        #    self.reset_ball()
        #if self.ball_pos[0]+self.ball_radius > self.width and self.height/3 < self.ball_pos[1] < 2*self.height/3:
        #    self.score[1] += 1
        #    self.reset_ball()
        
        
        if self.ball_pos[0]-self.ball_radius < 0:
            self.ball_pos[0] = self.ball_radius
            self.ball_vel[0] *= -1
        if self.ball_pos[1]-self.ball_radius < 0:
            self.ball_pos[1] = self.ball_radius
            self.ball_vel[1] *= -1
        if self.ball_pos[0]+self.ball_radius > self.width:
            self.ball_pos[0] = self.width - self.ball_radius
            self.ball_vel[0] *= -1
        if self.ball_pos[1]+self.ball_radius > self.height:
            self.ball_pos[1] = self.height - self.ball_radius
            self.ball_vel[1] *= -1
            
        for i, p in enumerate(self.players):
            p.slide(dt=dt, velocity=slide[i*2])
            p.rotate(dt=dt, velocity=slide[i*2+1])
            cx, cy = p.collide(self.ball_pos[0], self.ball_pos[1])
            self.ball_pos += [cx, cy]
            new_v = np.array([cx, cy])
            v_norm = np.linalg.norm(new_v)
            if v_norm > 0:
                mag = np.linalg.norm(self.ball_vel)
                self.ball_vel = mag * new_v / v_norm + p.velocity
        
    def svg(self, prediction=None):
    
        if prediction is None:
            pred_def_y = 200
            pred_goalie_y = 200
            pred_path = ''
        else:
            prediction, pred_goalie_y, pred_def_y = prediction[:-2], prediction[-2],prediction[-1]
            
            pred = prediction.reshape(len(prediction)//2, 2)
            pred_path = ''.join(['<circle cx="{x}" cy="{y}" fill="white", r="2" />'.format(x=p[0], y=p[1]) for p in pred])            
            
        template = '''<svg width="100%" height="100%" viewbox="0 0 {width} {height}">

        <rect x="0" y="0" height="{height}" width="{width}" fill="green"/>
        <rect x="0" y="{goal_height}" height="{goal_height}" width="10" fill="yellow"/>
        <rect x="{goal2width}" y="{goal_height}" height="{goal_height}" width="10" fill="lightblue"/>
        
        <rect x="40", y="{pred_goalie_y}" height="20" width="20" fill="rgba(255, 255, 0, 0.5)"/>
        <rect x="140", y="{pred_def_y_plus}" height="20" width="20" fill="rgba(255, 255, 0, 0.5)" />  
        <rect x="140", y="{pred_def_y_minus}" height="20" width="20" fill="rgba(255, 255, 0, 0.5)" />

        {players}

        <circle cx="{bx}" cy="{by}" fill="white" r="{ball_radius}" />

        {pred_path}

        </svg>'''.format(width=self.width, height=self.height, 
                         bx=self.ball_pos[0], by=self.ball_pos[1], 
                         ball_radius=self.ball_radius,
                         goal2width=self.width-10,
                         score2width=self.width-100,
                         score0=int(self.score[0]),
                         score1=int(self.score[1]),
                         players=''.join([p.svg() for p in self.players]),
                         goal_height=self.height/3,
                         pred_def_y_plus=pred_def_y+100-10,
                         pred_def_y_minus=pred_def_y-100-10,
                         pred_path=pred_path,
                         pred_goalie_y=pred_goalie_y)

        return template


npzfile = np.load('prediction_decoder.npz')   # load up the goalie decoder
dec = npzfile['dec']
npzfile2 = np.load('prediction_decoder_2ndRow.npz')
dec2 = npzfile2['dec2']

dec3 = np.zeros((52, 2000))
dec3[:50,:] = dec[:50,:]
dec3[50,:] = dec[-1,:]
dec3[51,:] = dec2[-1,:]

inp_mean = npzfile['inp_mean']
inp_sd = npzfile['inp_sd']
outp_mean = np.hstack([npzfile['outp_mean'], npzfile2['outp_mean'][-1:]])
outp_sd = np.hstack([npzfile['outp_sd'], npzfile2['outp_sd'][-1:]])

def inp2inpz(x):
    return (x-inp_mean[None,:])/inp_sd[None,:]
def outp2outpz(x):
    return (x-outp_mean[None,:])/outp_sd[None,:]
def inpz2inp(x):
    return x*inp_sd[None,:]+inp_mean[None,:]
def outpz2outp(x):
    return x*outp_sd[None,:]+outp_mean[None,:]
    
foosball = Foosball(ball_noise=1.0)


foosball.add_player(Player(x=50, 
                           ys=[foosball.height/3], 
                           max_y=foosball.height/3,
                           color="blue", goal_left=False))
foosball.add_player(Player(x=150, 
                           ys=[0, foosball.height/2], 
                           max_y=foosball.height/2,
                           color="blue", goal_left=False))


def foosball_node(t, x):
    prediction = outpz2outp(x[:-2])[0]
    
    #Kp = 20.0
    #target_goalie = prediction[-2]
    #actual_goalie = foosball.players[0].offset + foosball.players[0].ys[0]    
    #move_goalie = Kp*(target_goalie-actual_goalie)
    move_goalie = x[-2]
    
    #Kp = 20.0
    #target_def = prediction[-1]
    #actual_def = foosball.players[1].offset + np.mean(foosball.players[0].ys)    
    #move_def = Kp*(target_def-actual_def)
    move_def = x[-1]
    
    
    foosball.step(0.001, slide=[move_goalie,0,move_def,0])
    foosball_node._nengo_html_ = foosball.svg(prediction)
    ball_output = np.array([foosball.ball_pos[0], foosball.ball_pos[1], foosball.ball_vel[0], foosball.ball_vel[1]])    
    ball_output = inp2inpz([ball_output])[0]
    pos_output = np.array([p.offset+np.mean(p.ys) for p in foosball.players])
    pos_output = (pos_output-inp_mean[1])/inp_sd[1]
    
    return np.hstack([ball_output, pos_output])

model = nengo.Network()

with model:
    f = nengo.Node(foosball_node, size_in=dec3.shape[0]+2)
    ens = nengo.Ensemble(n_neurons=2000, dimensions=4, 
                         neuron_type=nengo.LIFRate(),
                         radius=2, seed=1,
                         label='prediction')
    conn = nengo.Connection(ens.neurons, f[:-2], transform=dec3, synapse=0)
    
    nengo.Connection(f[:4], ens, synapse=None)
    
    
    Kp = 2000
    error_goalie = nengo.Ensemble(n_neurons=100, dimensions=1)
    nengo.Connection(ens.neurons, error_goalie, transform=dec3[-2:-1,:])
    nengo.Connection(f[4], error_goalie, transform=-1)
    nengo.Connection(error_goalie, f[-2], transform=Kp)

    error_def = nengo.Ensemble(n_neurons=100, dimensions=1)
    nengo.Connection(ens.neurons, error_def, transform=dec3[-1:,:])
    nengo.Connection(f[5], error_def, transform=-1)
    nengo.Connection(error_def, f[-1], transform=Kp)
    