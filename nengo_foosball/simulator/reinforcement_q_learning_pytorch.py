import math
import random
import pickle
import numpy as np
from collections import namedtuple
from itertools import count

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision.transforms as T

from environment import Foosball

assert torch.__version__ == '0.4.0'


env = Foosball()

# if gpu is to be used
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

Transition = namedtuple('Transition',
                        ('state', 'blue_action', 'yellow_action', 'next_state', 'blue_reward', 'yellow_reward'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        """Saves a transition."""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

class DQN_blue(nn.Module):
    def __init__(self):
        super(DQN_blue, self).__init__()
        self.l1 = nn.Linear(36, 1000)
        self.l2 = nn.Linear(1000, 500)
        self.head = nn.Linear(500, 8*2)

    def forward(self, x):
        x = F.relu(self.l1(x))
        x = F.relu(self.l2(x))
        return self.head(x)

class DQN_yellow(nn.Module):
    def __init__(self):
        super(DQN_yellow, self).__init__()
        self.l1 = nn.Linear(36, 250)
        self.head = nn.Linear(250, 8*2)

    def forward(self, x):
        x = F.relu(self.l1(x))
        return self.head(x)

env.reset()

BATCH_SIZE = 128
GAMMA = 0.999
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 200
TARGET_UPDATE = 10

blue_policy_net = DQN_blue().to(device)
blue_target_net = DQN_blue().to(device)
blue_target_net.load_state_dict(blue_policy_net.state_dict())
blue_target_net.eval()

yellow_policy_net = DQN_yellow().to(device)
yellow_target_net = DQN_yellow().to(device)
yellow_target_net.load_state_dict(yellow_policy_net.state_dict())
yellow_target_net.eval()

blue_optimizer = optim.RMSprop(blue_policy_net.parameters())
yellow_optimizer = optim.RMSprop(yellow_policy_net.parameters())

memory = ReplayMemory(10000)

steps_done = 0

def select_action(state, model):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            return model(torch.Tensor(state, device=device)).max(0)[1].view(1, 1)
    else:
        return torch.tensor([[random.randrange(16)]], device=device, dtype=torch.long)


def optimize_model(color):
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see http://stackoverflow.com/a/19343/3343043 for
    # detailed explanation).
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                          batch.next_state)), device=device, dtype=torch.uint8)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                                if s is not None])
    state_batch = torch.cat(batch.state)

    if color == "yellow":
        action_batch = torch.cat(batch.yellow_action)
        reward_batch = torch.cat(batch.yellow_reward)
        policy_net = yellow_policy_net
        optimizer = yellow_optimizer
        target_net = yellow_target_net
    elif color == "blue":
        action_batch = torch.cat(batch.blue_action)
        reward_batch = torch.cat(batch.blue_reward)
        policy_net = blue_policy_net
        optimizer = blue_optimizer
        target_net = blue_target_net


    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken

    state_action_values = policy_net(state_batch).gather(1, action_batch) #MRED

    # Compute V(s_{t+1}) for all next states.
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0].detach() #MRED
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    for param in policy_net.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()


num_episodes = 50
episode_durations = []
for i_episode in range(num_episodes):
    # Initialize the environment and state
    env.reset()
    
    state = env.get_state() / 1000 # scale by 1000 for NN

    all_actions = []

    for t in count():
        # Select and perform an action
        b_action = select_action(state, blue_policy_net)
        y_action = select_action(state, yellow_policy_net)

        action = np.zeros(16)

        b, y = int(b_action[0][0]), int(y_action[0][0])

        unit = 100

        if b_action % 2 != 0:
            # convert to negative
            action[(b - 1)//2] = -unit
        else:
            action[b//2] = unit

        if y_action % 2 != 0:
            # convert to negative
            action[8 + (y - 1)//2] = -unit
        else:
            action[8 + y//2] = unit

        all_actions.append(np.round(action))
        next_state, reward, done = env.step(action)
        next_state /= 1000

        # Store the transition in memory
        memory.push(torch.Tensor(state, device=device).unsqueeze(0), 
            b_action, y_action, 
            torch.Tensor(next_state, device=device).unsqueeze(0), 
            torch.Tensor([reward[0]], device=device),  
            torch.Tensor([reward[1]], device=device)
        )

        # Move to the next state
        state = next_state

        # Perform one step of the optimization (on the target network)
        optimize_model("yellow")
        optimize_model("blue")

        if done:
            episode_durations.append(t + 1)
            print("episode {}, score [B,Y] {}, dur {}".format(i_episode, reward, episode_durations[-1]))
            pickle.dump(np.array(all_actions), open("episode_{}_[B,Y] {}.p".format(i_episode, reward), "wb"))
            break

    # Update the target network
    if i_episode % TARGET_UPDATE == 0:
        yellow_target_net.load_state_dict(yellow_policy_net.state_dict())
        blue_target_net.load_state_dict(blue_policy_net.state_dict())

print('Complete')

