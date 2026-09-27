// Network.cpp
#include "Network.h"

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, NET_MAC_END };
IPAddress ip(192, 168, 1, NET_IP_END); 

const char* mqtt_server = "192.168.1.1";  
EthernetClient ethClient;
PubSubClient client(ethClient);

void executeCommand(int cmd, int node_id) {
    switch(cmd) {
        case 1: setAxisState(node_id, AXIS_STATE_ENCODER_OFFSET_CALIBRATION); break;
        case 2: setAxisState(node_id, AXIS_STATE_CLOSED_LOOP_CONTROL); break;
        case 3: setControlMode(node_id, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_PASSTHROUGH); break;
        case 4: setControlMode(node_id, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_VEL_RAMP); break;
        case 5: requestODriveErrors(node_id); break;
        case 6: rebootODrive(node_id); break;
        
        // --- NOWY CASE 7: NATYCHMIASTOWE HAMOWANIE ---
        case 7: 
            if (node_id == ODRIVE_FRONT_ID) targetVelocityFront = 0.0f;
            if (node_id == ODRIVE_REAR_ID)  targetVelocityRear = 0.0f;
            
            // Wyłączamy rampę - przełączamy w tryb natychmiastowy (PASSTHROUGH)
            setControlMode(node_id, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_PASSTHROUGH);
            
            // Natychmiast wymuszamy zerową prędkość po szynie CAN
            sendVelocity(node_id, 0.0f);
            break;
    }
}

void callback(char* topic, byte* payload, unsigned int length) {
  if (length > 1024) return;    
  String topicStr = String(topic);
  String messageTemp;
  messageTemp.reserve(length);
  for (unsigned int i = 0; i < length; i++) messageTemp += (char)payload[i];
  
  if (topicStr == TOPIC_CMD) {
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, messageTemp);
    
    // (początek funkcji callback pozostaje bez zmian)

    if (!error) {
      if (doc["eventType"] == "propulsion") {
        JsonObject payloadObj = doc["velocity"];
        
        targetVelocityFront = payloadObj[JSON_FRONT_SPEED].as<float>();
        targetVelocityRear  = payloadObj[JSON_REAR_SPEED].as<float>();
        
        targetSteeringFront = payloadObj[JSON_FRONT_STEER].as<float>();
        targetSteeringRear  = payloadObj[JSON_REAR_STEER].as<float>();
        
        // --- DODANE: Zapewniamy powrót do łagodnej rampy przy normalnej jeździe ---
        setControlMode(ODRIVE_FRONT_ID, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_VEL_RAMP);
        setControlMode(ODRIVE_REAR_ID, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_VEL_RAMP);
        
        lastMqttCmdTime = millis();
      }
      else if (doc.is<JsonArray>()) {
        JsonArray arr = doc.as<JsonArray>();
        if(arr.size() == 5) {
            int lf_cmd = arr[CMD_IDX_FRONT]; 
            int lr_cmd = arr[CMD_IDX_REAR];  
            int override_cmd = arr[4];
                         
            int cmd_front = override_cmd ? override_cmd : lf_cmd;
            int cmd_rear = override_cmd ? override_cmd : lr_cmd;
            if(cmd_front != 0) executeCommand(cmd_front, ODRIVE_FRONT_ID);
            if(cmd_rear != 0) executeCommand(cmd_rear, ODRIVE_REAR_ID);
        }
      }
    }
  }
}

void reconnect() {
  if (!client.connected()) {
      static unsigned long lastRec = 0;
      static int failedAttempts = 0; // Zliczanie błędów z poprzedniego kroku

      if (millis() - lastRec > 3000) {
        lastRec = millis();
        Serial.print("[MQTT] Connecting to "); Serial.print(mqtt_server); Serial.println("...");
        
        if (client.connect(MQTT_CLIENT_ID)) {  
          Serial.println("[MQTT] Connected!");
          failedAttempts = 0;  
          client.subscribe(TOPIC_CMD);
        } else {
          failedAttempts++;  
          Serial.print("[MQTT] Failed to connect, attempt: ");
          Serial.println(failedAttempts);
          
          if (failedAttempts >= 2) {
            Serial.println("[NETWORK] 5 failed attempts! Hard resetting Wiznet...");
            initNetwork();       
            failedAttempts = 0;  
          }
        }
      }
  }
}

void initNetwork() {
  Serial.println("Init Ethernet...");
  pinMode(ETH_RST_PIN, OUTPUT);
  digitalWrite(ETH_RST_PIN, LOW); delay(100);
  digitalWrite(ETH_RST_PIN, HIGH); delay(200);    
  SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN, ETH_CS_PIN);
  Ethernet.init(ETH_CS_PIN);
  Ethernet.begin(mac, ip);
  client.setServer(mqtt_server, MQTT_PORT);
  client.setCallback(callback);
  client.setBufferSize(1024); 
}

void handleNetwork() {
  reconnect();
  client.loop();
}

void sendFeedbackMessage() {
    if (!client.connected()) return;
    StaticJsonDocument<512> doc; // Zwiększony dokument, bo dodajemy klucze JSON
    
    doc["side_id"] = FEEDBACK_SIDE_ID;
    
    // Dane z ODrive
    doc["vel_front"] = measuredVelFront;
    doc["pos_front"] = measuredPosFront;
    doc["vel_rear"]  = measuredVelRear;
    doc["pos_rear"]  = measuredPosRear;
    
    // Dane telemetryczne z Serw
    doc["servoA_vfb"] = servoVoltageA;
    doc["servoA_cfb"] = servoCurrentA; // Prąd w Amperach
    doc["servoB_vfb"] = servoVoltageB;
    doc["servoB_cfb"] = servoCurrentB; // Prąd w Amperach

    char buffer[512];
    serializeJson(doc, buffer);
    client.publish(TOPIC_FEEDBACK, buffer);
}

void sendErrorMessage(uint32_t errorDesc, int odrive_id) {
    if (!client.connected()) return;
    StaticJsonDocument<256> doc;
    doc["error"] = errorDesc;
    doc["odrive_id"] = odrive_id;
         
    char errBuf[256];
    serializeJson(doc, errBuf);
    client.publish(TOPIC_FEEDBACK, errBuf);
}

bool isMqttConnected() {
    return client.connected();
}