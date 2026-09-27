// ODriveCAN.h
#ifndef ODRIVE_CAN_H
#define ODRIVE_CAN_H

#include <Arduino.h>
#include <CAN.h>
#include "Config.h"

// Komendy ODrive
#define CMD_ID_GET_ERROR       0x003
#define CMD_ID_SET_AXIS_STATE  0x007
#define CMD_ID_GET_ENCODER     0x009
#define CMD_ID_SET_CONTROLLER_MODE 0x00B
#define CMD_ID_SET_INPUT_VEL   0x00D
#define CMD_ID_REBOOT_ODRIVE   0x016 
#define CMD_ID_CLEAR_ERRORS    0x018

#define AXIS_STATE_ENCODER_OFFSET_CALIBRATION 7
#define AXIS_STATE_CLOSED_LOOP_CONTROL        8
#define CONTROL_MODE_VELOCITY_CONTROL         2
#define INPUT_MODE_PASSTHROUGH                1
#define INPUT_MODE_VEL_RAMP                   2  

void initCAN();
void sendVelocity(int node_id, float velocity);
void setAxisState(int node_id, int32_t state);
void setControlMode(int node_id, int32_t controlMode, int32_t inputMode);
void requestODriveErrors(int node_id);
void requestEncoderData(int node_id);
void clearErrors(int node_id);
void rebootODrive(int node_id);
void handleCANMessages(); 

#endif