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
        
        # Nowa zmienna: zapamiętuje limit ustawiony przez strzałki (krzyżak) na Steam Deck
        self.pad_max_limit = 10.0

    def scan_joysticks(self):
        self.joysticks = []
        pygame.joystick.quit()
        pygame.joystick.init()
        pygame.event.clear()
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
        try:
            events = pygame.event.get()
        except (KeyError, SystemError, Exception) as e: # <--- Zmień tę linijkę
            # Złap błędy SystemError wynikające z odłączenia / błędu Pygame
            events = []
            pygame.event.clear() # Wyczyść kolejkę, żeby program nie utknął
            
        for event in events:
            # ==========================================
            # 1. NAJWAŻNIEJSZE: USTAWIENIE PRĘDKOŚCI (D-PAD)
            # ==========================================
            if event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1: # Strzałka w górę
                    self.pad_max_limit = min(config.ABSOLUTE_MAX_LIMIT, self.pad_max_limit + 1.0)
                elif event.value[1] == -1: # Strzałka w dół
                    self.pad_max_limit = max(1.0, self.pad_max_limit - 1.0)
            
            # ==========================================
            # 2. PRZYCISKI STEAM DECK
            # ==========================================
            elif event.type == pygame.JOYBUTTONDOWN:
                
                # --- PRZYCISK 'A' (button 0): Tryb Obrotu ---
                if event.button == 0: 
                    # ZABEZPIECZENIE: Zmiana trybu tylko w spoczynku
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
                        app_state.log("!!! ODMOWA ZMIANY TRYBU: Najpierw zatrzymaj łazika !!!")
                
                # --- PRZYCISK 'R3' (button 9): Blokada bezpieczeństwa ---
                elif event.button == 9: 
                    # Pobieramy stan blokady (lub domyślnie False, jeśli brak)
                    current_lock = getattr(app_state, 'buttons_locked', False)
                    app_state.buttons_locked = not current_lock
                    stan_txt = "WŁĄCZONA" if app_state.buttons_locked else "WYŁĄCZONA"
                    app_state.log(f"[Bezpieczeństwo] Blokada przycisków: {stan_txt}")
                
                # --- PRZYCISK 'X' (button 2): Full Start (Auto) ---
                elif event.button == 2:
                    if not getattr(app_state, 'buttons_locked', False):
                        app_state.trigger_full_start = True
                    else:
                        app_state.log("!! ODRZUCONO: Przyciski zablokowane. Wciśnij prawą gałkę (R3), aby odblokować.")

        joy_throttle = 0.0
        joy_active = False
        steering = 0.0
        
        # Obsługa Joysticka
        if self.joysticks:
            try:
                joy = self.joysticks[0]
                
                # Przekazujemy limit ze strzałek do stanu aplikacji
                app_state.current_speed_limit = self.pad_max_limit
                
                # Gaz (Axis 1 - lewa gałka pionowo)
                axis1 = -joy.get_axis(1)
                if abs(axis1) > config.JOYSTICK_DEADZONE:
                    joy_throttle = axis1 * app_state.current_speed_limit
                    joy_active = True
                
                # Skręt (Axis 5 lub 2 - zależy czy sterownik PC czy bezpośrednio konsola)
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