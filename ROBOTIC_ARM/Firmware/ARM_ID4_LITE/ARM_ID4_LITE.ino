#include <Arduino.h>
#include <CAN.h>
#include <SCServo.h>

SMS_STS st; 

const int16_t SERVO1_OFFSET_STEPS = 2048;
const int16_t SERVO2_OFFSET_STEPS = 3413;
const int16_t SERVO3_OFFSET_STEPS = 2400;

// ==========================================
// KONFIGURACJA PINÓW I ID
// ==========================================
#define RX_CAN_PIN   3
#define TX_CAN_PIN   1
#define RX_SERVO_PIN 16
#define TX_SERVO_PIN 17

#define COMMAND_ID   0x14
#define TELEMETRY_ID 0x04

#define NUM_SERVOS 4
uint8_t servo_ids[4] = {1, 2, 3, 4};

// Zmienne dzielone (Pozycyjne dla serw 1-3)
int16_t target_pos[4]  = {2048, 2048, 2048, 2048};
// Zmniejszenie prędkości bazowych z 200 na 20 oraz ze 100 na 10
uint16_t target_spd[4] = {10, 10, 10, 10};
int16_t cached_pos[4]  = {2048, 2048, 2048, 0};

// Zmienne dla serwa 4 (Tryb 1 - Prędkość)
unsigned long servo4_last_cmd_time = 0;
int16_t servo4_speed = 0;

unsigned long lastServoTime = 0;
const unsigned long servoInterval = 20;

void setup() {
    Serial2.begin(1000000, SERIAL_8N1, RX_SERVO_PIN, TX_SERVO_PIN);
    st.pSerial = &Serial2;
    delay(3000);

    // POPRAWKA NR 1: Przełączenie serwa nr 4 w tryb Wheel Mode 
    // na podstawie logiki z pliku wheel_mode.ino
    st.WheelMode(servo_ids[3]);
    delay(500); // Niewielkie opóźnienie dla pewności zastosowania zmian

    CAN.setPins(RX_CAN_PIN, TX_CAN_PIN);
    while (!CAN.begin(500E3)) { 
        delay(100);
    }

    // Pobranie pierwszej pozycji na starcie TYLKO dla serw pozycyjnych (1, 2, 3)
    for(int i = 0; i < 3; i++) {
        int16_t p = st.ReadPos(servo_ids[i]);
        if(p != -1) {
            target_pos[i] = p;
            if (i == 0) {
                cached_pos[i] = (int16_t)((int32_t)p - SERVO1_OFFSET_STEPS);
            } else if (i == 1) {
                cached_pos[i] = (int16_t)((int32_t)p - SERVO2_OFFSET_STEPS);
            } else if (i == 2) {
                cached_pos[i] = (int16_t)((int32_t)p - SERVO3_OFFSET_STEPS);
            }
        }
    }
}

// ==========================================
// ODBIÓR KOMEND I TELEMETRIA (PING-PONG)
// ==========================================
void handleCan() {
    while (int packetSize = CAN.parsePacket()) {
        if (CAN.packetId() == COMMAND_ID && packetSize >= 5) {
            uint8_t s_idx = CAN.read();
            if (s_idx < NUM_SERVOS) {
                uint8_t buf[4];
                for (int i = 0; i < 4; i++) buf[i] = CAN.read(); 
                
                int16_t pos, speed;
                memcpy(&pos, &buf[0], 2);
                memcpy(&speed, &buf[2], 2);

                if (s_idx == 3) {
                    // --- SERWO 4: Tylko odczyt prędkości z odświeżeniem Watchdoga ---
                    servo4_speed = speed;
                    servo4_last_cmd_time = millis();
                } else {
                    // --- SERWA 1-3: Standardowa logika pozycji ---
                    int16_t actual_speed = map(speed, 0, 100, 0, 200);
                    if (actual_speed <= 0) actual_speed = 1500;
                    target_spd[s_idx] = actual_speed;

                    int32_t phys_pos = 0;
                    int32_t limit_max = 0;
                    int32_t limit_min = 0;

                    if (s_idx == 0) {
                        phys_pos = (int32_t)SERVO1_OFFSET_STEPS + pos;
                        limit_max = SERVO1_OFFSET_STEPS + 8192;
                        limit_min = SERVO1_OFFSET_STEPS - 8192;
                    } else if (s_idx == 1) {
                        phys_pos = (int32_t)SERVO2_OFFSET_STEPS + pos;
                        limit_max = SERVO2_OFFSET_STEPS + 8192;
                        limit_min = SERVO2_OFFSET_STEPS - 8192;
                    } else if (s_idx == 2) {
                        phys_pos = (int32_t)SERVO3_OFFSET_STEPS + pos;
                        limit_max = SERVO3_OFFSET_STEPS + 8192;
                        limit_min = SERVO3_OFFSET_STEPS - 8192;
                    }
                    
                    if (phys_pos > limit_max) phys_pos = limit_max;
                    if (phys_pos < limit_min) phys_pos = limit_min;
                    
                    target_pos[s_idx] = (int16_t)phys_pos;
                }
                
                // USUNIĘTO: Wysyłanie CAN.beginPacket() z tego miejsca
            }
        }
    }
}
// ==========================================
// OBSŁUGA RUCHU I ODCZYT SERW
// ==========================================
void handleServos() {
    static uint8_t acc[4] = {1, 1, 1, 1};
    static int16_t last_sent_pos[3] = {-1, -1, -1};
    static uint8_t read_idx = 0;
    static bool first_run = true;
    
    if (first_run) {
        for(int i = 0; i < 3; i++) last_sent_pos[i] = target_pos[i];
        first_run = false;
    }

    // 1. Serwa pozycyjne (ID 1, 2, 3)
    int16_t p[3];
    uint16_t s[3];
    bool move_needed = false;
    for(int i = 0; i < 3; i++) {
        p[i] = target_pos[i];
        s[i] = target_spd[i];
        if (abs(p[i] - last_sent_pos[i]) > 8) move_needed = true;
    }

    int16_t current_wheel_speed = 0;
    // Jeżeli odbieramy z CAN nowe dane na czas, przeliczamy zadaną prędkość
    if (millis() - servo4_last_cmd_time < 1000) {
        
        // Strefa martwa dla nowej pozycji środkowej (100)
        if (abs(servo4_speed - 100) > 2) {
            
            // Mapowanie: z 0-200 na odpowiednio -2400 do 2400
            int16_t mapped_speed = map(servo4_speed, 0, 200, -2400, 2400);
            
            // POPRAWKA: Ręczna konwersja na format Sign-Magnitude dla trybu Wheel Mode.
            // Najwyższy bit (0x8000) definiuje kierunek ujemny, reszta to wartość absolutna.
          
            current_wheel_speed = mapped_speed;
            

        } else {
            current_wheel_speed = 0; // Zatrzymanie
        }
    } else {
        current_wheel_speed = 0; // Natychmiastowe zahamowanie po zerwaniu komunikacji
    }

    // POPRAWKA: Usunięto instrukcję "if (current_wheel_speed != last_wheel_speed)".
    // Ciągłe obroty wysyłamy w każdej pętli serwa. Zabezpiecza to przed sytuacją,
    // gdzie komenda ruchu została zagłuszona przy poborze piku prądu.
    static int16_t last_sent_wheel_speed = 0; // Wartość początkowa poza zakresem
    static unsigned long last_wheel_send_time = 0;

    // Wysyłamy komendę do serwa TYLKO gdy żądana prędkość ulega zmianie, 
    // LUB prewencyjnie co 1000 ms, by uchronić się przed zagłuszeniem komendy.
    if (current_wheel_speed != last_sent_wheel_speed) {
        
        st.WriteSpe(servo_ids[3], current_wheel_speed, 50); 
        
        last_sent_wheel_speed = current_wheel_speed;
        last_wheel_send_time = millis();
    }
    

    if (move_needed) {
        st.SyncWritePosEx(servo_ids, 3, p, s, acc);
        for(int i = 0; i < 3; i++) last_sent_pos[i] = p[i];
    } 
        
        // POPRAWKA NR 2: Pomijanie odczytu pozycji (ReadPos) dla serwa działającego jako koło.
        // Odczytywanie pozycji z serwa rotacyjnego mija się z celem i może generować błędy na magistrali
        // ... reszta kodu handleServos wyżej ...
                else {
                    uint8_t s_id = servo_ids[read_idx];
                    // Pomijanie odczytu pozycji dla serwa działającego jako koło.
                    if (s_id != servo_ids[3]) {
                        int16_t cp = st.ReadPos(s_id);
                        if (cp != -1) {
                            if (read_idx == 0) {
                                cached_pos[read_idx] = (int16_t)((int32_t)cp - SERVO1_OFFSET_STEPS);
                            } else if (read_idx == 1) {
                                cached_pos[read_idx] = (int16_t)((int32_t)cp - SERVO2_OFFSET_STEPS);
                            } else if (read_idx == 2) {
                                cached_pos[read_idx] = (int16_t)((int32_t)cp - SERVO3_OFFSET_STEPS);
                            }
                        }
                    }
                    
                    read_idx++;
                    if (read_idx >= NUM_SERVOS) {
                        read_idx = 0; // Reset karuzeli odczytu
                        
                        // NOWOŚĆ: Wysyłanie telemetrii na magistralę CAN TYLKO 
                        // po tym, jak zakończono odpytywanie wszystkich 4 serw 
                        CAN.beginPacket(TELEMETRY_ID);
                        for(int i = 0; i < 4; i++) {
                            int16_t c_pos = cached_pos[i];
                            CAN.write((const uint8_t*)&c_pos, 2);
                        }
                        CAN.endPacket();
                    }
                }

// 2. Serwo 4 (Tryb 1 - Prędkość z Watchdogiem)

}
void loop() {
    handleCan();
    if (millis() - lastServoTime >= servoInterval) {
        lastServoTime = millis();
        handleServos(); 
    }
}