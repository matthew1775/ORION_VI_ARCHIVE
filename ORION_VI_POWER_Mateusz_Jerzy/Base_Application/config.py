# config.py

# --- KONFIGURACJA SIECI ---
BROKER_ADDRESS = "192.168.1.1"   # IP brokera/ESP32
BROKER_PORT = 1883

# Tematy MQTT
TOPIC_CMD      = "Power/cmd"
TOPIC_FEEDBACK = "Power/feedback"

# --- KOLORY GUI ---
BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
BTN_OFF_COLOR = "#cc3333"   # Czerwony - wyłączone
BTN_ON_COLOR = "#228822"    # Zielony - włączone


# --- KALIBRACJA ACS712 ---
# Wpisz tutaj odczyty RAW, gdy prąd wynosi fizycznie 0 Amperów (wartości z Twojego screena)
ACS712_ZERO_RAW = {
    "adc_wl": 3002,
    "adc_wr": 3008,
    "adc_ram": 3057,
    "adc_elek": 3036,
    "adc_sci": 2994,
    "adc_inne": 2976
}

# Czułość sensora:
# 0.185 dla modułu 5A
# 0.100 dla modułu 20A
# 0.066 dla modułu 30A
ACS712_SENSITIVITY = 0.185