// Network.h
#ifndef NETWORK_H
#define NETWORK_H

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "Config.h"
#include "ODriveCAN.h"

void initNetwork();
void handleNetwork();
void sendFeedbackMessage();
void sendErrorMessage(uint32_t errorDesc, int odrive_id);
bool isMqttConnected();


#endif