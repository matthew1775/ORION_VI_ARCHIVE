// ODriveCAN.cpp
#include "ODriveCAN.h"
#include "Network.h" 

void initCAN() {
  CAN.setPins(CAN_RX_PIN, CAN_TX_PIN);
  if (!CAN.begin(CAN_BAUDRATE)) {
    Serial.println("ERROR: CAN Init Failed!");
  } else {
    Serial.println("CAN Init OK");
  }
}

void sendVelocity(int node_id, float velocity) {
  float torqueFF = 0.0f;
  int id = (node_id << 5) | CMD_ID_SET_INPUT_VEL;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&velocity, 4);
  CAN.write((uint8_t*)&torqueFF, 4);
  CAN.endPacket();
}

void setAxisState(int node_id, int32_t state) {
  int id = (node_id << 5) | CMD_ID_SET_AXIS_STATE;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&state, 4);
  CAN.endPacket();
}

void setControlMode(int node_id, int32_t controlMode, int32_t inputMode) {
  int id = (node_id << 5) | CMD_ID_SET_CONTROLLER_MODE;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&controlMode, 4);
  CAN.write((uint8_t*)&inputMode, 4);
  CAN.endPacket();
}

void requestEncoderData(int node_id) {
  int id = (node_id << 5) | CMD_ID_GET_ENCODER;
  CAN.beginPacket(id, 8, true);
  CAN.endPacket();
}

void clearErrors(int node_id) {
  int id = (node_id << 5) | CMD_ID_CLEAR_ERRORS;
  CAN.beginPacket(id);
  CAN.endPacket();
}

void rebootODrive(int node_id) {
  int id = (node_id << 5) | CMD_ID_REBOOT_ODRIVE;
  CAN.beginPacket(id);
  CAN.endPacket();
}

void requestODriveErrors(int node_id) {
  int id = (node_id << 5) | CMD_ID_GET_ERROR;
  CAN.beginPacket(id, 8, true);
  CAN.endPacket();
}

void handleCANMessages() {
  int packetSize = CAN.parsePacket();
  if (packetSize) {
    long id = CAN.packetId();
    int cmdId = id & 0x01F;
    int nodeId = (id >> 5) & 0x3F;
    
    if (cmdId == CMD_ID_GET_ENCODER && packetSize >= 8) {
        uint8_t buffer[8];
        CAN.readBytes(buffer, 8);
        float pos, vel;
        memcpy(&pos, &buffer[0], 4);
        memcpy(&vel, &buffer[4], 4);
                
        if (nodeId == ODRIVE_FRONT_ID) {
            measuredPosFront = pos * DIR_FRONT; // Korekta kierunku
            measuredVelFront = vel * DIR_FRONT; // Korekta kierunku
        } else if (nodeId == ODRIVE_REAR_ID) {
            measuredPosRear = pos * DIR_REAR;   // Korekta kierunku
            measuredVelRear = vel * DIR_REAR;   // Korekta kierunku
        }
     }
    else if (cmdId == CMD_ID_GET_ERROR && packetSize >= 4) {
       uint8_t buffer[4];
       CAN.readBytes(buffer, 4);
       uint32_t errors;
       memcpy(&errors, &buffer[0], 4);
       
       if (nodeId == ODRIVE_FRONT_ID) activeErrorsFront = errors;
       else if (nodeId == ODRIVE_REAR_ID) activeErrorsRear = errors;
       
       if (errors != 0) {
           sendErrorMessage(errors, nodeId);
       }
    }
  }
}