#include <Wire.h>

/// state_type represents the calibration status.
enum state_type {
    uncalibrated,
    calibrating,
    calibrated,
};

/// constants
const unsigned long frame_duration = 20; // time between I2C writes in ms
const bool enabled[8] = {true, true, false, false, false, false, false, false}; // enabled motors
const byte translation_calibration_speed = 60;

/// state variables
byte are_clockwise = 0;
byte speeds[8];
byte new_are_clockwise = 0;
byte new_speeds[8];
byte serial_message_index = 0;
unsigned long previous_write = 0;

/// read_from_slave reads a slave's state and position.
void read_from_slave(byte index, state_type* state, uint16_t* pulses, uint16_t* maximum_pulses) {
    Wire.requestFrom(index + 8, 5);
    byte wire_bytes[5];
    byte wire_bytes_index = 0;
    while (Wire.available()) {
        if (wire_bytes_index < sizeof(wire_bytes)) {
            wire_bytes[wire_bytes_index] = Wire.read();
            ++wire_bytes_index;
        }
    }
    if (wire_bytes_index == 5) {
        if (state) {
            switch (wire_bytes[0]) {
                case 1:
                    *state = calibrating;
                    break;
                case 2:
                    *state = calibrated;
                    break;
                default:
                    *state = uncalibrated;
            }
        }
        if (pulses) {
            *pulses = (uint16_t)wire_bytes[1] | (((uint16_t)wire_bytes[2]) << 8);
        }
        if (maximum_pulses) {
            *maximum_pulses = (uint16_t)wire_bytes[3] | (((uint16_t)wire_bytes[4]) << 8);
        }
    } else {
        if (state) {
            *state = uncalibrated;
        }
        if (pulses) {
            *pulses = 32767;
        }
        if (maximum_pulses) {
            *maximum_pulses = 32767;
        }
    }
}

/// calibrate manages the slaves' calibration.
void calibrate(bool force) {
    state_type states[8];
    for (byte index = 0; index < 8; ++index) {
        if (enabled[index]) {
            Wire.beginTransmission(index + 8);
            Wire.write(0);
            Wire.write(0);
            Wire.endTransmission();
            if (force) {
                states[index] = uncalibrated;
            } else {
                read_from_slave(index, &(states[index]), nullptr, nullptr);
            }
        }
    }
    for (bool calibration_done = false; !calibration_done;) {
        for (byte index = 0; index < 4; ++index) {
            if (enabled[index * 2]) {
                switch (states[index * 2]) {
                    case uncalibrated:
                        Wire.beginTransmission(index * 2 + 8);
                        Wire.write(0);
                        Wire.endTransmission();
                        states[index * 2] = calibrating;
                        break;
                    case calibrating:
                        read_from_slave(index * 2, &(states[index * 2]), nullptr, nullptr);
                        break;
                    case calibrated:
                        Wire.beginTransmission(index * 2 + 8);
                        Wire.write(0);
                        Wire.write(translation_calibration_speed);
                        Wire.endTransmission();
                        if (enabled[index * 2 + 1]) {
                            switch (states[index * 2 + 1]) {
                                case uncalibrated:
                                    uint16_t pulses;
                                    read_from_slave(index * 2, nullptr, &pulses, nullptr);
                                    if (pulses == 0) {
                                        Wire.beginTransmission(index * 2 + 1 + 8);
                                        Wire.write(0);
                                        Wire.endTransmission();
                                        states[index * 2 + 1] = calibrating;
                                    }
                                    break;
                                case calibrating:
                                    read_from_slave(index * 2 + 1, &(states[index * 2 + 1]), nullptr, nullptr);
                                    break;
                                case calibrated:
                                    break;
                            }
                        }
                        break;
                }
            }
        }
        calibration_done = true;
        for (byte index = 0; index < 8; ++index) {
            if (enabled[index]) {
                if (states[index] != calibrated) {
                    calibration_done = false;
                    break;
                }
            }
        }
    }
}

void setup() {
    Serial.begin(115200);
    Wire.begin();
    calibrate(false);
}

void loop() {
    const unsigned long now = millis();
    if (now - previous_write >= frame_duration) {
        previous_write = now;
        for (byte index = 0; index < 8; ++index) {
            if (enabled[index]) {
                Wire.beginTransmission(index + 8);
                Wire.write((are_clockwise >> index) & 1);
                Wire.write(speeds[index]);
                Wire.endTransmission();
                uint16_t pulses;
                uint16_t maximum_pulses;
                read_from_slave(index, nullptr, &pulses, &maximum_pulses);
                Serial.write(pulses & 0xff);
                Serial.write((pulses >> 8) & 0xff);
                Serial.write(maximum_pulses & 0xff);
                Serial.write((maximum_pulses >> 8) & 0xff);
            } else {
                Serial.write(0);
                Serial.write(0);
                Serial.write(0);
                Serial.write(0);
            }
        }
    }
    if (Serial.available()) {
        const byte serial_byte = Serial.read();
        switch (serial_message_index) {
            case 0:
                if (serial_byte == 0xff) {
                    calibrate(true);
                } else {
                    ++serial_message_index;
                }
                break;
            case 1:
                new_are_clockwise = serial_byte;
                ++serial_message_index;
                break;
            default:
                new_speeds[serial_message_index - 2] = serial_byte;
                if (serial_message_index == 9) {
                    serial_message_index = 0;
                    are_clockwise = new_are_clockwise;
                    memcpy(speeds, new_speeds, sizeof(new_speeds));
                } else {
                    ++serial_message_index;
                }
        }
    }
}
