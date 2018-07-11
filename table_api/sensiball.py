import serial
import struct
import threading
import sys

class Table:
    def __init__(self, device, delay_init=False):
        self.sensiball_serial = None
        if not delay_init:
            self.init(device)

    def init(self, device):
        if self.sensiball_serial:
            raise Exception('already initialized')
        self.sensiball_serial = serial.Serial(device, baudrate=115200, rtscts=True, timeout=None)
        self.sensiball_serial.reset_input_buffer()
        self.handlers = []
        self.speeds = (0, 0, 0, 0, 0, 0, 0, 0)
        self.running = True
        def reader():
            previous_positions = (0, 980, 0, 980, 0, 980, 0, 980, 0, 980, 0, 980, 0, 980, 0, 980)
            try:
                while self.running:
                    positions = tuple(
                        position if position != 32767 else previous_positions[index]
                        for index, position in enumerate(struct.unpack('h' * 16, self.sensiball_serial.read(32))))
                    for handler in self.handlers:
                        handler.handle_positions(positions)
                    buffer = bytearray(10)
                    are_clockwise = 0
                    local_speeds = self.speeds
                    for index, speed in enumerate(local_speeds):
                        are_clockwise |= ((1 if speed > 0 else 0) << index)
                        if abs(speed) > 255: 
                            buffer[index + 2] = 255
                        else:
                            buffer[index + 2] = abs(speed)
                    buffer[1] = are_clockwise
                    self.sensiball_serial.write(buffer)
                    self.sensiball_serial.flush()
                    previous_positions = positions
            except serial.SerialException as error:
                if self.running:
                    raise
        self.communication_thread = threading.Thread(target=reader)
        self.communication_thread.daemon = True
        self.communication_thread.start()

    def add_handler(self, handler):
        self.handlers.append(handler)

    def set_speeds(self, speeds):
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
        if len(speeds) != 8:
            raise ValueError('speeds must contain height values')
        self.speeds = speeds

    def calibrate(self):
        self.sensiball_serial.write(struct.pack('B', 255))
        self.sensiball_serial.flush()

    def close(self):
        self.running = False
        self.communication_thread.join()
        self.sensiball_serial.write(bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        self.sensiball_serial.flush()
        self.sensiball_serial.close()
