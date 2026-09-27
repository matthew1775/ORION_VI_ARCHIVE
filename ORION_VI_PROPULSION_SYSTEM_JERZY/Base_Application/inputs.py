# inputs.py
import pygame
import config
import time


class InputManager:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = []
        self.scan_joysticks()
        
        # Zmienne klawiatury
        self.key_throttle = 0.0
        self.key_max_limit = 10.0
        self.btn_mode_last = False #

    def scan_joysticks(self):
        self.joysticks = []
        pygame.joystick.quit()
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(count)]
        for joy in self.joysticks:
            joy.init()
        return self.joysticks

    def handle_keyboard(self, event_type, key_code):
        """Metoda wywoływana z GUI przy zdarzeniach klawiatury"""
        k = key_code.lower()
        
        if event_type == 'press':
            if k == 'w': self.key_throttle = 1.0
            elif k == 's': self.key_throttle = -1.0
            elif k == 'r': self.key_max_limit = min(config.ABSOLUTE_MAX_LIMIT, self.key_max_limit + 1.0)
            elif k == 'f': self.key_max_limit = max(1.0, self.key_max_limit - 1.0)
            
        elif event_type == 'release':
            if k in ['w', 's']: self.key_throttle = 0.0
            
    def update(self, app_state):
        """Oblicza sterowanie i aktualizuje AppState"""
        pygame.event.pump()
        
        joy_throttle = 0.0
        joy_active = False
        steering = 0.0
        
        # Obsługa Joysticka
        if self.joysticks:
            try:
                joy = self.joysticks[0]
                
                # --- NOWY KOD: PRZEŁĄCZANIE TRYBÓW PRZYCISKIEM ---
                if joy.get_numbuttons() > 1:
                    btn_mode = joy.get_button(1) # Przycisk 0 (zwykle A/Krzyżyk)
                    
                    if btn_mode and not self.btn_mode_last: # Wykrycie pojedynczego kliknięcia
                        
                        # ZABEZPIECZENIE: Sprawdzamy, czy zadana prędkość z joysticka jest bliska 0
                        if abs(app_state.target_rps) < 0.1:
                            if app_state.drive_mode == 1:
                                app_state.drive_mode = 2
                                app_state.mode_switch_time = time.time()
                                app_state.log(">>> TRYB JAZDY: OBRÓT W MIEJSCU (Czekaj na serwa) <<<")
                            else:
                                app_state.drive_mode = 1
                                app_state.mode_switch_time = time.time()
                                app_state.log(">>> TRYB JAZDY: NORMALNY <<<")
                        else:
                            # Odrzucenie polecenia, gdy łazik jest w ruchu
                            app_state.log("!!! ODMOWA ZMIANY TRYBU: Najpierw zatrzymaj łazika !!!")
                            
                    self.btn_mode_last = btn_mode
                
                # Limit prędkości (Axis 3 - suwak/przepustnica)
                if joy.get_numaxes() > 3:
                    axis3 = joy.get_axis(3)
                    # Mapowanie -1..1 na 0..MAX
                    app_state.current_speed_limit = ((1.0 - axis3) / 2.0) * config.ABSOLUTE_MAX_LIMIT
                else:
                    app_state.current_speed_limit = self.key_max_limit

                # Gaz (Axis 1 - lewa gałka pionowo)
                axis1 = -joy.get_axis(1)
                if abs(axis1) > config.JOYSTICK_DEADZONE:
                    joy_throttle = axis1 * app_state.current_speed_limit
                    joy_active = True
                
                # Skręt (Axis 5 lub 2)
                if joy.get_numaxes() > config.STEERING_AXIS_INDEX:
                    steering = joy.get_axis(config.STEERING_AXIS_INDEX)
                elif joy.get_numaxes() > 2:
                    steering = joy.get_axis(2)
                    
            except Exception:
                pass
        else:
            app_state.current_speed_limit = self.key_max_limit

        # Wybór źródła (Joystick vs Klawiatura)
        if joy_active:
            app_state.target_rps = joy_throttle
        else:
            app_state.target_rps = self.key_throttle * app_state.current_speed_limit
            
        app_state.steering_val = steering