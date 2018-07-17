#include <Wire.h>

//##################################################################
// CONFIGURATION
//##################################################################
#define LED_FLASH_PERIOD_MS     1000
#define UPDATE_PERIOD_MS        10
#define I2C_BASE_ADDRESS        12          // 8 or 12 for Defenders or Attackers
#define I2C_NUM_SLAVES          4
#define I2C_TIMEOUT_MS          25
#define I2C_SLAVE_EN_1          true
#define I2C_SLAVE_EN_2          true
#define I2C_SLAVE_EN_3          false
#define I2C_SLAVE_EN_4          false
#define SERIAL_SOF              0xAA
#define SERIAL_MAX_PKT_LENGTH   32

#define MSG_HALT                0xC0
#define MSG_CALIBRATE           0xC1
#define MSG_SLIDE               0xC2
#define MSG_KICK                0xC3
#define MSG_CAL_DONE            0xCA
#define MSG_POSITION            0xCB

#define STATUS_OFFLINE          0x50
#define STATUS_CRC_ERROR        0x51
#define STATUS_UNCALIBRATED     0x52
#define STATUS_CALIBRATED       0x53

#define CMD_HALT                0xF0
#define CMD_CALIBRATE           0xF1
#define CMD_SLIDE               0xF2
#define CMD_KICK                0xF3
#define RESP_ACK                0xFA
#define RESP_NACK               0xFB

//##################################################################
// GLOBAL VARIABLES
//##################################################################
byte          serialBufferRx[128];
byte          serialBufferTx[44];
bool          i2cSlaveOnline[I2C_NUM_SLAVES] = {I2C_SLAVE_EN_1, I2C_SLAVE_EN_2, I2C_SLAVE_EN_3, I2C_SLAVE_EN_4};
byte          i2cBuffer[6];
bool          i2cSuccess;
unsigned long i2cTimestamp;

//##################################################################
// INITIALISATION
//##################################################################
void setup()
{
  byte i;
  byte cnt;

  pinMode(LED_BUILTIN, OUTPUT);
  ledOn(true);
  
  Wire.begin();
  Serial.begin(115200);

  // Determine which slaves are available
  // Make 2 attempts to get a response
  //poke(2);
}

//##################################################################
// MAIN LOOP
//##################################################################
void loop()
{
  static bool           forceSpeedUpdate  = true;
  static unsigned long  ledTimestamp      = 0;
  static unsigned long  updateTimestamp   = 0;
  static bool           ledState          = true;
  static byte           rxCnt             = 0;
  unsigned long         timeNow;
  byte                  cnt;
  byte                  idx;
  byte                  i;
  byte                  pktLen;
  
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
  // Get Updates from All Slaves
  ///////////////////////////////////////////////////
  if ((timeNow - updateTimestamp) >= UPDATE_PERIOD_MS)
  {
    updateTimestamp = timeNow;

    serialBufferTx[0] = SERIAL_SOF;
    serialBufferTx[1] = MSG_POSITION;
    serialBufferTx[2] = 4 + (5 * I2C_NUM_SLAVES);
    cnt               = 3;
    
    for (i = 0; i < I2C_NUM_SLAVES; i++)
    {
      serialBufferTx[cnt+4] = STATUS_OFFLINE;

      // Request position and status update from slave
      if (i2cSlaveOnline[i])
      {
        Wire.requestFrom(I2C_BASE_ADDRESS + i, 6);
        idx = 0;
        i2cTimestamp = millis();
        while ((millis() - i2cTimestamp) < I2C_TIMEOUT_MS)
        {
          if (Wire.available())
          {
            i2cBuffer[idx] = Wire.read();
            idx++;
          }

          if (idx == 6)
          {         
            while (Wire.available()) Wire.read();
             
            // Only accept packet if CRC is valid
            if (crcIsValid(i2cBuffer, 5, i2cBuffer[5]))
            {
              serialBufferTx[cnt  ] = i2cBuffer[0];
              serialBufferTx[cnt+1] = i2cBuffer[1];
              serialBufferTx[cnt+2] = i2cBuffer[2];
              serialBufferTx[cnt+3] = i2cBuffer[3];
              serialBufferTx[cnt+4] = i2cBuffer[4] == 0x01 ? STATUS_CALIBRATED : STATUS_UNCALIBRATED;
            }
            else
            {
              serialBufferTx[cnt+4] = STATUS_CRC_ERROR;
            }

            break;
          }
        }
      }
      
      cnt += 5;
    }

    serialBufferTx[cnt] = crc(serialBufferTx, cnt);
    Serial.write(serialBufferTx, ++cnt);
  }

  ///////////////////////////////////////////////////
  // Process Commands from PC
  ///////////////////////////////////////////////////
  while (Serial.available())
  {
    serialBufferRx[rxCnt] = Serial.read();
    rxCnt++;
  }

  // Message must be at least 4 bytes
  if (rxCnt >= 4)
  {
    idx = 0;
    
    // Message must start with SOF character
    if (serialBufferRx[0] == SERIAL_SOF)
    {
      // Packet length must be less than the max
      pktLen = serialBufferRx[2];
      if (pktLen <= SERIAL_MAX_PKT_LENGTH)
      {
        // Receive entire message packet (including CRC)
        if (rxCnt >= pktLen)
        {
          // Validate message integrity
          if (crcIsValid(serialBufferRx, pktLen-1, serialBufferRx[pktLen-1]))
          {
            // Process message
            switch (serialBufferRx[1])
            {
              case MSG_HALT:
              {
                if (pktLen == 4)
                {
                  halt();
                }
                break;
              }
        
              case MSG_CALIBRATE:
              {
                if (pktLen == 4)
                {
                  calibrate();
                }
                break;
              }
        
              case MSG_SLIDE:
              {
                if (pktLen == 7)
                {
                  int pos = (((int)serialBufferRx[5])<<8) | ((int)serialBufferRx[4]);
                  slide(serialBufferRx[3], pos);
                }
                break;
              }

              case MSG_KICK:
              {
                if (pktLen == 5)
                {
                  kick(serialBufferRx[3]);
                }
              }
        
              default:
              {
                break;
              }
            }

            idx = pktLen;   // Trim message
          }
          else
          {
            idx = 1;  // Trim SOF and start looking for the next packet
          }
        }
      }
      else
      {
        idx = 2;    // Trim SOF and invalid packet length
      }
    }
    else
    {
      idx = 1;  // Trim invalid SOF
    }

    // Shift buffer until first character is SOF
    if (idx != 0)
    {
      for (; idx < rxCnt; idx++)
      {
        if (serialBufferRx[idx] == SERIAL_SOF)
        {
          break;
        }
      }
  
      rxCnt -= idx;
      for (i = 0; i < rxCnt; i++)
      {
        serialBufferRx[i] = serialBufferRx[idx+i];
      }
    }
  }
}

//##################################################################
// COMMANDS
//##################################################################
void halt(void)
{
  byte msg[4];
  byte i;

  msg[0] = CMD_HALT;
  msg[1] = 0;
  msg[2] = 0;
  msg[3] = crc(msg, 3);

  for (i = 0; i < I2C_NUM_SLAVES; i++)
  {
    if (i2cSlaveOnline[i])
    {
      i2cSuccess = false;
      while (!i2cSuccess)
      {
        Wire.beginTransmission(I2C_BASE_ADDRESS + i);
        Wire.write(msg, 4);
        Wire.endTransmission();

        Wire.requestFrom(I2C_BASE_ADDRESS + i, 2);
        i2cTimestamp = millis();
        while ((millis() - i2cTimestamp) < I2C_TIMEOUT_MS)
        {
          if (Wire.available() >= 2)
          {
            i2cBuffer[0] = Wire.read();
            i2cBuffer[1] = Wire.read();
            while (Wire.available()) Wire.read();

            if ((i2cBuffer[0] == RESP_ACK) && (i2cBuffer[1] == ((byte)~RESP_ACK)))
            {
              i2cSuccess = true;
            }
            break;
          }
        }
      }
    }
  }
}

void calibrate(void)
{
  byte msg[4];
  byte i;
  byte idx;

  msg[0] = CMD_CALIBRATE;
  msg[1] = 0;
  msg[2] = 0;
  msg[3] = crc(msg, 3);

  for (i = 0; i < I2C_NUM_SLAVES; i++)
  {
    if (i2cSlaveOnline[i])
    {  
      // Send command to slave
      i2cSuccess = false;
      while (!i2cSuccess)
      {
        Wire.beginTransmission(I2C_BASE_ADDRESS + i);
        Wire.write(msg, 4);
        Wire.endTransmission();

        Wire.requestFrom(I2C_BASE_ADDRESS + i, 2);
        i2cTimestamp = millis();
        while ((millis() - i2cTimestamp) < I2C_TIMEOUT_MS)
        {
          if (Wire.available() >= 2)
          {
            i2cBuffer[0] = Wire.read();
            i2cBuffer[1] = Wire.read();
            while (Wire.available()) Wire.read();
            
            if ((i2cBuffer[0] == RESP_ACK) && (i2cBuffer[1] == ((byte)~RESP_ACK)))
            {
              i2cSuccess = true;
            }

            break;
          }
        }
      }

      // Wait for calibration to be done
      i2cSuccess = false;
      while (!i2cSuccess)
      {
        delay(100);

        Wire.requestFrom(I2C_BASE_ADDRESS + i, 6);
        idx = 0;
        i2cTimestamp = millis();
        while ((millis() - i2cTimestamp) < I2C_TIMEOUT_MS)
        {
          if (Wire.available())
          {
            i2cBuffer[idx] = Wire.read();
            idx++;
          }

          if (idx == 6)
          {
            while (Wire.available()) Wire.read();
            
            if (crcIsValid(i2cBuffer, 5, i2cBuffer[5]))
            {
              if (i2cBuffer[4] == 0x01)
              {
                i2cSuccess = true;
              }
            }

            break;
          }
        }
      }
    }
  }

  serialBufferTx[0] = SERIAL_SOF;
  serialBufferTx[1] = MSG_CAL_DONE;
  serialBufferTx[2] = 4;
  serialBufferTx[3] = crc(serialBufferTx, 3);
  Serial.write(serialBufferTx, 4);
}

void slide(byte index, int position)
{
  byte msg[4];

  if (index == 0)
  {
    index = 0;
  }
  else if (index == 1)
  {
    index = 2;
  }
  else
  {
    return;
  }

  msg[0] = CMD_SLIDE;
  msg[1] = (byte)position;
  msg[2] = (byte)(position >> 8);
  msg[3] = crc(msg, 3);

  if (i2cSlaveOnline[index])
  {
    i2cSuccess = false;
    while (!i2cSuccess)
    {
      Wire.beginTransmission(I2C_BASE_ADDRESS + index);
      Wire.write(msg, 4);
      Wire.endTransmission();

      Wire.requestFrom(I2C_BASE_ADDRESS + index, 2);
      i2cTimestamp = millis();
      while ((millis() - i2cTimestamp) < I2C_TIMEOUT_MS)
      {
        if (Wire.available() >= 2)
        {
          i2cBuffer[0] = Wire.read();
          i2cBuffer[1] = Wire.read();
          while (Wire.available()) Wire.read();

          if ((i2cBuffer[0] == RESP_ACK) && (i2cBuffer[1] == ((byte)~RESP_ACK)))
          {
            i2cSuccess = true;
          }
          break;
        }
      }
    }
  }
}

void kick(byte index)
{
  byte msg[4];
  byte i;

  if (index == 0)
  {
    index = 1;
  }
  else if (index == 1)
  {
    index = 3;
  }
  else
  {
    return;
  }

  msg[0] = CMD_KICK;
  msg[1] = 0;
  msg[2] = 0;
  msg[3] = crc(msg, 3);

  if (i2cSlaveOnline[index])
  {
    i2cSuccess = false;
    while (!i2cSuccess)
    {
      Wire.beginTransmission(I2C_BASE_ADDRESS + index);
      Wire.write(msg, 4);
      Wire.endTransmission();

      Wire.requestFrom(I2C_BASE_ADDRESS + index, 2);
      i2cTimestamp = millis();
      while ((millis() - i2cTimestamp) < I2C_TIMEOUT_MS)
      {
        if (Wire.available() >= 2)
        {
          i2cBuffer[0] = Wire.read();
          i2cBuffer[1] = Wire.read();
          while (Wire.available()) Wire.read();

          if ((i2cBuffer[0] == RESP_ACK) && (i2cBuffer[1] == ((byte)~RESP_ACK)))
          {
            i2cSuccess = true;
          }
          break;
        }
      }
    }
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

