#include <Arduino.h>
#include <ESP32Servo.h>

// --- Konfiguracja pinów PWM (ESP32) ---
const int PIN_SERVO_ROLL  = 25;
const int PIN_SERVO_PITCH = 26;
const int PIN_SERVO_GRIP1 = 13;
const int PIN_SERVO_GRIP2 = 12;

Servo servos[4];
const int servoPins[4] = {PIN_SERVO_ROLL, PIN_SERVO_PITCH, PIN_SERVO_GRIP1, PIN_SERVO_GRIP2};

// --- Zmienne do sterowania ---
int currentPWM[4] = {1500, 1500, 1500, 1500};
unsigned long lastKeyTime = 0;
const int TIMEOUT_MS = 200; // Czas po puszczeniu klawisza, po którym serwa stają

// --- Zmienne do spowalniania (PULSOWANIE) ---
const unsigned long T_ACTIVE = 40;   // Czas ruchu (ms) - impuls poruszający
const unsigned long T_PAUSE  = 10;  // Czas postoju (ms) - wymuszenie STOP (zwiększ aby zwolnić bardziej)
unsigned long lastToggleTime = 0;
bool isPulseActive = false;          // Flaga określająca, czy aktualnie wysyłamy sygnał ruchu czy stopu

// --- Współczynniki (Coupling) ---
const float COUPLING_PITCH_JAW1 = 0.8;
const float COUPLING_PITCH_JAW2 = 0.5;
const float RATIO_PITCH = 2.0;
const float RATIO_JAW = 2.0;

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
    servos[i].writeMicroseconds(1500); // Pozycja spoczynkowa (STOP)
  }
}

void loop() {
  // 1. Sprawdzanie czy przyszedł nowy znak
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    // Ignorowanie znaków końca linii
    if (cmd != '\n' && cmd != '\r') {
      lastKeyTime = millis(); // Zresetuj timer, bo trzymasz klawisz

      // Przypisanie "docelowego" PWM (1500 to pozycja neutralna)
      switch (cmd) {
        // --- BAZOWE STEROWANIE ---
        case 'w': case 'W': 
          currentPWM[0] = 1650; 
          break;
        case 's': case 'S': 
          currentPWM[0] = 1350; 
          break;
        
        // --- OTWIERANIE / ZAMYKANIE SZCZĘK (r/f) ---
        case 'r': case 'R': 
          currentPWM[2] = 1650; 
          currentPWM[3] = 1650; 
          break;
        case 'f': case 'F': 
          currentPWM[2] = 1350; 
          currentPWM[3] = 1350; 
          break;
        
        // --- PRAWO / LEWO (t/g) ---
        case 't': case 'T': 
          currentPWM[2] = 1600; 
          currentPWM[3] = 1350; 
          break;
        case 'g': case 'G': 
          currentPWM[2] = 1350; 
          currentPWM[3] = 1600; 
          break;

        // --- RUCH Z KOMPENSACJĄ / COUPLING (e/d) ---
        case 'e': case 'E': 
          currentPWM[1] = 1650; 
          currentPWM[2] = 1500 + (150 * COUPLING_PITCH_JAW2); 
          currentPWM[3] = 1500 + (-150 * COUPLING_PITCH_JAW1); 
          break;
        case 'd': case 'D': 
          currentPWM[1] = 1350; 
          currentPWM[2] = 1500 - (150 * COUPLING_PITCH_JAW1); 
          currentPWM[3] = 1500 - (-150 * COUPLING_PITCH_JAW2); 
          break;
      }
    }
  }

  // 2. TIMEOUT - Jeśli od 200ms nie przyszedł żaden znak, zresetuj docelowe PWM na 1500
  if (millis() - lastKeyTime > TIMEOUT_MS) {
    currentPWM[0] = 1500;
    currentPWM[1] = 1500;
    currentPWM[2] = 1500;
    currentPWM[3] = 1500;
  }

  // 3. LOGIKA PULSOWANIA (SPOWALNIANIA)
  unsigned long currentMillis = millis();
  unsigned long currentInterval = isPulseActive ? T_ACTIVE : T_PAUSE;

  if (currentMillis - lastToggleTime >= currentInterval) {
    lastToggleTime = currentMillis;
    isPulseActive = !isPulseActive; // Przełącz stan
  }

  // 4. FIZYCZNE WYSŁANIE SYGNAŁÓW DO SERW
  for (int i = 0; i < 4; i++) {
    if (isPulseActive) {
      // W fazie aktywnej wysyłamy zadane wychylenie (z klawiatury)
      servos[i].writeMicroseconds(currentPWM[i]);
    } else {
      // W fazie pauzy wymuszamy zatrzymanie, żeby sztucznie spowolnić ruch
      servos[i].writeMicroseconds(1500);
    }
  }
}