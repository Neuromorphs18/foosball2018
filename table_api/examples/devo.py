sys.path.insert(0, '..')
from sensiball import Sensiball
import time
import sys
import pyglet

next_song = False
beat = 3 # times 50 ms
gains = (300, 500) * 4
max_speeds = (200, 255) * 4
song_started = False

def clamp(minimum, value, maximum):
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value

def cut(minimum, value, maximum):
    if value > minimum and value < maximum:
        return 0
    return value

def target_positions_at_t(t):
    global next_song
    global song_started
    translation_program = '>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|>||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||<<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<'
    rotation_program = 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv'
    t_modulus = int(t / beat) % len(translation_program)
    if t_modulus == 0 and not song_started:
        next_song = True
        song_started = True
    if t_modulus > 0:
        song_started = False
    translation_code = translation_program[t_modulus]
    rotation_code = rotation_program[t_modulus]
    translation = 0.85
    if translation_code == '>':
        translation = 0.15
    elif translation_code == '|':
        translation = 0.5
    rotation = 0
    if rotation_code == '/':
        rotation = 0.7
    elif rotation_code == '|':
        rotation = 0.3
    return (translation, rotation) * 4

class Handler(object):
    def __init__(self):
        self.t = 0

    def __call__(self, positions):
        self.t += 1
        positions = tuple(float(positions[index * 2]) / float(positions[index * 2 + 1]) for index in range(0, 8))
        target_positions = target_positions_at_t(self.t)
        speeds = tuple(
            cut(-50, clamp(-max_speed, int(gain * (target_position - position)), max_speed), 50)
            for gain, max_speed, position, target_position in zip(gains, max_speeds, positions, target_positions))
        table.set_speeds(speeds)

sb = Sensiball(device='/dev/cu.usbmodemFA131')
table.add_handler(Handler())

time.sleep(2)
sb.send_calibrate()

player = pyglet.media.Player()
while True:
    pyglet.clock.tick()
    if next_song:
        player.next_source()
        player.queue(pyglet.media.load('devo_loop.wav'))
        player.play()
        next_song = False
    for window in pyglet.app.windows:
        window.switch_to()
        window.dispatch_events()
        window.dispatch_event('on_draw')
        window.flip()
