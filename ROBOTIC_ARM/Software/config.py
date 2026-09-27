import math

# --- KONFIGURACJA SIECI ---
BROKER_ADDRESS = "192.168.1.1"   
BROKER_PORT = 1883
TOPIC_CMD      = "Robotic_arm_cmd"
TOPIC_FEEDBACK = "Robotic_arm_enc"

# --- LIMITY STOPNI SWOBODY (Min, Max) w stopniach ---
AXIS_LIMITS = [
    (0.0, 90.0),    # 1. Obrotnica
    (0.0, 90.0),    # 2. Bark (Zmieniono z 60 na 90)
    (0.0, 110.0),   # 3. Łokieć
    (-180, 180.0),   # 4. Nadgarstek
    (-300.0, 60.0),   # 5. Oś 5 (Przegub - tu już było 360)
    (-211.0, 149.0),   # 6. Wysuw (Zmieniono z 20 na 360)
    (0.0, 360.0),   # 7. Rotacja końcówki (Zostawiamy dla GUI, limit zdejmiemy w kodzie wejść)
    (0.0, 60.0)     # 8. Szczęki
]

# --- PRĘDKOŚCI RUCHU (Stopnie na cykl dla Osi 1-8) ---
# Prędkości zmniejszone 10-krotnie
AXIS_SPEEDS = [
    0.15,   # 1. Obrotnica
    0.1,    # 2. Bark
    0.1,    # 3. Łokieć
    2,   # 4. Nadgarstek
    1.5,    # 5. Oś 5
    1.5,   # 6. Wysuw
    100,    # 7. Rotacja Końcówki
    0.2     # 8. Szczęki
]

JOYSTICK_DEADZONE = 0.15

# --- KOLORY GUI ---
BG_COLOR = "#10112E"
FG_COLOR = "#ffffff"
BTN_RESET_COLOR = "#cc3333"