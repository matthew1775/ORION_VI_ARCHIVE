#ifndef NETWORK_H
#define NETWORK_H

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "Config.h"

void initNetwork();
void handleNetwork(); 
void sendFeedbackMessage();
bool isMqttConnected(); // <--- Nowa funkcja do sprawdzania statusu

#endif