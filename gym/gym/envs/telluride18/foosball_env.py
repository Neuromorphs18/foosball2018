#!/bin/python
#-----------------------------------------------------------------------------
# File Name : foosball_env.py
# Author: Emre Neftci
#
# Creation Date : Mon 09 Jul 2018 09:30:03 PM MDT
# Last Modified : 
#
# Copyright : (c) UC Regents, Emre Neftci
# Licence : GPLv2
#----------------------------------------------------------------------------- 
import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
from .foosball_standalone import Player, Foosball

class Foosball2(Foosball):
    def __init__(self, *args, **kwargs):
        super(Foosball2, self).__init__(*args, **kwargs)
        self.done = 0

    @property
    def diffscore(self):
        return int(np.diff(self.score))

    def get_players_state(self):
        return [np.array([p.offset, p.rotate_offset]) for p in self.players]

    def get_ball_state(self):
        return self.ball_pos

    def get_state(self):
        pstate = self.get_players_state()
        bstate = self.get_ball_state()
        return  [bstate]+pstate

    def get_state_flat(self):
        pstate = np.array(self.get_players_state()).flatten()
        bstate = self.get_ball_state()
        return  np.concatenate([bstate,pstate])
        
    def act(self, time, action_vector):
        reward = self.step(time, action_vector)
        return self.get_state_flat(), reward, self.done

SLIMIN = -1
SLIMAX = +1
ROTMIN = -1
ROTMAX = +1

class FoosballEnv(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, dt=1e-2):
    self.reset()
    self.time = 0
    self.dt = dt
    self.build_action_obs_space()

  def build_action_obs_space(self): 
    self.action_space = spaces.Discrete(32)
    W = self.foosball.width
    H = self.foosball.height
    self.observation_space = spaces.Box(low=np.zeros(18),high=H+np.zeros(18))

  def get_observation(self):
    obs = self.foosball.get_state_flat()
    return obs

  def decode_discrete_action(self, action):
      action_decoded = np.zeros([16])
      action_decoded[int(action//2)] = 1 - 2*(action%2)
      return action_decoded
    
  def step(self, action):
    action_decoded = self.decode_discrete_action(action)
    state, score, done = self.foosball.act(self.time, action_decoded)
    self.time += self.dt
    return state, score, done, {} 

  def reset(self):
    self.foosball = foosball = Foosball2()
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
    return self.get_observation()

  def seed(self, seed=None):
      return [seed]

  def render(self, mode='human', close=False):
      self.foosball.svg()

class FoosballEnvContinuous(FoosballEnv):
  def build_action_obs_space(self): 
    self.action_space = spaces.Tuple((spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=SLIMIN, high=SLIMAX, shape=[1,], dtype='int'),
                                      spaces.Box(low=ROTMIN, high=ROTMAX, shape=[1,], dtype='int')
                                      ))
    W = self.foosball.width
    H = self.foosball.height
    self.observation_space = spaces.Tuple((
        spaces.Box(low=np.array([0,0]), high=np.array([W, H]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        spaces.Box(low=np.array([0,0]), high=np.array([0, 360]), dtype='float32'),
        ))

#if __name__ == '__main__':
#    print('starting run')
#    import time
#    dt = 1e-2
#    t = 0
#    for i in range(10000):
#        print(foosball.get_state())
#        frame, state = foosball_node(t, [0]*16)
#        with open('foos.svg', 'w') as f:
#            f.write(frame)
#        time.sleep(1e-2)
#        t += dt
