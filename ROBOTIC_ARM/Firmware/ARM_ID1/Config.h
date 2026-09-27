#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// --- KONFIGURACJA SIECI ---
const int MQTT_PORT = 1883;
const char* const TOPIC_CMD      = "Robotic_arm_cmd"; // Odbieranie (z PC do ESP)
const char* const TOPIC_FEEDBACK = "Robotic_arm_enc"; // Wysyłanie (z ESP do PC)

// ==========================================
// ZMIENNE GLOBALNE DLA RAMIENIA
// ==========================================
// Pozycje zadane (z MQTT)
extern float target_joints[8];
extern float target_mini_joints[5];
extern float target_speeds[8];

extern float target_mini_speeds[5];
extern bool fan_state;

// Dane z enkoderów i telemetria (do wysłania)
extern float enc_joints[8];
extern float enc_mini_joints[5];
extern float sensA, sensB, ampermeter;
extern int system_error;
extern bool can_status[7]; // ID 2 do 8

extern unsigned long lastMqttCmdTime; 

// ==========================================
// DANE TELEMETRYCZNE Z WĘZŁA ID_4 (SERWA ST3025)
// ==========================================
struct ST3025_Data {
    bool is_connected = false;
    bool is_moving = false;
    int16_t position = 0;
    int16_t speed = 0;
    int16_t load = 0;
    int16_t current = 0;
    uint8_t voltage = 0;
    uint8_t temperature = 0;
};

// Tablica przechowująca stan 4 serw z węzła ID_4
extern ST3025_Data servos_id4[4];


#endif