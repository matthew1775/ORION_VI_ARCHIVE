#include "ARM_CAN.h"

// ==========================================
// Ustawienia sprzętowe i protokołu
// ==========================================
constexpr long CAN_BAUDRATE     = 500E3; // 500 kbps
constexpr uint32_t MY_NODE_ID   = 0x01;  // ID Głównego ESP32

constexpr uint32_t JOINT_2_ID   = 0x02;  // Docelowe ID dla Joint 2
constexpr uint32_t JOINT_3_ID   = 0x03;  // Docelowe ID dla Joint 3 (Dodane do karuzeli)
constexpr uint32_t JOINT_4_ID   = 0x04;  // Telemetria z ID 4
constexpr uint32_t JOINT_4_CMD_ID = 0x14; // Komendy ruchu dla ID 4
constexpr uint32_t MINI_SERVO_ID = 5;   // Docelowe ID 10 dla Mini Serw

ST3025_Data servos_id4[4];  


static unsigned long last_rx_time[15] = {0};

void initCAN() {
    CAN.setPins(Pins::RX_CAN_PIN, Pins::TX_CAN_PIN);
    CAN.begin(CAN_BAUDRATE);
}


void handleCAN() {
    int max_packets = 10;
    // ==========================================
    // 1. ODBIÓR DANYCH Z CAN (Błyskawiczny nasłuch)
    // ZMIANA: Używamy 'while' zamiast 'if'. Dzięki temu jeśli przyjdą 
    // np. 2 ramki na raz, procesor ściągnie obie zanim ruszy dalej.
    // ==========================================
    while (int packetSize = CAN.parsePacket()) {
        max_packets--;
        uint32_t receivedId = CAN.packetId();
        if (receivedId < 15) {
            last_rx_time[receivedId] = millis();
        }        
        // --- Odbiór enkodera z Joint 2 (ID 2) ---
        if (receivedId == JOINT_2_ID && packetSize >= 4) {
            float enc_pos = 0.0f;
            uint8_t buffer[4];
            for (int i = 0; i < 4; i++) buffer[i] = CAN.read();
            memcpy(&enc_pos, &buffer[0], 4);
            enc_joints[1] = enc_pos; 
            can_status[0] = true; 
        }
        // --- Odbiór enkodera z Joint 3 (ID 3) ---
        else if (receivedId == JOINT_3_ID && packetSize >= 4) {
            float enc_pos = 0.0f;
            uint8_t buffer[4];
            for (int i = 0; i < 4; i++) buffer[i] = CAN.read();
            memcpy(&enc_pos, &buffer[0], 4);
            enc_joints[2] = enc_pos; 
            can_status[1] = true; 
        }
        // --- Odbiór telemetrii z ID 4 (Ping-Pong z ST3025) ---
        // --- Odbiór telemetrii z ID 4 (Ping-Pong z ST3025) ---
// --- Odbiór telemetrii z ID 4 (Zbiorcza ramka 8-bajtowa) ---
        else if (receivedId == JOINT_4_ID && packetSize == 8) { 
            can_status[2] = true; // Flaga utrzymująca węzeł przy życiu
            
            uint8_t buf[8];
            for (int i = 0; i < 8; i++) buf[i] = CAN.read(); 
            
            // Dekodowanie 4 silników jednocześnie z jednej ramki
            for (int servo_idx = 0; servo_idx < 4; servo_idx++) {
                servos_id4[servo_idx].is_connected = true; 
                
                int16_t pos;
                memcpy(&pos, &buf[servo_idx * 2], 2);
                servos_id4[servo_idx].position = pos;

                // Konwersja z kroków (0-4095) na radiany
                float radians = pos * (360.0f / 4096.0f) * (PI / 180.0f);
                
                // Mapowanie: servo_idx 0..3 odpowiada za joint4..joint7 w głównej tablicy
                enc_joints[servo_idx + 3] = radians;
            }
        }
    }

    // ==========================================
    // 2. NADAWANIE SEKWENCYJNE (KARUZELA MASTER-SLAVE)
    // Procesor ID 1 co 3 milisekundy strzela kolejną ramką
    // do kolejnego serwa, upewniając się, że kabel CAN jest pusty.
    // ==========================================
static unsigned long last_poll_time = 0;
    static uint8_t poll_step = 0;
    static unsigned long last_ping_time = 0; // Dodany timer dla pingu

    if (millis() - last_poll_time >= 3) {
        last_poll_time = millis();

        // KROK A: Określamy, z jakiego ID przychodzi odpowiedź dla obecnego kroku
        uint32_t expected_rx_id = 0;
        if (poll_step == 0) expected_rx_id = JOINT_2_ID;
        else if (poll_step == 1) expected_rx_id = JOINT_3_ID;
        else if (poll_step >= 2 && poll_step <= 6) expected_rx_id = MINI_SERVO_ID;
        else if (poll_step >= 7 && poll_step <= 10) expected_rx_id = JOINT_4_ID; // Telemetria ID4 przychodzi z 4

        // KROK B: Czy węzeł żyje? (Odezwał się w ciągu ostatnich 1000 ms)
        // KROK B: Czy węzeł żyje? (Dla ID 5 wymuszamy true)
bool is_alive = (expected_rx_id == MINI_SERVO_ID) || (millis() - last_rx_time[expected_rx_id] < 1000);

        // KROK C: Ping - raz na sekundę wysyłamy w ciemno, aby "obudzić" nowo podłączone kable
        bool ping_cycle = (millis() - last_ping_time > 1000);

        // WYSYŁAJ TYLKO JEŚLI MODUŁ ŻYJE LUB JEST TO CYKL PINGU
        if (is_alive || ping_cycle) {
            switch(poll_step) {
                case 0: { 
                // Krok 0: Wyślij komendę do Joint 2
                  CAN.beginPacket(JOINT_2_ID);
                  float j2_pos = target_joints[1];   
                  float j2_speed = target_speeds[1]; 
                  CAN.write((const uint8_t*)&j2_pos, 4);
                  CAN.write((const uint8_t*)&j2_speed, 4);
                  CAN.endPacket();
                  break;
            }
            case 1: { 
                // Krok 1: Wyślij komendę do Joint 3
                CAN.beginPacket(JOINT_3_ID);
                float j3_pos = target_joints[2];   
                float j3_speed = target_speeds[2]; 
                CAN.write((const uint8_t*)&j3_pos, 4);
                CAN.write((const uint8_t*)&j3_speed, 4);
                CAN.endPacket();
                break;
            }
            case 2:
            case 3:
            case 4:
            case 5:
            case 6: { 
                // Kroki 2 do 6: Wyślij komendy do 5 Mini Serw (ID 5)
                uint8_t mini_idx = poll_step - 2; 
                CAN.beginPacket(MINI_SERVO_ID);
                
                // Pobieramy zadaną prędkość z MQTT (zakładając, że to tutaj spływają komendy 0/100/200)
                uint16_t can_val = (uint16_t)target_mini_speeds[mini_idx];
                
                CAN.write(mini_idx); 
                CAN.write((const uint8_t*)&can_val, 2); 
                CAN.endPacket();
                break;
            }
            case 7:
            case 8:
            case 9:
            case 10: { 
                // Kroki 7 do 10: Wyślij komendy do Serw ID 4 
                uint8_t id4_idx = poll_step - 7; 
                CAN.beginPacket(JOINT_4_CMD_ID); 
                
                int16_t target_pos_steps = 0; 
                int16_t speed = 0;
                
                if (id4_idx == 3) {
                    // --- SERWO 4 (Rotacja ciągła) ---
                    // Pobieramy wartość sterującą (0-200) ze zmiennej pozycji (joysticka),
                    // a nie z globalnego limitu prędkości.
                    speed = (int16_t)target_speeds[id4_idx + 3];

                    if (speed != 100) {
                        target_pos_steps = 1000; // Kręć przez maks 1 sekundę
                    } else {
                        target_pos_steps = 0;    // Natychmiastowe hamowanie (puszczony przycisk)
                    }
                } else {
                    // --- Standardowe serwa pozycyjne (id4_idx 0, 1, 2) ---
                    // Tutaj normalnie pobieramy docelową prędkość oraz pozycję w radianach
                    speed = (int16_t)target_speeds[id4_idx + 3];
                    float radians = target_joints[id4_idx + 3]; 
                    target_pos_steps = (int16_t)(radians * (180.0 / PI) * (4096.0 / 360.0)); 
                }
                
                CAN.write(id4_idx); 
                CAN.write((const uint8_t*)&target_pos_steps, 2); 
                CAN.write((const uint8_t*)&speed, 2);            
                CAN.endPacket();
                break;
            }
        }
        }

        // Przejście do kolejnego węzła
        poll_step++;
        if (poll_step > 10) {
            poll_step = 0; // Reset karuzeli na koniec cyklu
            if (ping_cycle) last_ping_time = millis(); // Resetujemy licznik pingu po pełnym obiegu
        }
    }
}