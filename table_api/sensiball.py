import serial
import struct
import threading
import sys
import time

SERIAL_SOF          = 0xAA
MSG_HALT            = 0xC0
MSG_CALIBRATE       = 0xC1
MSG_SET_SPEEDS      = 0xC2
MSG_UPDATE          = 0xCA
STATUS_OFFLINE      = 0x50
STATUS_CRC_ERROR    = 0x51
STATUS_UNCALIBRATED = 0x52
STATUS_CALIBRATED   = 0x53

class Sensiball:
    def __init__(self):
        self.device         = None
        self.handlers       = []
        self.running        = False
        self.prevPositions  = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
        self.printInfo      = False

    def open(self, port, baud):
        if self.device:
            raise Exception('Already open')
        self.device = serial.Serial(port, baudrate=baud, timeout=None)
        self.device.reset_input_buffer()
        self.running = True
        self.communication_thread = threading.Thread(target=self._reader)
        self.communication_thread.daemon = True
        self.communication_thread.start()

    def close(self):
        self.running = False
        self.communication_thread.join()
        self.send_halt()
        self.device.close()

    def enable_printout(self, en):
        self.printInfo = en

    def add_handler(self, handler):
        """
        Handler function must have the following format:
            my_handler(positions)
                positions   List containing the following structure:
                                [   (goalie_pulses, goalie_pulses_max),
                                    (defender_pulses, defender_pulses_max),
                                    (midfield_pulses, midfield_pulses_max),
                                    (forward_pulses, forward_pulses_max)  ]
        """
        self.handlers.append(handler)

    def send_halt(self):
        msg = [SERIAL_SOF, MSG_HALT, 4]
        msg.append(self._crc(msg))
        self.device.write(bytearray(msg))
        self.device.flush()

    def send_calibrate(self):
        msg = [SERIAL_SOF, MSG_CALIBRATE, 4]
        msg.append(self._crc(msg))
        self.device.write(bytearray(msg))
        self.device.flush()
        time.sleep(5)

    def send_speeds(self, speeds):
        """
        speeds = (  goalie_translation,
                    goalie_rotation,
                    defender_translation,
                    defender_rotation,
                    midfield_translation,
                    midfield_rotation,
                    forward_translation,
                    forward_rotation    )
        Speeds must be in the range [-255, 255]
        """
        if len(speeds) != 8:
            raise ValueError('speeds must contain height values')

        clockwise   = 0
        spd         = []
        for i, speed in enumerate(speeds):
            clockwise |= ((1 if speed >= 0 else 0) << i)
            if abs(speed) > 255:
                spd.append(255)
            else:
                spd.append(abs(speed))

        msg  = [SERIAL_SOF, MSG_SET_SPEEDS, 13, clockwise]
        msg += spd
        msg.append(self._crc(msg))
        self.device.write(bytearray(msg))
        self.device.flush()

    def _reader(self):
        msg = []
        while self.running:
            msg.append(ord(self.device.read()))

            # Message must start with SOF character
            while (len(msg) > 0) and (msg[0] != SERIAL_SOF):
                del msg[0]

            # Message must be at least 4 bytes
            if len(msg) < 4:
                continue

            # Wait to receive entire message (including CRC)
            msgLen = msg[2]
            if len(msg) < msgLen:
                continue

            # Verify integrity of message
            if msg[-1] != self._crc(msg[:-1]):
                del msg[0]
                continue

            # Process messages
            msgType = msg[1]

            if (msgType == MSG_UPDATE) and (msgLen == 44):
                status = []
                for i in range(3,43,5):
                    status.append(struct.unpack('hhB', bytes(msg[i:i+5])))

                # Update handlers
                positions = []
                for i, s in enumerate(status):
                    if s[2] == STATUS_CALIBRATED:
                        self.prevPositions[i] = (s[0], s[1])
                    positions.append(self.prevPositions[i])
                for handler in self.handlers:
                    handler.handle_positions(positions)

                # Print info
                if self.printInfo:
                    txt = ""
                    for s in status:
                        if s[2] == STATUS_OFFLINE:      txt += "     offline"
                        if s[2] == STATUS_CRC_ERROR:    txt += "   CRC error"
                        if s[2] == STATUS_UNCALIBRATED: txt += "uncalibrated"
                        if s[2] == STATUS_CALIBRATED:   txt += "  calibrated"
                        txt += str.format(":{0:+05}:{1:+05} ", s[0], s[1])
                    print(txt[:-1])

            else:
                raise ValueError("Invalid message received [code: {0:02X} length: {1}".format(msgType, msgLen))

            del msg[:]

    def _crc(self, msg):
        crc8 = 0x00

        for i in range(len(msg)):
            val = msg[i]
            for b in range(8):
                sum = (crc8 ^ val) & 0x01
                crc8 >>= 1
                if sum > 0:
                    crc8 ^= 0x8C
                val >>= 1

        return crc8
