import sys
sys.path.insert(0, '..')
from sensiball import Sensiball
import time

sensiball = Sensiball()
sensiball.open('/dev/cu.usbmodemFD121', '/dev/cu.usbmodemFA131', 115200)
time.sleep(1)
sensiball.send_calibrate()
