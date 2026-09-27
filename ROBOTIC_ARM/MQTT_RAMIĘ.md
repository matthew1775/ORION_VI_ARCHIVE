192.168.1.1 - Serwer mqtt
Robotic_Arm: 192.168.1.53 - ip adress esp32
Mqtt name from esp to main computer: Robotic_arm_enc
Mqtt name from main computer to esp computer: Robotic_arm_cmd

{
  "eventType": "Robotic_arm_cmd", // Typ wiadomości: wysyłanie poleceń do ramienia
  "payload": {
    /* --- POZYCJE GŁÓWNYCH PRZEGUBÓW --- */
    "joint1_rad": 0.0,        // Pozycja kątowa przegubu 1 [zakres: 0.0 do 3.0 rad]
    "joint2_rad": 0.0,        // Pozycja kątowa przegubu 2 [zakres: 0.0 do 3.0 rad]
    "joint3_rad": 0.0,        // Pozycja kątowa przegubu 3 [zakres: 0.0 do 3.0 rad]
    "joint4_rad": 0.0,        // Pozycja kątowa przegubu 4 [zakres: 0.0 do 3.0 rad]
    "joint5_rad": 0.0,        // Pozycja kątowa przegubu 5 [zakres: 0.0 do 3.0 rad]
    "joint6_rad": 0.0,        // Pozycja kątowa przegubu 6 [zakres: 0.0 do 3.0 rad]
    "joint7_rad": 0.0,        // Pozycja kątowa przegubu 7 [zakres: 0.0 do 3.0 rad]
    "joint8_rad": 0.0,        // Pozycja kątowa przegubu 8 [zakres: 0.0 do 3.0 rad]

    /* --- POZYCJE PRZEGUBÓW POMOCNICZYCH MINI --- */
    "joint_mini_1_rad": 0.0,  // Pozycja kątowa przegubu mini 1 [zakres: 0.0 do 3.0 rad]
    "joint_mini_2_rad": 0.0,  // Pozycja kątowa przegubu mini 2 [zakres: 0.0 do 3.0 rad]
    "joint_mini_3_rad": 0.0,  // Pozycja kątowa przegubu mini 3 [zakres: 0.0 do 3.0 rad]
    "joint_mini_4_rad": 0.0,  // Pozycja kątowa przegubu mini 4 [zakres: 0.0 do 3.0 rad]
    "joint_mini_5_rad": 0.0,  // Pozycja kątowa przegubu mini 5 [zakres: 0.0 do 3.0 rad]

    /* --- PRĘDKOŚCI GŁÓWNYCH PRZEGUBÓW --- */
    "joint1_speed": 0.0,      // Prędkość obrotowa przegubu 1 [zakres: 0 do 100]
    "joint2_speed": 0.0,      // Prędkość obrotowa przegubu 2 [zakres: 0 do 100]
    "joint3_speed": 0.0,      // Prędkość obrotowa przegubu 3 [zakres: 0 do 100]
    "joint4_speed": 0.0,      // Prędkość obrotowa przegubu 4 [zakres: 0 do 100]
    "joint5_speed": 0.0,      // Prędkość obrotowa przegubu 5 [zakres: 0 do 100]
    "joint6_speed": 0.0,      // Prędkość obrotowa przegubu 6 [zakres: 0 do 100]
    "joint7_speed": 0.0,      // Prędkość obrotowa przegubu 7 [zakres: 0 do 100]
    "joint8_speed": 0.0,      // Prędkość obrotowa przegubu 8 [zakres: 0 do 100]

    /* --- PRĘDKOŚCI PRZEGUBÓW POMOCNICZYCH MINI --- */
    "joint_mini_1_speed": 0.0, // Prędkość obrotowa przegubu mini 1 [zakres: 0 do 100]
    "joint_mini_2_speed": 0.0, // Prędkość obrotowa przegubu mini 2 [zakres: 0 do 100]
    "joint_mini_3_speed": 0.0, // Prędkość obrotowa przegubu mini 3 [zakres: 0 do 100]
    "joint_mini_4_speed": 0.0, // Prędkość obrotowa przegubu mini 4 [zakres: 0 do 100]
    "joint_mini_5_speed": 0.0  // Prędkość obrotowa przegubu mini 5 [zakres: 0 do 100]
  },
  "cmd": {
    "fan": false              // Sterowanie chłodzeniem: true (włącz), false (wyłącz)
  }
}

{
  "eventType": "Robotic_arm_enc", // Typ wiadomości: odczyt statusu i danych z czujników
  "payload": {
    /* --- ODCZYTY Z ENKODERÓW: GŁÓWNE PRZEGUBY --- */
    "enc_joint1_rad": 0.0,        // Aktualna pozycja przegubu 1 [zakres: 0.0 do 3.0 rad]
    "enc_joint2_rad": 0.0,        // Aktualna pozycja przegubu 2 [zakres: 0.0 do 3.0 rad]
    "enc_joint3_rad": 0.0,        // Aktualna pozycja przegubu 3 [zakres: 0.0 do 3.0 rad]
    "enc_joint4_rad": 0.0,        // Aktualna pozycja przegubu 4 [zakres: 0.0 do 3.0 rad]
    "enc_joint5_rad": 0.0,        // Aktualna pozycja przegubu 5 [zakres: 0.0 do 3.0 rad]
    "enc_joint6_rad": 0.0,        // Aktualna pozycja przegubu 6 [zakres: 0.0 do 3.0 rad]
    "enc_joint7_rad": 0.0,        // Aktualna pozycja przegubu 7 [zakres: 0.0 do 3.0 rad]
    "enc_joint8_rad": 0.0,        // Aktualna pozycja przegubu 8 [zakres: 0.0 do 3.0 rad]

    /* --- ODCZYTY Z ENKODERÓW: PRZEGUBY MINI --- */
    "enc_joint_mini_1_rad": 0.0,  // Aktualna pozycja przegubu mini 1 [zakres: 0.0 do 3.0 rad]
    "enc_joint_mini_2_rad": 0.0,  // Aktualna pozycja przegubu mini 2 [zakres: 0.0 do 3.0 rad]
    "enc_joint_mini_3_rad": 0.0,  // Aktualna pozycja przegubu mini 3 [zakres: 0.0 do 3.0 rad]
    "enc_joint_mini_4_rad": 0.0,  // Aktualna pozycja przegubu mini 4 [zakres: 0.0 do 3.0 rad]
    "enc_joint_mini_5_rad": 0.0,  // Aktualna pozycja przegubu mini 5 [zakres: 0.0 do 3.0 rad]

    /* --- TELEMETRIA: ZASILANIE I BEZPIECZEŃSTWO --- */
    "sensA": 0.0,                 // Odczyt prądu silnika A [zakres: 0.0 do 2.0 A]
    "sensB": 0.0,                 // Odczyt prądu silnika B [zakres: 0.0 do 2.0 A]
    "ampermeter": 0.0,            // Całkowity pobór prądu przez urządzenie [zakres: 0.0 do 20.0 A]
    "error": 0,                   // Kod błędu systemu (0 = OK, 1/2/3 = określone błędy)

    /* --- STATUSY POŁĄCZEŃ MAGISTRALI CAN --- */
    "canid2": 1,                  // Status CAN ID 2 (1 = połączony, 0 = rozłączony)
    "canid3": 1,                  // Status CAN ID 3 (1 = połączony, 0 = rozłączony)
    "canid4": 1,                  // Status CAN ID 4 (1 = połączony, 0 = rozłączony)
    "canid5": 1,                  // Status CAN ID 5 (1 = połączony, 0 = rozłączony)
    "canid6": 1,                  // Status CAN ID 6 (1 = połączony, 0 = rozłączony)
    "canid7": 1,                  // Status CAN ID 7 (1 = połączony, 0 = rozłączony)
    "canid8": 1                   // Status CAN ID 8 (1 = połączony, 0 = rozłączony)
  }
}