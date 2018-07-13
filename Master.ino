#include <Wire.h>

//##################################################################
// CONFIGURATION
//##################################################################
#define LED_FLASH_PERIOD_MS   1000
#define UPDATE_PERIOD_MS      50
#define SERIAL_SOF            0xAA

#define MSG_HALT              0xC0
#define MSG_CALIBRATE         0xC1
#define MSG_MOVE              0xC2
#define MSG_UPDATE            0xCA

#define STATUS_OFFLINE        0x50
#define STATUS_CRC_ERROR      0x51
#define STATUS_UNCALIBRATED   0x52
#define STATUS_CALIBRATED     0x53

#define CMD_HALT              0xF0
#define CMD_CALIBRATE         0xF1
#define CMD_MOVE              0xF2

//##################################################################
// GLOBAL VARIABLES
//##################################################################
bool slaveOnline[8] = {true, true, true, true, true, true, false, false};
byte serialBufferRx[256];
byte serialBufferTx[44];
byte i2cBuffer[6];

//##################################################################
// INITIALISATION
//##################################################################
void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  ledOn(true);
  
  Wire.begin();
  Wire.setClock(10000);
  Serial.begin(115200);
}

//##################################################################
// MAIN LOOP
//##################################################################
void loop()
{
  static unsigned long  ledTimestamp    = 0;
  static unsigned long  updateTimestamp = 0;
  static bool           ledState        = true;
  static byte           rxCnt           = 0;
  unsigned long         timeNow;
  byte                  idx;
  byte                  i;
  
  timeNow = millis();

  ///////////////////////////////////////////////////
  // Flash LED
  ///////////////////////////////////////////////////
  if ((timeNow - ledTimestamp) >= (LED_FLASH_PERIOD_MS/2))
  {
    ledTimestamp  = timeNow;
    ledState      = !ledState;
    //ledOn(ledState);
  }

  ///////////////////////////////////////////////////
  // Get Updates from All Slaves
  ///////////////////////////////////////////////////
  if ((timeNow - updateTimestamp) >= UPDATE_PERIOD_MS)
  {
    updateTimestamp = timeNow;

    serialBufferTx[0] = SERIAL_SOF;
    serialBufferTx[1] = MSG_UPDATE;
    serialBufferTx[2] = 4 + 40;
    idx               = 3;
    
    for (i = 0; i < 8; i++)
    {
      serialBufferTx[idx+4] = STATUS_OFFLINE;

      if (slaveOnline[i])
      {
        Wire.requestFrom(8 + i, 6);
        if (Wire.available() >= 6)
        {
          i2cBuffer[0] = Wire.read();
          i2cBuffer[1] = Wire.read();
          i2cBuffer[2] = Wire.read();
          i2cBuffer[3] = Wire.read();
          i2cBuffer[4] = Wire.read();
          i2cBuffer[5] = Wire.read();
          while (Wire.available())
          {
            Wire.read();
          }

          // Only accept packet if CRC is valid
          if (crcIsValid(i2cBuffer, 5, i2cBuffer[5]))
          {
            serialBufferTx[idx  ] = i2cBuffer[0];
            serialBufferTx[idx+1] = i2cBuffer[1];
            serialBufferTx[idx+2] = i2cBuffer[2];
            serialBufferTx[idx+3] = i2cBuffer[3];
            serialBufferTx[idx+4] = i2cBuffer[4];
          }
          else
          {
            serialBufferTx[idx+4] = STATUS_CRC_ERROR;
          }
        }
      }
      
      idx += 5;
    }

    serialBufferTx[idx] = crc(serialBufferTx, idx);
    Serial.write(serialBufferTx, ++idx);
  }

  ///////////////////////////////////////////////////
  // Process Commands from PC
  ///////////////////////////////////////////////////
  if (Serial.available())
  {
    serialBufferRx[rxCnt] = Serial.read();
    rxCnt++;
  }
  
  // Message must start with SOF character
  for (idx = 0; idx < rxCnt; idx++)
  {
    if (serialBufferRx[idx] == SERIAL_SOF)
    {
      break;
    }
  }

  // Shift buffer until first character is SOF
  if (idx != 0)
  {
    rxCnt -= idx;
    for (i = 0; i < rxCnt; i++)
    {
      serialBufferRx[i] = serialBufferRx[idx+i];
    }
  }
  
  // Message must be at least 4 bytes
  if (rxCnt >= 4)
  { 
    // Wait to receive entire message (including CRC)
    if (rxCnt >= serialBufferRx[2])
    {
      // Validate message integrity
      if (crcIsValid(serialBufferRx, rxCnt-1, serialBufferRx[rxCnt-1]))
      {
        // Process messages
        switch (serialBufferRx[1])
        {
          case MSG_HALT:
          {
            if (rxCnt == 4)
            {
              halt();
            }
            break;
          }
    
          case MSG_CALIBRATE:
          {
            if (rxCnt == 4)
            {
              calibrate();
            }
            break;
          }
    
          case MSG_MOVE:
          {
            if (rxCnt == 13)
            {
              sendSpeeds(serialBufferRx[3], &serialBufferRx[4]);
            }
            break;
          }
    
          default:
          {
            break;
          }
        }
      }

      // Move on to next packet in buffer
      serialBufferRx[0] = (byte)~SERIAL_SOF;
    }
  }
}

//##################################################################
// COMMANDS
//##################################################################
void halt(void)
{
  byte msg[4];
  msg[0] = CMD_HALT;
  msg[1] = 0;
  msg[2] = 0;
  msg[3] = crc(msg, 3);

  for (byte i = 0; i < 8; i++)
  {
    if (slaveOnline[i])
    {
      Wire.beginTransmission(8 + i);
      Wire.write(msg, 4);
      Wire.endTransmission();
    }
  }
}

void calibrate(void)
{
  byte msg[4];

  msg[0] = CMD_CALIBRATE;
  msg[1] = 0;
  msg[2] = 0;
  msg[3] = crc(msg, 3);

  for (byte i = 0; i < 8; i++)
  {
    if (slaveOnline[i])
    {
      Wire.beginTransmission(8 + i);
      Wire.write(msg, 4);
      Wire.endTransmission();

      // Wait for calibration to be done
      while (true)
      {
        delay(100);
        
        Wire.requestFrom(8 + i, 6);
        if (Wire.available() >= 6)
        {
          i2cBuffer[0] = Wire.read();
          i2cBuffer[1] = Wire.read();
          i2cBuffer[2] = Wire.read();
          i2cBuffer[3] = Wire.read();
          i2cBuffer[4] = Wire.read();
          i2cBuffer[5] = Wire.read();
          
          while (Wire.available())
          {
            Wire.read();
          }

          if (crcIsValid(i2cBuffer, 5, i2cBuffer[5]))
          {
            if (i2cBuffer[4] == STATUS_CALIBRATED)
            {
              break;
            }
          }
        }
      }
    }
  }
}

void sendSpeeds(byte direction, byte speed[])
{
  byte msg[4];
  msg[0] = CMD_MOVE;

  for (byte i = 0; i < 8; i++)
  {
    msg[1] = (direction >> i) & 0x01;
    msg[2] = speed[i];
    msg[3] = crc(msg, 3); 
     
    Wire.beginTransmission(8 + i);
    Wire.write(msg, 4);
    Wire.endTransmission();
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

