/*
 * Power requirements
 * 5v dc supply for Arduino, DRV8801 driver and Encoders
 * OPB705 Reflective Sensor
 * 12v dc for Motors
*/
#define rotate_dir 7
#define rotate_pwm 9
#define vert 6       // Vertical position sensor for player shaft

void setup()
{
 pinMode(rotate_dir, OUTPUT);
 pinMode(rotate_pwm, OUTPUT);
 Serial.begin(9600);
 //pinMode (vert, INPUT_PULLUP);
 delay(3000);                  //wait here until Slide has positioned at Inner Limit. Players must be at
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
void loop()
{
   //delay(10);
   spd = Serial.read(); //reads uint8_t
   if (spd != -1) {
     if (spd > 127) {spd -= 256;}
     if (spd < 0) {
       digitalWrite(rotate_dir, LOW);   //CCW
     } else {
       digitalWrite(rotate_dir, HIGH);   //CW
     }
     spd = abs(spd);
     //Serial.write(spd);
     analogWrite(rotate_pwm, spd);    //
   }
}

