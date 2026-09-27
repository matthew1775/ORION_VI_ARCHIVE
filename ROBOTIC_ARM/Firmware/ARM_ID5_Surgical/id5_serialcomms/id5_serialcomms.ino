#include <Arduino.h>
#include <ESP32Servo.h>

// Konfiguracja pinów PWM (ESP32)
const int PIN_SERVO_ROLL  = 25;
const int PIN_SERVO_PITCH = 26;
const int PIN_SERVO_GRIP1 = 13;
const int PIN_SERVO_GRIP2 = 12;

Servo servos[4];
const int servoPins[4] = {PIN_SERVO_ROLL, PIN_SERVO_PITCH, PIN_SERVO_GRIP1, PIN_SERVO_GRIP2};

// Zmienne do sterowania
int targetPWM[4] = {1520, 1520, 1520, 1520};   
float actualPWM[4] = {1520, 1520, 1520, 1520}; 

unsigned long lastKeyTime = 0;
const int TIMEOUT_MS = 200; 

// --- POPRAWIONE ZMIENNE PRĘDKOŚCI ---
unsigned long lastMoveTime = 0;
const int MOVE_INTERVAL = 20;  // 20ms idealnie odpowiada taktowaniu serwa 50Hz!
const float STEP_SPEED = 10.0;  // Szybkość ruchu. (4.0 co 20ms = płynny ruch do pełnego wychylenia w ~0.7 sekundy)

void setup() {
  Serial.begin(115200);
  Serial.println("Start. Trzymaj klawisze: W/S, E/D, R/F, T/G. Pusc, aby zatrzymac.");

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for(int i = 0; i < 4; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(servoPins[i], 500, 2500);
    servos[i].writeMicroseconds(1500); 
  }
}

const float COUPLING_PITCH_JAW1 = 0.8;
const float COUPLING_PITCH_JAW2 = 0.5;

void loop() {
  // 1. Sprawdzanie znaków z portu szeregowego
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd != '\n' && cmd != '\r') {
      lastKeyTime = millis(); 

      switch (cmd) {
        case 'w': case 'W': targetPWM[0] = 1650; break;
        case 's': case 'S': targetPWM[0] = 1370; break;
        
        case 'r': case 'R': 
          targetPWM[2] = 1650; targetPWM[3] = 1650; 
          break;
        case 'f': case 'F': 
          targetPWM[2] = 1370; targetPWM[3] = 1370; 
          break;
        
        case 't': case 'T': 
          targetPWM[2] = 1600; targetPWM[3] = 1370; 
          break;
        case 'g': case 'G': 
          targetPWM[2] = 1370; targetPWM[3] = 1600; 
          break;

        case 'e': case 'E': 
          targetPWM[1] = 1650; 
          targetPWM[2] = 1520 + (150 * COUPLING_PITCH_JAW2); 
          targetPWM[3] = 1520 + (-150 * COUPLING_PITCH_JAW1); 
          break;
        case 'd': case 'D': 
          targetPWM[1] = 1370; 
          targetPWM[2] = 1520 - (150 * COUPLING_PITCH_JAW1); 
          targetPWM[3] = 1520 - (-150 * COUPLING_PITCH_JAW2); 
          break;
      }
    }
  }

  // 2. TIMEOUT (zatrzymanie po puszczeniu klawisza)
  if (millis() - lastKeyTime > TIMEOUT_MS) {
    for (int i = 0; i < 4; i++) targetPWM[i] = 1520;
  }

  // 3. PŁYNNY RUCH (Dopasowany do sprzętu)
  if (millis() - lastMoveTime >= MOVE_INTERVAL) {
    lastMoveTime = millis();
    
    for (int i = 0; i < 4; i++) {
      bool needUpdate = false; // flaga sprawdzająca, czy pozycja się zmieniła

      if (actualPWM[i] < targetPWM[i]) {
        actualPWM[i] += STEP_SPEED;
        if (actualPWM[i] > targetPWM[i]) actualPWM[i] = targetPWM[i]; 
        needUpdate = true;
      } 
      else if (actualPWM[i] > targetPWM[i]) {
        actualPWM[i] -= STEP_SPEED;
        if (actualPWM[i] < targetPWM[i]) actualPWM[i] = targetPWM[i];
        needUpdate = true;
      }
      
      // Aktualizujemy sygnał PWM tylko jeśli serwo ma się przesunąć
      if (needUpdate) {
        servos[i].writeMicroseconds((int)actualPWM[i]);
      }
    }
  }
}