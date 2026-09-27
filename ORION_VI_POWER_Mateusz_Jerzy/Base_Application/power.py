# main.py
import tkinter as tk
from utils import AppState
from comms import MqttManager
from gui import PowerDashboardGUI

def main():
    root = tk.Tk()
    root.title("Orion Power Station Dashboard")
    
    # --- ZMIANA NA PEŁNY EKRAN (FULLSCREEN) ---
    root.attributes('-fullscreen', True)

    # Funkcja pozwalająca wyjść z pełnego ekranu po wciśnięciu klawisza ESC
    def exit_fullscreen(event):
        root.attributes('-fullscreen', False)
        # Po wyjściu z trybu pełnoekranowego ustawiamy standardowy rozmiar, by okno nie zniknęło
        root.geometry("1400x800")

    # Przypisanie zdarzenia klawiatury
    root.bind("<Escape>", exit_fullscreen)

    # Inicjalizacja Stanu i Modułów
    app_state = AppState()
    mqtt_manager = MqttManager(app_state)
    gui = PowerDashboardGUI(root, app_state, mqtt_manager)

    # Start MQTT
    mqtt_manager.connect()

    def main_loop():
        # Odświeżenie GUI nowymi danymi
        gui.update_interface()
        
        # Zapętlenie wywołania interfejsu (co 100ms)
        root.after(100, main_loop)

    main_loop()
    root.mainloop()

if __name__ == "__main__":
    main()