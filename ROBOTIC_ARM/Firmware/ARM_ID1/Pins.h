#pragma once

#include <Arduino.h>
#include <cstdint>

namespace Pins
{
    // two HDR-M-2.54_1x3
    constexpr uint8_t POT_1_PIN      = GPIO_NUM_36; // +
    constexpr uint8_t POT_2_PIN      = GPIO_NUM_39; // +

    // ACS712-30A-SMD-IC
    constexpr uint8_t ADC_PIN        = GPIO_NUM_32; // +
    
    // NeoPixel
    constexpr uint8_t NEOPIXEL_PIN   = GPIO_NUM_4; // +

    // CAN/TWAI
    constexpr uint8_t RX_CAN_PIN     = GPIO_NUM_3; // +
    constexpr uint8_t TX_CAN_PIN     = GPIO_NUM_1; // +

    // WIZNET (WN_W5500) !!! TODO: need more info !!!
    constexpr uint8_t WIZ_MOSI_PIN   = GPIO_NUM_23;
    constexpr uint8_t WIZ_SCLK_PIN   = GPIO_NUM_18;
    constexpr uint8_t WIZ_SCN_PIN    = GPIO_NUM_33;
    constexpr uint8_t WIZ_RST_PIN    = GPIO_NUM_5;
    constexpr uint8_t WIZ_MISO_PIN   = GPIO_NUM_19;

    // Servo (class?)
    constexpr uint8_t SERVO1_PWM_PIN = GPIO_NUM_25; // +
    constexpr uint8_t SERVO2_PWM_PIN = GPIO_NUM_26; // +
    constexpr uint8_t SERVO3_PWM_PIN = GPIO_NUM_27; // +
    constexpr uint8_t SERVO4_PWM_PIN = GPIO_NUM_14; // +
    constexpr uint8_t SERVO5_PWM_PIN = GPIO_NUM_12; // +
    constexpr uint8_t SERVO6_PWM_PIN = GPIO_NUM_13; // +
    constexpr uint8_t RX_SERVO_PIN   = GPIO_NUM_16; // +
    constexpr uint8_t TX_SERVO_PIN   = GPIO_NUM_17; // +

    // L298N motor driver module
    constexpr uint8_t SENS_A_PIN     = GPIO_NUM_34; // +- with workaround
    constexpr uint8_t SENS_B_PIN     = GPIO_NUM_35; // +- with workaround
    constexpr uint8_t IN_POS_PIN     = GPIO_NUM_0; // +
    constexpr uint8_t IN_NEG_PIN     = GPIO_NUM_2; // +
    constexpr uint8_t ENABLE_PIN     = GPIO_NUM_15; // +

    // I2C
    constexpr uint8_t SDA_PIN        = GPIO_NUM_21;
    constexpr uint8_t SCL_PIN        = GPIO_NUM_22;

    inline void init_pins()
    {
        pinMode(POT_1_PIN, INPUT);
        pinMode(POT_2_PIN, INPUT);
        
        pinMode(SENS_A_PIN, INPUT);
        pinMode(SENS_B_PIN, INPUT);

        pinMode(SERVO1_PWM_PIN, OUTPUT);
        pinMode(SERVO2_PWM_PIN, OUTPUT);
        pinMode(SERVO3_PWM_PIN, OUTPUT);
        pinMode(SERVO4_PWM_PIN, OUTPUT);
        pinMode(SERVO5_PWM_PIN, OUTPUT);
        pinMode(SERVO6_PWM_PIN, OUTPUT);
        pinMode(RX_SERVO_PIN, INPUT);
        pinMode(TX_SERVO_PIN, OUTPUT);

        // Konfiguracja pinów L298N jako wyjścia
        pinMode(IN_POS_PIN, OUTPUT);
        pinMode(IN_NEG_PIN, OUTPUT);
        pinMode(ENABLE_PIN, OUTPUT);
    }
}