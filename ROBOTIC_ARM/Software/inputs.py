import pygame
import config

class InputManager:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = []
        self.scan_joysticks()

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
        if event_type == 'press' and key_code.lower() == 'x':
            self.keyboard_toggle_mode = True
            
    def update(self, app_state):
        pygame.event.pump()

        # --- ZMIANA TRYBÓW PRZYCISKIEM / KLAWISZEM X ---
        mode_toggle_requested = False
        if getattr(self, 'keyboard_toggle_mode', False):
            self.keyboard_toggle_mode = False
            mode_toggle_requested = True

        if not self.joysticks:
            if mode_toggle_requested:
                app_state.secondary_mode = not app_state.secondary_mode
                app_state.log("Tryb: " + ("NARZĘDZIE (Mini-Jointy)" if app_state.secondary_mode else "RAMIĘ (6 osi)"))
            return 

        joy = self.joysticks[0]
        
        def get_btn(idx):
            return joy.get_button(idx) if idx < joy.get_numbuttons() else 0
            
        def get_ax(idx):
            if idx < joy.get_numaxes():
                val = joy.get_axis(idx)
                return val if abs(val) > config.JOYSTICK_DEADZONE else 0.0
            return 0.0
            
        def get_hat_y(): 
            return joy.get_hat(0)[1] if joy.get_numhats() > 0 else 0

        # Przycisk X na kontrolerze (indeks 2)
        btn_x_current = get_btn(2)
        if btn_x_current and not getattr(self, 'btn_x_last', False):
            mode_toggle_requested = True
        self.btn_x_last = btn_x_current

        if mode_toggle_requested:
            app_state.secondary_mode = not app_state.secondary_mode
            app_state.log("Tryb: " + ("NARZĘDZIE (Mini-Jointy)" if app_state.secondary_mode else "RAMIĘ (6 osi)"))

        # ==========================================
        # TRYB 2: NARZĘDZIE / MINI-JOINTY (Prędkość: 100 neutral, 200 przód, 0 tył)
        # ==========================================
        if app_state.secondary_mode:
            # 1. Mini 1 (LT/RT)
            lt = (joy.get_axis(4) + 1.0) / 2.0 if joy.get_numaxes() > 4 else 0.0
            rt = (joy.get_axis(5) + 1.0) / 2.0 if joy.get_numaxes() > 5 else 0.0
            lt = lt if lt > config.JOYSTICK_DEADZONE else 0.0
            rt = rt if rt > config.JOYSTICK_DEADZONE else 0.0
            if rt > lt and rt > 0.0:
                app_state.mini_joint_speeds[0] = 200.0
            elif lt > rt and lt > 0.0:
                app_state.mini_joint_speeds[0] = 0.0
            else:
                app_state.mini_joint_speeds[0] = 100.0

            # 2. Mini 2 (JoyL GÓRA/DÓŁ - Oś 1)
            ax1 = -get_ax(1)
            if ax1 > 0.0:
                app_state.mini_joint_speeds[1] = 200.0
            elif ax1 < 0.0:
                app_state.mini_joint_speeds[1] = 0.0
            else:
                app_state.mini_joint_speeds[1] = 100.0

            # 3. Mini 3 (JoyR LEWO/PRAWO - Oś 2)
            ax2 = get_ax(2)
            if ax2 > 0.0:
                app_state.mini_joint_speeds[3] = 200.0
            elif ax2 < 0.0:
                app_state.mini_joint_speeds[3] = 0.0
            else:
                app_state.mini_joint_speeds[3] = 100.0

            # 4. Mini 4 (LB / RB)
            btn_lb = get_btn(4)
            btn_rb = get_btn(5)
            if btn_rb and not btn_lb:
                app_state.mini_joint_speeds[2] = 200.0
            elif btn_lb and not btn_rb:
                app_state.mini_joint_speeds[2] = 0.0
            else:
                app_state.mini_joint_speeds[2] = 100.0

        # ==========================================
        # TRYB 1: RAMIĘ GŁÓWNE (Pozycja)
        # ==========================================
        else:
            # Zatrzymanie narzędzia (prędkość neutralna 100) gdy sterujemy ramieniem
            app_state.mini_joint_speeds = [100.0, 100.0, 100.0, 100.0]

            deltas = [0.0] * 6
            # 1. OBROTNICA (Triggery)
            trig_left = joy.get_axis(4) if joy.get_numaxes() > 4 else -1.0
            trig_right = joy.get_axis(5) if joy.get_numaxes() > 5 else -1.0
            if trig_left > -0.5: deltas[0] += 1.0
            if trig_right > -0.5: deltas[0] -= 1.0

            # 2. BARK (Lewa gałka Y)
            deltas[1] = -get_ax(1)
            # 3. ŁOKIEĆ (Prawa gałka Y)
            deltas[2] = -get_ax(3)
            # 4. NADGARSTEK (Krzyżak)
            hat_val = get_hat_y()
            if hat_val == -1: deltas[4] -= 0.5
            elif hat_val == 1: deltas[4] += 0.5
            # 5. OŚ 5 (LB / RB)
            if get_btn(4): deltas[3] += 0.5
            if get_btn(5): deltas[3] -= 0.5 
            # 6. WYSUW (L3 / R3)
            if get_btn(8): deltas[5] -= 0.5
            if get_btn(9): deltas[5] += 0.5

            for i in range(6):
                if deltas[i] != 0.0:
                    new_val = app_state.target_joints_deg[i] + (deltas[i] * config.AXIS_SPEEDS[i])
                    l_min, l_max = config.AXIS_LIMITS[i]
                    app_state.target_joints_deg[i] = max(l_min, min(l_max, new_val))