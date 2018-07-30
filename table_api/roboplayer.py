import random
import select
import sys
import time
from sensiball import Sensiball

###############################################################################
# Configuration
###############################################################################
TABLE_HEIGHT        = 150
TABLE_WIDTH         = 240
MIN_KICK_DISTANCE   = 5

# Player positions/ranges, in pixels.
PLAYER_X = [
    228,    # Goalie
    197,    # Defence 
    140,    # Midfield
    73      # Forward
]

PLAYER_Y = [
    [(104, 61)],                                            # Goalie
    [(147, 79), (81, 21)],                                  # Defence
    [(147, 117), (122, 91), (96, 66), (70, 42), (46, 17)],  # Midfield
    [(147, 102), (104, 59), (61,19)]                        # Forward
]

# Increment distance that each row slide when using the move command. Values
# are given as a percentage. 100% would be a complete movement across the
# width of the table.
MOVE_DISTANCE = [
    5.0,       # Goalie
    4.0,       # Defence
    9.0,       # Midfield
    10.0       # Forward
]

# Increment distance used when the slide direction has changed in a row.
# A greater slide distance is required when changing direction as the string
# is loose and the first bit of movement will take up any slack.
MOVE_DISTANCE_DIR_CHANGE = [
    12.0,       # Goalie
     6.0,       # Defenders
    17.0,       # Midfield
    15.0        # Forward
]

###############################################################################
# RoboPlayer Class
###############################################################################
class RoboPlayer:
    def __init__(self, serialPortBack=None, serialPortFront=None):
        self.sb = Sensiball()
        self.sb.open(serialPortBack, serialPortFront, 115200)
        self.curPositions   = [0] * 8
        self.maxPositions   = [0] * 8
        self.pulsePerPixel  = [0] * 4
        self.lastDirection  = [0] * 4
        def _updatePostions(v):
            for i, s in enumerate(v):
                self.curPositions[i] = s[0]
                self.maxPositions[i] = s[1]
                if i % 2 == 0:
                    self.pulsePerPixel[i//2] = self.maxPositions[i] / (PLAYER_Y[i//2][0][0] - PLAYER_Y[i//2][0][1])
        self.sb.add_handler(_updatePostions)
        time.sleep(1)
        self.sb.calibrate()
   
    def getCurrentPosition(self):
        """
        Return a vector of current positions of the sliders, given as percentage moved from the
        outer side of the table (the side that doesn't have the machinery).
        Vector is organised as [Goalie, Defenders, Midfield, Forwards]
        """
        pos = [ 0.0 if self.maxPositions[0] == 0 else (self.maxPositions[0] - self.curPositions[0])/self.maxPositions[0],
                0.0 if self.maxPositions[2] == 0 else (self.maxPositions[2] - self.curPositions[2])/self.maxPositions[2],
                0.0 if self.maxPositions[4] == 0 else (self.maxPositions[4] - self.curPositions[4])/self.maxPositions[4],
                0.0 if self.maxPositions[6] == 0 else (self.maxPositions[6] - self.curPositions[6])/self.maxPositions[5]]
        pos = [p if p <= 100.0 else 100.0 for p in pos]
        pos = [p if p >=   0.0 else   0.0 for p in pos]
        return pos

    def move(self, val):
        """
        Send movement commands for each player. Options are: 
            0   Still
            1   Move In (towards the machinery)
            2   Move Out
            3   Kick
        Vector is organised as [Goalie, Defenders, Midfield, Forwards]
        """
        if len(val) != 4:
            raise ValueError('Invalid vector specified for move')
        for i,v in enumerate(val):
            if v in [1,2]:
                if self.lastDirection[i] != v:
                    moveInc = self.maxPositions[i*2] * (MOVE_DISTANCE_DIR_CHANGE[i] / 100.0)
                    self.lastDirection[i] = v
                else:
                    moveInc = self.maxPositions[i*2] * (MOVE_DISTANCE[i] / 100.0)

            if v == 1:
                pos = round(self.curPositions[i*2] - moveInc)
                pos = pos if pos > 0 else 0
                self.sb.slide(i, pos)
            elif v == 2:
                pos = round(self.curPositions[i*2] + moveInc)
                pos = pos if pos < self.maxPositions[i*2] else self.maxPositions[i*2]
                self.sb.slide(i, pos)
            elif v == 3:
                self.sb.kick(i)

    def rule_player(self, pos_x, pos_y):
        """
        Update the table with the current ball position and perform a rule-based play.
        pos_x, pos_y - The current ball position
        """
        row = self._get_row(pos_x)
        if row:
            player = self._get_player(row, pos_y)
            pixDist = TABLE_HEIGHT - (pos_y - PLAYER_Y[row][player][1])
            self.sb.slide(row, round(self.pulsePerPixel[row] * pixDist))
            if (row < 3) and ((PLAYER_X[row] - pos_x) > MIN_KICK_DISTANCE):
                self.sb.kick(row)
        
    def _get_row(self, pos_x):
        """
        Find the row that is closest to the current x ball position. The row must also
        be located behind the ball.
        Returns:
            None    Ball is behind Goalie
            0       Goalie
            1       Defence
            2       Midfield
            3       Forward
        """
        distances = [(r - float(pos_x)) for r in PLAYER_X if (r - float(pos_x)) > 0]
        if len(distances) == 0:
            return None
        else:
            return distances.index(min(distances))

    def _get_player(self, row, pos_y):
        """
        Get the player in given row that is closest the current y ball position.
        """
        minDist = 1000
        minIdx  = None
        for i, p in enumerate(PLAYER_Y[row]):
            avg = (p[0] + p[2]) / 2.0
            dst = abs(avg - pos_y)
            if dst < minDist:
                minDist = dst
                minIdx = i
        return minIdx

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
def getMaxPostionHandler(v):
    for i, s in enumerate(v):
        curPositions[i] = s[0]
        maxPositions[i] = s[1]
sb.add_handler(getMaxPostionHandler)

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

# 
def move(val):
    currPositions

while True:
    pulsesPerPixelGoalie    = maxPositions[0] / (TABLE_Y_MAX - TABLE_Y_MIN)
    pulsesPerPixelDefender  = maxPositions[2] / (TABLE_Y_MAX - TABLE_Y_MIN)
    pulsesPerPixelMidfield  = maxPositions[4] / (TABLE_Y_MAX - TABLE_Y_MIN)

    #p = get_pos()
    p = [random.randint(0, 140), random.randint(-70, 70)]
    px = p[0]
    py = p[1] + -TABLE_Y_MIN

    pulseGoalie = py * pulsesPerPixelGoalie
    pulseGoalie = pulseGoalie if pulseGoalie < maxPositions[0] else maxPositions[0]
    pulseGoalie = pulseGoalie if pulseGoalie > 0 else 0
    sb.slide(0, round(pulseGoalie))

    print(p[1])
    print(pulseGoalie)

    time.sleep(2)
