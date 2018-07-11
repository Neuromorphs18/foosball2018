/*
 * Power requirements
 * 5v dc supply for Arduino, DRV8801 driver and Encoders
 * OPB705 Reflective Sensor
 * 12v dc for Motors
*/
#define rotate_dir 7
#define rotate_pwm 9
#define encoder_a 2
#define encoder_b 3
#define vert 6       // Vertical position sensor for player shaft

void setup()
{
 Serial.begin(9600);
 pinMode(rotate_dir, OUTPUT);
 pinMode(rotate_pwm, OUTPUT);
 pinMode(encoder_a, INPUT);
 pinMode(encoder_b, INPUT);
 //pinMode (vert, INPUT_PULLUP);
 delay(3000);                  //wait here until Slide has positioned at Inner Limit. Players must be at
 attachInterrupt(0, A_CHANGE, CHANGE);
 attachInterrupt(1, B_CHANGE, CHANGE);
 rotateInit();                  // inner Limit so that the Opto lines up with the heat shrink.
 delay(3000);                 // Wait here so that Slide moves player 
}

void rotateInit()
{
  digitalWrite(rotate_dir, HIGH); // Set direction to CW
  analogWrite(rotate_pwm, 85);    // 50 seems ok on bench as minimum @12v Vm
  delay(1000);                    // Rotate for 1 sec
  digitalWrite(rotate_dir, LOW);  // reverse direction
  delay(1000);                    // and rotate for another sec  
  analogWrite(rotate_pwm, 0);     // stop rotating
  delay(1000);
/*  while(digitalRead(vert) == HIGH) // Rotate until Vertical Opto is triggered
  {
    analogWrite(rotate_pwm, 75);   
  } */
  analogWrite(rotate_pwm, 0);
}

int spd = 0;
int dir = 0; 
void loop()
{
   if (Serial.available() >=2) {
     spd = Serial.read(); //reads uint8_t
     dir = Serial.read();
     if (dir > 0) {
       digitalWrite(rotate_dir, LOW);   //CCW
     } else {
       digitalWrite(rotate_dir, HIGH);   //CW
     }
   }
   //Serial.write(spd);
   analogWrite(rotate_pwm, spd);    //   
}

