import sys
import os
import math
import tkinter as tk
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock paho-mqtt
mock_paho = MagicMock()
sys.modules["paho"] = mock_paho
sys.modules["paho.mqtt"] = mock_paho.mqtt
sys.modules["paho.mqtt.client"] = mock_paho.mqtt.client

import config
from utils import AppState
from inputs import InputManager
from comms import MqttManager
from gui import DashboardGUI

def test_full_flow():
    root = tk.Tk()
    root.withdraw() # Headless

    app_state = AppState()
    input_manager = InputManager()
    mqtt_manager = MqttManager(app_state)

    gui = DashboardGUI(root, app_state, input_manager, mqtt_manager)

    # 1. Sprawdzenie czy symulacja narzędzia i kinematyka ramienia zostały całkowicie usunięte
    assert not hasattr(gui, "tip_frame") or gui.tip_frame is None or not hasattr(gui, "canvas_tip"), "Symulacja narzędzia nie powinna istnieć w GUI"
    assert not hasattr(gui, "draw_scissor_tip"), "Metoda draw_scissor_tip powinna być usunięta"
    assert not hasattr(gui, "canvas_arm"), "canvas_arm (kinematyka 2D) powinien być całkowicie usunięty"
    assert not hasattr(gui, "draw_arm"), "Metoda draw_arm powinna być całkowicie usunięta"
    assert not hasattr(config, "LINK_LENGTHS"), "LINK_LENGTHS powinny być usunięte z config.py"

    # 2. Sprawdzenie obecności 10 stopni swobody na jednym ekranie
    assert len(gui.arm_widgets) == 6, f"Oczekiwano 6 widgetów ramienia, znaleziono {len(gui.arm_widgets)}"
    assert len(gui.tool_widgets) == 4, f"Oczekiwano 4 widgetów narzędzia, znaleziono {len(gui.tool_widgets)}"
    assert len(gui.joint_widgets) == 10, f"Oczekiwano 10 widgetów łącznie, znaleziono {len(gui.joint_widgets)}"

    # 3. Test trybu domyślnego (RAMIĘ GŁÓWNE)
    assert app_state.secondary_mode is False
    gui.update_interface()
    assert "RAMIĘ" in gui.lbl_mode.cget("text")
    assert "AKTYWNE" in gui.arm_group.cget("text")
    assert "NIEAKTYWNE" in gui.tool_group.cget("text")

    # 4. Test przełączania klawiszem 'x' (klawiatura)
    input_manager.handle_keyboard('press', 'x')
    input_manager.update(app_state)
    assert app_state.secondary_mode is True, "Wciśnięcie klawisza 'x' powinno włączyć tryb narzędzia"

    gui.update_interface()
    assert "NARZĘDZIE" in gui.lbl_mode.cget("text")
    assert "AKTYWNE" in gui.tool_group.cget("text")
    assert "ZABLOKOWANE" in gui.arm_group.cget("text")

    # 5. Sprawdzenie że wszystkie 10 kafelków nadal istnieje i jest zmapowane
    for cvs, lbl, frame in gui.arm_widgets:
        assert frame.winfo_exists(), "Kafelek ramienia powinien być widoczny"
    for cvs, lbl, frame in gui.tool_widgets:
        assert frame.winfo_exists(), "Kafelek narzędzia powinien być widoczny"

    # 6. Test symulacji ramienia w trybie narzędzia (ramię nie powinno znikać)
    assert gui.arm_frame.winfo_exists(), "Symulacja ramienia powinna być widoczna także w trybie narzędzia"
    # 6. Test panelu wykresów (zamiast symulacji 2D)
    assert gui.plots_frame.winfo_exists(), "Panel wykresów powinien być widoczny"
    assert len(gui.plot_widgets) == 6, f"Oczekiwano 6 wykresów, znaleziono {len(gui.plot_widgets)}"
    for cvs, val_lbl, cell in gui.plot_widgets:
        assert cvs.winfo_exists(), "Płótno wykresu powinno istnieć"

    # 7. Test ponownego przełączenia klawiszem 'X' z powrotem na ramię
    input_manager.handle_keyboard('press', 'X')
    input_manager.update(app_state)
    assert app_state.secondary_mode is False, "Ponowne wciśnięcie 'X' powinno przywrócić tryb ramienia"

    gui.update_interface()
    assert "RAMIĘ" in gui.lbl_mode.cget("text")

    # 8. Test odbierania MQTT bez błędów indeksowania
    mock_payload = {
        "eventType": "Robotic_arm_enc",
        "payload": {
            f"enc_joint{i+1}_rad": math.radians(15 * (i + 1)) for i in range(8)
        }
    }
    mock_payload["payload"]["enc_joint_mini_1_rad"] = math.radians(45.0)
    
    class MockMsg:
        payload = str(mock_payload).replace("'", '"').encode()
    
    mqtt_manager._on_message(None, None, MockMsg())
    assert len(app_state.actual_joints_deg) >= 8
    assert math.isclose(app_state.actual_joints_deg[0], 15.0, abs_tol=1e-3)
    assert math.isclose(app_state.actual_joints_deg[7], 120.0, abs_tol=1e-3)

    # Odświeżenie interfejsu z nowymi odczytami
    gui.update_interface()

    # 9. Test prędkości minijointów (100 stop, 200 przód, 0 tył)
    assert app_state.mini_joint_speeds == [100.0, 100.0, 100.0, 100.0]
    app_state.secondary_mode = True
    app_state.mini_joint_speeds = [200.0, 0.0, 100.0, 100.0]
    gui.update_interface()
    assert "200 (PRZÓD)" in gui.tool_widgets[0][1].cget("text")
    assert "0 (TYŁ)" in gui.tool_widgets[1][1].cget("text")
    assert "100 (STOP)" in gui.tool_widgets[2][1].cget("text")

    # 10. Test bufora historii wykresów (kąty w czasie)
    assert len(gui.joint_history) == 6, "Powinno być 6 buforów historii dla 6 osi"
    for i in range(6):
        assert len(gui.joint_history[i]) > 0, f"Bufor historii osi {i+1} powinien zawierać próbki"
        last_target, last_actual = gui.joint_history[i][-1]
        assert math.isclose(last_target, app_state.target_joints_deg[i])
        assert math.isclose(last_actual, app_state.actual_joints_deg[i])

    root.destroy()
    print("ALL 9 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("ALL 10 VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_flow()
