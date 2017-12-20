// Arduino Script

// Direction : 0 => forward, 1 => backward
int lwd = 2;  // LW direction - black 
int lwa = 3;  // LW activator - brown
int rwa = 4;  // RW activator - white
int rwd = 5;  // RW direction - gray

int bzp = 11; // Buzzer pin
int ifr = 8;  // Infrared pin

void setup() {  
  // Buzzer pin
  pinMode(bzp,OUTPUT);

  // Infrared pin
  pinMode(ifr,INPUT);
  
  // H bridge pins
  pinMode(lwd,OUTPUT); 
  pinMode(lwa,OUTPUT); 
  pinMode(rwa,OUTPUT); 
  pinMode(rwd,OUTPUT);

  Serial.begin(9600);  
}

void enable_wheels_fwd() {
  digitalWrite(lwd, LOW);
  digitalWrite(lwa, HIGH);
  digitalWrite(rwa, HIGH);
  digitalWrite(rwd, LOW);
}

void enable_wheels_rgt() {
  digitalWrite(lwd, LOW);
  digitalWrite(lwa, HIGH);
  digitalWrite(rwa, LOW);
  digitalWrite(rwd, LOW);
}

void enable_wheels_lft() {
  digitalWrite(lwd, LOW);
  digitalWrite(lwa, LOW);
  digitalWrite(rwa, HIGH);
  digitalWrite(rwd, LOW);
}

int blocked() {
  return digitalRead(ifr) != 1;
}

void forward(int msecs) {
  enable_wheels_fwd();
  while (msecs--) {
    if (blocked()) {
      stop();
      while (blocked());
      enable_wheels_fwd();
    }
    delay(1);
  }
  
  stop();
}

void backward(int msecs) {
  digitalWrite(lwd, HIGH);
  digitalWrite(lwa, HIGH);
  digitalWrite(rwa, HIGH);
  digitalWrite(rwd, HIGH);

  delay(msecs);
  stop();
}

void turn_right(int msecs) {
  enable_wheels_rgt();
  while (msecs--) {
    if (blocked()) {
      stop();
      while (blocked());
      enable_wheels_rgt();
    }
    delay(1);
  }
  
  stop();
}

void turn_left(int msecs) {
  enable_wheels_lft();
  while (msecs--) {
    if (blocked()) {
      stop();
      while (blocked());
      enable_wheels_lft();
    }
    delay(1);
  }
  
  stop();
}

void stop() {
  digitalWrite(lwd, LOW);
  digitalWrite(lwa, LOW);
  digitalWrite(rwa, LOW);
  digitalWrite(rwd, LOW);
}

void beep(int times) {
  for(int i=0; i<times; i++) {
    tone(bzp, 262, 100); // pin, freq, time
    delay(200);
  }
}

void forward_until_block() {
  enable_wheels_fwd();
  while (1) {
    if (blocked()) {
      stop();
      int timer = 1500;
      while (timer && blocked()) {
        timer--;
        delay(1);
      }
      if (!timer)
        break;
      enable_wheels_fwd();
    }
    delay(1);
  }
  
  stop();
  beep(3);
}

void exec_cmd(int cmd, int param) {
  switch (cmd) {
      
    case 1:
      forward(param);
      break;
    
    case 2:
      turn_right(param);
      break;
    
    case 3:
      turn_left(param);
      break; 
    
    case 4:
      backward(param);
      break;
    
    case 5:
      beep(param);
      break;
    
    case 6:
      forward_until_block();
      break;
    
    default:
      stop();
    
  }
}

void serialEvent() {    
  int cmd, param = 0;
  
  while (Serial.available()) {
    // Catching command
    cmd = Serial.read();
    cmd -= '0';
  
    if (cmd && cmd != 6) {
      while (!Serial.available());
      
      // Catching parameter
      param = Serial.read();
      param -= '0';
      param++;
      
      if(cmd != 5)
        param *= 10;
    }
    
    // Executing command
    exec_cmd(cmd, param);
  }
}

void loop() {
  serialEvent();
}

