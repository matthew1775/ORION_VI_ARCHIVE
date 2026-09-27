import sys
import os
import multiprocessing
import tkinter as tk

from utils import AppState
from inputs import InputManager
from comms import MqttManager
from gui import DashboardGUI

def main():
    root = tk.Tk()
    root.title("Robotic Arm Control Dashboard")
    root.attributes('-fullscreen', True)
    
    app_state = AppState()
    input_manager = InputManager()
    mqtt_manager = MqttManager(app_state)
    
    gui = DashboardGUI(root, app_state, input_manager, mqtt_manager)
    
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

    mqtt_manager.connect()
    
    def main_loop():
        # A. Odczyt danych i kalkulacja
        input_manager.update(app_state)
        
        # B. Wysłanie komend do ESP32
        mqtt_manager.send_drive_command()
        
        # C. Odświeżenie animacji GUI
        gui.update_interface()
        
        # D. Pętla 50ms (20FPS)
        root.after(50, main_loop)

    gui.refresh_joysticks()
    main_loop()
    root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()