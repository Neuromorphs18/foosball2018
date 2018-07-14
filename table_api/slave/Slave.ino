#include <Wire.h>

//##################################################################
// CONFIGURATION
//##################################################################
#define LED_FLASH_PERIOD_MS   1000
#define SLAVE_ADDRESS         12           // 8/10/12/14 for Goalie/Defender/Midfield/Forward
#define SLAVE_MODE            1           // 0/1 for Translation/Rotation
#define TRANSLATION_CAL_SPEED 120
#define ROTATION_CAL_SPEED    110

#define STATUS_OFFLINE        0x50
#define STATUS_CRC_ERROR      0x51
#define STATUS_UNCALIBRATED   0x52
#define STATUS_CALIBRATED     0x53

#define CMD_POKE              0xF0
#define CMD_HALT              0xF1
#define CMD_CALIBRATE         0xF2
#define CMD_SET_SPEED         0xF3
#define RESP_ACK              0xFA
#define RESP_NACK             0xFB

// Pins
#define PIN_DIRECTION         8
#define PIN_PWM               9
#define PIN_OUTER_SWITCH      11 
#define PIN_INNER_SWITCH      12
#define PIN_ENCODER_FORWARD   2
#define PIN_ENCODER_BACKWARD  3
#define PIN_VERTICAL_SWITCH   A0

//##################################################################
// GLOBAL VARIABLES
//##################################################################
typedef enum
{
  STATE_UNCALIBRATED,
  STATE_CALIBRATING,
  STATE_CALIBRATED
} state_t;

typedef enum
{
  RESULT_NONE,
  RESULT_ACK,
  RESULT_NACK
} result_t;

// State variables
volatile state_t  state          = STATE_UNCALIBRATED;
volatile result_t result         = RESULT_NONE;
volatile int      minimum_pulses = 0;
volatile int      maximum_pulses = 980;
volatile int      pulses         = 0;
volatile bool     clockwise      = false;
volatile byte     speed          = 0;

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
  //Wire.setClock(10000);
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
  static unsigned long  ledTimestamp    = 0;
  static unsigned long  updateTimestamp = 0;
  static bool           ledState        = true;
  static byte           calState        = 0;
  unsigned long         timeNow;
  
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
    case STATE_UNCALIBRATED:
    {
      break;
    }

    case STATE_CALIBRATING:
    {
      #if SLAVE_MODE == 0
      switch (calState)
      {
        case 0:
        {
          digitalWrite(PIN_DIRECTION, HIGH);
          analogWrite(PIN_PWM, TRANSLATION_CAL_SPEED);
          calState++;
          break;
        }

        case 1:
        {
          if (digitalRead(PIN_OUTER_SWITCH) == LOW)
          {
              analogWrite(PIN_PWM, 0);
              noInterrupts();
              maximum_pulses = pulses + 1;
              interrupts();
              digitalWrite(PIN_DIRECTION, LOW);
              analogWrite(PIN_PWM, TRANSLATION_CAL_SPEED);
              calState++;
          }
          break;
        }

        case 2:
        {
          if (digitalRead(PIN_INNER_SWITCH) == LOW)
          {
              analogWrite(PIN_PWM, 0);
              noInterrupts();
              minimum_pulses = pulses;
              interrupts();
              calState++;
          }
          break;
        }

        default:
        {
          calState  = 0;
          state     = STATE_CALIBRATED;
          break;
        }
      }
      #else
      // Forwards has a busted sensor, so ignore calibration
      #if SLAVE_ADDRESS == 14
      calState  = 0;
      state     = STATE_CALIBRATED;
      #else
      switch (calState)
      {
        case 0:
        {
          digitalWrite(PIN_DIRECTION, HIGH);
          analogWrite(PIN_PWM, ROTATION_CAL_SPEED);
          calState++;
          break;
        }

        case 1:
        {
          if (digitalRead(PIN_VERTICAL_SWITCH) == LOW)
          {
              analogWrite(PIN_PWM, 0);
              noInterrupts();
              pulses = 0;
              interrupts();
              calState++;
          }
          break;
        }

        default:
        {
          calState  = 0;
          state     = STATE_CALIBRATED;
          break;
        }
      }
      #endif
      #endif
      break;
    }
  
    case STATE_CALIBRATED:
    {
      noInterrupts();
      bool local_clockwise  = clockwise;
      byte local_speed      = speed;
      interrupts();

      #if SLAVE_MODE == 0
      if (digitalRead(PIN_INNER_SWITCH) == LOW)
      {
        noInterrupts();
        minimum_pulses = pulses;
        interrupts();
        if (!local_clockwise)
        {
            local_speed = 0;
        }
      }
      else if (digitalRead(PIN_OUTER_SWITCH) == LOW)
      {
        noInterrupts();
        maximum_pulses = pulses + 1;
        interrupts();
        if (local_clockwise)
        {
            local_speed = 0;
        }
      }
      else
      {
        if (pulses + 1 > maximum_pulses)
        {
            noInterrupts();
            maximum_pulses = pulses + 1;
            interrupts();
        }
        else if (pulses < minimum_pulses)
        {
            noInterrupts();
            minimum_pulses = pulses;
            interrupts();
        }
      }
      #endif

      digitalWrite(PIN_DIRECTION, local_clockwise ? HIGH : LOW);
      analogWrite(PIN_PWM, local_speed);
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
        case CMD_POKE:
        {
          break;
        }

        case CMD_HALT:
        {
          if (state == STATE_CALIBRATING)
          {
            state = STATE_UNCALIBRATED;
          }
          clockwise = false;
          speed     = 0;
          break;
        }

        case CMD_CALIBRATE:
        {
          state = STATE_CALIBRATING;
          break;
        }

        case CMD_SET_SPEED:
        {
          if (state == STATE_CALIBRATING)
          {
            state = STATE_UNCALIBRATED;
          }
          clockwise = (cmd[1] != 0);
          speed     = cmd[2];
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
    int norm_pulses      = pulses - minimum_pulses;
    int norm_max_pulses  = maximum_pulses - minimum_pulses;

    buffer[0] = (byte)( norm_pulses           & 0xFF);
    buffer[1] = (byte)((norm_pulses     >> 8) & 0xFF);
    buffer[2] = (byte)( norm_max_pulses       & 0xFF);
    buffer[3] = (byte)((norm_max_pulses >> 8) & 0xFF);
    buffer[4] = (state == STATE_CALIBRATED) ? STATUS_CALIBRATED : STATUS_UNCALIBRATED;
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


