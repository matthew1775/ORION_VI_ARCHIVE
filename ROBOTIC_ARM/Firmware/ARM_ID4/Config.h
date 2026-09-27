#ifndef CONFIG_ID4_H
#define CONFIG_ID4_H

#include <Arduino.h>

// ==========================================
// KONFIGURACJA PROTOKOŁU CAN
// ==========================================
constexpr long CAN_BAUDRATE      = 500E3; // 500 kbps
constexpr uint32_t TELEMETRY_ID  = 0x04;  // ID do wysyłania telemetrii do ID_1
constexpr uint32_t COMMAND_ID    = 0x14;  // ID do nasłuchiwania komend z ID_1

// ==========================================
// KONFIGURACJA SERW ST3025
// ==========================================
// Zakładamy, że serwa mają przypisane sprzętowe ID: 1, 2, 3, 4
const uint8_t SERVO_IDS[4] = {1, 2, 3, 4};

#endif