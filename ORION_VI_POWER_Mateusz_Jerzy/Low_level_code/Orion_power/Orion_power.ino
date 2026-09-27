#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_NeoPixel.h>
#include "Pins.h"

// --- KONFIGURACJA SIECI ---
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x56 };
IPAddress ip(192, 168, 1, 56);
const char* mqtt_server = "192.168.1.1"; // Zmień na IP swojego brokera MQTT
const int MQTT_PORT = 1883;

// --- TOPIKI MQTT ---
const char* TOPIC_CMD      = "Power/cmd";
const char* TOPIC_FEEDBACK = "Power/feedback";
const char* MQTT_CLIENT_ID = "ESP32_Power_Module";

EthernetClient ethClient;
PubSubClient mqttClient(ethClient);

// --- NEOPIXEL ---
#define NUMPIXELS 8
Adafruit_NeoPixel pixels(NUMPIXELS, Pins::NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// --- DS18B20 ---
OneWire oneWire(Pins::TEMP_PIN);
DallasTemperature sensors(&oneWire);
       

// Interwał wysyłania danych (w milisekundach)
const unsigned long MQTT_PUB_INTERVAL = 1000; 
unsigned long lastMqttPub = 0;
bool lastMqttState = false;

// --- FUNKCJE POMOCNICZE ---

void setStripColor(uint32_t color) {
    for(int i = 0; i < NUMPIXELS; i++) {
        pixels.setPixelColor(i, color);
    }
    pixels.show();
}

// --- PARAMETRY POMIARÓW ADC ---
const float ADC_VREF = 3.3f;        
const int ADC_RES = 4095;           

// INDYWIDUALNE WSPÓŁCZYNNIKI BATERII
// Bateria 1 wyliczona na 7.286. Pozostałe ustawione domyślnie na 7.8 (zmień je, gdy je zmierzysz)
float bat_multipliers[4] = {7.286f, 7.8f, 7.8f, 7.8f};

// Zmieniona funkcja odczytu napięcia przyjmująca indywidualny mnożnik
float readBatteryVoltage(uint8_t pin, float multiplier) {
    float vAdc = (analogRead(pin) * ADC_VREF) / (float)ADC_RES;
    return vAdc * multiplier;
}

// --- INICJALIZACJA SIECI (WYODRĘBNIONA) ---

void initNetwork() {
    Serial.println("[ETH] Reset układu Wiznet...");
    digitalWrite(Pins::WIZ_RST_PIN, LOW); 
    delay(100);
    digitalWrite(Pins::WIZ_RST_PIN, HIGH); 
    delay(200);

    // Wymuszenie własnych pinów SPI dla ESP32 -> W5500
    SPI.begin(Pins::WIZ_SCLK_PIN, Pins::WIZ_MISO_PIN, Pins::WIZ_MOSI_PIN, Pins::WIZ_SCN_PIN);
    Ethernet.init(Pins::WIZ_SCN_PIN);
    Ethernet.begin(mac, ip);
}

// --- OBSŁUGA MQTT ---

void callback(char* topic, byte* payload, unsigned int length) {
    String topicStr = String(topic);
    String messageTemp;
    messageTemp.reserve(length);
    for (unsigned int i = 0; i < length; i++) {
        messageTemp += (char)payload[i];
    }

    if (topicStr == TOPIC_CMD) {
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, messageTemp);
        
        if (!error) {
            if (doc.containsKey("S_INNE")) digitalWrite(Pins::S_INNE_PIN, doc["S_INNE"].as<int>() ? HIGH : LOW);
            if (doc.containsKey("S_SCI")) digitalWrite(Pins::S_SCI_PIN, doc["S_SCI"].as<int>() ? HIGH : LOW);
            if (doc.containsKey("S_ELEK")) digitalWrite(Pins::S_ELEK_PIN, doc["S_ELEK"].as<int>() ? HIGH : LOW);
            if (doc.containsKey("S_RAM")) digitalWrite(Pins::S_RAM_PIN, doc["S_RAM"].as<int>() ? HIGH : LOW);
            if (doc.containsKey("S_W_R")) digitalWrite(Pins::S_W_R_PIN, doc["S_W_R"].as<int>() ? HIGH : LOW);
            if (doc.containsKey("S_W_L")) digitalWrite(Pins::S_W_L_PIN, doc["S_W_L"].as<int>() ? HIGH : LOW);
            
            if (doc.containsKey("FAN1_ON")) digitalWrite(Pins::FAN1_ON_PIN, doc["FAN1_ON"].as<int>() ? HIGH : LOW);
        } else {
            Serial.println("[MQTT] Błąd parsowania JSON");
        }
    }
}

// --- NOWY RECONNECT ---

void reconnect() {
    if (!mqttClient.connected()) {
        static unsigned long lastRec = 0;
        static int failedAttempts = 0; // Zliczanie błędów z poprzedniego kroku

        if (millis() - lastRec > 5000) {
            lastRec = millis();
            Serial.print("[MQTT] Connecting to "); Serial.print(mqtt_server); Serial.println("...");
            
            if (mqttClient.connect(MQTT_CLIENT_ID)) { 
                Serial.println("[MQTT] Connected!");
                failedAttempts = 0;  
                mqttClient.subscribe(TOPIC_CMD);
            } else {
                failedAttempts++;  
                Serial.print("[MQTT] Failed to connect, attempt: ");
                Serial.println(failedAttempts);
                
                if (failedAttempts >= 5) {
                    Serial.println("[NETWORK] 5 failed attempts! Hard resetting Wiznet...");
                    initNetwork();       
                    failedAttempts = 0;  
                }
            }
        }
    }
}

void sendFeedbackMessage() {
    if (!mqttClient.connected()) return;
    StaticJsonDocument<1024> doc; 

    sensors.requestTemperatures();
    float tempC = sensors.getTempCByIndex(0);
    doc["temp_c"] = (tempC == DEVICE_DISCONNECTED_C) ? -127.0 : tempC;

    doc["bat_1_v"] = readBatteryVoltage(Pins::BAT_1_ADC_PIN, bat_multipliers[0]);
    doc["bat_2_v"] = readBatteryVoltage(Pins::BAT_2_ADC_PIN, bat_multipliers[1]);
    doc["bat_3_v"] = readBatteryVoltage(Pins::BAT_3_ADC_PIN, bat_multipliers[2]);
    doc["bat_4_v"] = readBatteryVoltage(Pins::BAT_4_ADC_PIN, bat_multipliers[3]);

    doc["adc_wl"]   = analogRead(Pins::ADC_WL_PIN);
    doc["adc_wr"]   = analogRead(Pins::ADC_WR_PIN);
    doc["adc_ram"]  = analogRead(Pins::ADC_RAM_PIN);
    doc["adc_elek"] = analogRead(Pins::ADC_ELEK_PIN);
    doc["adc_sci"]  = analogRead(Pins::ADC_SCI_PIN);
    doc["adc_inne"] = analogRead(Pins::ADC_INNE_PIN);

    char buffer[1024];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_FEEDBACK, buffer);
}

// --- SETUP & LOOP ---

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n\n>>> SYSTEM POWER START <<<");

    Pins::init_pins();

    pixels.begin();
    pixels.setBrightness(50);
    setStripColor(pixels.Color(128, 0, 128)); // Fioletowy
    
    sensors.begin();

    // Pierwsza inicjalizacja sieci używa teraz naszej nowej funkcji
    initNetwork();

    mqttClient.setServer(mqtt_server, MQTT_PORT);
    mqttClient.setCallback(callback);
    mqttClient.setBufferSize(1024);

    Serial.println(">>> SETUP COMPLETE <<<");
    setStripColor(pixels.Color(255, 255, 0)); // Żółty
}

void loop() {
    unsigned long now = millis();
    bool currentMqttState = mqttClient.connected();

    if (currentMqttState != lastMqttState) {
        lastMqttState = currentMqttState;
        if (currentMqttState) {
            setStripColor(pixels.Color(0, 255, 0)); // ZIELONY
            Serial.println("[LED] Status: MQTT Połączone");
        } else {
            setStripColor(pixels.Color(255, 0, 0)); // CZERWONY
            Serial.println("[LED] Status: MQTT Rozłączone");
        }
    }

    reconnect();
    mqttClient.loop();

    if (now - lastMqttPub > MQTT_PUB_INTERVAL) {
        lastMqttPub = now;
        sendFeedbackMessage();
    }
}