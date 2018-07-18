import time
import random
import redis
import select
import sys
from sensiball import Sensiball

# Move increments, given a percentage, 100% would be a complete movement
# across the width of the table.
MOVE_DISTANCE = [
    5.0,       # Goalie
    4.0,       # Defenders
    9.0,       # Midfield
    10.0        # Forward
]

# Move a bit greater when changing direction as string is loose.
MOVE_DISTANCE_CHANGE = [
    12.0,       # Goalie
     6.0,       # Defenders
    17.0,       # Midfield
    15.0        # Forward
]

# # Setup redis
# db = redis.StrictRedis("10.162.177.1")
# db.set('pos', '0;0')
# db.set('vel', '0;0')

# def get_pos():
#     pos = db.get('pos').decode('utf-8').split(';')
#     return [float(e) for e in pos]

# def get_vel():
#     vel = db.get('vel').decode('utf-8').split(';')
#     return [float(e) for e in vel]

###############################################################################
# Setup Sensiball
###############################################################################
sb = Sensiball()
sb.open('/dev/cu.usbmodem1411', '/dev/cu.usbmodem1421', 115200)
#sb.enable_printout(True)

# Handler that gets called approx every 10 ms to get latest positions from
# table.
curPositions = [0] * 8
maxPositions = [0] * 8
def getPostionsHandler(v):
    for i, s in enumerate(v):
        curPositions[i] = s[0]
        maxPositions[i] = s[1]
sb.add_handler(getPostionsHandler)

# Calibrate
time.sleep(1)
sb.send_calibrate()

# Return a vector of current positions given as percentage moved from the
# inner side of the table (the side that has the machinery).
# Vector is organised as [Goalie, Defenders, Midfield, Forwards]
def getCurrentPosition():
    return [0.0 if maxPositions[0] == 0 else curPositions[0]/maxPositions[0],
            0.0 if maxPositions[1] == 0 else curPositions[1]/maxPositions[1],
            0.0 if maxPositions[2] == 0 else curPositions[2]/maxPositions[2],
            0.0 if maxPositions[3] == 0 else curPositions[3]/maxPositions[3]]

# Movement commands for each player.
# Options are: 
#   0   Still
#   1   Move In (towards the machinery)
#   2   Move Out
#   3   Kick
# Vector is organised as [Goalie, Defenders, Midfield, Forwards]
lastDirection = [0, 0, 0, 0]
def move(val):
    if len(val) != 4:
        raise ValueError('Invalid vector specified for move')
    for i,v in enumerate(val):
        if v in [1,2]:
            if lastDirection[i] != v:
                moveInc = maxPositions[i*2] * (MOVE_DISTANCE_CHANGE[i] / 100.0)
                lastDirection[i] = v
            else:
                moveInc = maxPositions[i*2] * (MOVE_DISTANCE[i] / 100.0)

        if v == 1:
            pos = round(curPositions[i*2] - moveInc)
            pos = pos if pos > 0 else 0
            sb.slide(i, pos)
        elif v == 2:
            pos = round(curPositions[i*2] + moveInc)
            pos = pos if pos < maxPositions[i*2] else maxPositions[i*2]
            sb.slide(i, pos)
        elif v == 3:
            sb.kick(i)

