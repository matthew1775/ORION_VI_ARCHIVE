#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <Arduino.h>
#include "Config.h"
#include "pins.h"

// ==========================================
// KONFIGURACJA SILNIKA LOKALNEGO (JOINT 1 / L298N)
// ==========================================
// Kalibracja potencjometru (odczyty z ADC ESP32)
constexpr int POT1_MIN_ADC = 0;         // Wartość ADC dla 0 stopni
constexpr int POT1_MAX_ADC = 4095;      // Wartość ADC dla 120 stopni (granica bezpieczeństwa)
constexpr float POT1_MAX_ANGLE = 120.0; // Maksymalny dopuszczalny kąt w stopniach

// Konfiguracja sprzętowa
constexpr uint8_t MOTOR1_DIRECTION = 1; // 0 lub 1 - zmiana kierunku obrotu
constexpr float ANGLE_TOLERANCE = 0.2;  // Martwa strefa (histereza) w stopniach

// Deklaracja funkcji
void handleLocalMotor();

#endif