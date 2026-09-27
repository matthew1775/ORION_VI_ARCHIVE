# comms.py
import paho.mqtt.client as mqtt
import json
import config
import time
from utils import AppState

class MqttManager:
    def __init__(self, app_state):
        self.client = mqtt.Client()
        self.state: AppState = app_state

    def connect(self):
        self.state.log("--- Inicjalizacja MQTT Power ---")
        try:
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
            client.subscribe(config.TOPIC_FEEDBACK)
            self.state.log(">> Połączono z brokerem (RC=0).")
        else:
            self.state.mqtt_status_text = f"MQTT: Błąd {rc}"

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            if isinstance(payload, dict):
                self.state.last_feedback_time = time.time()
                # Zapisujemy odczyty z modułu zasilania
                if "temp_c" in payload:
                    self.state.temp_c = payload.get("temp_c", 0.0)
                    
                    self.state.bat_v[0] = payload.get("bat_1_v", 0.0)
                    self.state.bat_v[1] = payload.get("bat_2_v", 0.0)
                    self.state.bat_v[2] = payload.get("bat_3_v", 0.0)
                    self.state.bat_v[3] = payload.get("bat_4_v", 0.0)
                    
                    self.state.adc["adc_wl"]   = payload.get("adc_wl", 0)
                    self.state.adc["adc_wr"]   = payload.get("adc_wr", 0)
                    self.state.adc["adc_ram"]  = payload.get("adc_ram", 0)
                    self.state.adc["adc_elek"] = payload.get("adc_elek", 0)
                    self.state.adc["adc_sci"]  = payload.get("adc_sci", 0)
                    self.state.adc["adc_inne"] = payload.get("adc_inne", 0)
                    
        except json.JSONDecodeError:
            pass
        except Exception as e:
            self.state.log(f"Błąd parsowania: {e}")

    def set_switch(self, switch_name, new_state):
        """Metoda wywoływana z GUI przy kliknięciu przycisku ON lub OFF"""
        if self.client and self.state.mqtt_connected:
            # Jeśli stan się nie zmienił, ignorujemy kliknięcie
            if self.state.switches.get(switch_name) == new_state:
                return
            
            # Zapisz nowy stan w AppState by GUI natychmiast zareagowało
            self.state.switches[switch_name] = new_state
            
            # Utworzenie i wysłanie komendy JSON
            payload = {switch_name: new_state}
            try:
                payload_json = json.dumps(payload)
                self.client.publish(config.TOPIC_CMD, payload_json)
                state_str = "ON (1)" if new_state == 1 else "OFF (0)"
                self.state.log(f">> CMD: Wysłano {switch_name} -> {state_str}")
            except Exception as e:
                self.state.log(f"Błąd wysyłania: {e}")

    def force_reconnect(self):
        self.state.log(">> Wymuszam ręczny restart połączenia MQTT...")
        try:
            self.client.disconnect()
            self.connect()
        except Exception as e:
            self.state.log(f"Błąd podczas restartu: {e}")