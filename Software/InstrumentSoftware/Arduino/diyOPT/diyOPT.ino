/****************************************************************************** 
AIBSopt optDriverBoard shield sketch.
Drives stepper motor with BigEasyDriver.
Toggles pins for illumination through channels 1-5. 

Motor driver code based on:

SparkFun Big Easy Driver Basic Demo
Toni Klopfenstein @ SparkFun Electronics
February 2015
https://github.com/sparkfun/Big_Easy_Driver

PRNicovich
Allen Institute for Brain Science
2019

******************************************************************************/
//Declare pin functions on Arduino
#define stp 2
#define dir 3
#define MS1 4
#define MS2 5
#define MS3 6
#define EN  7
#define btn 15
#define led 13
#define chan1 10
#define chan2 8
#define chan3 9
#define chan4 11
#define chan5 12

//Declare variables for functions
char user_input;
int x;
int y;
int state;

int buttonState;             // the current reading from the input pin
int lastButtonState = LOW;
unsigned long lastDebounceTime = 0;  // the last time the output pin was toggled
unsigned long debounceDelay = 50;    // the debounce time; increase if the output flickers

void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  pinMode(MS1, OUTPUT);
  pinMode(MS2, OUTPUT);
  pinMode(MS3, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(btn, INPUT);
  pinMode(led, OUTPUT);
  pinMode(chan1, OUTPUT);
  pinMode(chan2, OUTPUT);
  pinMode(chan3, OUTPUT);
  pinMode(chan4, OUTPUT);
  pinMode(chan5, OUTPUT);

  digitalWrite(EN, LOW); //Pull enable pin low to set FETs active and allow motor control

  digitalWrite(chan1, LOW);
  digitalWrite(chan2, LOW);
  digitalWrite(chan3, LOW);
  digitalWrite(chan4, LOW);
  digitalWrite(chan5, LOW);
  
  resetBEDPins(); //Set step, direction, microstep and enable pins to default states
  
  Serial.begin(9600); //Open Serial connection for debugging
  Serial.println("Begin motor control");
  Serial.println();
  //Print function list for user selection
  Serial.println("Enter number for control option:");
  Serial.println("1. Turn at default microstep mode.");
  Serial.println("2. Reverse direction at default microstep mode.");
  Serial.println("3. Turn at 1/16th microstep mode.");
  Serial.println("4. Step forward and reverse directions.");
  Serial.println("5. Step default step forward.");
  Serial.println("6. Step default step reverse.");
  Serial.println("7. Step micro step forward.");
  Serial.println("8. Step micro step reverse.");
  Serial.println("9. Step 16 x 1/16th microsteps forward.");
  Serial.println("A. Step 16 x 1/16th microsteps reverse.");
  Serial.println();
}

//Main loop
void loop() {
  while(Serial.available()){
      user_input = Serial.read(); //Read user input and trigger appropriate function
      
      if (user_input =='1')
      {
         StepForwardDefault();
      }
      else if(user_input =='2')
      {
        ReverseStepDefault();
      }
      else if(user_input =='3')
      {
        SmallStepMode();
      }
      else if(user_input =='4')
      {
        ForwardBackwardStep();
      }
      else if(user_input =='5')
      {
        ForwardSingleStepDefault();
      }
      else if(user_input =='6')
      {
        ReverseSingleStepDefault();
      }
      else if(user_input =='7')
      {
        ForwardSingleStepMicrostep();
      }
      else if(user_input =='8')
      {
        ReverseSingleStepMicrostep();
      }
      else if(user_input =='9')
      {
        SixteenMicrostepsForward();
      }
      else if(user_input =='A')
      {
        SixteenMicrostepsForward();
      }
      else if(user_input == 'T')
      {
        digitalWrite(chan1, HIGH);
      }
      else if(user_input == 't')
      {
        digitalWrite(chan1, LOW);
      }
      else if(user_input == 'F')
      {
        digitalWrite(chan2, HIGH);
      }
      else if(user_input == 'f')
      {
        digitalWrite(chan2, LOW);
      }
      else if(user_input == 'G')
      {
        digitalWrite(chan3, HIGH);
      }
      else if(user_input == 'g')
      {
        digitalWrite(chan3, LOW);
      }
      else if(user_input == 'H')
      {
        digitalWrite(chan4, HIGH);
      }
      else if(user_input == 'h')
      {
        digitalWrite(chan4, LOW);
      }
      else if(user_input == 'J')
      {
        digitalWrite(chan5, HIGH);
      }
      else if(user_input == 'j')
      {
        digitalWrite(chan5, LOW);
      }

      else if (user_input == '\n'){
        // if newline char do nothing
      }
      
      else
      {
        Serial.println("Invalid option entered.");
      } 
      } // serial available


      int reading = digitalRead(btn);
      if (reading != lastButtonState) {

          // State change here
          lastDebounceTime = millis();
          
          //Serial.println("bounce");
          
          }

      if ((millis() - lastDebounceTime) > debounceDelay) {

          if (reading == HIGH) {
            
            ledToggle(reading);
            
            ReverseSingleStepDefault();
          }
          else if (reading == LOW) {
            ledToggle(reading);
          }
          
      }   

      lastButtonState = reading;
      
      
  }

void ledToggle(bool state){
  digitalWrite(led, state);
}


//Reset Big Easy Driver pins to default states
void resetBEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
  digitalWrite(MS1, LOW);
  digitalWrite(MS2, LOW);
  digitalWrite(MS3, LOW);
 // digitalWrite(EN, HIGH);
}

//Default microstep mode function
void StepForwardDefault()
{
  Serial.println("Moving forward at default step mode.");
  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
  for(x= 1; x<1000; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  Serial.println("Enter new option");
  Serial.println();
}

//Reverse default microstep mode function
void ReverseStepDefault()
{
  Serial.println("Moving in reverse at default step mode.");
  digitalWrite(dir, HIGH); //Pull direction pin high to move in "reverse"
  for(x= 1; x<1000; x++)  //Loop the stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  Serial.println("Enter new option");
  Serial.println();
}

// 1/16th microstep foward mode function
void SmallStepMode()
{
  Serial.println("Stepping at 1/16th microstep mode.");
  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
  digitalWrite(MS1, HIGH); //Pull MS1,MS2, and MS3 high to set logic to 1/16th microstep resolution
  digitalWrite(MS2, HIGH);
  digitalWrite(MS3, HIGH);
  for(x= 1; x<1000; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  Serial.println("Enter new option");
  Serial.println();
}

//Forward/reverse stepping function
void ForwardBackwardStep()
{
  Serial.println("Alternate between stepping forward and reverse.");
  for(x= 1; x<5; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    //Read direction pin state and change it
    state=digitalRead(dir);
    if(state == HIGH)
    {
      digitalWrite(dir, LOW);
    }
    else if(state ==LOW)
    {
      digitalWrite(dir,HIGH);
    }
    
    for(y=1; y<1000; y++)
    {
      digitalWrite(stp,HIGH); //Trigger one step
      delay(1);
      digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
      delay(1);
    }
  }
  resetBEDPins();
  Serial.println("Enter new option");
  Serial.println();
}

//One standard step forward
void ForwardSingleStepDefault()
{
  Serial.println("step");
  //Serial.println("Moving forward at default step mode.");
  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
  for(x= 1; x<2; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  //Serial.println("Enter new option");
  Serial.println();
}

//Reverse default microstep mode function
void ReverseSingleStepDefault()
{
 // Serial.println("Moving in reverse at default step mode.");
  digitalWrite(dir, HIGH); //Pull direction pin high to move in "reverse"
  for(x= 1; x<2; x++)  //Loop the stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  //Serial.println("Enter new option");
  Serial.println();
}

//One 1/16th microstep step forward
void ForwardSingleStepMicrostep()
{
 // Serial.println("Moving forward at default step mode.");
  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
  digitalWrite(MS1, HIGH); //Pull MS1,MS2, and MS3 high to set logic to 1/16th microstep resolution
  digitalWrite(MS2, HIGH);
  digitalWrite(MS3, HIGH);
  for(x= 1; x<2; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  //Serial.println("Enter new option");
  Serial.println();
}

//Reverse 1/16th microstep mode single step
void ReverseSingleStepMicrostep()
{
 // Serial.println("Moving in reverse at default step mode.");
  digitalWrite(dir, HIGH); //Pull direction pin high to move in "reverse"
  digitalWrite(MS1, HIGH); //Pull MS1,MS2, and MS3 high to set logic to 1/16th microstep resolution
  digitalWrite(MS2, HIGH);
  digitalWrite(MS3, HIGH);
  for(x= 1; x<2; x++)  //Loop the stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  //Serial.println("Enter new option");
  Serial.println();
}

//Sixteen 1/16th microsteps step forward
void SixteenMicrostepsForward()
{
 // Serial.println("Moving forward at default step mode.");
  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
  digitalWrite(MS1, HIGH); //Pull MS1,MS2, and MS3 high to set logic to 1/16th microstep resolution
  digitalWrite(MS2, HIGH);
  digitalWrite(MS3, HIGH);
  for(x= 0; x<16; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  //Serial.println("Enter new option");
  Serial.println();
}

//Sixteen 1/16th microsteps step reverse
void SixteenMicrostepsReverse()
{
 // Serial.println("Moving forward at default step mode.");
  digitalWrite(dir, HIGH); //Pull direction pin low to move "forward"
  digitalWrite(MS1, HIGH); //Pull MS1,MS2, and MS3 high to set logic to 1/16th microstep resolution
  digitalWrite(MS2, HIGH);
  digitalWrite(MS3, HIGH);
  for(x= 0; x<16; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delay(1);
  }
  resetBEDPins();
  //Serial.println("Enter new option");
  Serial.println();
}
