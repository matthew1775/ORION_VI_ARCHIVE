#include "ID4_CAN.h"
#include <CAN.h>
#include <SCServo.h>
#include "Pins.h"
#include "Config.h"

SMS_STS st; // Obiekt do sterowania serwami STS
unsigned long lastCanRxTime = 0;
unsigned long lastTelemetryTime = 0;
int16_t last_servo1_pos = 0;
// Przechowuje pozycję dla NeoPixel

int16_t getServo1Position() {
    return last_servo1_pos;
}


void initCanAndServos() {
    //Serial.println("[ID4_CAN] Inicjalizacja magistrali serw...");
    
    // NAPRAWA 1: Używamy Serial2 (dedykowane dla pinów 16 i 17 na ESP32)
    Serial2.begin(1000000, SERIAL_8N1, Pins::RX_SERVO_PIN, Pins::TX_SERVO_PIN);
    st.pSerial = &Serial2;
    delay(500);

    Serial.println("[ID4_CAN] Inicjalizacja CAN...");
    CAN.setPins(Pins::RX_CAN_PIN, Pins::TX_CAN_PIN);
    if (!CAN.begin(CAN_BAUDRATE)) {
        Serial.println("[ID4_CAN] BŁĄD: Inicjalizacja CAN nie powiodła się!");
        while (1) { delay(1000); } 
    }
    //Serial.println("[ID4_CAN] CAN uruchomiony.");
}

void handleCanAndServos() {
    // ==========================================
    // 1. ODBIÓR KOMEND Z MAGISTRALI CAN (OD ID 1)
    // ==========================================
    int packetSize = CAN.parsePacket();
    if (packetSize) {
        uint32_t receivedId = CAN.packetId();
        
        if (receivedId == COMMAND_ID && packetSize >= 5) {
            uint8_t s_idx = CAN.read();
            
            if (s_idx < 4) {
                int16_t target_pos = 0;
                int16_t target_speed = 0;
                
                uint8_t buf[4];
                for (int i = 0; i < 4; i++) buf[i] = CAN.read();
                
                memcpy(&target_pos, &buf[0], 2);
                memcpy(&target_speed, &buf[2], 2);

                // NAPRAWA 2: Skalowanie prędkości
                // MQTT daje 0-100. My przeliczamy to na format SCServo (0-2400)
                int16_t actual_speed = map(target_speed, 0, 100, 0, 2400); 
                if (actual_speed <= 0) actual_speed = 1500; // Domyślna prędkość dla bezpieczeństwa
                
                // Wysyłamy polecenie: ID serwa, Pozycja, Przeskalowana Prędkość, Przyspieszenie (50)
                st.WritePosEx(SERVO_IDS[s_idx], target_pos, actual_speed, 50);
                
                lastCanRxTime = millis();
            }
        }
    }

    // ==========================================
    // 2. WYSYŁANIE TELEMETRII DO ID 1 (Co 50ms)
    // ==========================================
    if (millis() - lastTelemetryTime >= 50) {
        lastTelemetryTime = millis();

        for (int i = 0; i < 4; i++) {
            uint8_t s_id = SERVO_IDS[i];
            
            // Ping sprawdza czy serwo w ogóle żyje
            bool connected = (st.Ping(s_id) != -1);
            
            int16_t pos = 0, speed = 0, load = 0, current = 0;
            uint8_t voltage = 0, temper = 0;
            bool move = false;

            // NAPRAWA 3: Odpytujemy tylko połączone serwa, żeby uniknąć timeoutów magistrali
            // NAPRAWA 3: Odpytujemy tylko połączone serwa...
            if (connected) {
                move     = (st.ReadMove(s_id) == 1);
                pos      = st.ReadPos(s_id);
                speed    = st.ReadSpeed(s_id);
                load     = st.ReadLoad(s_id);
                current  = st.ReadCurrent(s_id);
                voltage  = st.ReadVoltage(s_id);
                temper   = st.ReadTemper(s_id);
                
                // NOWE: Jeśli to pierwsze serwo (indeks 0), zapisz jego pozycję
                if (i == 0) last_servo1_pos = pos; 
            }

            // WYSYŁANIE RAMKI "A"
            CAN.beginPacket(TELEMETRY_ID);
            CAN.write(i);                             
            CAN.write(0);                             
            CAN.write(connected);                     
            CAN.write(move);                          
            CAN.write((const uint8_t*)&pos, 2);       
            CAN.write((const uint8_t*)&speed, 2);     
            CAN.endPacket();

            delay(2); 

            // WYSYŁANIE RAMKI "B"
            CAN.beginPacket(TELEMETRY_ID);
            CAN.write(i);                             
            CAN.write(1);                             
            CAN.write((const uint8_t*)&load, 2);      
            CAN.write((const uint8_t*)&current, 2);   
            CAN.write(voltage);                       
            CAN.write(temper);                        
            CAN.endPacket();

            delay(2); 
        }
    }
}

bool isReceivingCommands() {
    return (millis() - lastCanRxTime < 500);
}

