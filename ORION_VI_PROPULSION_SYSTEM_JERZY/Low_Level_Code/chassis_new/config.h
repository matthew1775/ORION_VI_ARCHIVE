// Config.h
#ifndef CONFIG_H
#define CONFIG_H
#include <Arduino.h>

// ==========================================
// WYBÓR STRONY (Zmień na SIDE_LEFT lub SIDE_RIGHT)
// ==========================================
#define SIDE_LEFT 0
#define SIDE_RIGHT 1

#define CURRENT_SIDE SIDE_RIGHT

// --- KONFIGURACJA ZALEŻNA OD STRONY ---
#if CURRENT_SIDE == SIDE_LEFT
  #define NET_MAC_END 0x51
  #define NET_IP_END 51
  #define MQTT_CLIENT_ID "ESP32_Left_Drive"
  #define TOPIC_FEEDBACK_DEF "propulsion/feedback_left"
  #define CMD_IDX_FRONT 0
  #define CMD_IDX_REAR 1
  #define FEEDBACK_SIDE_ID 0
  #define MQTT_PUB_INTERVAL 100
  
  #define DIR_FRONT 1.0f
  #define DIR_REAR  1.0f

  #define JSON_FRONT_SPEED "fl_speed"
  #define JSON_REAR_SPEED  "rl_speed"
  #define JSON_FRONT_STEER "fl_rad"
  #define JSON_REAR_STEER  "rl_rad"

  const int FRONT_MIN_PULSE = 1479; 
  const int FRONT_MAX_PULSE = 2813; 
  const int FRONT_MID_PULSE = 2146;

  const int REAR_MIN_PULSE = 1329; 
  const int REAR_MAX_PULSE = 2663; 
  const int REAR_MID_PULSE = 1996;

#elif CURRENT_SIDE == SIDE_RIGHT
  #define NET_MAC_END 0x52
  #define NET_IP_END 52
  #define MQTT_CLIENT_ID "ESP32_Right_Drive"
  #define TOPIC_FEEDBACK_DEF "propulsion/feedback_right"
  #define CMD_IDX_FRONT 2
  #define CMD_IDX_REAR 3
  #define FEEDBACK_SIDE_ID 1
  #define MQTT_PUB_INTERVAL 100

  #define DIR_FRONT -1.0f 
  #define DIR_REAR  -1.0f

  #define JSON_FRONT_SPEED "fr_speed"
  #define JSON_REAR_SPEED  "rr_speed"
  #define JSON_FRONT_STEER "fr_rad"
  #define JSON_REAR_STEER  "rr_rad"



  const int FRONT_MIN_PULSE = 1409; 
  const int FRONT_MAX_PULSE = 2743; 
  const int FRONT_MID_PULSE = 2076;

  const int REAR_MIN_PULSE = 1129; 
  const int REAR_MAX_PULSE = 2463; 
  const int REAR_MID_PULSE = 1796;
#endif

// --- PINY SIECI I CAN ---
#define SPI_MISO_PIN  19
#define SPI_MOSI_PIN  23
#define SPI_SCK_PIN   18
#define ETH_CS_PIN    5
#define ETH_RST_PIN   27
#define CAN_TX_PIN    26
#define CAN_RX_PIN    25


// PINY DODATKOWE 

#define NEOPIXEL_PIN 7 

// --- PINY SERW I SENSORÓW (Zgodnie z podanym schematem) ---
#define SV_CFB_B     15
#define SV_CFB_A     2
#define SV_VFB_A     0
#define SV_VFB_B     4
#define SV_A_PIN     33
#define SV_B_PIN     32

// --- KONFIGURACJA CAN ---
#define CAN_BAUDRATE  500000
#define ODRIVE_FRONT_ID 0x00
#define ODRIVE_REAR_ID  0x01

// --- KONFIGURACJA SERWA --
// --- KONFIGURACJA SERWA ---
// (Usuń SMOOTH_FACTOR i DEADBAND, jeśli jeszcze je masz)
#define MAX_STEER_RAD 1.0f 

// ==========================================
// USTAWIENIA PID DLA SKRĘTU (ZABEZPIECZENIA)
// ==========================================
#define STEER_KP 5.0f        // (Proporcjonalny) Jak agresywnie goni cel
#define STEER_KI 0.1f        // (Całkujący) Niweluje uchyb ustalony
#define STEER_KD 0.05f       // (Różniczkujący) Hamuje przed celem, zapobiega oscylacjom
#define STEER_MAX_VEL 0.5f   // ZABEZPIECZENIE: Maksymalna prędkość skrętu (radiany na sekundę)

// --- PARAMETRY POMIARÓW ADC (ACS712 - 5A) ---
const float ADC_VREF = 3.3f;        // Napięcie referencyjne ESP32
const int ADC_RES = 4095;           // Rozdzielczość 12-bit
const float ACS712_SENS = 0.185f;   // 185 mV/A dla modułu 5A
const float ACS712_OFFSET = 1.65f;  // Przewidywane napięcie na pinie przy prądzie 0A (Zakładając podział z 5V)

// --- KONFIGURACJA SIECI ---
const int MQTT_PORT = 1883;
const char* const TOPIC_CMD      = "propulsion/cmd"; 
const char* const TOPIC_FEEDBACK = TOPIC_FEEDBACK_DEF;

// --- ZMIENNE GLOBALNE ---
extern volatile float targetVelocityFront;
extern volatile float targetVelocityRear;
extern volatile float targetSteeringFront; // Niezależny kąt dla przodu
extern volatile float targetSteeringRear;  // Niezależny kąt dla tyłu

extern float currentServoPosA;
extern float currentServoPosB;

// Zmienne z odczytów ADC
extern float servoVoltageA;
extern float servoVoltageB;
extern float servoCurrentA;
extern float servoCurrentB;

extern float measuredPosFront;
extern float measuredVelFront;
extern float measuredPosRear;
extern float measuredVelRear;
extern uint32_t activeErrorsFront;
extern uint32_t activeErrorsRear;

extern const unsigned long SAFETY_TIMEOUT;
extern unsigned long lastMqttCmdTime;

#endif