#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "Config.h"
#include "pins.h"
#include "Network.h"
#include "ARM_CAN.h"
#include "MotorControl.h"


#define NUMPIXELS 8
Adafruit_NeoPixel pixels(NUMPIXELS, Pins::NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);
unsigned long lastMqttCmdTime = 0;
bool lastMqttState = false;
bool isFirstLoop = true;

void setStripColor(uint32_t color) {
    for(int i = 0; i < NUMPIXELS; i++) {
        pixels.setPixelColor(i, color);
    }
    pixels.show();
}


void setup() {
  //Serial.begin(115200);
  Pins::init_pins();
  
  // Ustawienie 10-bitowej rozdzielczości dla pinów PWM (zakres 0 - 1023)
  analogWriteResolution(10); 

  pixels.begin();
  pixels.setBrightness(50);
  setStripColor(pixels.Color(128, 0, 128)); // Fioletowy
  pixels.show();
  //Serial.println("[SYSTEM] Start konfiguracji...");
  
  initNetwork();
  initCAN();

  setStripColor(pixels.Color(255, 255, 0)); // Żółty
  pixels.show();
  //Serial.println("[SYSTEM] Konfiguracja zakończona!");
  delay(1000);
}

void loop() {
  handleNetwork(); 
  handleCAN();
  
  // ---> Wywołanie naszej nowej funkcji <---
  handleLocalMotor();

  // ==========================================
  // OBSŁUGA STATUSU NEOPIXEL
  // ==========================================
  bool currentMqttState = isMqttConnected();
  if (currentMqttState != lastMqttState || isFirstLoop) {
      lastMqttState = currentMqttState;
      isFirstLoop = false;
      
      if (currentMqttState) {
          setStripColor(pixels.Color(0, 255, 0)); // ZIELONY - Połączono
      } else {
          setStripColor(pixels.Color(255, 0, 0)); // CZERWONY - Brak połączenia
      }
  }

  // ==========================================
  // WYSYŁANIE TELEMETRII CO 100ms
  // ==========================================
  static unsigned long lastPub = 0;
  if (millis() - lastPub > 100) {
    lastPub = millis();
    sensA = analogRead(Pins::SENS_A_PIN) * (2.0 / 4095.0);
    sendFeedbackMessage();
  }
  delay(1);
}