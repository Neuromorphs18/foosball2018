import time
import random
import select
import sys
from sensiball import Sensiball
import redis
import numpy as np

database = redis.StrictRedis("192.168.0.150")
database.set("pos", "0;0")
database.set("vel", "0;0")

kick_range = 10

# in = towards machine
yranges = [
    # in, out 
    [(104, 61)], #goal
    [(147, 79), (81, 21)], # def
    [(147, 117), (122, 91), (96, 66), (70, 42), (46, 17)], #mid
    [(147, 102), (104, 59), (61,19)] #str
]

height = 150
width = 240

xpos = [
    228, #goal
    197, #def 
    140, #mid
    73, #str
]

curPositions = [0] * 8
maxPositions = [0] * 8
ppps = [0] * len(yranges)

def getMaxPostionHandler(v):
    for i, s in enumerate(v):
        curPositions[i] = s[0]
        maxPositions[i] = s[1]
        if i < 4:
            ppps[i] = maxPositions[i] / (yranges[i][0][0] - yranges[i][0][1])


tableSize = 0

a = "/dev/cu.usbmodem142121"
b = "/dev/cu.usbmodem142131"
sb = Sensiball()
sb.open(a, b, 115200)
#sb.enable_printout(True)
sb.add_handler(getMaxPostionHandler)
time.sleep(1)

# Calibrate
sb.send_calibrate()

def get_row(bx):
    distances = [(r - float(bx)) for r in xpos if (r - float(bx)) > 0]
    if not(len(distances)):
        return None
    return distances.index(min(distances))

def get_player(row, by):
    for i, p in enumerate(yranges[row]):
        if by >= p[1] and by <= p[0]:
            return i
    else:
        if by >= yranges[row][0][0]:
            return 0
        else:
            return len(yranges[row])-1


def move(row, player, by):
    sb.slide(row, round((maxPositions[row] - ppps[row])*float(by)))

def kick(i, bx):
    if 0 < float(r - bx) < 5:
        sb.kick(i)

# while True:
#     ball_x, ball_y = database.get('pos').decode('utf-8').split(";")
#     vx, vy = database.get('vel').decode('utf-8').split(";")
#     pred_x, pred_y = float(ball_x) + float(vx), float(ball_y) + float(vy)
#     row = get_row(pred_x)
#     print(row)
#     if (row is not None) and row == 0:
#         player = get_player(row, pred_y)
#         print("---p", player)
#         move(row, player, pred_y)
#         if row < 3:
#             sb.kick(row)
#     time.sleep(0.1)

while True:
    ball_x, ball_y = database.get('pos').decode('utf-8').split(";")
    ball_x = float(ball_x)
    ball_y = float(ball_y)
    vx, vy = database.get('vel').decode('utf-8').split(";")
    print(vx, vy, ball_x, ball_y)
    pred_x, pred_y = float(ball_x) + 10*float(vx), float(ball_y) + 10*float(vy)
 
    ppp = maxPositions[0] / (yranges[0][0][0] - yranges[0][0][1])
    sb.slide(0, round((maxPositions[0] - ppp)*float(ball_y)))

    if ball_x < xpos[0] and (xpos[0] - ball_x) < 10:
        sb.kick(0)

    time.sleep(0.01)

