# PROPULSION CONTROL DASHBOARD - MAIN MODULE
import tkinter as tk
import os          # <-- DODAJ TO
import pygame      # <-- DODAJ TO

# --- ZABEZPIECZENIE AUDIO DLA STEAM DECK ---
# Musi być ustawione PRZED inicjalizacją jakiegokolwiek modułu pygame!
# -------------------------------------------

from utils import AppState
from inputs import InputManager
from comms import MqttManager
from gui import DashboardGUI

# --- ZABEZPIECZENIE AUDIO DLA STEAM DECK ---
# Musi być ustawione PRZED inicjalizacją jakiegokolwiek modułu pygame!
#####os.environ["SDL_AUDIODRIVER"] = "pulse"


def main():
    # 1. Inicjalizacja Głównego Okna
    root = tk.Tk()
    root.title("ODrive Control Modular")
    root.attributes('-fullscreen', True)
    
    # 2. Inicjalizacja Stanu i Modułów
    app_state : AppState = AppState()
    input_manager : InputManager = InputManager()
    mqtt_manager : MqttManager = MqttManager(app_state)
    
    # 3. Inicjalizacja GUI
    gui = DashboardGUI(root, app_state, input_manager, mqtt_manager)
    
    # 4. Bindings (Klawiatura musi być podpięta pod root)
    def on_key_press(event):
        if event.keysym.lower() == 'escape':
            root.attributes('-fullscreen', False)
            root.geometry("1200x800")
        else:
            input_manager.handle_keyboard('press', event.keysym)

    def on_key_release(event):
        input_manager.handle_keyboard('release', event.keysym)

    root.bind("<KeyPress>", on_key_press)
    root.bind("<KeyRelease>", on_key_release)

    # 5. Start MQTT
    mqtt_manager.connect()
    
    # 6. Pętla Główna
    def main_loop():
        # A. Odczyt wejść (Joystick/Klawiatura) -> Aktualizacja AppState
        input_manager.update(app_state)
        
        # B. Wysłanie komend do ODrive przez MQTT
        mqtt_manager.send_drive_command()
        # --- NOWY KOD: Sprawdzenie wyzwolenia z pada ---
        if getattr(app_state, 'trigger_full_start', False):
            gui.run_full_start()
            app_state.trigger_full_start = False
        # -----------------------------------------------
        
        # C. Odświeżenie GUI (Wykresy, Labele)
        gui.update_interface()
        
        # D. Planowanie kolejnej klatki (50ms = 20 FPS odświeżania logiki)
        root.after(50, main_loop)

    gui.refresh_joysticks()
    main_loop()
    root.mainloop()

if __name__ == "__main__":
    main()