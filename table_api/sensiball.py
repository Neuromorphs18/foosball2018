import serial
import struct
import threading
import sys
import time

SERIAL_SOF          = 0xAA
MSG_HALT            = 0xC0
MSG_CALIBRATE       = 0xC1
MSG_SET_SPEEDS      = 0xC2
MSG_KICK            = 0xC3
MSG_POSITION        = 0xCA
STATUS_OFFLINE      = 0x50
STATUS_CRC_ERROR    = 0x51
STATUS_UNCALIBRATED = 0x52
STATUS_CALIBRATED   = 0x53

class Sensiball:
    def __init__(self):
        self.device1        = None
        self.device2        = None
        self.handlers       = []
        self.running        = False
        self.prevPositions  = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
        self.printInfo      = False
        self.dataReady1     = False
        self.dataReady2     = False
        self.status         = [(0,0,STATUS_OFFLINE)]*8

    def open(self, port1, port2, baud):
        self.running = True
        self.dataHandleLock = threading.Lock()
        if port1:
            self.device1 = serial.Serial(port1, baudrate=baud, timeout=None)
            self.device1.reset_input_buffer()
            self.communication_thread1 = threading.Thread(target=self._reader1)
            self.communication_thread1.daemon = True
            self.communication_thread1.start()
        if port2:
            self.device2 = serial.Serial(port2, baudrate=baud, timeout=None)
            self.device2.reset_input_buffer()
            self.communication_thread2 = threading.Thread(target=self._reader2)
            self.communication_thread2.daemon = True
            self.communication_thread2.start()

    def close(self):
        self.running = False
        self.send_halt()
        if self.device1:
            self.communication_thread1.join()
            self.device1.close()
            self.device1 = None
        if self.device2:
            self.communication_thread2.join()
            self.device2.close()
            self.device2 = None

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
        if self.device1:
            self.device1.write(bytearray(msg))
            self.device1.flush()
        if self.device2:
            self.device2.write(bytearray(msg))
            self.device2.flush()

    def send_calibrate(self):
        msg = [SERIAL_SOF, MSG_CALIBRATE, 4]
        msg.append(self._crc(msg))
        if self.device1:
            self.device1.write(bytearray(msg))
            self.device1.flush()
        if self.device2:
            self.device2.write(bytearray(msg))
            self.device2.flush()
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

        if self.device1:
            msg  = [SERIAL_SOF, MSG_SET_SPEEDS, 9, (clockwise & 0x0F)]
            msg += spd[0:4]
            msg.append(self._crc(msg))
            self.device1.write(bytearray(msg))
            self.device1.flush()
        if self.device2:
            msg  = [SERIAL_SOF, MSG_SET_SPEEDS, 9, ((clockwise >> 4) & 0x0F)]
            msg += spd[4:8]
            msg.append(self._crc(msg))
            self.device2.write(bytearray(msg))
            self.device2.flush()

    def send_kick(self, position):
        """
        position = 0, 1, 2 or 3
            0 => Goalie
            1 => Defender
            2 => Midfield
            3 => Forward
        """
        if position not in [0,1,2,3]:
            raise ValueError('Invalid position specified for kick')

        if   self.device1 and position in [0,1]:
            msg  = [SERIAL_SOF, MSG_KICK, 5, position]
            msg.append(self._crc(msg))
            self.device1.write(bytearray(msg))
            self.device1.flush()
        elif self.device2 and position in [2,3]:
            msg  = [SERIAL_SOF, MSG_KICK, 5, position-2]
            msg.append(self._crc(msg))
            print(msg)
            self.device2.write(bytearray(msg))
            self.device2.flush()

    def _reader1(self):
        msg = []
        while self.running:
            msg.append(ord(self.device1.read()))
            
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

            if (msgType == MSG_POSITION) and (msgLen == 24):
                with self.dataHandleLock:
                    for i in range(0,4):
                        idx = 3 + i*5
                        self.status[i] = struct.unpack('hhB', bytes(msg[idx:idx+5]))
                    
                    if not self.device2 or self.dataReady2:
                        # Update handlers
                        positions = []
                        for i, s in enumerate(self.status):
                            if s[2] == STATUS_CALIBRATED:
                                self.prevPositions[i] = (s[0], s[1])
                            positions.append(self.prevPositions[i])
                        for handler in self.handlers:
                            handler(positions)

                        # Print info
                        if self.printInfo:
                            txt = ""
                            for s in self.status:
                                if s[2] == STATUS_OFFLINE:      txt += "offline"
                                if s[2] == STATUS_CRC_ERROR:    txt += "  error"
                                if s[2] == STATUS_UNCALIBRATED: txt += "  uncal"
                                if s[2] == STATUS_CALIBRATED:   txt += "    cal"
                                txt += str.format(":{0:+06}:{1:+06} ", s[0], s[1])
                            print(txt[:-1])

                        self.dataReady1 = False
                        self.dataReady2 = False
                    else:
                        self.dataReady1 = True
            else:
                raise ValueError("Invalid message received from device 1 [code: {0:02X} length: {1}]".format(msgType, msgLen))

            del msg[:]

    def _reader2(self):
        msg = []
        while self.running:
            msg.append(ord(self.device2.read()))

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

            if (msgType == MSG_POSITION) and (msgLen == 24):
                
                with self.dataHandleLock:
                    for i in range(0,4):
                        idx = 3 + i*5
                        self.status[i+4] = struct.unpack('hhB', bytes(msg[idx:idx+5]))
    
                    if not self.device1 or self.dataReady1:
                        # Update handlers
                        positions = []
                        for i, s in enumerate(self.status):
                            if s[2] == STATUS_CALIBRATED:
                                self.prevPositions[i] = (s[0], s[1])
                            positions.append(self.prevPositions[i])
                        for handler in self.handlers:
                            handler(positions)

                        # Print info
                        if self.printInfo:
                            txt = ""
                            for s in self.status:
                                if s[2] == STATUS_OFFLINE:      txt += "offline"
                                if s[2] == STATUS_CRC_ERROR:    txt += "  error"
                                if s[2] == STATUS_UNCALIBRATED: txt += "  uncal"
                                if s[2] == STATUS_CALIBRATED:   txt += "    cal"
                                txt += str.format(":{0:+06}:{1:+06} ", s[0], s[1])
                            print(txt[:-1])

                        self.dataReady1 = False
                        self.dataReady2 = False
                    else:
                        self.dataReady2 = True
            else:
                raise ValueError("Invalid message received from device 2 [code: {0:02X} length: {1}]".format(msgType, msgLen))

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
