/*
Interface wtih Python through COM port communication
Read input
*/

int userCommand = 0;

// the setup function runs once when you press reset or power the board
void setup() {
  Serial.begin(9600);
  // initialize digital pin 9 as an output.
  pinMode(12, OUTPUT);
  // initial state
  digitalWrite (12,LOW);
}

// the loop function runs over and over again forever
void loop() {
  while (Serial.available()){
    userCommand = Serial.read();
    if (userCommand == '1'){
        digitalWrite(12, HIGH);   // turn the LED on (HIGH is the voltage level)
        //delay(1000);                       // wait for a second
    }
    if (userCommand == '0'){
        digitalWrite(12, LOW);    // turn the LED off by making the voltage LOW
        //delay(1000);                       // wait for a second
    }
    if (userCommand == '2'){
        digitalWrite(12, HIGH);    // turn the LED ON and OFF for one cycle
        delay(1000);
        digitalWrite(12, LOW);
        delay(1000);// wait for a second
//        digitalWrite(9, HIGH);    // turn the LED off by making the voltage LOW
//        delay(1000);
//        digitalWrite(9, LOW);
    }
  }
}
