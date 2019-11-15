//Distance & Weight Sensor Main Program
#include "HX711.h"
#define calibration_factor 7000 //#define calibration_factor 7000
#define DOUT  3
#define CLK  2
HX711 scale;

#include <NewPing.h>
// defines pins numbers
const int trigPin = 12;
const int echoPin = 11;
// defines variables
long duration;
int distance;

void setup() {
  Serial.begin(9600);
  scale.begin(DOUT, CLK);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  Serial.begin(9600); // Starts the serial communication
}

void loop() {
  Serial.print("Weight: ");
  Serial.print(scale.get_units(), 1); //scale.get_units() returns a float
  Serial.print(" lbs");
  // Clears the trigPin
  digitalWrite(trigPin, LOW); 
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  // Calculating the distance in cm
  distance= duration*0.034/2;
  // Prints the distance on the Serial Monitor
  Serial.print("          ");
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.print(" cm");
  Serial.println();
  delay(1000);
}
