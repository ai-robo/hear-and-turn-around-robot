#include <Servo.h>
Servo servo;
int angle;

void setup() {
  servo.attach(7);
  Serial.begin(115200);
  servo.write(0);

}

void loop() {
/*if (Serial.available() > 0)
  Serial.println("aboba!");
  delay(900);*/
  if (Serial.available() > 0) {
    angle = Serial.readString().toInt();
    servo.write(angle);
  }
}
