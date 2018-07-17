import math
import random
import pickle
import numpy as np
from collections import namedtuple
from itertools import count

import pygame
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import itertools

from environment import Foosball

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

class DQN_yellow(nn.Module):
    def __init__(self):
        super(DQN_yellow, self).__init__()
        self.l1 = nn.Linear(6, 250)
        self.l2 = nn.Linear(250, 250)
        """self.goalie = nn.Linear(250, 4)
        self.defend = nn.Linear(250, 4)
        self.midfield = nn.Linear(250, 4)
        self.striker = nn.Linear(250, 4)
        """
        self.head = nn.Linear(250, len(ACTIONS))

    def forward(self, x):
        x = F.relu(self.l1(x))
        x = F.relu(self.l2(x))
        return self.head(x) #self.goalie(x), self.defend(x), self.midfield(x), self.striker(x)

def select_action(state, model):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        inp = torch.Tensor(state, device=device)
        if torch.cuda.is_available():
            inp = inp.cuda()
        with torch.no_grad():
            return F.softmax(model(inp).unsqueeze(0)).max(1)[0]
    else:
        return torch.tensor([[random.randrange(len(ACTIONS))]], device=device, dtype=torch.long)


def optimize_model(color):
    memory = blue_memory if color == "blue" else yellow_memory

    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see http://stackoverflow.com/a/19343/3343043 for
    # detailed explanation).
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                          batch.next_state)), device=device, dtype=torch.uint8).to(device)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                                if s is not None]).to(device)
    state_batch = torch.cat(batch.state).to(device)

    if color == "yellow":
        policy_net = yellow_policy_net
        optimizer = yellow_optimizer
        target_net = yellow_target_net

    action_batch = torch.cat(batch.action).to(device)
    reward_batch = torch.cat(batch.reward).to(device)

    state_action_values = policy_net(state_batch).gather(1, action_batch) #MRED

    next_state_values = torch.zeros(BATCH_SIZE, device=device)

    next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0].detach() #MRED

    expected_state_action_values = (next_state_values * GAMMA) + reward_batch
    
    loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    for param in policy_net.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()


if __name__ == "__main__":
    draw = False

    env = Foosball(display=draw)

    # if gpu is to be used
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    Transition = namedtuple('Transition',
                            ('state', 'action', 'next_state', 'reward'))
    env.reset()

    BATCH_SIZE = 128
    GAMMA = 0.999
    EPS_START = 0.9
    EPS_END = 0.05
    EPS_DECAY = 200
    TARGET_UPDATE = 10

    ACTIONS = [
        [1, 0, 0, 0],
        [2, 0, 0, 0],
        [3, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 2, 0, 0],
        [0, 3, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 2, 0],
        [0, 0, 3, 0],
        [0, 0, 0, 1],
        [0, 0, 0, 2],
        [0, 0, 0, 3],
        [0, 0, 0, 0],
    ]

    [torch.Tensor(x, device=device) for x in ACTIONS]

    yellow_policy_net = DQN_yellow().to(device)
    yellow_target_net = DQN_yellow().to(device)
    yellow_target_net.load_state_dict(yellow_policy_net.state_dict())
    yellow_target_net.eval()

    yellow_optimizer = optim.RMSprop(yellow_policy_net.parameters())

    yellow_memory = ReplayMemory(10000)

    steps_done = 0

    yellow_policy_net = yellow_policy_net
    yellow_target_net = yellow_target_net

    num_episodes = 150
    episode_durations = []

    wins = [0,0]

    for i_episode in range(num_episodes):
        # Initialize the environment and state
        env.reset()

        state = env.get_state()

        state = state / 1000 # scale by 1000 for NN

        for t in count():
            # Select and perform an action

            print(select_action(state, yellow_policy_net))
            act_int = select_action(state, yellow_policy_net)
            action = ACTIONS[int(act_int.squeeze().item())]

            next_state, yreward, done, score = env.step(action)

            next_state /= 1000

            print(torch.Tensor([action], device=device).long())

            yellow_memory.push(
                torch.Tensor(state, device=device).unsqueeze(0),
                torch.Tensor([act_int], device=device).long().unsqueeze(0),
                torch.Tensor(next_state, device=device).unsqueeze(0),
                torch.Tensor([yreward], device=device)
            )

            # Move to the next state
            state = next_state

            if draw and t % 10 == 0:
                env.draw()

            # Perform one step of the optimization (on the target network)
            optimize_model("yellow")

            if done:
                if score[0] > score[1]:
                    wins[0] += 1
                else:
                    wins[1] += 1
                episode_durations.append(t + 1)
                print("episode {}, score [B,Y] {}, dur {}".format(i_episode, reward, episode_durations[-1]))
                break

        # Update the target network
        if i_episode % TARGET_UPDATE == 0:
            episode_durations.append(t + 1)
            print("episode {}, score [B,Y] {}, dur {}".format(i_episode, reward, episode_durations[-1]))
            yellow_target_net.load_state_dict(yellow_policy_net.state_dict())
            torch.save(yellow_target_net, "yellow.pt")


        if sum(wins) > 20 and wins[1] / sum(wins) > 0.95:
            print("Yellow wins 95% of the time, saving model and stopping training...")
            break

    torch.save(yellow_target_net, "yellow.pt")

    print('Complete')



