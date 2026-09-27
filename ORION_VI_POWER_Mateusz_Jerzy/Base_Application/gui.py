# gui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import config
from utils import AppState
from comms import MqttManager


# Importy dla wykresów
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class PowerDashboardGUI:
    def __init__(self, root, app_state, mqtt_manager):
        self.root = root
        self.state: AppState = app_state
        self.mqtt_manager: MqttManager = mqtt_manager
        
        self.plot_counter = 0 # Licznik do spowalniania odświeżania wykresów
        self.setup_ui()
        
    def setup_ui(self):
        self.root.configure(bg=config.BG_COLOR)
        
        # Pasek Statusu MQTT
        self.header = tk.Frame(self.root, bg="#111")
        self.header.pack(fill="x")
        self.lbl_mqtt_status = tk.Label(self.header, text="MQTT: --", bg="#111", fg="white", font=("Arial", 14, "bold"))
        self.lbl_mqtt_status.pack(side="left", padx=15, pady=10)
        self.lbl_packet_age = tk.Label(self.header, text="Opóźnienie: -- ms", bg="#111", fg="#aaaaaa", font=("Consolas", 12))
        self.lbl_packet_age.pack(side="left", padx=15, pady=10)
        self.btn_reset = tk.Button(self.header, text="Reset MQTT", bg="#d9534f", fg="white", font=("Arial", 10, "bold"), command=self._cmd_reset_mqtt)
        self.btn_reset.pack(side="right", padx=15, pady=10)
        
        self.main_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- ZMIANA LAYOUTU NA 3 KOLUMNY ---
        
        # Panel lewy: Odczyty tekstowe
        self.left_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR, width=350)
        self.left_frame.pack(side="left", fill="y", padx=(0, 10))
        self.left_frame.pack_propagate(False)
        
        # Panel prawy: Sterowanie i konsola (pakujemy go przed środkiem)
        self.right_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR, width=400)
        self.right_frame.pack(side="right", fill="y")
        self.right_frame.pack_propagate(False)

        # Panel środkowy: 6 Wykresów
        self.center_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR)
        self.center_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        self._build_telemetry_panel()
        self._build_charts_panel()
        self._build_control_panel()
        
    def _cmd_reset_mqtt(self):
        threading.Thread(target=self.mqtt_manager.force_reconnect, daemon=True).start()

    def _build_telemetry_panel(self):
        # 1. Odczyty z baterii
        bat_frame = tk.LabelFrame(self.left_frame, text="Napięcia Baterii (20V MAX)", bg=config.BG_COLOR, fg="#00ff00", font=("Arial", 12))
        bat_frame.pack(fill="x", pady=5)
        self.lbl_bats = []
        for i in range(4):
            lbl = tk.Label(bat_frame, text=f"Bateria {i+1}: 0.00 V", bg=config.BG_COLOR, fg="white", font=("Consolas", 18))
            lbl.pack(anchor="w", padx=15, pady=2)
            self.lbl_bats.append(lbl)
            
        # 2. Odczyt Temperatury
        temp_frame = tk.LabelFrame(self.left_frame, text="Czujnik DS18B20", bg=config.BG_COLOR, fg="#00ccff", font=("Arial", 12))
        temp_frame.pack(fill="x", pady=10)
        self.lbl_temp = tk.Label(temp_frame, text="Temp: 0.0 °C", bg=config.BG_COLOR, fg="#00ccff", font=("Consolas", 20, "bold"))
        self.lbl_temp.pack(anchor="w", padx=15, pady=5)
        
        # 3. Odczyty ADC (Tekstowe)
        adc_frame = tk.LabelFrame(self.left_frame, text="Pobór Prądu Linii (ACS712)", bg=config.BG_COLOR, fg="#ffaa00", font=("Arial", 12))
        adc_frame.pack(fill="x", pady=5)
        self.lbl_adcs = {}
        keys = ["adc_wl", "adc_wr", "adc_ram", "adc_elek", "adc_sci", "adc_inne"]
        for key in keys:
            lbl = tk.Label(adc_frame, text=f"{key.upper()}: RAW 0 | 0.00 A", bg=config.BG_COLOR, fg="white", font=("Consolas", 14))
            lbl.pack(anchor="w", padx=15, pady=4)
            self.lbl_adcs[key] = lbl

    def _build_charts_panel(self):
        chart_container = tk.LabelFrame(self.center_frame, text="Pobór Prądu w Czasie [A]", bg=config.BG_COLOR, fg="#00ccff", font=("Arial", 12))
        chart_container.pack(fill="both", expand=True)

        # Tworzenie figury Matplotlib
        self.fig = Figure(figsize=(6, 8), dpi=100, facecolor=config.BG_COLOR)
        self.axes = {}
        self.lines = {}

        keys = ["adc_wl", "adc_wr", "adc_ram", "adc_elek", "adc_sci", "adc_inne"]
        titles = ["Koło Lewe (WL)", "Koło Prawe (WR)", "Ramię (RAM)", "Elektronika (ELEK)", "Sprzęt Sci (SCI)", "Inne (INNE)"]
        colors = ["#ff5555", "#55ff55", "#5555ff", "#ffff55", "#ff55ff", "#55ffff"]

        # Siatka 3 rzędy x 2 kolumny
        for i, key in enumerate(keys):
            ax = self.fig.add_subplot(3, 2, i+1)
            ax.set_facecolor("#111111")
            ax.tick_params(colors="white", labelsize=8)
            for spine in ax.spines.values(): spine.set_color('#444')
            ax.grid(True, color='#333', linestyle=':')
            ax.set_title(titles[i], color="#dddddd", fontsize=10)

            line, = ax.plot([], [], color=colors[i], lw=2)
            self.axes[key] = ax
            self.lines[key] = line

        self.fig.tight_layout()
        
        # Zagnieżdżenie w Tkinterze
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def _build_control_panel(self):
        # 1. 6 Przycisków zasilania + Wentylator (Układ ON / OFF)
        ctrl_frame = tk.LabelFrame(self.right_frame, text="Zarządzanie Liniami Zasilania", bg=config.BG_COLOR, fg="#00ff00", font=("Arial", 12))
        ctrl_frame.pack(fill="x", pady=5)
        
        self.btn_switches = {}
        switches = ["S_INNE", "S_SCI", "S_ELEK", "S_RAM", "S_W_R", "S_W_L", "FAN1_ON"]
        
        for sw in switches:
            # Kontener na jeden rząd (Etykieta + Przycisk OFF + Przycisk ON)
            row_frame = tk.Frame(ctrl_frame, bg=config.BG_COLOR)
            row_frame.pack(fill="x", padx=10, pady=3)
            
            # Nazwa pinu
            lbl = tk.Label(row_frame, text=sw, width=10, anchor="w", bg=config.BG_COLOR, fg="white", font=("Arial", 11, "bold"))
            lbl.pack(side="left")
            
            # Przycisk OFF (Czerwony)
            btn_off = tk.Button(row_frame, text="OFF", font=("Arial", 10, "bold"), width=8,
                                command=lambda s=sw: self.mqtt_manager.set_switch(s, 0))
            btn_off.pack(side="right", padx=(5, 0))
            
            # Przycisk ON (Zielony)
            btn_on = tk.Button(row_frame, text="ON", font=("Arial", 10, "bold"), width=8,
                               command=lambda s=sw: self.mqtt_manager.set_switch(s, 1))
            btn_on.pack(side="right")
            
            # Zapisujemy referencje do obu przycisków, by móc nimi zarządzać
            self.btn_switches[sw] = {"on": btn_on, "off": btn_off}
            
        # 2. Konsola na dole
        log_frame = tk.LabelFrame(self.right_frame, text="Konsola Poleceń", bg=config.BG_COLOR, fg="#ffffff")
        log_frame.pack(fill="both", expand=True, pady=10)
        self.console = scrolledtext.ScrolledText(log_frame, bg="#222", fg="#0f0", font=("Consolas", 10))
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        
    def _calc_current_acs712(self, raw_adc, key):
        zero_raw = config.ACS712_ZERO_RAW.get(key, 3000)
        delta_raw = raw_adc - zero_raw
        delta_v = delta_raw * (3.3 / 4095.0)
        current_a = delta_v / config.ACS712_SENSITIVITY
        return current_a

    def update_interface(self):
        # 1. Update statusu i Packet Age
        self.lbl_mqtt_status.config(text=self.state.mqtt_status_text)
        if self.state.mqtt_connected: self.lbl_mqtt_status.config(fg="#00ff00")
        else: self.lbl_mqtt_status.config(fg="red")

        # Flaga sprawdzająca, czy ESP32 faktycznie żyje i nadaje
        is_esp_alive = False
        
        if self.state.last_feedback_time > 0:
            age_ms = (time.time() - self.state.last_feedback_time) * 1000.0
            self.lbl_packet_age.config(text=f"Opóźnienie: {int(age_ms)} ms")
            
            if age_ms < 300: 
                self.lbl_packet_age.config(fg="#00ff00")
            elif age_ms < 1000: 
                self.lbl_packet_age.config(fg="orange")
            else: 
                self.lbl_packet_age.config(fg="red")
                
            # Uznajemy, że ESP "żyje" tylko, gdy MQTT jest połączone, a wiek pakietu jest mniejszy niż 2.5 sekundy
            if self.state.mqtt_connected and age_ms < 2500:
                is_esp_alive = True
        else:
            self.lbl_packet_age.config(text="Opóźnienie: Brak danych", fg="grey")
            
        # 2. Update Baterii & Temp
        for i in range(4): self.lbl_bats[i].config(text=f"Bateria {i+1}: {self.state.bat_v[i]:.2f} V")
        self.lbl_temp.config(text=f"Temp: {self.state.temp_c:.1f} °C")
        
        # 3. Update Tekstu ADC & Historii do Wykresów
        current_time = time.time() - self.state.start_time
        self.state.history_time.append(current_time)

        for key, lbl in self.lbl_adcs.items():
            raw = self.state.adc[key]
            current_amps = self._calc_current_acs712(raw, key)
            lbl.config(text=f"{key.upper():<8}: RAW {raw:>4d}  |  {current_amps:>5.2f} A")
            self.state.history_amps[key].append(current_amps)

        # 4. Rysowanie Wykresów
        self.plot_counter += 1
        if self.plot_counter % 5 == 0 and len(self.state.history_time) > 1:
            for key in self.lines:
                self.lines[key].set_data(list(self.state.history_time), list(self.state.history_amps[key]))
                ax = self.axes[key]
                ax.set_xlim(self.state.history_time[0], self.state.history_time[-1])
                amps = list(self.state.history_amps[key])
                c_min, c_max = min(amps), max(amps)
                if c_max - c_min < 2.0:
                    mid = (c_max + c_min) / 2.0
                    ax.set_ylim(mid - 1.0, mid + 1.0)
                else:
                    ax.set_ylim(c_min - 0.5, c_max + 0.5)
            self.canvas.draw_idle()
            
        # 5. Aktualizacja Przycisków (BLOKOWANIE I KOLORY)
        for sw, btns in self.btn_switches.items():
            state = self.state.switches[sw]
            btn_on = btns["on"]
            btn_off = btns["off"]
            
            if not is_esp_alive:
                # Jeśli ESP nie żyje, szarzemy i wyłączamy klikanie w oba przyciski
                btn_on.config(state=tk.DISABLED, bg="#444444", fg="#888888")
                btn_off.config(state=tk.DISABLED, bg="#444444", fg="#888888")
            else:
                # Jeśli żyje, wyłączamy klikalność tego przycisku, który odpowiada za aktualny stan.
                # Np. jak jest WŁĄCZONY, to przycisk ON jest "wciśnięty" (nieaktywny do kliku), a OFF czeka na klik.
                if state == 1:
                    btn_on.config(state=tk.DISABLED, bg=config.BTN_ON_COLOR, fg="white")    # Aktywny stan (Zielony)
                    btn_off.config(state=tk.NORMAL, bg="#552222", fg="#cccccc")             # Czeka na wyłączenie (Ciemny czerwony)
                else:
                    btn_on.config(state=tk.NORMAL, bg="#225522", fg="#cccccc")              # Czeka na włączenie (Ciemny zielony)
                    btn_off.config(state=tk.DISABLED, bg=config.BTN_OFF_COLOR, fg="white")  # Aktywny stan (Czerwony)
                
        # 6. Wypisywanie logów
        while self.state.logs:
            msg = self.state.logs.pop(0)
            self.console.insert(tk.END, msg + "\n")
            self.console.see(tk.END)