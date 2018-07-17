import time
import random
import select
import sys
from sensiball import Sensiball

maxPositions = [0] * 8
def getMaxPostionHandler(v):
    for i, s in enumerate(v):
        maxPositions[i] = s[1]

sb = Sensiball()
sb.open('/dev/cu.usbmodem1411', '/dev/cu.usbmodem1421', 115200)
sb.enable_printout(True)
sb.add_handler(getMaxPostionHandler)
time.sleep(1)

# Calibrate
sb.send_calibrate()

# Slide and kick random play
while True:
    kick_select = random.randint(0,3)
    if   kick_select == 0:  sb.kick(0)
    elif kick_select == 1:  sb.kick(1)
    elif kick_select == 2:  sb.kick(2)

    if random.randint(0,1) == 1:
        sb.slide(0, random.randint(0,maxPositions[0]))
    if random.randint(0,1) == 1:
        sb.slide(1, random.randint(0,maxPositions[2]))
    if random.randint(0,1) == 1:
        sb.slide(2, random.randint(0,maxPositions[4]))

    time.sleep(0.1)