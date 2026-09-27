#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "Pins.h"
#include "Config.h"
#include "ID4_CAN.h"

// Pasek 8 diod NeoPixel
#define NUMPIXELS 8
Adafruit_NeoPixel pixels(NUMPIXELS, Pins::NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
    //Serial.begin(115200);
    //Serial.println("[SYSTEM] Uruchamianie węzła ID 4...");

    // 1. Inicjalizacja NeoPixel (początkowo jasność 0)
    pixels.begin();
    pixels.setBrightness(255);
    for(int i = 0; i < NUMPIXELS; i++) {
        pixels.setPixelColor(i, pixels.Color(255, 0, 0)); // Domyślnie czerwony (brak CAN)
    }
    pixels.show();

    // 2. Inicjalizacja modułów CAN i Serw
    initCanAndServos();

    //Serial.println("[SYSTEM] Konfiguracja zakończona.");
}

void loop() {
    // 1. Obsługa zadań cyklicznych serw i magistrali CAN
    handleCanAndServos();

    // 2. Pobranie pozycji z pierwszego serwa (0 do 4095 dla 360 stopni)
    int16_t current_pos = getServo1Position();
    
    // Zabezpieczenie na wypadek wyjazdu poza bezpieczny zakres 0-360
    if (current_pos < 0) current_pos = 0;
    if (current_pos > 4095) current_pos = 4095;

    // 3. Mapowanie pozycji enkodera (0-4095) na jasność diod (0-255)
    uint8_t brightness = map(current_pos, 0, 4095, 100, 255);
    
    // 4. Ustalenie koloru na podstawie połączenia z głównym ESP32
    bool isActive = isReceivingCommands();
    uint32_t color = isActive ? pixels.Color(0, 255, 0) : pixels.Color(255, 0, 0);

    // 5. Aktualizacja całego paska LED
    pixels.setBrightness(brightness);
    for(int i = 0; i < NUMPIXELS; i++) {
        pixels.setPixelColor(i, color);
    }
    pixels.show();
}