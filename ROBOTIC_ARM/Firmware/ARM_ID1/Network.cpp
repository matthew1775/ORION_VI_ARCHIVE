#include "Network.h"
#include <SPI.h>
#include "pins.h" // <--- Ważne: dołączamy plik z pinami

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 1, 53);      
const char* mqtt_server = "192.168.1.1"; 

EthernetClient ethClient;
PubSubClient client(ethClient);

// Definicje zmiennych globalnych
float target_joints[8], target_mini_joints[5];
float target_speeds[8] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 100.0f, 0.0f};
bool fan_state = false;
float enc_joints[8], enc_mini_joints[5], sensA, sensB, ampermeter;
int system_error = 0;
bool can_status[7] = {false};

float target_mini_speeds[5] = {100.0f, 100.0f, 100.0f, 100.0f, 100.0f}; // Wartość 100 = STOP

void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<1536> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    //Serial.print("[MQTT] JSON Error: "); Serial.println(error.c_str());
    return;
  }

  String eventType = doc["eventType"] | "";
  if (eventType == "Robotic_arm_cmd") {
    lastMqttCmdTime = millis();
    JsonObject p = doc["payload"];
    
    // Pobieranie pozycji i prędkości głównej
    for(int i=0; i<8; i++) {
      char keyRad[15], keySpeed[15];
      sprintf(keyRad, "joint%d_rad", i+1);
      sprintf(keySpeed, "joint%d_speed", i+1);
      target_joints[i] = p[keyRad] | 0.0f;
      target_speeds[i] = p[keySpeed] | 0.0f;
    }

    // Pobieranie przegubów mini
    for(int i=0; i<5; i++) {
      char keyRad[20], keySpeed[20];
      sprintf(keyRad, "joint_mini_%d_rad", i+1);
      sprintf(keySpeed, "joint_mini_%d_speed", i+1);
      target_mini_joints[i] = p[keyRad] | 0.0f;
      target_mini_speeds[i] = p[keySpeed] | 100.0f;
    }

    fan_state = doc["cmd"]["fan"] | false;
    //Serial.println("[MQTT] Command Received & Parsed");
  }
}

void initNetwork() {
  //Serial.println("Init Ethernet...");
  
  // Zaktualizowane piny z przestrzeni nazw Pins::
  pinMode(Pins::WIZ_RST_PIN, OUTPUT);
  digitalWrite(Pins::WIZ_RST_PIN, LOW); delay(100);
  digitalWrite(Pins::WIZ_RST_PIN, HIGH); delay(200);
  
  SPI.begin(Pins::WIZ_SCLK_PIN, Pins::WIZ_MISO_PIN, Pins::WIZ_MOSI_PIN, Pins::WIZ_SCN_PIN);
  Ethernet.init(Pins::WIZ_SCN_PIN);
  Ethernet.begin(mac, ip);
  
  client.setServer(mqtt_server, MQTT_PORT);
  client.setCallback(callback);
  client.setBufferSize(2048); 
}

void sendFeedbackMessage() {
    if (!client.connected()) return;

    StaticJsonDocument<1536> doc;
    doc["eventType"] = "Robotic_arm_enc";
    JsonObject p = doc.createNestedObject("payload");

    // Pakowanie enkoderów
    for(int i=0; i<8; i++) {
      char key[20]; sprintf(key, "enc_joint%d_rad", i+1);
      p[key] = enc_joints[i];
    }
    for(int i=0; i<5; i++) {
      char key[25]; sprintf(key, "enc_joint_mini_%d_rad", i+1);
      p[key] = enc_mini_joints[i];
    }

    // Telemetria
    p["error"] = system_error;

    // Statusy CAN
    for(int i=0; i<7; i++) {
      char key[10]; sprintf(key, "canid%d", i+2);
      p[key] = can_status[i] ? 1 : 0;
    }

    char buffer[1536];
    serializeJson(doc, buffer);
    client.publish(TOPIC_FEEDBACK, buffer);
}

void handleNetwork() {
  if (!client.connected()) {
    if (client.connect("Robotic_Arm_ESP32")) {
      client.subscribe(TOPIC_CMD);
    }
  }
  client.loop();
}

// ... reszta pliku Network.cpp bez zmian ...

bool isMqttConnected() {
    return client.connected();
}