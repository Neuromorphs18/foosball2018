import sys
sys.path.insert(0, '..')
from sensiball import Sensiball
import pyglet
import threading
import time
import timeit

next_song = True
beat = 0.15
song_started = False

def target_positions_at_index(index):
    global next_song
    global song_started
    translation_program = '>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<>><<>>|>||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||<<>><<|<>><<>>|><<>><<|<>><<>>|><<>><<|<'
    rotation_program = 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|/|vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv'
    index_modulus = index % len(translation_program)
    if index_modulus == 0 and not song_started:
        next_song = True
        song_started = True
    if index_modulus > 0:
        song_started = False
    translation_code = translation_program[index_modulus]
    rotation_code = rotation_program[index_modulus]
    translation = 0.85
    if translation_code == '>':
        translation = 0.15
    elif translation_code == '|':
        translation = 0.5
    rotation = 0
    if rotation_code == '/':
        rotation = -0.75
    elif rotation_code == '|':
        rotation = 0.75
    return (translation, rotation) * 4

maxima = (0,) * 8
def handle_positions_and_maxima(positions_and_maxima):
    global maxima
    maxima = tuple(position_and_maximum[1] for position_and_maximum in positions_and_maxima)

sensiball = Sensiball()
sensiball.open('/dev/cu.usbmodemFD121', '/dev/cu.usbmodemFA131', 115200)
sensiball.add_handler(handle_positions_and_maxima)
time.sleep(1)
#sensiball.send_calibrate()

def dance():
    begin = timeit.default_timer()
    index = 0
    while True:
        now = timeit.default_timer()
        if now - begin > index * beat:
            target_positions = target_positions_at_index(index)
            sensiball.slide(0, int(target_positions[0] * maxima[0]))
            sensiball.slide(1, int(target_positions[2] * maxima[2]))
            sensiball.slide(2, int(target_positions[4] * maxima[4]))
            sensiball.rotate(0, int(target_positions[1] * maxima[1]))
            sensiball.rotate(1, int(target_positions[3] * maxima[3]))
            sensiball.rotate(2, int(target_positions[5] * maxima[5]))
            index += 1
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            time.sleep(0.01)
dance_thread = threading.Thread(target=dance)
dance_thread.daemon = True
dance_started = False

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
    if not dance_started:
        dance_started = True
        dance_thread.start()
