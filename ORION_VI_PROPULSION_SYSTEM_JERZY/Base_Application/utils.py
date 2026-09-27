# utils.py
import time
from collections import deque

class LatencyEstimator:
    def __init__(self, maxlen=50):
        self.history:deque[tuple[float, float]] = deque(maxlen=maxlen)
    
    def push_target(self, target_vel: float):
        self.history.append((time.time(), target_vel))
        
    def estimate_lag(self, current_measured_vel):
        if abs(current_measured_vel) < 0.5:
            return None
        best_time = None
        min_diff = float('inf')
        # Przeszukiwanie historii w poszukiwaniu pasującej prędkości
        for t_stamp, t_vel in reversed(self.history):
            diff = abs(t_vel - current_measured_vel)
            if diff < min_diff:
                min_diff = diff
                best_time = t_stamp
            if diff > min_diff + 2.0: 
                break
        if best_time:
            lag_seconds = time.time() - best_time
            return lag_seconds * 1000.0 
        return None

class ODrive:
    """Klasa przechowująca lokalną reprezentację ODrive"""
    def __init__(self):
        self.measured_velocity = 0.0
        self.measured_position = 0.0
        self.start_position_offset = 0.0
        self.last_feedback_time = 0.0
        # NOWE POLA DLA SERWO
        self.servo_current = 0.0
        self.servo_angle_deg = 0.0

class AppState:
    """Klasa przechowująca współdzielony stan aplikacji"""
    def __init__(self):
        # Dane pomiarowe
        self.o_drives:dict[str, ODrive] = {
            "00": ODrive(),
            "10": ODrive(),
            "01": ODrive(),
            "11": ODrive()
        }

        # self.measured_velocity = 0.0
        # self.measured_position = 0.0
        # self.start_position_offset = 0.0
        # self.last_feedback_time = 0.0
        
        # Dane sterujące
        self.target_rps = 0.0
        self.steering_val = 0.0
        self.current_speed_limit = 10.0
        
        # --- NOWE ZMIENNE DLA TRYBÓW JAZDY ---
        self.drive_mode = 1           # 1: Normalny, 2: Obrót w miejscu
        self.mode_switch_time = 0.0   # Czas ostatniej zmiany trybu (do opóźnienia)
        # ------------------------------------
        
        # Statusy
        self.mqtt_connected = False
        self.mqtt_status_text = "MQTT: Rozłączono"
        
        # Logi
        self.logs = [] # Lista do przechowywania logów dla GUI
        
        # Narzędzia
        self.latency_estimator = LatencyEstimator(maxlen=100)

        self.ping_broker_ok = False
        self.ping_router_ok = False
        self.ping_ground_ok = False

    def log(self, message):
        self.logs.append(message)