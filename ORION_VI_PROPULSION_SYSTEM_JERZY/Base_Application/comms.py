# comms.py
from numpy import int8, isin
import paho.mqtt.client as mqtt
import json
import time
import config
from utils import AppState

class MqttManager:
    def __init__(self, app_state):
        self.client = None
        self.state:AppState = app_state

    def connect(self):
        self.state.log("--- Inicjalizacja MQTT ---")
        try:
            # Używamy dokładnie tej samej wersji API co w Twoim pliku (limited)
            #self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

            self.client = mqtt.Client()
            
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            
            self.state.log(f"Łączenie z {config.BROKER_ADDRESS}...")
            self.client.connect(config.BROKER_ADDRESS, config.BROKER_PORT)
            self.client.loop_start()
            
        except Exception as e:
            self.state.mqtt_status_text = "MQTT: Błąd"
            self.state.log(f"Błąd krytyczny połączenia: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.state.mqtt_connected = True
            self.state.mqtt_status_text = "MQTT: POŁĄCZONO"
            client.subscribe(config.TOPIC_FEEDBACK_LEFT)
            client.subscribe(config.TOPIC_FEEDBACK_RIGHT)
            self.state.log(">> Połączono z brokerem (RC=0).")
        else:
            self.state.mqtt_status_text = f"MQTT: Błąd {rc}"
            self.state.log(f"Błąd połączenia, kod: {rc}")

    #feedback message:
    #[
    #   0: side (0- left|1- right)
    #   1: measured velocity of the front ODrive
    #   2: measured position of the front ODrive
    #   3: measured velocity of the rear ODrive
    #   4: measured position of the rear ODrive
    #]
    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            # Obsługa logowania błędów 
            if isinstance(payload, dict) and "error" in payload:
                oid = payload.get("odrive_id", "-")
                self.state.log(f"!! ODRIVE ERROR: {payload['error']} (ID: {oid})")
                return 

            # Obsługa nowego formatu telemetrii (obiekt JSON z kluczami zamiast listy)
            if isinstance(payload, dict) and "side_id" in payload:
                side = str(payload["side_id"])
                
                id_front = "0" + side
                id_rear  = "1" + side
                
                vel_front = payload.get("vel_front", 0.0)
                pos_front = payload.get("pos_front", 0.0)
                vel_rear  = payload.get("vel_rear", 0.0)
                pos_rear  = payload.get("pos_rear", 0.0)
                
                # Dodano: Pobranie wartości prądu z serw (A - przód, B - tył)
                cfb_a = payload.get("servoA_cfb", 0.0)
                cfb_b = payload.get("servoB_cfb", 0.0)
                
                # Zapis do współdzielonego stanu (AppState)
                self.state.o_drives[id_front].measured_velocity = vel_front
                self.state.o_drives[id_front].measured_position = pos_front
                self.state.o_drives[id_front].servo_current = cfb_a
                self.state.o_drives[id_front].last_feedback_time = time.time()
                
                self.state.o_drives[id_rear].measured_velocity = vel_rear
                self.state.o_drives[id_rear].measured_position = pos_rear
                self.state.o_drives[id_rear].servo_current = cfb_b
                self.state.o_drives[id_rear].last_feedback_time = time.time()

                # Estymacja opóźnień
                estimate_lag_sum = vel_front + vel_rear
                self.state.latency_estimator.estimate_lag(estimate_lag_sum / 2.0)
                
            elif isinstance(payload, list):
                self.state.log(f"!! Odrzucono przestarzały format ramki: {payload}")
                                  
        except json.JSONDecodeError:
            raw = msg.payload.decode()
            self.state.log(f"[JSON DECODE ERROR] MSG (RAW): {raw}")
        except Exception as e:
            pass

    def send_drive_command(self):
        """Wysyła ramkę sterującą JSON zależnie od wybranego trybu jazdy"""
        if self.client and self.state.mqtt_connected:
            v = round(self.state.target_rps, 3)
            s = round(self.state.steering_val, 3)
            s = 0.0 if abs(s) < 0.25 else s
            
            # 1. Deklaracja pustej zmiennej - to usuwa czerwone podkreślenie!
            payload = None 
                         
            # ===================================================
            # TRYB 1: JAZDA NORMALNA
            # ===================================================
            if getattr(self.state, 'drive_mode', 1) == 1:
                payload = {
                    "eventType": "propulsion",
                    "velocity": {
                        "fl_speed": -v,
                        "rl_speed": v,
                        "fr_speed": -v,
                        "rr_speed": -v,
                        "fl_rad": s,
                        "rl_rad": -s,
                        "fr_rad": s,
                        "rr_rad": -s
                    }
                }

            # ===================================================
            # TRYB 2: OBRÓT W MIEJSCU
            # ===================================================
            elif self.state.drive_mode == 2:
                TURN_ANGLE = 1.0 
                v_rot = s * self.state.current_speed_limit 

                if time.time() - self.state.mode_switch_time < 1.5:
                    v_rot = 0.0

                payload = {
                    "eventType": "propulsion",
                    "velocity": {
                        "fl_speed": -v_rot,
                        "rl_speed": v_rot,
                        "fr_speed": v_rot,  
                        "rr_speed": v_rot,  
                        "fl_rad": TURN_ANGLE,       
                        "fr_rad": -TURN_ANGLE,      
                        "rl_rad": -TURN_ANGLE,       
                        "rr_rad": TURN_ANGLE        
                    }
                }

            # 2. Zabezpieczenie: jeśli payload jest puste, nie wysyłaj
            if payload is None:
                return

            # --- PUBLIKACJA WYGENEROWANEGO PAYLOADU ---
            try:
                payload_json = json.dumps(payload)
                self.client.publish(config.TOPIC_CMD, payload_json)
                self.state.latency_estimator.push_target(self.state.target_rps)
                
            except Exception as e:
                self.state.log(f"Błąd wysyłania: {e}")
            

    def send_cmd(self, cmd, target="a"):
            """
            target:
                "a" -> override
                "l" -> LF+LR
                "r" -> RF+RR
                "lf", "lr", "rf", "rr" -> single wheel
            """
            if not (self.client and self.state.mqtt_connected):
                return

            #   command:
            #   0 - no command,
            #   1 - calibrate,
            #   2 - closed_loop,
            #   3 - set_vel_mode,
            #   4 - set_ramp_mode,
            #   5 - dump_errors,
            #   6 - reboot_odrive
            
            if cmd not in config.CMD_MAP:
                self.state.log(f"[MQTT] Unknown cmd: {cmd}")
                return

            payload = [0, 0, 0, 0, 0]  # LF, LR, RF, RR, OVERRIDE
            val = config.CMD_MAP[cmd]

            if target == "a":
                payload[4] = val
            elif target == "l":
                payload[0] = payload[1] = val
            elif target == "r":
                payload[2] = payload[3] = val
            elif target == "lf":
                payload[0] = val
            elif target == "lr":
                payload[1] = val
            elif target == "rf":
                payload[2] = val
            elif target == "rr":
                payload[3] = val

            try:
                # Generujemy JSONa raz
                payload_json = json.dumps(payload)
                
                # Publikacja na wspólny temat komend
                self.client.publish(config.TOPIC_CMD, payload_json)
                
                self.state.log(f">> CMD: {cmd} ({target}) -> {payload}")
            except Exception as e:
                self.state.log(f"[MQTT] Send error: {e}")