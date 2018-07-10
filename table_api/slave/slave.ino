#include <Wire.h>

/// motion_type lists the motors roles.
enum motion_type {
    translation,
    rotation,
};

/// position_type lists the players rows.
enum position_type {
    goalie,
    defender,
    midfield,
    forward,
};

/// state_type represents the calibration status.
enum state_type {
    uncalibrated,
    calibrating,
    calibrated,
};

/// configuration
const motion_type motion = translation;
const position_type position = goalie;
const byte translation_calibration_speed = 60;
const byte rotation_calibration_speed = 100;

/// pins and addresses declarations
const int direction_pin = 8;
const int pwm_pin = 9;
const int inner_switch_pin = 12;
const int outer_switch_pin = 11;
const int forward_encoder_pin = 2;
const int backward_encoder_pin = 3;
const int vertical_switch_pin = A0;

/// state variables
volatile state_type state = uncalibrated;
byte calibration_step = 0;
volatile int16_t minimum_pulses = 0;
volatile int16_t maximum_pulses = 980;
volatile int16_t pulses = 0;
volatile bool is_clockwise = false;
volatile byte speed = 0;

/// receive_event is called when the I2C master sends data.
void handle_receive_event(int bytes_received) {
    byte wire_bytes[2];
    byte wire_bytes_index = 0;
    while (Wire.available()) {
        if (wire_bytes_index < sizeof(wire_bytes)) {
            wire_bytes[wire_bytes_index] = Wire.read();
            ++wire_bytes_index;
        }
    }
    if (wire_bytes_index == 1) {
        state = calibrating;
    } else {
        is_clockwise = (wire_bytes[0] == 1);
        speed = wire_bytes[1];
    }
}

/// handle_request_event is called when the I2C master requests data.
void handle_request_event() {
    const uint16_t normalized_pulses = pulses - minimum_pulses;
    const uint16_t normalized_maximum_pulses = maximum_pulses - minimum_pulses;
    Wire.write(state);
    Wire.write(normalized_pulses & 0xff);
    Wire.write((normalized_pulses >> 8) & 0xff);
    Wire.write(normalized_maximum_pulses & 0xff);
    Wire.write((normalized_maximum_pulses >> 8) & 0xff);
}

/// forward_change is called when the forward encoder's value changes.
void forward_change() {
    if (digitalRead(backward_encoder_pin) == 0) {
        if (digitalRead(forward_encoder_pin) == 0) {
            ++pulses;
        } else {
            --pulses;
        }
    } else {
        if (digitalRead(forward_encoder_pin) == 0) {
            --pulses;
        } else {
            ++pulses;
        }
    }
}

/// backward_change is called when the backward encoder's value changes.
void backward_change() {
    if(digitalRead(forward_encoder_pin) == 0) {
        if (digitalRead(backward_encoder_pin) == 0) {
            --pulses;
        } else {
            ++pulses;
        }
    } else {
        if (digitalRead(backward_encoder_pin) == 0) {
            ++pulses;
        } else {
            --pulses;
        }
    }
}

/// setup runs once on boot.
void setup() {

    Serial.begin(9600); // @DEBUG

    pinMode(direction_pin, OUTPUT);
    pinMode(forward_encoder_pin, INPUT);
    pinMode(backward_encoder_pin, INPUT);
    attachInterrupt(0, forward_change, CHANGE);
    attachInterrupt(1, backward_change, CHANGE);
    switch (position) {
        case goalie:
            Wire.begin(8 + (motion == translation ? 0 : 1));
            break;
        case defender:
            Wire.begin(10 + (motion == translation ? 0 : 1));
            break;
        case midfield:
            Wire.begin(12 + (motion == translation ? 0 : 1));
            break;
        case forward:
            Wire.begin(14 + (motion == translation ? 0 : 1));
            break;
    }
    Wire.onReceive(handle_receive_event);
    Wire.onRequest(handle_request_event);
    switch (motion) {
        case translation: {
            pinMode(inner_switch_pin, INPUT_PULLUP);
            pinMode(outer_switch_pin, INPUT_PULLUP);
            break;
        }
        case rotation: {
            pinMode(vertical_switch_pin, INPUT_PULLUP);
            break;
        }
    }
}

void loop() {
    switch (state) {
        case uncalibrated:
            break;
        case calibrating:
            switch (motion) {
                case translation: {
                    switch (calibration_step) {
                        case 0:
                            digitalWrite(direction_pin, LOW);
                            analogWrite(pwm_pin, translation_calibration_speed);
                            ++calibration_step;
                            break;
                        case 1:
                            if (digitalRead(inner_switch_pin) == LOW) {
                                analogWrite(pwm_pin, 0);
                                noInterrupts();
                                pulses = 0;
                                interrupts();
                                digitalWrite(direction_pin, HIGH);
                                analogWrite(pwm_pin, translation_calibration_speed);
                                ++calibration_step;
                            }
                            break;
                        case 2:
                            if (digitalRead(outer_switch_pin) == LOW) {
                                analogWrite(pwm_pin, 0);
                                noInterrupts();
                                maximum_pulses = pulses + 1;
                                interrupts();
                                digitalWrite(direction_pin, LOW);
                                analogWrite(pwm_pin, translation_calibration_speed);
                                ++calibration_step;
                            }
                            break;
                        case 3:
                            if (digitalRead(inner_switch_pin) == LOW) {
                                analogWrite(pwm_pin, 0);
                                ++calibration_step;
                            }
                            break;
                        default:
                            calibration_step = 0;
                            state = calibrated;
                    }
                    break;
                }
                case rotation: {
                    switch (calibration_step) {
                        case 0:
                            digitalWrite(direction_pin, HIGH);
                            analogWrite(pwm_pin, rotation_calibration_speed);
                            ++calibration_step;
                            break;
                        case 1:
                            if (digitalRead(vertical_switch_pin) == LOW) {
                                analogWrite(pwm_pin, 0);
                                noInterrupts();
                                pulses = 0;
                                interrupts();
                                ++calibration_step;
                            }
                            break;
                        default:
                            calibration_step = 0;
                            state = calibrated;
                    }
                    break;
                }
            }
            break;
        case calibrated:
            noInterrupts();
            const bool local_is_clockwise = is_clockwise;
            byte local_speed = speed;
            interrupts();
            if (motion == translation) {
                if (digitalRead(inner_switch_pin) == LOW) {
                    noInterrupts();
                    minimum_pulses = pulses;
                    interrupts();
                    if (!local_is_clockwise) {
                        local_speed = 0;
                    }
                } else if (digitalRead(outer_switch_pin) == LOW) {
                    noInterrupts();
                    maximum_pulses = pulses + 1;
                    interrupts();
                    if (local_is_clockwise) {
                        local_speed = 0;
                    }
                } else {
                    if (pulses + 1 > maximum_pulses) {
                        noInterrupts();
                        maximum_pulses = pulses + 1;
                        interrupts();
                    } else if (pulses < minimum_pulses) {
                        noInterrupts();
                        minimum_pulses = pulses;
                        interrupts();
                    }
                }
            }
            digitalWrite(direction_pin, local_is_clockwise ? HIGH : LOW);
            analogWrite(pwm_pin, local_speed);
            break;
    }
}
