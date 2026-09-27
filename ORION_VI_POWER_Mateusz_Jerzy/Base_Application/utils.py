# utils.py
import time
from collections import deque

class AppState:
    """Klasa przechowująca współdzielony stan aplikacji Power"""
    def __init__(self):
        # Statusy MQTT
        self.mqtt_connected = False
        self.mqtt_status_text = "MQTT: Rozłączono"
        self.last_feedback_time = 0.0
        
        # Logi
        self.logs = [] 

        # Stany przełączników
        self.switches = {
            "S_INNE": 0, "S_SCI": 0, "S_ELEK": 0, "S_RAM": 0, "S_W_R": 0, "S_W_L": 0, "FAN1_ON": 0
        }

        # Dane telemetryczne bieżące
        self.temp_c = 0.0
        self.bat_v = [0.0, 0.0, 0.0, 0.0]  
        self.adc = {
            "adc_wl": 0, "adc_wr": 0, "adc_ram": 0, "adc_elek": 0, "adc_sci": 0, "adc_inne": 0
        }

        # --- DANE DO WYKRESÓW (Historia) ---
        self.start_time = time.time()
        self.history_time = deque(maxlen=100)  # Pamięta 100 ostatnich odczytów
        self.history_amps = {
            "adc_wl": deque(maxlen=100),
            "adc_wr": deque(maxlen=100),
            "adc_ram": deque(maxlen=100),
            "adc_elek": deque(maxlen=100),
            "adc_sci": deque(maxlen=100),
            "adc_inne": deque(maxlen=100)
        }

    def log(self, message):
        self.logs.append(message)