#include <Arduino.h>
#include <CAN.h>

// ==========================================
// WYBÓR ID WĘZŁA
// Zmień na 3 przed wgraniem do kolejnego ESP32!
// ==========================================
#define NODE_ID 3

// ==========================================
// DEFINICJE PINÓW (zgodne z Pins.h)
// ==========================================
constexpr uint8_t POT_1_PIN  = 36;
constexpr uint8_t IN_POS_PIN = 0;
constexpr uint8_t IN_NEG_PIN = 2;
constexpr uint8_t ENABLE_PIN = 15;
constexpr uint8_t RX_CAN_PIN = 3;
constexpr uint8_t TX_CAN_PIN = 1;

// ==========================================
// USTAWIENIA SILNIKA (zgodne z MotorControl.h)
// ==========================================
constexpr int POT1_MIN_ADC = 0;
constexpr int POT1_MAX_ADC = 4095;      
constexpr float POT1_MAX_ANGLE = 120.0; 
constexpr uint8_t MOTOR1_DIRECTION = 1; 

// Zmieniona tolerancja dla uzyskania dokładności 0.3 stopnia (+- 0.15)
constexpr float ANGLE_TOLERANCE = 0.15;

// ==========================================
// ZMIENNE GLOBALNE
// ==========================================
float target_pos_rad = 0.0f;
float target_speed_percent = 0.0f;
float current_pos_rad = 0.0f;

// Zmienne do uśredniania z potencjometru
int pot_readings[10] = {0};
int read_index = 0;
long pot_total = 0;
bool is_first_read = true;

unsigned long last_can_tx = 0;

void setup() {
    // Konfiguracja pinów mostka L298N
    pinMode(IN_POS_PIN, OUTPUT);
    pinMode(IN_NEG_PIN, OUTPUT);
    pinMode(ENABLE_PIN, OUTPUT);
    
    // Pin potencjometru
    pinMode(POT_1_PIN, INPUT);

    // Ustawienie 10-bitowej rozdzielczości dla pinów PWM (zakres 0 - 1023)
    analogWriteResolution(10);

    // Konfiguracja CAN z prędkością 500 kbps
    CAN.setPins(RX_CAN_PIN, TX_CAN_PIN);
    if (!CAN.begin(500E3)) {
        while (1); // Błąd inicjalizacji - zatrzymaj
    }
}

void handleMotor() {
    // 1. Odczyt i uśrednianie (Średnia krocząca)
    int raw_read = analogRead(POT_1_PIN);
    if (is_first_read) {
        for (int i = 0; i < 10; i++) {
            pot_readings[i] = raw_read;
            pot_total += raw_read;
        }
        is_first_read = false;
    }

    pot_total = pot_total - pot_readings[read_index];
    pot_readings[read_index] = raw_read;
    pot_total = pot_total + pot_readings[read_index];
    read_index = (read_index + 1) % 10;
    int potValue = pot_total / 10;

    // Obliczenia kąta i zabezpieczenia
    potValue = constrain(potValue, POT1_MIN_ADC, POT1_MAX_ADC);
    float currentAngle = (float)(potValue - POT1_MIN_ADC) * POT1_MAX_ANGLE / (POT1_MAX_ADC - POT1_MIN_ADC);
    
    // Zapisanie do zmiennej globalnej dla magistrali CAN (w radianach)
    current_pos_rad = currentAngle * (PI / 180.0);
    
    float targetAngle = target_pos_rad * (180.0 / PI);
    targetAngle = constrain(targetAngle, 0.0, POT1_MAX_ANGLE);

    // 2. Obliczenie uchybu
    float error = targetAngle - currentAngle;

    // 3. Konwersja prędkości (0-100 na PWM 0-1023)
    int base_pwm = map(target_speed_percent, 0, 100, 0, 1023);
    int final_pwm = base_pwm;

    // Proporcjonalne zwalnianie w pobliżu celu
    float slowdown_zone = 3.0; // Strefa hamowania w stopniach
    if (abs(error) < slowdown_zone) {
        // Im mniejszy błąd, tym mniejszy współczynnik PWM
        final_pwm = base_pwm * (abs(error) / slowdown_zone);
        
        // Minimalny PWM pozwalający pokonać tarcie silnika i mechanizmu
        // Wartość 200 można dostosować (zwiększyć/zmniejszyć) w zależności od oporów
        int min_pwm = 800; 
        if (final_pwm < min_pwm) final_pwm = min_pwm;
    }

    final_pwm = constrain(final_pwm, 0, 1023);

    // 4. Sterowanie ON/OFF z histerezą
    if (abs(error) > ANGLE_TOLERANCE) {
        bool moveForward = (error > 0);
        if (MOTOR1_DIRECTION == 1) moveForward = !moveForward;
        
        if (moveForward) {
            digitalWrite(IN_POS_PIN, HIGH);
            digitalWrite(IN_NEG_PIN, LOW);
        } else {
            digitalWrite(IN_POS_PIN, LOW);
            digitalWrite(IN_NEG_PIN, HIGH);
        }
        analogWrite(ENABLE_PIN, final_pwm);
    } else {
        // Cel osiągnięty - zatrzymanie po wejściu w zakres +- 0.15 stopnia
        digitalWrite(IN_POS_PIN, LOW);
        digitalWrite(IN_NEG_PIN, LOW);
        analogWrite(ENABLE_PIN, 0);
    }
}

void handleCAN() {
    int packetSize = CAN.parsePacket();
    if (packetSize) {
        long receivedId = CAN.packetId();

        // Sprawdzamy czy to ramka do nas i czy ma dokładnie 8 bajtów (2x float)
        if (receivedId == NODE_ID && packetSize == 8) {
            
            // 1. ODCZYT KOMENDY OD MASTERA (RX)
            uint8_t buffer[8];
            for (int i = 0; i < 8; i++) buffer[i] = CAN.read();
            
            memcpy(&target_pos_rad, &buffer[0], 4);
            memcpy(&target_speed_percent, &buffer[4], 4);

            // 2. NATYCHMIASTOWA ODPOWIEDŹ TELEMETRYCZNA (TX - Master/Slave)
            // Wysyłamy aktualną pozycję od razu po odebraniu nowych wytycznych
            CAN.beginPacket(NODE_ID);
            CAN.write((const uint8_t*)&current_pos_rad, 4);
            CAN.endPacket();
        }
    }
}

void loop() {
    handleCAN();
    handleMotor();
    delay(1);
}