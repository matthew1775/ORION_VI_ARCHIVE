class AppState:
    def __init__(self):
        # Główne ramię (6 osi) oraz dodatkowe osie
        self.target_joints_deg = [0.0, 0.0, 50.0, 40.0, 0.0, 0.0]
        self.actual_joints_deg = [0.0] * 10
        self.target_speeds = [50.0] * 6 

        # Narzędzie (4 mini-jointy)
        self.secondary_mode = False 
        self.mini_joint_speeds = [100.0, 100.0, 100.0, 100.0] 
        self.actual_mini_joints_deg = [0.0, 0.0, 0.0, 0.0] 

        self.mqtt_connected = False
        self.mqtt_status_text = "MQTT: Rozłączono"
        self.logs = [] 
        
        self.ping_broker_ok = False   
        self.ping_router_ok = False   
        self.ping_ground_ok = False   

        self.can_status = {2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False}
        self.initial_sync_done = False

    def log(self, message):
        self.logs.append(message)