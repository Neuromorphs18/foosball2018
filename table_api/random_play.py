import time
import random
import select
import sys
from sensiball import Sensiball

sb = Sensiball()
sb.open('/dev/cu.usbmodem1411', '/dev/cu.usbmodem1421', 115200)
#sb.open(None, '/dev/cu.usbmodem1421', 115200)
sb.enable_printout(True)
time.sleep(1)

# Calibrate
#sb.send_calibrate()

sb.send_kick(0)
time.sleep(1)
sb.send_kick(1)
time.sleep(1)
sb.send_kick(2)
time.sleep(5)

exit()


# Slide and kick random play
slide_goalie    = 0
slide_defender  = 0
slide_midfield  = 0

while True:
    kick_select = random.randint(0,3)

    # Kick
    if kick_select == 1:
        sb.send_speeds([0,-110,0,0,0,0,0,0])
        time.sleep(0.2)
        sb.send_speeds([0,255,0,0,0,0,0,0])
        time.sleep(0.1)
        sb.send_speeds([0,0,0,0,0,0,0,0])
    elif kick_select == 2:
        sb.send_speeds([0,0,0,-110,0,0,0,0])
        time.sleep(0.2)
        sb.send_speeds([0,0,0,255,0,0,0,0])
        time.sleep(0.1)
        sb.send_speeds([0,0,0,0,0,0,0,0])
    elif kick_select == 3:
        sb.send_speeds([0,0,0,0,0,-110,0,0])
        time.sleep(0.2)
        sb.send_speeds([0,0,0,0,0,255,0,0])
        time.sleep(0.1)
        sb.send_speeds([0,0,0,0,0,0,0,0])

    if random.randint(0,1) == 1:
        slide_goalie    = random.randint(-255,255)
    else:
        slide_goalie    = 0

    if random.randint(0,1) == 1:
        slide_defender  = random.randint(-255,255)
    else:
        slide_defender  = 0  

    if random.randint(0,1) == 1:
        slide_midfield  = random.randint(-255,255)
    else:
        slide_midfield  = 0  
    
    sb.send_speeds([slide_goalie,0,slide_defender,0,slide_midfield,0,0,0])
    time.sleep(0.1)
