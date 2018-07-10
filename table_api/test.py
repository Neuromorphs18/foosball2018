import sensiball
import time

ready = False

def listener(positions):
    """
    positions = (
        pulses,  # goalie translation
        maximum_pulses, # goalie translation
        pulses, # goalie rotation
        maximum_pulses, # goalie rotation
        pulses, # defender translation
        maximum_pulses, # defender translation
        pulses, # defender rotation
        maximum_pulses, # defender rotation
        pulses, # midfield translation
        maximum_pulses, # midfield translation
        pulses, # midfield rotation
        maximum_pulses, # midfield rotation
        pulses, # forward translation
        maximum_pulses, # forward translation
        pulses, # forward rotation
        maximum_pulses, # forward rotation
    )
    For each motor, `pulses` is in the integer range [0, maximum_pulses - 1].
    For translations, `pulses == 0` means the shaft reached the inner limit,
        and `pulses == maximum_pulses - 1` means it reached the outer one.
    For rotations, `maximum_pulses` is always `980`.
        `pulses == 0` means vertical (default player position).
    """
    global ready
    ready = True
    print(positions)

sensiball.add_listener(listener)

while True:
    if ready:
        sensiball.set_speeds((255, 255, 0, 0, 0, 0, 0, 0))
        time.sleep(1.5)
        sensiball.set_speeds((-120, -120, 0, 0, 0, 0, 0, 0))
        time.sleep(1.5)
        sensiball.set_speeds((0, 0, 0, 0, 0, 0, 0, 0))
        sensiball.calibrate()
        time.sleep(5)
