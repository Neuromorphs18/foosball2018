import serial
import struct
import threading
import sys
import time

SERIAL_SOF          = 0xAA
MSG_HALT            = 0xC0
MSG_CALIBRATE       = 0xC1
MSG_SLIDE           = 0xC2
MSG_ROTATE          = 0xC3
MSG_KICK            = 0xC4
MSG_CAL_DONE        = 0xCA
MSG_POSITION        = 0xCB
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
        self.calFinished1   = False
        self.calFinished2   = False
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
                                [   (goalie_position, goalie_position_max),
                                    (defender_position, defender_position_max),
                                    (midfield_position, midfield_position_max),
                                    (forward_position, forward_position_max)  ]
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
        self.calFinished1 = False
        self.calFinished2 = False
        msg = [SERIAL_SOF, MSG_CALIBRATE, 4]
        msg.append(self._crc(msg))
        if self.device1:
            self.device1.write(bytearray(msg))
            self.device1.flush()
        if self.device2:
            self.device2.write(bytearray(msg))
            self.device2.flush()
        while (self.device1 and not self.calFinished1) or (self.device2 and not self.calFinished2):
            None
        maxVals = []
        def calHandler(v):
            for s in v:
                maxVals.append(s[1])
        self.handlers.append(calHandler)
        while len(maxVals) == 0:
            None
        del self.handlers[-1]
        return maxVals

    def slide(self, player, position):
        """
        Slide player to position.
        player = 0, 1, 2 or 3
                0 => Goalie
                1 => Defender
                2 => Midfield
                3 => Forward
        """
        if player not in [0,1,2,3]:
            raise ValueError('Invalid player specified for slide')

        if   self.device1 and player in [0,1]:
            msg  = [SERIAL_SOF, MSG_SLIDE, 7, player, position & 0xFF, (position >> 8) & 0xFF]
            msg.append(self._crc(msg))
            self.device1.write(bytearray(msg))
            self.device1.flush()
        elif self.device2 and player in [2,3]:
            msg  = [SERIAL_SOF, MSG_SLIDE, 7, player-2, position & 0xFF, (position >> 8) & 0xFF]
            msg.append(self._crc(msg))
            self.device2.write(bytearray(msg))
            self.device2.flush()

    def rotate(self, player, position):
        """
        Rotate player to position.
        player = 0, 1, 2 or 3
                0 => Goalie
                1 => Defender
                2 => Midfield
                3 => Forward
        """
        if player not in [0,1,2,3]:
            raise ValueError('Invalid player specified for rotate')

        if   self.device1 and player in [0,1]:
            msg  = [SERIAL_SOF, MSG_ROTATE, 7, player, position & 0xFF, (position >> 8) & 0xFF]
            msg.append(self._crc(msg))
            self.device1.write(bytearray(msg))
            self.device1.flush()
        elif self.device2 and player in [2,3]:
            msg  = [SERIAL_SOF, MSG_ROTATE, 7, player-2, position & 0xFF, (position >> 8) & 0xFF]
            msg.append(self._crc(msg))
            self.device2.write(bytearray(msg))
            self.device2.flush()

    def kick(self, player):
        """
        Kick player.
        player = 0, 1, 2 or 3
                0 => Goalie
                1 => Defender
                2 => Midfield
                3 => Forward
        """
        if player not in [0,1,2,3]:
            raise ValueError('Invalid player specified for kick')

        if   self.device1 and player in [0,1]:
            msg  = [SERIAL_SOF, MSG_KICK, 5, player]
            msg.append(self._crc(msg))
            self.device1.write(bytearray(msg))
            self.device1.flush()
        elif self.device2 and player in [2,3]:
            msg  = [SERIAL_SOF, MSG_KICK, 5, player-2]
            msg.append(self._crc(msg))
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

            elif (msgType == MSG_CAL_DONE) and (msgLen == 4):
                self.calFinished1 = True
                        
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

            elif (msgType == MSG_CAL_DONE) and (msgLen == 4):
                self.calFinished2 = True
            
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
