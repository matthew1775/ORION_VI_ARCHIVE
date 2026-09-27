#include "MotorControl.h"

// Zmienne statyczne do filtra uśredniającego (brak zmiennych PID)
static int pot_readings[10] = {0};
static int read_index = 0;
static long pot_total = 0;
static bool is_first_read = true;

void handleLocalMotor() {
    // 1. ODCZYT I UŚREDNIANIE (Średnia krocząca)
    int raw_read = analogRead(Pins::POT_1_PIN);

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

    potValue = constrain(potValue, POT1_MIN_ADC, POT1_MAX_ADC);
    float currentAngle = (float)(potValue - POT1_MIN_ADC) * POT1_MAX_ANGLE / (POT1_MAX_ADC - POT1_MIN_ADC);
    
    // Aktualizacja tablicy telemetrii do JSON (w radianach)
    enc_joints[0] = currentAngle * (PI / 180.0);
    
    float targetAngle = target_joints[0] * (180.0 / PI);
    targetAngle = constrain(targetAngle, 0.0, POT1_MAX_ANGLE);
    
    // 2. Obliczenie uchybu (tylko w celu określenia kierunku i momentu stopu)
    float error = targetAngle - currentAngle;
    
    // 3. Konwersja zadanej prędkości z suwaka w aplikacji MQTT (0-100) na PWM
    // Przy ustawieniu prędkości na 100%, final_pwm wyniesie równe 1023 (pełne 12V z L298N)
    int final_pwm = map(target_speeds[0], 0, 100, 0, 1023);
    final_pwm = constrain(final_pwm, 0, 1023);

    // ==========================================
    // 4. WYSTEROWANIE SILNIKA (Tryb dwustawny ON/OFF)
    // ==========================================
    if (abs(error) > ANGLE_TOLERANCE) {
        // Jeśli uchyb jest poza martwą strefą, dajemy pełne napięcie
        bool moveForward = (error > 0);
        if (MOTOR1_DIRECTION == 1) moveForward = !moveForward;
        
        if (moveForward) {
            digitalWrite(Pins::IN_POS_PIN, HIGH);
            digitalWrite(Pins::IN_NEG_PIN, LOW);
        } else {
            digitalWrite(Pins::IN_POS_PIN, LOW);
            digitalWrite(Pins::IN_NEG_PIN, HIGH);
        }
        analogWrite(Pins::ENABLE_PIN, final_pwm); // Cały czas stały "kop" napięcia
    } else {
        // Jesteśmy w celu (wewnątrz tolerancji) - odcięcie zasilania
        digitalWrite(Pins::IN_POS_PIN, LOW);
        digitalWrite(Pins::IN_NEG_PIN, LOW);
        analogWrite(Pins::ENABLE_PIN, 0);
    }
}