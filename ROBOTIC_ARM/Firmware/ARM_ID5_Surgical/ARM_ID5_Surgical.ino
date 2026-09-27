#include <Arduino.h>
#include <ESP32Servo.h>
#include <CAN.h>

// --- Definicja ID węzła oraz pinów CAN ---
constexpr uint32_t MY_NODE_ID = 0x05;
constexpr uint8_t RX_CAN_PIN = 3;
constexpr uint8_t TX_CAN_PIN = 1;

// --- Konfiguracja pinów PWM (ESP32) ---
const int PIN_SERVO_ROLL  = 25;
const int PIN_SERVO_PITCH = 26;
const int PIN_SERVO_GRIP1 = 13;
const int PIN_SERVO_GRIP2 = 12;

Servo servos[4];
const int servoPins[4] = {PIN_SERVO_ROLL, PIN_SERVO_PITCH, PIN_SERVO_GRIP1, PIN_SERVO_GRIP2};

// --- Zmienne do sterowania ---
int currentPWM[4] = {1500, 1500, 1500, 1500};
int action_val[4] = {100, 100, 100, 100}; // Pamięć ostatniej wartości z CAN (100 = STOP)

unsigned long lastKeyTime = 0;
const int TIMEOUT_MS = 1000; // Czas po zaniku ramek CAN, po którym serwa stają

// --- Zmienne do spowalniania (PULSOWANIE) ---
const unsigned long T_ACTIVE = 20;   // Czas ruchu (ms) - impuls poruszający
const unsigned long T_PAUSE  = 20;   // Czas postoju (ms) - wymuszenie STOP
unsigned long lastToggleTime = 0;
bool isPulseActive = false;          // Flaga określająca faza ruchu/stopu

// --- Współczynniki (Coupling) ---
const float COUPLING_PITCH_JAW1 = 0.7;
const float COUPLING_PITCH_JAW2 = 0.5;

void setup() {
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for(int i = 0; i < 4; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(servoPins[i], 500, 2500);
    servos[i].writeMicroseconds(1500); // Pozycja spoczynkowa (STOP)
  }

  // Inicjalizacja CAN
  CAN.setPins(RX_CAN_PIN, TX_CAN_PIN);
  if (!CAN.begin(500E3)) {
    Serial.println("Blad inicjalizacji CAN!");
    while (1); 
  }
}

void loop() {
  // =========================================================
  // 1. ODBIÓR DANYCH (BUFOROWANIE STANÓW - NIE BLOKUJE RUCHU)
  // =========================================================
  int packetSize = CAN.parsePacket();
  
  if (packetSize) {
    long receivedId = CAN.packetId();

    if (receivedId == MY_NODE_ID && packetSize == 3) {
      uint8_t action_id = CAN.read(); 
      
      uint16_t can_val = 0;
      uint8_t buf[2];
      buf[0] = CAN.read();
      buf[1] = CAN.read();
      
      memcpy(&can_val, buf, 2);
      can_val = constrain(can_val, 0, 200);
      
      // Zapisujemy odebraną wartość dla danej osi
      if (action_id < 4) {
        action_val[action_id] = can_val;
        lastKeyTime = millis();
      }
    }
  }

  // =========================================================
  // 2. TIMEOUT (ZATRZYMANIE W PRZYPADKU BRAKU POŁĄCZENIA)
  // =========================================================
  if (millis() - lastKeyTime > TIMEOUT_MS) {
    action_val[0] = 100;
    action_val[1] = 100;
    action_val[2] = 100;
    action_val[3] = 100;
  }

  // =========================================================
  // 3. KALKULACJA KOMPLEKSOWEGO RUCHU (PRIORYTETYZACJA)
  // =========================================================
  
  // Oś 0 (Roll) - ruch bezpośredni (odpowiednik W/S)
  currentPWM[0] = map(action_val[0], 0, 200, 1200, 1800);

  // Oś 1 (Pitch) - ruch bezpośredni (odpowiednik E/D, sam w sobie)
  currentPWM[1] = map(action_val[1], 0, 200, 1200, 1800);

  // LOGIKA SZCZĘK (Dotyczy serw 2 i 3)
  // Jeśli odczyt nie jest w centrum (margin błędu +/- 5)
  if (action_val[1] > 105) { 
    // Priorytet 1: Kompensacja przy ruchu Pitch do przodu (E)
    currentPWM[2] = 1500 + (300 * COUPLING_PITCH_JAW2); 
    currentPWM[3] = 1500 - (300 * COUPLING_PITCH_JAW1); 
  } 
  else if (action_val[1] < 95) { 
    // Priorytet 1: Kompensacja przy ruchu Pitch do tyłu (D)
    currentPWM[2] = 1500 - (300 * COUPLING_PITCH_JAW1); 
    currentPWM[3] = 1500 + (300 * COUPLING_PITCH_JAW2); 
  }
  else if (action_val[2] > 105) { 
    // Priorytet 2: Otwieranie szczęk (R)
    currentPWM[2] = 1800; 
    currentPWM[3] = 1800; 
  }
  else if (action_val[2] < 95) { 
    // Priorytet 2: Zamykanie szczęk (F)
    currentPWM[2] = 1200; 
    currentPWM[3] = 1200; 
  }
  else if (action_val[3] > 105) { 
    // Priorytet 3: Obrót szczęk w lewo (T)
    currentPWM[2] = 1750; 
    currentPWM[3] = 1200; 
  }
  else if (action_val[3] < 95) { 
    // Priorytet 3: Obrót szczęk w prawo (G)
    currentPWM[2] = 1200; 
    currentPWM[3] = 1700; 
  }
  else {
    // Jeśli z CAN nie płynie żaden ruch dla szczęk, wracają do STOPu
    currentPWM[2] = 1500;
    currentPWM[3] = 1500;
  }

  // =========================================================
  // 4. LOGIKA PULSOWANIA I WYSYŁANIE SYGNAŁÓW DO SERW
  // =========================================================
  unsigned long currentMillis = millis();
  unsigned long currentInterval = isPulseActive ? T_ACTIVE : T_PAUSE;

  if (currentMillis - lastToggleTime >= currentInterval) {
    lastToggleTime = currentMillis;
    isPulseActive = !isPulseActive; // Przełącz stan
  }

  for (int i = 0; i < 4; i++) {
    if (isPulseActive) {
      servos[i].writeMicroseconds(currentPWM[i]);
    } else {
      servos[i].writeMicroseconds(1500); // Faza stop - wymuszenie zatrzymania (spowalnianie)
    }
  }
}