import pygame
import serial
import time
import sys

# Konfiguracja portu szeregowego
PORT_COM = 'COM32'
BAUDRATE = 115200
DEADZONE = 0.5  # Martwa strefa gałek (zapobiega dryfowaniu, gdy pad jest puszczony)

def main():
    # 1. Inicjalizacja portu szeregowego
    try:
        ser = serial.Serial(PORT_COM, BAUDRATE, timeout=0.1)
        print(f"[{PORT_COM}] Połączono z ESP32 z prędkością {BAUDRATE} baud.")
    except Exception as e:
        print(f"BŁĄD: Nie można otworzyć portu {PORT_COM}. Sprawdź, czy nie jest używany przez Arduino IDE!")
        print(e)
        sys.exit()

    # 2. Inicjalizacja biblioteki pygame i pada
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("BŁĄD: Nie znaleziono żadnego podłączonego kontrolera (pada).")
        sys.exit()

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"[PAD] Wykryto kontroler: {joystick.get_name()}")
    print("Sterowanie:")
    print(" - Lewa gałka (Y):    W / S (Serwo 1)")
    print(" - Prawa gałka (Y):   E / D (Serwo 2 + kompensacja)")
    print(" - Prawa gałka (X):   T / G (Prawo / Lewo)")
    print(" - Bumpery (LB/RB):   F / R (Zamykanie / Otwieranie)")
    print("\nNaciśnij Ctrl+C w konsoli, aby zakończyć.\n")

    try:
        while True:
            # Pobranie aktualnego stanu kontrolera
            pygame.event.pump()
            
            commands_to_send = ""

            # Odczyt osi: 
            # Oś 1 to Lewa gałka Y (ujemna wartość to góra, dodatnia dół)
            axis_left_y = joystick.get_axis(0)
            if axis_left_y < -DEADZONE:
                commands_to_send += 'w'
            elif axis_left_y > DEADZONE:
                commands_to_send += 's'

            # Oś 3 to Prawa gałka Y
            axis_right_y = joystick.get_axis(1)
            if axis_right_y < -DEADZONE:
                commands_to_send += 'e'
            elif axis_right_y > DEADZONE:
                commands_to_send += 'd'

            # Oś 2 to Prawa gałka X (lewo/prawo)
            axis_right_x = joystick.get_axis(2)
            if axis_right_x < -DEADZONE:
                commands_to_send += 't'
            elif axis_right_x > DEADZONE:
                commands_to_send += 'g'

            # Odczyt przycisków bumperów (LB = przycisk 4, RB = przycisk 5)
            if joystick.get_button(4):  # Lewy bumper (LB)
                commands_to_send += 'f'
            if joystick.get_button(5):  # Prawy bumper (RB)
                commands_to_send += 'r'

            # Wysłanie komend do ESP32, jeśli cokolwiek zostało wciśnięte
            if commands_to_send:
                ser.write(commands_to_send.encode('utf-8'))
                # print(f"Wysłano: {commands_to_send}") # Odkomentuj, by widzieć co wysyła w konsoli

            # Czekamy 50ms - to wystarczająco szybko, by ESP32 (timeout 200ms) utrzymywało ruch
            time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\nZamykanie programu...")
    finally:
        ser.close()
        pygame.quit()
        print("Rozłączono.")

if __name__ == "__main__":
    main()