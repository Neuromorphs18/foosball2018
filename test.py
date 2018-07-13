import time
from sensiball import Sensiball

def myHandlerFunc(pos):
    print(pos)

sb = Sensiball()
sb.open('/dev/cu.usbmodem1411', 115200)
#sb.add_handler(myFunc)
sb.enable_printout(True)

# Calibrate
time.sleep(2)
sb.send_calibrate()

sb.send_speeds([50,150,0,0,0,0,0,0])
time.sleep(1)

sb.send_speeds([0,0,50,150,0,0,0,0])
time.sleep(1)

sb.send_speeds([0,0,0,0,50,150,0,0])
time.sleep(1)

sb.send_speeds([-50,-150,0,0,0,0,0,0])
time.sleep(1)

sb.send_speeds([0,0,-50,-150,0,0,0,0])
time.sleep(1)

sb.send_speeds([0,0,0,0,-50,-150,0,0])
time.sleep(1)

sb.send_halt()
