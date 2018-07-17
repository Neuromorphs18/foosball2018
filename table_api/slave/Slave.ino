#include <Wire.h>

//##################################################################
// CONFIGURATION
//##################################################################
#define LED_FLASH_PERIOD_MS     1000
#define SLAVE_ADDRESS           12           // 8/10/12/14 for Goalie/Defender/Midfield/Forward
#define SLAVE_MODE              1            // 0/1 for Translation/Rotation
#define SPEED_CAL_TRANSLATION   125
#define SPEED_CAL_ROTATION      110
#define SPEED_SLIDE_FAST        125
#define SPEED_SLIDE_SLOW        100
#define SPEED_ROTATE_FAST       125
#define SPEED_ROTATE_SLOW       100
#define SPEED_WINDUP            220
#define SPEED_KICK              250
#define SPEED_RESET             100
#define POS_WINDUP              -180
#define POS_KICK                80
#define POS_RESET               0
#define DIFF_SLIDE_SLOW         200
#define DIFF_ROTATE_SLOW        100

#define CMD_HALT                0xF0
#define CMD_CALIBRATE           0xF1
#define CMD_SLIDE               0xF2
#define CMD_ROTATE              0xF3
#define CMD_KICK                0xF4
#define RESP_ACK                0xFA
#define RESP_NACK               0xFB

// Pins
#define PIN_DIRECTION           8
#define PIN_PWM                 9
#define PIN_OUTER_SWITCH        11
#define PIN_INNER_SWITCH        12
#define PIN_ENCODER_FORWARD     2
#define PIN_ENCODER_BACKWARD    3
#define PIN_VERTICAL_SWITCH     A0

//##################################################################
// GLOBAL VARIABLES
//##################################################################
typedef enum
{
  STATE_IDLE,
  STATE_CALIBRATING_1,
  STATE_CALIBRATING_2,
  STATE_CALIBRATING_3,
  STATE_CALIBRATING_4,
  STATE_SLIDE,
  STATE_SLIDE_IN,
  STATE_SLIDE_OUT,
  STATE_ROTATE,
  STATE_WINDUP,
  STATE_KICK,
  STATE_RESET
} state_t;

typedef enum
{
  RESULT_NONE,
  RESULT_ACK,
  RESULT_NACK
} result_t;

// State variables
volatile state_t  state           = STATE_IDLE;
volatile result_t result          = RESULT_NONE;
volatile int      target_pulse    = 0;
volatile int      maximum_pulses  = 0;
volatile int      pulses          = 0;
volatile bool     isCalibrated    = false;

//##################################################################
// INITIALISATION
//##################################################################
void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIN_DIRECTION, OUTPUT);
  pinMode(PIN_PWM, OUTPUT);
  pinMode(PIN_ENCODER_FORWARD, INPUT);
  pinMode(PIN_ENCODER_BACKWARD, INPUT);
  pinMode(PIN_OUTER_SWITCH, INPUT_PULLUP);
  pinMode(PIN_INNER_SWITCH, INPUT_PULLUP);
  pinMode(PIN_VERTICAL_SWITCH, INPUT_PULLUP);

  ledOn(true);
  analogWrite(PIN_PWM, 0);

  Wire.begin(SLAVE_ADDRESS + SLAVE_MODE);
  Wire.onReceive(receive_event);
  Wire.onRequest(request_event);

  attachInterrupt(0, forward_change, CHANGE);
  attachInterrupt(1, backward_change, CHANGE);
}

//##################################################################
// MAIN LOOP
//##################################################################
void loop()
{
  static unsigned long  ledTimestamp  = 0;
  static unsigned long  dlyTimestamp  = 0;
  static bool           ledState      = true;
  static byte           slideState    = 0;
  static byte           rotState      = 0;
  static bool           moveFast;
  unsigned long         timeNow;
  int                   diff;

  timeNow = millis();

  ///////////////////////////////////////////////////
  // Flash LED
  ///////////////////////////////////////////////////
  if ((timeNow - ledTimestamp) >= (LED_FLASH_PERIOD_MS/2))
  {
    ledTimestamp  = timeNow;
    ledState      = !ledState;
    ledOn(ledState);
  }

  ///////////////////////////////////////////////////
  // State Machines
  ///////////////////////////////////////////////////
  switch (state)
  {
    case STATE_IDLE:
    {
      analogWrite(PIN_PWM, 0);
      slideState = 0;
      rotState = 0;
      break;
    }

    #if SLAVE_MODE == 0
    case STATE_CALIBRATING_1:
    {
      digitalWrite(PIN_DIRECTION, LOW);
      analogWrite(PIN_PWM, SPEED_CAL_TRANSLATION);
      state = STATE_CALIBRATING_2;
      break;
    }

    case STATE_CALIBRATING_2:
    {
      if (digitalRead(PIN_INNER_SWITCH) == LOW)
      {
        analogWrite(PIN_PWM, 0);
        delay(50);
        digitalWrite(PIN_DIRECTION, HIGH);
        analogWrite(PIN_PWM, SPEED_CAL_TRANSLATION);
        state = STATE_CALIBRATING_3;
      }
      break;
    }

    case STATE_CALIBRATING_3:
    {
      if (digitalRead(PIN_OUTER_SWITCH) == LOW)
      {
        analogWrite(PIN_PWM, 0);
        delay(100);
        noInterrupts();
        maximum_pulses = pulses;
        interrupts();
        digitalWrite(PIN_DIRECTION, LOW);
        analogWrite(PIN_PWM, SPEED_CAL_TRANSLATION);
        state = STATE_CALIBRATING_4;
      }
      break;
    }

    case STATE_CALIBRATING_4:
    {
      if (digitalRead(PIN_INNER_SWITCH) == LOW)
      {
        analogWrite(PIN_PWM, 0);
        delay(100);
        isCalibrated = true;
        noInterrupts();
        maximum_pulses -= pulses;
        pulses = 0;
        interrupts();
        state = STATE_IDLE;
      }
      break;
    }
    #else
    case STATE_CALIBRATING_1:
    {
      digitalWrite(PIN_DIRECTION, HIGH);
      analogWrite(PIN_PWM, SPEED_CAL_ROTATION);
      state = STATE_CALIBRATING_2;
      delay(50);
      break;
    }

    case STATE_CALIBRATING_2:
    {
      if (digitalRead(PIN_VERTICAL_SWITCH) == LOW)
      {
        analogWrite(PIN_PWM, 0);
        delay(100);
        noInterrupts();
        pulses = 0;
        interrupts();
        digitalWrite(PIN_DIRECTION, HIGH);
        analogWrite(PIN_PWM, SPEED_CAL_ROTATION);
        state = STATE_CALIBRATING_3;
        delay(50);
      }
      break;
    }

    case STATE_CALIBRATING_3:
    {
      if (digitalRead(PIN_VERTICAL_SWITCH) == LOW)
      {
        analogWrite(PIN_PWM, 0);
        delay(100);
        isCalibrated = true;
        noInterrupts();
        maximum_pulses = pulses >> 1;
        pulses = 0;
        interrupts();
        state = STATE_IDLE;
      }
      break;
    }
    #endif

    case STATE_SLIDE:
    {

      // Move towards inner switch
      if (target_pulse < pulses)
      {
        if (slideState == 2)
        {
          analogWrite(PIN_PWM, 0);
        }
        slideState = 1;
        digitalWrite(PIN_DIRECTION, LOW);
        state = STATE_SLIDE_IN;
      }
      // Move towards outer switch
      else
      {
        if (slideState == 1)
        {
          analogWrite(PIN_PWM, 0);
        }
        slideState = 2;
        digitalWrite(PIN_DIRECTION, HIGH);
        state = STATE_SLIDE_OUT;
      }
      moveFast = true;
      break;
    }

    case STATE_SLIDE_IN:
    {
        if (digitalRead(PIN_INNER_SWITCH) == LOW)
        {
          analogWrite(PIN_PWM, 0);
          delay(100);
          slideState = 0;
          noInterrupts();
          maximum_pulses -= pulses;
          pulses = 0;
          state = (state == STATE_SLIDE_IN) ? STATE_IDLE : state;
          interrupts();
        }
        else
        {
          diff = pulses - target_pulse;
          if (moveFast || (diff > DIFF_SLIDE_SLOW))
          {
            moveFast = false;
            analogWrite(PIN_PWM, SPEED_SLIDE_FAST);
          }
          else if (diff > 0)
          {
            analogWrite(PIN_PWM, SPEED_SLIDE_SLOW);
          }
          else
          {
            analogWrite(PIN_PWM, 0);
            slideState = 0;
            noInterrupts();
            state = (state == STATE_SLIDE_IN) ? STATE_IDLE : state;
            interrupts();
          }
        }
        break;
    }

    case STATE_SLIDE_OUT:
    {
        if (digitalRead(PIN_OUTER_SWITCH) == LOW)
        {
          analogWrite(PIN_PWM, 0);
          delay(100);
          slideState = 0;
          noInterrupts();
          maximum_pulses = pulses;
          state = (state == STATE_SLIDE_OUT) ? STATE_IDLE : state;
          interrupts();
        }
        else
        {
          diff = target_pulse - pulses;
          if (moveFast || (diff > DIFF_SLIDE_SLOW))
          {
            moveFast = false;
            analogWrite(PIN_PWM, SPEED_SLIDE_FAST);
          }
          else if (diff > 0)
          {
            analogWrite(PIN_PWM, SPEED_SLIDE_SLOW);
          }
          else
          {
            analogWrite(PIN_PWM, 0);
            slideState = 0;
            noInterrupts();
            state = (state == STATE_SLIDE_OUT) ? STATE_IDLE : state;
            interrupts();
          }
        }
        break;
    }

    case STATE_ROTATE:
    {
      int distance = (target_pulse % (maximum_pulses * 2)) - (pulses % (maximum_pulses * 2));
      if (distance > maximum_pulses)
      {
        distance -= 2 * maximum_pulses;
      }
      else if (distance < -maximum_pulses)
      {
        distance += 2 * maximum_pulses;
      }
      digitalWrite(PIN_DIRECTION, distance > 0 ? HIGH : LOW);
      int speed = abs(distance);
      if (speed > 255)
      {
        speed = 255;
      }
      else if (speed < 30)
      {
        speed = 0;
      }
      analogWrite(PIN_PWM, (byte)speed);
      break;
    }

    case STATE_WINDUP:
    {
      if (digitalRead(PIN_VERTICAL_SWITCH) != LOW)
      {
        digitalWrite(PIN_DIRECTION, HIGH);
        analogWrite(PIN_PWM, SPEED_CAL_ROTATION);
        while (digitalRead(PIN_VERTICAL_SWITCH) != LOW);
        analogWrite(PIN_PWM, 0);
      }

      digitalWrite(PIN_DIRECTION, LOW);
      analogWrite(PIN_PWM, SPEED_WINDUP);
      while (pulses >= POS_WINDUP);
      analogWrite(PIN_PWM, 0);
      state = STATE_KICK;
      break;
    }

    case STATE_KICK:
    {
      digitalWrite(PIN_DIRECTION, HIGH);
      analogWrite(PIN_PWM, SPEED_KICK);
      while (pulses <= POS_KICK);
      analogWrite(PIN_PWM, 0);
      state = STATE_RESET;
      break;
    }

    case STATE_RESET:
    {
      digitalWrite(PIN_DIRECTION, LOW);
      analogWrite(PIN_PWM, SPEED_RESET);
      while (pulses >= POS_RESET);
      analogWrite(PIN_PWM, 0);
      state = STATE_IDLE;
      break;
    }

    default:
    {
      state = STATE_IDLE;
      break;
    }
  }
}

//##################################################################
// INTERRUPTS
//##################################################################
// Forward_change is called when the forward encoder's value changes.
void forward_change()
{
    if (digitalRead(PIN_ENCODER_BACKWARD) == 0)
    {
        if (digitalRead(PIN_ENCODER_FORWARD) == 0)
        {
            ++pulses;
        }
        else
        {
            --pulses;
        }
    }
    else
    {
        if (digitalRead(PIN_ENCODER_FORWARD) == 0)
        {
            --pulses;
        }
        else
        {
            ++pulses;
        }
    }
}

// Backward_change is called when the backward encoder's value changes.
void backward_change()
{
    if (digitalRead(PIN_ENCODER_FORWARD) == 0)
    {
        if (digitalRead(PIN_ENCODER_BACKWARD) == 0)
        {
            --pulses;
        }
        else
        {
            ++pulses;
        }
    }
    else
    {
        if (digitalRead(PIN_ENCODER_BACKWARD) == 0)
        {
            ++pulses;
        }
        else
        {
            --pulses;
        }
    }
}

// Receive_event is called when the I2C master sends data.
void receive_event(int len)
{
    byte cmd[4];
    byte cnt = 0;

    while (Wire.available() < 4);
    cmd[0] = Wire.read();
    cmd[1] = Wire.read();
    cmd[2] = Wire.read();
    cmd[3] = Wire.read();
    while (Wire.available()) Wire.read();

    if (crcIsValid(cmd, 3, cmd[3]))
    {
      result = RESULT_ACK;

      switch (cmd[0])
      {
        case CMD_HALT:
        {
          state = STATE_IDLE;
          break;
        }

        case CMD_CALIBRATE:
        {
          state = STATE_CALIBRATING_1;
          isCalibrated = false;
          break;
        }

        case CMD_SLIDE:
        {
          if (isCalibrated)
          {
            state = STATE_SLIDE;
            target_pulse = (((int)cmd[2]) << 8) | ((int)cmd[1]);
          }
          break;
        }

        case CMD_KICK:
        {
          if ((state == STATE_IDLE) && isCalibrated)
          {
            state = STATE_WINDUP;
          }
          break;
        }

        case CMD_ROTATE:
        {
          if ((state == STATE_IDLE || state == STATE_ROTATE) && isCalibrated)
          {
            state = STATE_ROTATE;
            target_pulse = (((int)cmd[2]) << 8) | ((int)cmd[1]);
          }
          break;
        }

        default:
        {
          break;
        }
      }
    }
    else
    {
      result = RESULT_NACK;
    }
}

// Request_event is called when the I2C master requests data.
void request_event()
{
  byte buffer[6];

  if (result == RESULT_NONE)
  {
    buffer[0] = (byte)( pulses               & 0xFF);
    buffer[1] = (byte)((pulses         >> 8) & 0xFF);
    buffer[2] = (byte)( maximum_pulses       & 0xFF);
    buffer[3] = (byte)((maximum_pulses >> 8) & 0xFF);
    buffer[4] = isCalibrated ? 0x01 : 0x00;
    buffer[5] = crc(buffer, 5);

    Wire.write(buffer, 6);
  }
  else if (result == RESULT_ACK)
  {
    buffer[0] = RESP_ACK;
    buffer[1] = (byte)~RESP_ACK;
    result    = RESULT_NONE;

    Wire.write(buffer, 2);
  }
  else
  {
    buffer[0] = RESP_NACK;
    buffer[1] = (byte)~RESP_NACK;
    result    = RESULT_NONE;

    Wire.write(buffer, 2);
  }
}

//##################################################################
// HELPER FUNCTIONS
//##################################################################
void ledOn(bool on)
{
  digitalWrite(LED_BUILTIN, on);
}

byte crc(const byte * message, byte len)
{
    byte crc8 = 0x00;

    while (len--)
    {
        byte val = *message++;
        for (byte i = 0; i < 8; i++)
        {
            byte sum = (crc8 ^ val) & 0x01;
            crc8 >>= 1;
            if (sum > 0)
            {
                crc8 ^= 0x8C;
            }
            val >>= 1;
        }
    }
    return crc8;
}

bool crcIsValid(const byte * message, byte msgLen, byte crcVal)
{
    return crcVal == crc(message, msgLen);
}
