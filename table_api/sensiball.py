import serial
import struct
import threading

class Table:
    def __init__(self, device):
        self.sensiball_serial = serial.Serial(device, baudrate=115200, rtscts=True)
        self.sensiball_serial.reset_input_buffer()
        self.handlers = []
        self.handlers_lock = threading.Lock()
        self.running = True
        def reader():
            received_bytes = bytearray()
            while self.running:
                received_bytes.append(struct.unpack('B', self.sensiball_serial.read(1))[0])
                if len(received_bytes) == 32:
                    positions = struct.unpack('h' * 16, received_bytes)
                    self.handlers_lock.acquire()
                    for handler in self.handlers:
                        handler.handle_positions(positions)
                    received_bytes = bytearray()
                    self.handlers_lock.release()
        self.reading_thread = threading.Thread(target=reader)
        self.reading_thread.daemon = True
        self.reading_thread.start()

    def add_handlers(self, handler):
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
        are_clockwise = 0
        for index, speed in enumerate(speeds):
            are_clockwise |= ((1 if speed > 0 else 0) << index)
        buffer = bytearray([0x00, are_clockwise])
        for speed in speeds:
            buffer.append(abs(speed))

        print("set_speeds", list(buffer))

        self.sensiball_serial.write(buffer)
        self.sensiball_serial.flush()

    def calibrate(self):
        self.sensiball_serial.write(struct.pack('B', 255))
        self.sensiball_serial.flush()

    def close(self):
        self.sensiball_serial.close()
        self.running = False
        self.reading_thread.join()
