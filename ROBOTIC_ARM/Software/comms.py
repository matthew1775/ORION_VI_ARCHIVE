import paho.mqtt.client as mqtt
import json
import math
import config

class MqttManager:
    def __init__(self, app_state):
        self.client = None
        self.state = app_state

    def connect(self):
        self.state.log("--- MQTT Initialization ---")
        try:
            if self.client:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except Exception as e:
                    self.state.log(f"Błąd zatrzymania starego klienta: {e}")
                    
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            self.client.connect(config.BROKER_ADDRESS, config.BROKER_PORT)
            self.client.loop_start()
        except Exception as e:
            self.state.log(f"Critical connection error: {e}")
            self.state.mqtt_connected = False
            self.state.mqtt_status_text = "MQTT: BŁĄD"

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.state.mqtt_connected = True
            self.state.mqtt_status_text = "MQTT: CONNECTED"
            client.subscribe(config.TOPIC_FEEDBACK)

    def _on_disconnect(self, client, userdata, rc):
        self.state.mqtt_connected = False
        self.state.mqtt_status_text = "MQTT: DISCONNECTED"
        self.state.log(f"MQTT rozłączono (kod: {rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload_wrapper = json.loads(msg.payload.decode())
            if payload_wrapper.get("eventType") == "Robotic_arm_enc":
                p = payload_wrapper.get("payload", {})
                
                # Konwersja odebranych RADIANÓW na STOPNIE
                for i in range(8):
                    key = f"enc_joint{i+1}_rad"
                    rad_val = p.get(key, 0.0)
                    if i < len(self.state.actual_joints_deg):
                        self.state.actual_joints_deg[i] = math.degrees(rad_val)

                for i in range(4):
                    key = f"enc_joint_mini_{i+1}_rad"
                    if key in p and hasattr(self.state, "actual_mini_joints_deg"):
                        self.state.actual_mini_joints_deg[i] = math.degrees(p.get(key, 0.0))
                    
                for i in range(2, 9):
                    key = f"canid{i}"
                    # Odczytujemy jako int i od razu konwertujemy na bool (True/False)
                    self.state.can_status[i] = bool(p.get(key, 0))

                if not self.state.initial_sync_done:
                    # Kopiujemy aktualny stan fizyczny enkoderów do pozycji zadanych joysticka (dla 6 osi ramienia)
                    self.state.target_joints_deg = list(self.state.actual_joints_deg[:6])
                    self.state.initial_sync_done = True
                    self.state.log("Pomyślnie zsynchronizowano pozycje startowe z ramieniem. Sterowanie odblokowane.")

        except Exception as e:
            self.state.log(f"MQTT receive error: {e}")

    def send_drive_command(self):
        if not self.state.initial_sync_done:
            return  
        
        if self.client and self.state.mqtt_connected:
            payload_data = {}
            
            # RAMIĘ GŁÓWNE (Zawsze wysyłamy aktualne docelowe pozycje)
            for i in range(6):
                rad_val = math.radians(self.state.target_joints_deg[i])
                payload_data[f"joint{i+1}_rad"] = round(rad_val, 4)
                payload_data[f"joint{i+1}_speed"] = round(self.state.target_speeds[i], 1)
                
            # NARZĘDZIE / MINI-JOINTY (Sterowane prędkością)
            for i in range(4):
                payload_data[f"joint_mini_{i+1}_rad"] = 0.0 
                payload_data[f"joint_mini_{i+1}_speed"] = round(self.state.mini_joint_speeds[i], 1)

            # Ewentualny piąty mini joint zgodnie z oryginalną pętlą dla kompatybilności 
            payload_data["joint_mini_5_rad"] = 0.0
            payload_data["joint_mini_5_speed"] = 100.0

            msg = {
                "eventType": "Robotic_arm_cmd",
                "payload": payload_data,
                "cmd": {"fan": False}
            }
            try:
                self.client.publish(config.TOPIC_CMD, json.dumps(msg))
            except Exception as e:
                self.state.log(f"Data send error: {e}")