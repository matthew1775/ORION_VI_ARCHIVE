#config.py
import math

# --- KONFIGURACJA SIECI ---
BROKER_ADDRESS = "192.168.1.1"   # IP brokera/ESP32
BROKER_PORT = 1883

# Tematy MQTT
TOPIC_CMD          = "propulsion/cmd"
TOPIC_FEEDBACK_LEFT = "propulsion/feedback_left"
TOPIC_FEEDBACK_RIGHT = "propulsion/feedback_right"


# Komendy MQTT
CMD_MAP = {
    "none": 0,
    "calibrate": 1,
    "closed_loop": 2,
    "set_vel_mode": 3,
    "set_ramp_mode": 4,
    "dump_errors": 5,
    "reboot_odrive": 6
}

# --- KONFIGURACJA STEROWANIA ---
ABSOLUTE_MAX_LIMIT = 30.0  
JOYSTICK_DEADZONE = 0.2    
STEERING_AXIS_INDEX = 4    # Oś 5 (indeks 4)

# --- KONFIGURACJA KOŁA ---
WHEEL_DIAMETER_CM = 45.0
GEAR_RATIO = 100.8
WHEEL_CIRCUMFERENCE_M = (WHEEL_DIAMETER_CM / 100.0) * math.pi
DISTANCE_PER_MOTOR_REV = WHEEL_CIRCUMFERENCE_M / GEAR_RATIO

# --- KONFIGURACJA WYKRESU ---
PLOT_SKIP_FRAMES = 4  # Odświeżaj wykres co N klatek

# --- KOLORY GUI ---
BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
BTN_RESET_COLOR = "#cc3333"
BTN_CMD_COLOR = "#0055aa"
BTN_FULL_START_COLOR = "#228822"
BTN_REBOOT_COLOR = "#aa0000"
BTN_DUMP_COLOR = "#d35400"