import nengo
import numpy as np

class Player(object):
    def __init__(self, x, ys, max_y, color, goal_left):
        self.x = x
        self.ys = ys
        self.max_y = max_y
        self.offset = max_y / 2
        self.radius = 18
        self.max_radius = 30
        self.color = color
        self.rotate_offset = 0
        self.goal_left = goal_left
        self.kick_deg = 40
        self.rot_velocity = 0
        self.slide_velocity = 0
        
    def slide(self, dt, velocity):
        self.slide_velocity = velocity
        self.offset = np.clip(self.offset + self.slide_velocity*dt, 0, self.max_y)
    
    def rotate(self, dt, velocity):
        self.rot_velocity = velocity 
        self.rotate_offset = (self.rotate_offset + self.rot_velocity*dt) % 360
        self.rot_off = self.rotate_offset 
        if (self.rotate_offset > 90 and self.rotate_offset < 180) or (
            self.rotate_offset > 270):
                self.rot_off = 90 - self.rotate_offset
        
    def collide(self, x, y, ball_radius=12):
        for player_y in self.ys:
            if self.rotate_offset < self.kick_deg or self.rotate_offset > 270 - self.kick_deg:
                delta_x = x - self.x
                delta_y = y - (player_y + self.offset)
                dist = np.sqrt(delta_x**2 + delta_y**2)
                if dist < (self.radius + ball_radius):
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
        
        players = ['<ellipse cx="{x}" cy="{y}" ry="{ry}" rx="{angle}" fill="{color}" fill-opacity="{opacity}"/>'.format(
            x=self.x - self.__cx_off(), y=yy+self.offset, ry=self.radius, angle=self.__rx(), color=self.color, opacity=self.__opacity()) for yy in self.ys]
        
        return '''
        <rect x="{x0}" y="0" width="{line_width}" height="{height}" fill="silver"/>
        {players}
        
        '''.format(x0=self.x-line_width/2, players=''.join(players), line_width=line_width, height=self.table.height)

class Foosball(object):
    def __init__(self):
        self.width = 800
        self.height = 400
        self.ball_radius = 12
                
        self.players = []

        self.add_player(Player(x=50, 
                           ys=[self.height/3], 
                           max_y=self.height/3,
                           color="blue", goal_left=False))
        self.add_player(Player(x=150, 
                                   ys=[0, self.height/2], 
                                   max_y=self.height/2,
                                   color="blue", goal_left=False))
        self.add_player(Player(x=350, 
                                   ys=np.linspace(0, self.height-self.height/3+25, 5), 
                                   max_y=self.height/3-25,
                                   color="blue", goal_left=False))
        self.add_player(Player(x=550, 
                                   ys=np.linspace(0, self.height-self.height/3-25, 3), 
                                   max_y=self.height/3+25,
                                   color="blue", goal_left=False))
                                   
                                   
        self.add_player(Player(x=750, 
                                   ys=[self.height/3], 
                                   max_y=self.height/3,
                                   color="yellow", goal_left=True))
        self.add_player(Player(x=800-150, 
                                   ys=[0, self.height/2], 
                                   max_y=self.height/2,
                                   color="yellow", goal_left=True))
        self.add_player(Player(x=800-350, 
                                   ys=np.linspace(0, self.height-self.height/3+25, 5), 
                                   max_y=self.height/3-25,
                                   color="yellow", goal_left=True))
        self.add_player(Player(x=800-550, 
                                   ys=np.linspace(0, self.height-self.height/3-25, 3), 
                                   max_y=self.height/3+25,
                                   color="yellow", goal_left=True))

        self.reset()

    def add_player(self, player):
        player.table = self
        self.players.append(player)
        
    def reset(self):
        self.reset_table()
        self.score = np.zeros(2)

    def reset_table(self):
        self.ball_pos = np.array([self.width/2, self.height/2])
        self.ball_vel = np.random.uniform(-10, 10, 2) # ball velocity at reset
        for p in self.players:
            p.offset = 0
            p.slide_velocity = 0
            p.rotate_offset = 0 
            p.rot_velocity = 0

        
    def update(self, dt, slide):
        self.ball_pos += self.ball_vel*dt  
        
        if self.ball_pos[0]-self.ball_radius < 0 and self.height/3 < self.ball_pos[1] < 2*self.height/3:
            self.score[1] += 1
            print("goal yellow")
            self.reset_table()
        if self.ball_pos[0]+self.ball_radius > self.width and self.height/3 < self.ball_pos[1] < 2*self.height/3:
            self.score[0] += 1
            print("goal blue")
            self.reset_table()
        
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
            cx, cy = p.collide(self.ball_pos[0], self.ball_pos[1], ball_radius=self.ball_radius)
            self.ball_pos += [cx, cy]
            new_v = np.array([cx, cy])
            v_norm = np.linalg.norm(new_v)
            if v_norm > 0:
                mag = np.linalg.norm(self.ball_vel)
                self.ball_vel = mag * new_v / v_norm + p.rot_velocity
        
    def svg(self):

        template = '''<svg width="100%" height="100%" viewbox="0 0 {width} {height}">

        <rect x="0" y="0" height="{height}" width="{width}" fill="green"/>
        <rect x="0" y="{goal_height}" height="{goal_height}" width="10" fill="blue"/>
        <rect x="{goal2width}" y="{goal_height}" height="{goal_height}" width="10" fill="yellow"/>

        {players}

        <circle cx="{bx}" cy="{by}" fill="white" r="{ball_radius}" />
        <text x="10" y="100" style="font:bold 80px sans-serif">{score0}</text>
        <text x="{score2width}" y="100" style="font:bold 80px sans-serif">{score1}</text>

        </svg>'''.format(width=self.width, height=self.height, 
                         bx=self.ball_pos[0], by=self.ball_pos[1], 
                         ball_radius=self.ball_radius,
                         goal2width=self.width-10,
                         score2width=self.width-100,
                         score0=int(self.score[0]),
                         score1=int(self.score[1]),
                         players=''.join([p.svg() for p in self.players]),
                         goal_height=self.height/3)

        return template
        
    def get_state(self):
        # b = blue, y = yellow, s = slide, r = rotate
        """ action_vector = [   
            ball_pos_x, ball_velocity_x, 
            ball_pos_y, ball_veolcity_y

             b_s_goalie_pos, b_s_goalie_vel,
             b_r_goalie_pos, b_r_goalie_vel,
             b_s_defenders_pos, b_s_defenders_vel,
             b_r_defenders_pos, b_r_defenders_vel,             
             b_s_midfield_pos, b_s_midfield_vel,
             b_r_midfield_pos, b_r_midfield_vel,             
             b_s_strikers_pos, b_s_strikers_vel,
             b_r_strikers_pos, b_r_strikers_vel,

            + REPEAT for yellows
             
        ]"""

        return np.concatenate([[self.ball_pos[0], self.ball_vel[0], self.ball_pos[1], self.ball_vel[1]],
            np.array([[p.offset, p.slide_velocity, p.rotate_offset, p.rot_velocity] for p in self.players]).flatten()
        ])
        
    def step(self, action_vector):
       
        self.update(0.01, action_vector)
        
        return self.get_state(), self.score, max(self.score) >= 10

"""
if __name__ == "__main__":
    f = Foosball()
    f.update(0.01, np.ones(16))
"""
