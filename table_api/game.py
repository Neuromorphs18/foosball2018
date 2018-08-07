import redis
import time
from roboplayer import RoboPlayer

# Setup RoboCop
sp1 = "/dev/cu.usbmodem142121"
sp2 = "/dev/cu.usbmodem142131"
rp = RoboPlayer(sp1, sp2)

# Setup Redis
database = redis.StrictRedis("192.168.0.150")
database.set("pos", "0;0")
database.set("vel", "0;0")

while True:
    xpos, ypos = database.get('pos').decode('utf-8').split(";")
    xpos = float(xpos)
    ypos = float(ypos)

    rp.rule_player(xpos, ypos)
    time.sleep(0.05)
