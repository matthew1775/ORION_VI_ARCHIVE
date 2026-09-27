// Pins.h
#ifndef PINS_H
#define PINS_H

#include <Arduino.h>
#include <cstdint>


// !!!GPIO 0, 2, 12, and 15 potentially unsafe!!!
namespace Pins
{
    // 21V -> 2.69V -> ADC
    constexpr uint8_t BAT_4_ADC_PIN = GPIO_NUM_36; // +
    constexpr uint8_t BAT_3_ADC_PIN = GPIO_NUM_39; // +
    constexpr uint8_t BAT_2_ADC_PIN = GPIO_NUM_34; // +
    constexpr uint8_t BAT_1_ADC_PIN = GPIO_NUM_35; // +

    // AMPERE METERS (class?)
    constexpr uint8_t ADC_WL_PIN    = GPIO_NUM_32; // +
    constexpr uint8_t ADC_WR_PIN    = GPIO_NUM_33; // +
    constexpr uint8_t ADC_RAM_PIN   = GPIO_NUM_25; // +
    constexpr uint8_t ADC_ELEK_PIN  = GPIO_NUM_26; // +
    constexpr uint8_t ADC_SCI_PIN   = GPIO_NUM_27; // +
    constexpr uint8_t ADC_INNE_PIN  = GPIO_NUM_14; // +
    // FANS (5V)
    constexpr uint8_t FAN1_ON_PIN   = GPIO_NUM_12; // +

    // DS18B20
    constexpr uint8_t TEMP_PIN      = GPIO_NUM_13; // +

    // NEOPIXEL
    constexpr uint8_t NEOPIXEL_PIN  = GPIO_NUM_15; // +

    // CAN
    constexpr uint8_t RX_CAN_PIN    = GPIO_NUM_3; // +
    constexpr uint8_t TX_CAN_PIN    = GPIO_NUM_1; // +

    // WIZNET (WN_W5500) !!! Needs asking !!!
    constexpr uint8_t WIZ_MOSI_PIN  = GPIO_NUM_23; // -
    constexpr uint8_t WIZ_SCLK_PIN  = GPIO_NUM_18; // -
    constexpr uint8_t WIZ_SCN_PIN   = GPIO_NUM_4;  // -
    constexpr uint8_t WIZ_MISO_PIN  = GPIO_NUM_19; // -
    constexpr uint8_t WIZ_RST_PIN   = GPIO_NUM_5;  // -

    // SWITCHES (class?)
    constexpr uint8_t S_INNE_PIN    = GPIO_NUM_2; // +
    constexpr uint8_t S_SCI_PIN     = GPIO_NUM_0; // +
    constexpr uint8_t S_ELEK_PIN    = GPIO_NUM_16; // +
    constexpr uint8_t S_RAM_PIN     = GPIO_NUM_17; // +
    constexpr uint8_t S_W_R_PIN     = GPIO_NUM_21; // +
    constexpr uint8_t S_W_L_PIN     = GPIO_NUM_22; // +

    inline void init_pins()
    {
        // Batteries
        pinMode(BAT_1_ADC_PIN, INPUT);
        pinMode(BAT_2_ADC_PIN, INPUT);
        pinMode(BAT_3_ADC_PIN, INPUT);
        pinMode(BAT_4_ADC_PIN, INPUT);

        // WIZNET
        pinMode(WIZ_RST_PIN, OUTPUT);

        // Fan
        pinMode(FAN1_ON_PIN, OUTPUT);
        digitalWrite(FAN1_ON_PIN, LOW);

        // Switches
        pinMode(S_INNE_PIN, OUTPUT);
        pinMode(S_SCI_PIN, OUTPUT);
        pinMode(S_ELEK_PIN, OUTPUT);
        pinMode(S_RAM_PIN, OUTPUT);
        pinMode(S_W_R_PIN, OUTPUT);
        pinMode(S_W_L_PIN, OUTPUT);

        digitalWrite(S_INNE_PIN, LOW);
        digitalWrite(S_SCI_PIN, LOW);
        digitalWrite(S_ELEK_PIN, LOW);
        digitalWrite(S_RAM_PIN, LOW);
        digitalWrite(S_W_R_PIN, LOW);
        digitalWrite(S_W_L_PIN, LOW);
    }
}

#endif