# 🚀 ORION VI - Archiwum Projektu

Witaj w głównym repozytorium projektu **ORION VI**. Repozytorium to zawiera kompletny kod źródłowy (zarówno oprogramowanie wysokiego poziomu (High-Level), jak i oprogramowanie sprzętowe (Low-Level/Firmware)) dla wielomodułowego systemu robotycznego/łazika.

Projekt został podzielony na niezależne, ale współpracujące ze sobą podsystemy odpowiedzialne za napęd, zasilanie, manipulację (ramię robotyczne), wizję (kamery) oraz komunikację sieciową.

---

## 🛠️ Użyte Technologie

W projekcie wykorzystano zróżnicowany stos technologiczny, dopasowany do specyfiki poszczególnych modułów:

**Oprogramowanie wysokiego poziomu (High-Level - PC / Steam Deck):**
*   **Język:** Python 3.10 / 3.12
*   **Interfejs graficzny (GUI):** Prawdopodobnie PyQt / Tkinter / CustomTkinter (pliki `gui.py`)
*   **Komunikacja:** Serial (UART), MQTT, TCP/IP, CAN Bus
*   **Testowanie:** Pytest (`test_comms.py`, `test_ui_and_modes.py`)
*   **Inne:** Przetwarzanie obrazu (OpenCV dla kamer), eksport do `.exe` (PyInstaller - plik `.spec`)

**Oprogramowanie niskiego poziomu (Low-Level - Mikrokontrolery):**
*   **Język:** C++ / Arduino (`.ino`, `.cpp`, `.h`)
*   **Komunikacja sprzętowa:** CAN Bus (`OdriveCAN`), Serial
*   **Sterowanie silnikami:** ODrive Controller

---

## 📂 Struktura Repozytorium i Opis Modułów

Repozytorium składa się z następujących głównych modułów. Wewnątrz każdego z nich znajduje się kod dedykowany konkretnej funkcjonalności łazika.

### 1. 📷 Kamery Axis (`KAMERY_AXIS_JERZY_MATEUSZ/`)
Moduł odpowiedzialny za obsługę systemu wizyjnego opartego na kamerach sieciowych AXIS.
*   **Funkcje:** Obsługa strumieni wideo z kamer, sterowanie ruchem kamery na ramieniu (`kamery_ramie.py`), nagrywanie obrazu (`nagranie_...mp4`), skanowanie i generowanie kodów QR (`import qrcode.py`).

> **📸 Zrzut ekranu: Podgląd z kamer**
> *Wklej tutaj screena pokazującego główny interfejs podglądu z kamer lub moment rozpoznawania kodu QR.*
> `![Interfejs Kamer Axis](KAMERY_AXIS_JERZY_MATEUSZ/screenshot_2026-06-22_13-36-13.png)`

### 2. 📡 Aplikacja Sieciowa (`NETWORK_APPLICATION_MATEUSZ/`)
Narzędzie do monitorowania statusu połączeń sieciowych (prawdopodobnie urządzeń Ubiquiti/UBNT).
*   **Funkcje:** Monitorowanie telemetrii sieciowej, generowanie logów do plików `.csv` (np. `LOGS_...csv`), graficzny interfejs z wbudowanymi ikonami (`logo.ico`).

> **📸 Zrzut ekranu: Monitor Sieci**
> *Wklej tutaj screena pokazującego wykresy lub tabelę ze statystykami sieci (ping, siła sygnału itp.).*
> `![Monitor UBNT](NETWORK_APPLICATION_MATEUSZ/Network_App_UI.png)` *(Plik do dodania)*

### 3. ⚡ System Zasilania (`ORION_VI_POWER_Mateusz_Jerzy/`)
Kompleksowy system zarządzania dystrybucją energii.
*   **Base_Application:** Aplikacja w Pythonie z GUI (`gui.py`) do monitorowania napięć, prądów i stanu akumulatorów. Komunikuje się (`comms.py`) z mikrokontrolerem.
*   **Low_level_code:** Firmware w C++ (`Orion_power.ino`, `Pins.h`) bezpośrednio sterujący przekaźnikami, odczytujący czujniki prądu/napięcia i zabezpieczający system.

> **📸 Zrzut ekranu: Panel Zasilania (Power GUI)**
> *Wklej tutaj zrzut ekranu aplikacji GUI pokazującej stan baterii, zużycie prądu poszczególnych modułów.*
> `![Power Management GUI](ORION_VI_POWER_Mateusz_Jerzy/Power_GUI_Screen.png)` *(Plik do dodania)*

### 4. 🛞 System Napędowy (`ORION_VI_PROPULSION_SYSTEM_JERZY/`)
Moduł sterowania jazdą (chassis) wykorzystujący kontrolery ODrive.
*   **Base_Application:** Standardowa aplikacja sterująca w Pythonie.
*   **Base_ApplicationSteamDeck:** Dedykowana aplikacja z GUI przystosowanym do obsługi na przenośnej konsoli Steam Deck (wykorzystanie wbudowanych kontrolerów).
*   **Low_Level_Code (`chassis_new`):** Firmware implementujący komunikację CAN (`OdriveCAN.cpp`) do precyzyjnego sterowania silnikami bezszczotkowymi (BLDC) kół.

> **📸 Zrzut ekranu: Interfejs Napędu (Steam Deck / PC)**
> *Najlepiej pokazać tutaj interfejs w wersji na Steam Decka (przyciski sterowania, parametry silników).*
> `![Interfejs Napędu](ORION_VI_PROPULSION_SYSTEM_JERZY/screenshot_app.png)`

### 5. 🦾 Ramię Robotyczne (`ROBOTIC_ARM/`)
Rozbudowany system sterowania manipulatorem łazika.
*   **Firmware:** Podzielony na poszczególne węzły/przeguby ramienia (ARM_ID1, ARM_ID23, ARM_ID4, ARM_ID5_Surgical). Każdy węzeł posiada własny kod komunikacji CAN (`ARM_CAN.cpp`) i kontroli silników.
*   **Software:** Oprogramowanie sterujące na PC (`Robotic_arm.py`, `gui.py`), mapowanie wejść z kontrolera/joysticka (`inputs.py`).
*   **Komunikacja:** Integracja z MQTT (`MQTT_RAMI .md`) do zdalnego przesyłania poleceń i telemetrii ramienia.

> **📸 Zrzut ekranu: Interfejs Kinematyki Ramienia**
> *Wklej tutaj screena aplikacji pokazującej pozycje poszczególnych członów ramienia (ID1 - ID5) oraz ewentualny podgląd 3D lub suwaki.*
> `![GUI Ramienia Robotycznego](ROBOTIC_ARM/Arm_GUI_Screen.png)` *(Plik do dodania)*

### 6. 🧹 Odkurzacz (`ODKURZACZ_JERZY_MATEUSZ/`)
Osobny moduł (skrypt w Pythonie) odpowiedzialny za sterowanie mechanizmem czyszczącym/zbierającym.

---

## ⚙️ Jak uruchomić projekt

*(Tutaj dodaj krótką instrukcję jak zainstalować zależności i uruchomić główny program. Poniżej znajduje się przykładowy szablon)*

1. Sklonuj repozytorium:
   ```bash
   git clone [URL_REPOZYTORIUM]
   ```
2. Zainstaluj wymagane pakiety Pythona (zalecane wirtualne środowisko `venv`):
   ```bash
   pip install -r requirements.txt # Jeśli plik istnieje
   ```
3. Wgraj oprogramowanie Low-Level (Firmware) na odpowiednie mikrokontrolery używając Arduino IDE lub PlatformIO.
4. Uruchom wybraną aplikację High-Level, np.:
   ```bash
   cd ORION_VI_PROPULSION_SYSTEM_JERZY/Base_Application
   python main.py
   ```

---
**Twórca:** Matvii
