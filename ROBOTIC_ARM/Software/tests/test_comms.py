import json
import math
try:
    import pytest
except ImportError:
    pytest = None
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mock paho-mqtt before importing MqttManager
mock_paho = MagicMock()
sys.modules["paho"] = mock_paho
sys.modules["paho.mqtt"] = mock_paho.mqtt
sys.modules["paho.mqtt.client"] = mock_paho.mqtt.client

from Software.comms import MqttManager
from Software.utils import AppState

class MockMsg:
    def __init__(self, payload):
        self.payload = payload

def test_on_message_valid_payload():
    state = AppState()
    mqtt_manager = MqttManager(state)

    # Mock payload with radians
    payload = {
        "eventType": "Robotic_arm_enc",
        "payload": {
            f"enc_joint{i+1}_rad": math.radians(10 * (i + 1)) for i in range(8)
        }
    }
    msg = MockMsg(json.dumps(payload).encode())

    mqtt_manager._on_message(None, None, msg)

    for i in range(8):
        assert math.isclose(state.actual_joints_deg[i], 10 * (i + 1), abs_tol=1e-5)

def test_on_message_missing_joints():
    state = AppState()
    mqtt_manager = MqttManager(state)

    # Start with non-zero values
    state.actual_joints_deg = [45.0] * 8

    # Mock payload with some missing joints
    payload = {
        "eventType": "Robotic_arm_enc",
        "payload": {
            "enc_joint1_rad": math.radians(10.0),
            # joint2 is missing
        }
    }
    msg = MockMsg(json.dumps(payload).encode())

    mqtt_manager._on_message(None, None, msg)

    assert math.isclose(state.actual_joints_deg[0], 10.0, abs_tol=1e-5)
    # The current implementation uses p.get(key, 0.0), so it should reset missing joints to 0.0
    assert state.actual_joints_deg[1] == 0.0

def test_on_message_wrong_event_type():
    state = AppState()
    state.actual_joints_deg = [45.0] * 8
    mqtt_manager = MqttManager(state)

    payload = {
        "eventType": "Other_event",
        "payload": {
            "enc_joint1_rad": math.radians(10.0)
        }
    }
    msg = MockMsg(json.dumps(payload).encode())

    mqtt_manager._on_message(None, None, msg)

    # Should not update state
    assert state.actual_joints_deg[0] == 45.0

def test_on_message_invalid_json():
    state = AppState()
    state.actual_joints_deg = [45.0] * 8
    mqtt_manager = MqttManager(state)

    msg = MockMsg(b"invalid json")

    # Should not raise exception because of try-except block in _on_message
    mqtt_manager._on_message(None, None, msg)

    # Should not update state
    assert state.actual_joints_deg[0] == 45.0

if __name__ == "__main__":
    test_on_message_valid_payload()
    test_on_message_missing_joints()
    test_on_message_wrong_event_type()
    test_on_message_invalid_json()
    print("ALL test_comms.py TESTS PASSED!")
