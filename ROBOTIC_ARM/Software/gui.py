import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import subprocess
import platform
import socket
import concurrent.futures
import collections
import config

class DashboardGUI:
    def __init__(self, root, app_state, input_manager, mqtt_manager):
        self.root = root
        self.state = app_state
        self.input_manager = input_manager
        self.mqtt_manager = mqtt_manager
        self.joint_history = [collections.deque(maxlen=100) for _ in range(6)]
        self.setup_ui()
        self._start_network_monitor()
    
    def _check_connection(self, host, port=None):
        """Zoptymalizowana funkcja sprawdzania dostępności w sieci"""
        if port:
            # Bardzo szybkie sprawdzenie za pomocą Socket (nie obciąża procesora)
            try:
                with socket.create_connection((host, port), timeout=0.5):
                    return True
            except OSError:
                return False
        else:
            # Klasyczny ping tylko dla urządzeń bez otwartych portów
            try:
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
                cmd = ['ping', param, '1', timeout_param, '500' if platform.system().lower() == 'windows' else '1', host]
                startupinfo = None
                if platform.system().lower() == 'windows':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                return subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo) == 0
            except Exception: return False

    def _start_network_monitor(self):
        def monitor_loop():
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                while True:
                    # Równoległe sprawdzenie połączeń z natychmiastową aktualizacją stanu
                    futures_to_attr = {
                        executor.submit(self._check_connection, "192.168.1.1", 1883): "ping_broker_ok",
                        executor.submit(self._check_connection, "192.168.1.102"): "ping_router_ok",
                        executor.submit(self._check_connection, "192.168.1.101"): "ping_ground_ok"
                    }

                    for future in concurrent.futures.as_completed(futures_to_attr):
                        attr_name = futures_to_attr[future]
                        try:
                            result = future.result()
                            setattr(self.state, attr_name, result)
                        except Exception:
                            setattr(self.state, attr_name, False)

                    time.sleep(1.5) # Zwiększono odstęp miedzy sprawdzeniami z 1s na 1.5s
        threading.Thread(target=monitor_loop, daemon=True).start()
    
    def setup_ui(self):
        self.root.configure(bg=config.BG_COLOR)
        self.top_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.top_frame.pack(side="top", fill="x", padx=10, pady=5)
        self.main_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_top_panel()
        self._build_joints_grid()
        self._build_plots_and_console()

    def _build_top_panel(self):
        joy_frame = tk.Frame(self.top_frame, bg=config.BG_COLOR)
        joy_frame.pack(side="left")
        tk.Button(joy_frame, text="⟳ RESET JOYSTICK", command=self.refresh_joysticks, bg=config.BTN_RESET_COLOR, fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(joy_frame, text="⟳ RESET NETWORK", command=self.reset_network, bg=config.BTN_RESET_COLOR, fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.lbl_joy = tk.Label(joy_frame, text="Joystick: Brak", bg=config.BG_COLOR, fg="yellow", font=("Arial", 10))
        self.lbl_joy.pack(side="left", padx=5)

        net_frame = tk.Frame(self.top_frame, bg=config.BG_COLOR)
        net_frame.pack(side="right")
        self.lbl_mqtt_status = tk.Label(net_frame, text="MQTT: --", bg=config.BG_COLOR, fg=config.FG_COLOR, font=("Arial", 10))
        self.lbl_mqtt_status.pack(side="left", padx=10)

        self.led_canvas = tk.Canvas(net_frame, width=200, height=25, bg=config.BG_COLOR, highlightthickness=0)
        self.led_canvas.pack(side="left", padx=5)
        self.led_ground = self.led_canvas.create_oval(5, 5, 20, 20, fill="grey", outline="white")
        self.led_canvas.create_text(25, 12, text="Gnd", fill="white", anchor="w", font=("Arial", 8))
        self.led_router = self.led_canvas.create_oval(65, 5, 80, 20, fill="grey", outline="white")
        self.led_canvas.create_text(85, 12, text="Router", fill="white", anchor="w", font=("Arial", 8))
        self.led_broker = self.led_canvas.create_oval(130, 5, 145, 20, fill="grey", outline="white")
        self.led_canvas.create_text(150, 12, text="MQTT", fill="white", anchor="w", font=("Arial", 8))

        # ---> NOWY KOD: Rysowanie diod od interfejsu CAN <---
        can_frame = tk.Frame(self.top_frame, bg=config.BG_COLOR)
        can_frame.pack(side="left", padx=40) 
        
        tk.Label(can_frame, text="Węzły CAN:", bg=config.BG_COLOR, fg="#888", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 10))
        
        self.can_leds = {} # Słownik przechowujący obiekty diod do ich odświeżania
        self.can_canvas = tk.Canvas(can_frame, width=(7 * 45), height=25, bg=config.BG_COLOR, highlightthickness=0)
        self.can_canvas.pack(side="left")
        
        # Wygenerowanie 7 kółek dla ID od 2 do 8
        for i in range(2, 9):
            x_offset = (i - 2) * 45
            # Szare koło na start
            led = self.can_canvas.create_oval(x_offset+5, 5, x_offset+20, 20, fill="#444", outline="#777")
            # Podpis (np. ID 4)
            self.can_canvas.create_text(x_offset+25, 12, text=f"ID{i}", fill="white", anchor="w", font=("Arial", 8))
            
            self.can_leds[i] = led # Zapisanie do pamięci GUI

        # Wskaźnik trybu sterowania (Ramię / Narzędzie)
        mode_frame = tk.Frame(self.top_frame, bg=config.BG_COLOR)
        mode_frame.pack(side="left", padx=25)
        self.lbl_mode = tk.Label(
            mode_frame,
            text="TRYB: RAMIĘ GŁÓWNE (1-6) [X]",
            bg="#004d26",
            fg="#00ff66",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=2,
            relief="groove"
        )
        self.lbl_mode.pack(side="left")

    def _build_joints_grid(self):
        self.grid_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR)
        self.grid_frame.pack(side="top", fill="x")

        # --- SEKCJA 1: RAMIĘ GŁÓWNE (6 DOF) ---
        self.arm_group = tk.LabelFrame(
            self.grid_frame,
            text="RAMIĘ GŁÓWNE (Osi 1-6) — [STEROWANIE AKTYWNE]",
            bg=config.BG_COLOR,
            fg="#00ff66",
            font=("Arial", 10, "bold"),
            bd=2
        )
        self.arm_group.pack(fill="x", padx=5, pady=(2, 3))

        self.arm_widgets = []
        arm_names = [
            "1. Obrotnica",
            "2. Bark",
            "3. Łokieć",
            "4. Nadgarstek",
            "5. Oś 5 (LB/RB)",
            "6. Wysuw"
        ]
        for i in range(6):
            self.arm_group.grid_columnconfigure(i, weight=1)
            frame = tk.LabelFrame(self.arm_group, text=arm_names[i], bg=config.BG_COLOR, fg="white", font=("Arial", 9, "bold"))
            frame.grid(row=0, column=i, padx=5, pady=3, sticky="nsew")

            cvs = tk.Canvas(frame, width=95, height=95, bg="#2b2b2b", highlightthickness=1, highlightbackground="#555")
            cvs.pack(pady=2)
            cvs.create_oval(8, 8, 87, 87, outline="#444", width=3, tags="bg_circle")

            lbl = tk.Label(frame, text="T: 0.0°\nA: 0.0°", bg=config.BG_COLOR, fg="white", font=("Consolas", 10))
            lbl.pack(pady=2)
            self.arm_widgets.append((cvs, lbl, frame))

        # --- SEKCJA 2: NARZĘDZIE / MINI-JOINTY (4 DOF) ---
        self.tool_group = tk.LabelFrame(
            self.grid_frame,
            text="NARZĘDZIE (Mini-Jointy 1-4) — [NIEAKTYWNE - Przełącz klawiszem X]",
            bg=config.BG_COLOR,
            fg="#888888",
            font=("Arial", 10, "bold"),
            bd=2
        )
        self.tool_group.pack(fill="x", padx=5, pady=(2, 3))

        self.tool_widgets = []
        tool_names = [
            "7. Mini 1 (LT/RT)",
            "8. Mini 2 (JoyL G/D)",
            "9. Mini 3 (JoyR L/P)",
            "10. Mini 4 (LB/RB)"
        ]
        for i in range(4):
            self.tool_group.grid_columnconfigure(i, weight=1)
            frame = tk.LabelFrame(self.tool_group, text=tool_names[i], bg=config.BG_COLOR, fg="#888888", font=("Arial", 9, "bold"))
            frame.grid(row=0, column=i, padx=8, pady=3, sticky="nsew")

            cvs = tk.Canvas(frame, width=95, height=95, bg="#2b2b2b", highlightthickness=1, highlightbackground="#444")
            cvs.pack(pady=2)
            cvs.create_oval(8, 8, 87, 87, outline="#383838", width=3, tags="bg_circle")
            cvs.create_line(47, 8, 47, 16, fill="#666", width=2, tags="zero_mark")

            lbl = tk.Label(frame, text="Prędkość:\n100 (STOP)", bg=config.BG_COLOR, fg="#888888", font=("Consolas", 10))
            lbl.pack(pady=2)
            self.tool_widgets.append((cvs, lbl, frame))

        # Kompatybilność wsteczna dla listy widgetów
        self.joint_widgets = self.arm_widgets + self.tool_widgets

    def _build_plots_and_console(self):
        bottom_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR)
        bottom_frame.pack(side="bottom", fill="both", expand=True, pady=5)
        
        self.plots_frame = tk.LabelFrame(
            bottom_frame,
            text="Wykresy Pozycji Osia 1-6 w Czasie  [ — Zadana (T),  — Rzeczywista (A) ]",
            bg=config.BG_COLOR,
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.plots_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.arm_frame = self.plots_frame  # Kompatybilność wsteczna

        self.plot_widgets = []
        plot_names = [
            "1. Obrotnica",
            "2. Bark",
            "3. Łokieć",
            "4. Nadgarstek",
            "5. Oś 5 (LB/RB)",
            "6. Wysuw"
        ]

        for r in range(2):
            self.plots_frame.grid_rowconfigure(r, weight=1)
        for c in range(3):
            self.plots_frame.grid_columnconfigure(c, weight=1)

        for i in range(6):
            r = i // 3
            c = i % 3
            cell = tk.Frame(self.plots_frame, bg="#181932", bd=1, relief="ridge")
            cell.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

            hdr = tk.Frame(cell, bg="#181932")
            hdr.pack(side="top", fill="x", padx=4, pady=(2, 0))

            lbl_title = tk.Label(hdr, text=plot_names[i], bg="#181932", fg="#00ffff", font=("Arial", 9, "bold"))
            lbl_title.pack(side="left")

            lbl_val = tk.Label(hdr, text="T: 0.0°  A: 0.0°", bg="#181932", fg="white", font=("Consolas", 9))
            lbl_val.pack(side="right")

            canvas = tk.Canvas(cell, bg="#0d0e24", highlightthickness=0)
            canvas.pack(fill="both", expand=True, padx=2, pady=(1, 2))

            self.plot_widgets.append((canvas, lbl_val, cell))

        self.console = scrolledtext.ScrolledText(bottom_frame, bg="#222", fg="#00ff00", width=40, font=("Consolas", 9))
        self.console.pack(side="right", fill="y", padx=(5, 0))

    _build_simulation_and_console = _build_plots_and_console

    def refresh_joysticks(self):
        joysticks = self.input_manager.scan_joysticks()
        if not joysticks: self.lbl_joy.config(text="Joystick: Brak", fg="yellow")
        else: self.lbl_joy.config(text=f"Joystick: {joysticks[0].get_name()[:20]}", fg="green")

    def reset_network(self):
        self.state.log("Zainicjowano twardy reset sieci (MQTT)...")
        self.mqtt_manager.connect()

    def update_interface(self):
        self.lbl_mqtt_status.config(text=self.state.mqtt_status_text)
        self.led_canvas.itemconfig(self.led_ground, fill="#00ff00" if self.state.ping_ground_ok else "#444")
        self.led_canvas.itemconfig(self.led_router, fill="#00ff00" if self.state.ping_router_ok else "#444")
        self.led_canvas.itemconfig(self.led_broker, fill="#00ff00" if self.state.ping_broker_ok else "#444")
        
        for i in range(2, 9):
            color = "#00ff00" if self.state.can_status[i] else "#ff0000"
            self.can_canvas.itemconfig(self.can_leds[i], fill=color)

        # Aktualizacja wskaźnika aktywnego trybu
        if self.state.secondary_mode:
            self.lbl_mode.config(text="TRYB: NARZĘDZIE (Mini 1-4) [X]", bg="#003366", fg="#00d4ff")
            self.arm_group.config(text="RAMIĘ GŁÓWNE (Osi 1-6) — [ZABLOKOWANE - Przełącz klawiszem X]", fg="#888888")
            self.tool_group.config(text="NARZĘDZIE (Mini-Jointy 1-4) — [STEROWANIE AKTYWNE]", fg="#00d4ff")
        else:
            self.lbl_mode.config(text="TRYB: RAMIĘ GŁÓWNE (1-6) [X]", bg="#004d26", fg="#00ff66")
            self.arm_group.config(text="RAMIĘ GŁÓWNE (Osi 1-6) — [STEROWANIE AKTYWNE]", fg="#00ff66")
            self.tool_group.config(text="NARZĘDZIE (Mini-Jointy 1-4) — [NIEAKTYWNE - Przełącz klawiszem X]", fg="#888888")

        # Aktualizacja 6 osi ramienia głównego
        for i in range(6):
            cvs, lbl, frame = self.arm_widgets[i]
            target_deg = self.state.target_joints_deg[i]
            actual_deg = self.state.actual_joints_deg[i]

            lbl.config(text=f"T: {target_deg:.1f}°\nA: {actual_deg:.1f}°")

            l_min, l_max = config.AXIS_LIMITS[i]
            rng = (l_max - l_min) if l_max != l_min else 360
            angle_arc = ((actual_deg - l_min) / rng) * 360 if rng != 0 else 0

            if not self.state.secondary_mode:
                frame.config(fg="white")
                lbl.config(fg="#00ff00" if abs(target_deg - actual_deg) < 2.0 else "orange")
                arc_color = "#00A2FF"
                cvs.config(highlightbackground="#555")
            else:
                frame.config(fg="#888888")
                lbl.config(fg="#777777")
                arc_color = "#005577"
                cvs.config(highlightbackground="#333")

            if not cvs.find_withtag("arc"):
                cvs.create_arc(8, 8, 87, 87, start=90, extent=-angle_arc, style="arc", outline=arc_color, width=7, tags="arc")
            else:
                cvs.itemconfig("arc", extent=-angle_arc, outline=arc_color)

        # Aktualizacja 4 mini-jointów narzędzia (0 = tył, 100 = stop, 200 = przód)
        for i in range(4):
            cvs, lbl, frame = self.tool_widgets[i]
            speed = self.state.mini_joint_speeds[i]

            if self.state.secondary_mode:
                frame.config(fg="white")
                cvs.config(highlightbackground="#555")

                if speed >= 150.0: # Przód (200)
                    lbl.config(text="Prędkość:\n200 (PRZÓD)", fg="#00ff00")
                    if not cvs.find_withtag("arc"):
                        cvs.create_arc(8, 8, 87, 87, start=90, extent=-120, style="arc", outline="#00ff00", width=7, tags="arc")
                    else:
                        cvs.itemconfig("arc", start=90, extent=-120, outline="#00ff00")
                elif speed <= 50.0: # Tył (0)
                    lbl.config(text="Prędkość:\n0 (TYŁ)", fg="#ffaa00")
                    if not cvs.find_withtag("arc"):
                        cvs.create_arc(8, 8, 87, 87, start=90, extent=120, style="arc", outline="#ffaa00", width=7, tags="arc")
                    else:
                        cvs.itemconfig("arc", start=90, extent=120, outline="#ffaa00")
                else: # Stop / Neutral (100)
                    lbl.config(text="Prędkość:\n100 (STOP)", fg="white")
                    cvs.delete("arc")
            else:
                frame.config(fg="#666666")
                cvs.config(highlightbackground="#333")
                lbl.config(text="Prędkość:\n100 (STOP)", fg="#555555")
                cvs.delete("arc")
        # Aktualizacja historii i wykresów dla pierwszych 6 osi w czasie rzeczywistym
        for i in range(6):
            self.joint_history[i].append((self.state.target_joints_deg[i], self.state.actual_joints_deg[i]))
        self.draw_joint_plots()

        while self.state.logs:
            self.console.insert(tk.END, "> " + self.state.logs.pop(0) + "\n")
            self.console.see(tk.END)

    def draw_joint_plots(self):
        M = 100  # Maksymalna liczba próbek na wykresie
        for i in range(6):
            canvas, lbl_val, cell = self.plot_widgets[i]
            history = self.joint_history[i]
            if not history:
                continue

            target_deg, actual_deg = history[-1]
            diff = abs(target_deg - actual_deg)
            lbl_val.config(
                text=f"T: {target_deg:5.1f}°  A: {actual_deg:5.1f}°",
                fg="#00FF66" if diff < 2.0 else "#FFAA00"
            )

            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 20 or h < 20:
                continue

            pad_l = 38
            pad_r = 6
            pad_t = 6
            pad_b = 6
            pw = w - pad_l - pad_r
            ph = h - pad_t - pad_b
            if pw < 10 or ph < 10:
                continue

            l_min, l_max = config.AXIS_LIMITS[i]
            y_min = float(l_min)
            y_max = float(l_max)
            if y_max <= y_min:
                y_max = y_min + 360.0

            # Oczyszczenie poprzednich elementów wykresu
            canvas.delete("plot_item")

            def to_y(val):
                clamped = max(y_min, min(y_max, val))
                return pad_t + ph * (1.0 - (clamped - y_min) / (y_max - y_min))

            y_top = pad_t
            y_bot = pad_t + ph

            # Linie siatki poziomej (góra, dół)
            canvas.create_line(pad_l, y_top, w - pad_r, y_top, fill="#252745", tags="plot_item")
            canvas.create_text(pad_l - 2, y_top, text=f"{y_max:.0f}°", fill="#666888", anchor="e", font=("Arial", 7), tags="plot_item")

            canvas.create_line(pad_l, y_bot, w - pad_r, y_bot, fill="#252745", tags="plot_item")
            canvas.create_text(pad_l - 2, y_bot, text=f"{y_min:.0f}°", fill="#666888", anchor="e", font=("Arial", 7), tags="plot_item")

            # Linia pozioma zerowa lub środkowa
            if y_min < 0.0 < y_max:
                y_zero = to_y(0.0)
                canvas.create_line(pad_l, y_zero, w - pad_r, y_zero, fill="#383a5e", dash=(3, 3), tags="plot_item")
                canvas.create_text(pad_l - 2, y_zero, text="0°", fill="#888aa8", anchor="e", font=("Arial", 7), tags="plot_item")
            else:
                y_mid = (y_min + y_max) / 2.0
                y_m_coord = to_y(y_mid)
                canvas.create_line(pad_l, y_m_coord, w - pad_r, y_m_coord, fill="#222440", dash=(2, 4), tags="plot_item")
                canvas.create_text(pad_l - 2, y_m_coord, text=f"{y_mid:.0f}°", fill="#555877", anchor="e", font=("Arial", 7), tags="plot_item")

            # Oś pionowa Y
            canvas.create_line(pad_l, y_top, pad_l, y_bot, fill="#383a5e", tags="plot_item")

            # Rysowanie serii czasowych
            n_pts = len(history)
            if n_pts < 2:
                continue

            target_coords = []
            actual_coords = []
            dx = pw / (M - 1)

            for k in range(n_pts):
                t_val, a_val = history[k]
                x = pad_l + pw - (n_pts - 1 - k) * dx
                target_coords.extend([x, to_y(t_val)])
                actual_coords.extend([x, to_y(a_val)])

            # Seria docelowa (Target) - niebieska
            canvas.create_line(*target_coords, fill="#00A2FF", width=2, tags="plot_item")
            tx_end, ty_end = target_coords[-2], target_coords[-1]
            canvas.create_oval(tx_end - 2, ty_end - 2, tx_end + 2, ty_end + 2, fill="#00A2FF", outline="", tags="plot_item")

            # Seria rzeczywista (Actual) - zielona / pomarańczowa
            act_col = "#00FF66" if diff < 2.0 else "#FFAA00"
            canvas.create_line(*actual_coords, fill=act_col, width=2, tags="plot_item")
            ax_end, ay_end = actual_coords[-2], actual_coords[-1]
            canvas.create_oval(ax_end - 3, ay_end - 3, ax_end + 3, ay_end + 3, fill=act_col, outline="", tags="plot_item")