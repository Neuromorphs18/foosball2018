import serial
import struct
import threading
import sys

class Table:
    def __init__(self, device):
        self.sensiball_serial = serial.Serial(device, baudrate=115200, rtscts=True)
        self.sensiball_serial.reset_input_buffer()
        self.handlers = []
        self.handlers_lock = threading.Lock()
        self.speeds = (0, 0, 0, 0, 0, 0, 0, 0)
        self.speeds_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.running = True
        def reader():
            previous_positions = (0 for index in range(0, 16))
            try:
                received_bytes = bytearray()
                while self.running:
                    received_bytes.append(struct.unpack('B', self.sensiball_serial.read(1))[0])
                    if len(received_bytes) == 32:
                        positions = tuple(
                            position if position != 32767 else previous_positions[index]
                            for index, position in enumerate(struct.unpack('h' * 16, received_bytes)))
                        self.handlers_lock.acquire()
                        for handler in self.handlers:
                            handler.handle_positions(positions)
                        self.handlers_lock.release()
                        buffer = bytearray(10)
                        are_clockwise = 0
                        self.speeds_lock.acquire()
                        local_speeds = self.speeds
                        self.speeds_lock.release()
                        for index, speed in enumerate(local_speeds):
                            are_clockwise |= ((1 if speed > 0 else 0) << index)
                            buffer[index + 2] = abs(speed)
                        buffer[1] = are_clockwise
                        self.write_lock.acquire()
                        self.sensiball_serial.write(buffer)
                        self.sensiball_serial.flush()
                        self.write_lock.release()
                        received_bytes = bytearray()
                        previous_positions = positions
            except serial.SerialException as error:
                if self.running:
                    raise
        self.communication_thread = threading.Thread(target=reader)
        self.communication_thread.daemon = True
        self.communication_thread.start()

    def add_handler(self, handler):
        self.handlers_lock.acquire()
        self.handlers.append(handler)
        self.handlers_lock.release()

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
        self.speeds_lock.acquire()
        self.speeds = speeds
        self.speeds_lock.release()

    def calibrate(self):
        self.write_lock.acquire()
        self.sensiball_serial.write(struct.pack('B', 255))
        self.sensiball_serial.flush()
        self.write_lock.release()

    def close(self):
        self.running = False
        self.communication_thread.join()
        self.write_lock.acquire()
        self.sensiball_serial.write(bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        self.sensiball_serial.flush()
        self.write_lock.release()
        self.sensiball_serial.close()
