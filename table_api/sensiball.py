import serial
import struct
import threading

sensiball_serial = serial.Serial('/dev/cu.usbmodemFA131', baudrate=115200, rtscts=True)
sensiball_serial.reset_input_buffer()

listeners = []
listeners_lock = threading.Lock()
def reader():
    received_bytes = bytearray()
    while True:
        received_bytes.append(struct.unpack('B', sensiball_serial.read(1))[0])
        if len(received_bytes) == 32:
            positions = struct.unpack('h' * 16, received_bytes)
            listeners_lock.acquire()
            for listener in listeners:
                listener(positions)
            received_bytes = bytearray()
            listeners_lock.release()
reading_thread = threading.Thread(target=reader)
reading_thread.daemon = True
reading_thread.start()

def add_listener(listener):
    listeners_lock.acquire()
    listeners.append(listener)
    listeners_lock.release()

def set_speeds(speeds):
    """
    speeds = (
        goalie_translation,
        goalie_rotation,
        defender_translation,
        defender_rotation,
        midfield_translation,
        midfield_rotation,
        forward_translation,
        forward_rotation,
    )
    Speeds must be in the range [-255, 255]
    """
    are_clockwise = 0
    for index, speed in enumerate(speeds):
        are_clockwise |= ((1 if speed > 0 else 0) << index)
    buffer = bytearray([0x00, are_clockwise])
    for speed in speeds:
        buffer.append(abs(speed))
    sensiball_serial.write(buffer)
    sensiball_serial.flush()

def calibrate():
    sensiball_serial.write(struct.pack('B', 255))
    sensiball_serial.flush()
