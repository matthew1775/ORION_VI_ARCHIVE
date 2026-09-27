# ORION_VI_PROPULSION_SYSTEM


# 🚗 ODrive MQTT-CAN Bridge & Control Station

A robust remote control system for a generic robotic vehicle platform (4-wheel steering/propulsion). This project bridges a high-level Python Control Station (PC) with low-level hardware (ODrive & Servos) using an **ESP32** via **Ethernet** and **CAN Bus**.


## 🌟 Features

  * **Hybrid Control:** Simultaneous control of ODrive BLDC motors (via CAN) and Steering Servos (via PWM).
  * **Low Latency:** Uses wired Ethernet (W5500) and UDP-like MQTT communication for fast response times.
  * **Python Control Station:** A complete GUI Dashboard built with `Tkinter` and `Pygame`.
      * Real-time telemetry graphs.
      * Analog gauges for Speed and Steering.
      * Gamepad/Joystick support (Xbox/PlayStation controllers).
      * Keyboard fallback control.
  * **Safety Watchdog:** The ESP32 automatically halts motors if the connection is lost for more than **500ms**.
  * **Feedback Loop:** Real-time feedback of estimated velocity and position from the ODrive encoder.

-----

## 🏗 System Architecture

The system follows a Client-Server architecture over a local network:

1.  **Control Station (PC):** Reads Joystick inputs, calculates physics (differential steering/Ackermann), and publishes commands via MQTT.
2.  **MQTT Broker:** (e.g., Raspberry Pi or Mosquitto on PC) at `192.168.1.1`.
3.  **Bridge (ESP32):** Subscribes to MQTT topics and translates commands to:
      * **CAN Frames:** For ODrive Velocity Control.
      * **PWM Signals:** For Servo Steering Angle.
4.  **Actuators:** ODrive v3.6 (Propulsion) and High-Torque Servos (Steering).

-----

## 🔌 Hardware Setup

### Pinout Configuration (ESP32)

Ensure your wiring matches the definitions in `ESP32_Propulsion_And_Steering.ino`.

#### 1\. Ethernet Module (W5500)

| W5500 Pin | ESP32 Pin | Note |
| :--- | :--- | :--- |
| **CS** | **GPIO 21** | *Custom Chip Select* |
| **RST** | **GPIO 22** | Hardware Reset |
| MOSI | GPIO 23 | Standard VSPI |
| MISO | GPIO 19 | Standard VSPI |
| SCK | GPIO 18 | Standard VSPI |
| VCC | 3.3V or 5V | Check your module specs |

#### 2\. CAN Bus Transceiver (TJA1050 / SN65HVD230)

| Module Pin | ESP32 Pin | Note |
| :--- | :--- | :--- |
| **CTX (TX)** | **GPIO 5** | Transmit |
| **CRX (RX)** | **GPIO 4** | Receive |
| CAN H | ODrive CAN H | |
| CAN L | ODrive CAN L | |

#### 3\. Steering Servos

| Function | ESP32 Pin | PWM Mapping |
| :--- | :--- | :--- |
| **Front Servo** | **GPIO 27** | 0° (Right) - 30° (Center) - 130° (Left) |
| **Rear Servo** | **GPIO 26** | Synchronized with Front |

-----

## 🛠️ Software Requirements

### 1\. ESP32 Firmware (Arduino IDE)

Install the following libraries via the Arduino Library Manager:

  * `Ethernet` (by Arduino)
  * `PubSubClient` (by Nick O'Leary)
  * `CAN` (by Sandeep Mistry)
  * `ArduinoJson` (by Benoit Blanchon)
  * `ESP32Servo` (by Kevin Harrington)

**ODrive Configuration:**

  * **Baudrate:** 250k (`250000`)
  * **Front Motor:** `node_id = 0`
  * **Rear Motor:** `node_id = 1`

### 2\. PC Application (Python)

Requires Python 3.8+. Install dependencies:

```bash
pip install pygame paho-mqtt matplotlib
```

*(Note: `tkinter` is usually included with standard Python installations).*

-----

## 🚀 Usage

### 1\. Network Configuration

Ensure all devices are on the same subnet (`192.168.1.x`).

  * **MQTT Broker:** `192.168.1.1`
  * **ESP32 Static IP:** `192.168.1.177` (Defined in firmware)

### 2\. Flash the ESP32

1.  Open `ESP32_Propulsion_And_Steering.ino` in Arduino IDE.
2.  Select board **ESP32 Dev Module**.
3.  Upload the code.
4.  Open Serial Monitor (`115200 baud`) to verify Ethernet and CAN initialization.

### 3\. Run the Control Station

Connect your Joystick and run the script:

```bash
python app_control_station.py
```

  * **Press `ESC`** to exit Fullscreen mode.
  * **Press `★ AUTO START ★`** to calibrate and arm the ODrive.

-----

## 📡 MQTT API Protocol

The system uses JSON payloads for data exchange.

**Topic Prefix:** `propulsion/`

| Topic | Direction | Payload Example | Description |
| :--- | :--- | :--- | :--- |
| `propulsion/set_velocity` | PC -\> ESP | `{"velocity": 12.5}` | Target RPS (Rotations Per Second). |
| `propulsion/steering` | PC -\> ESP | `{"angle": 45}` | Servo angle (0-130). |
| `propulsion/cmd` | PC -\> ESP | `"closed_loop"` | System commands: `calibrate`, `closed_loop`, `set_vel_mode`. |
| `propulsion/feedback` | ESP -\> PC | `{"v": 12.0, "p": 100.5, "angle": 30}` | Real-time telemetry (Velocity, Position, Angle). |

-----

## 🕹 Controls

| Input | Function |
| :--- | :--- |
| **Left Stick Y** | Throttle (Forward / Backward) |
| **Left Stick X** | Steering (Left / Right) |
| **Right Trigger** | Speed Limiter (Analog) |
| **Keyboard W/S** | Throttle |
| **Keyboard A/D** | Steering (Max Left/Right) |

-----

## ⚠️ Safety Features

**Connection Watchdog:**
The ESP32 firmware monitors the time since the last valid MQTT message. If no message is received for **500ms**, the system performs an emergency stop:

1.  Sets ODrive Velocity to `0.0`.
2.  Logs "Watchdog: STOP" to Serial.

-----

## 📜 License

This project is open-source. Feel free to modify and adapt it to your specific robot chassis.
