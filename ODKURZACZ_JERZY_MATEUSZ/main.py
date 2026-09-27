import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import json

# --- Configuration ---
BROKER_ADDRESS = "192.168.1.1"
TOPIC_ENC = "Vacuum_enc"
TOPIC_CMD = "Vacuum_cmd"
CLIENT_ID = "Vacuum_Monitor_GUI"

DEFAULT_COLLECTING_MS = 10000
DEFAULT_DROPPING_MS   = 10000
TELEMETRY_TIMEOUT_MS  = 5000  # Time without a message before UI goes idle

# Maps display label -> (uint8 command_id, button color, active/hover color)
VACUUM_COMMANDS = {
    "[0] TO_IDLE":       (0, "#4A90D9", "#357ABD"),
    "[1] TO_COLLECTING": (1, "#5BAD72", "#469A5A"),
    "[2] TO_DROPPING":   (2, "#5BAD72", "#469A5A"),
    "[3] TO_CLEANING":   (3, "#AD5BAC", "#8A3F89"),
    "[4] CLEAR_ERRORS":  (5, "#F0AD4E", "#D68C2E"),
    "[5] TO_ABORT":      (4, "#D9534F", "#C0302C"),
}

VACUUM_COMMANDS_ENUM: list[str] = [
    "TO_IDLE", "TO_COLLECTING", "TO_DROPPING", "TO_CLEANING", "TO_ABORT", "CLEAR_ERRORS"
]
VACUUM_STATES_ENUM: list[str] = [
    "IDLE", "COLLECTING", "DROPPING", "CLEANING", "ABORT", "ERROR"
]
ERROR_STATES_ENUM: list[str] = [
    "NO_ERROR", "HARDWARE_ERROR", "STATE_TRANSITION_ERROR", "UNKNOWN_COMMAND_ERROR"
]

# ServoLidState enum values (mirrored from firmware)
LID_OPEN   = 47
LID_CLOSED = 78

# Maps each vacuum state -> set of button-name substrings that are allowed.
# TO_ABORT is handled separately (always enabled) and need not be listed here.
STATE_ALLOWED_BUTTONS: dict[str, set[str]] = {
    "IDLE":       {"TO_IDLE", "TO_COLLECTING", "TO_DROPPING", "TO_CLEANING", "CLEAR_ERRORS"},
    "COLLECTING": {"TO_COLLECTING", "TO_DROPPING", "CLEAR_ERRORS"},
    "DROPPING":   {"TO_DROPPING", "TO_IDLE", "TO_CLEANING", "CLEAR_ERRORS"},
    "CLEANING":   {"TO_CLEANING", "TO_IDLE", "CLEAR_ERRORS"},
    "ABORT":      {"TO_IDLE"},
    "ERROR":      {"CLEAR_ERRORS", "TO_IDLE"},
    "CLEAR_ERRORS": {"TO_IDLE"}
}

# ── Colour tokens ──────────────────────────────────────────────────────────────
BG_DEEP        = "#1E1E2E"
BG_PANEL       = "#252535"
BG_INPUT       = "#2A2A3E"
FG_MAIN        = "#CDD6F4"
FG_DIM         = "#A6ADC8"
FG_MUTED       = "#6C7086"
ACCENT         = "#89B4FA"
ERR_RED        = "#F38BA8"
BORDER         = "#313244"
BAR_BG         = "#181825"
INDICATOR_ON   = "#A6E3A1"   # green  – active / good
INDICATOR_OFF  = "#F38BA8"   # red    – inactive / bad
INDICATOR_IDLE = "#45475A"   # grey   – no data yet
MONO           = ("Courier", 9)
MONO_BOLD      = ("Courier", 9, "bold")


# ── Reusable widgets ───────────────────────────────────────────────────────────

class UIntEntry(tk.Frame):
    """
    A labelled, validated entry that only accepts unsigned integers.
    Turns red on invalid input and exposes .get_value() -> int | None.
    """

    def __init__(self, parent, label: str, default: int, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)

        tk.Label(
            self, text=label, bg=BG_DEEP, fg=FG_DIM,
            font=MONO, anchor="w"
        ).pack(fill=tk.X)

        self._var = tk.StringVar(value=str(default))
        self._entry = tk.Entry(
            self,
            textvariable=self._var,
            bg=BG_INPUT,
            fg=FG_MAIN,
            insertbackground=FG_MAIN,
            selectbackground=ACCENT,
            selectforeground=BG_DEEP,
            font=MONO_BOLD,
            relief=tk.FLAT,
            bd=4,
            width=12,
        )
        self._entry.pack(fill=tk.X, ipady=4)

        self._var.trace_add("write", self._on_change)
        self._valid = True

    # ── validation ────────────────────────────────────────────────────────────

    def _on_change(self, *_):
        raw = self._var.get()
        if self._is_valid(raw):
            self._entry.config(fg=FG_MAIN)
            self._valid = True
        else:
            self._entry.config(fg=ERR_RED)
            self._valid = False

    @staticmethod
    def _is_valid(text: str) -> bool:
        if text == "":
            return False
        try:
            v = int(text)
            return v >= 0
        except ValueError:
            return False

    # ── public API ────────────────────────────────────────────────────────────

    def get_value(self) -> int | None:
        """Return the validated uint value, or None if invalid."""
        raw = self._var.get()
        if self._is_valid(raw):
            return int(raw)
        return None

    def mark_error(self):
        """Briefly flash the border red to signal a send-time validation error."""
        self._entry.config(fg=ERR_RED)
        self._entry.after(1200, lambda: self._entry.config(
            fg=FG_MAIN if self._valid else ERR_RED
        ))


class RoundIndicator(tk.Frame):
    """
    A circular LED-style status indicator with a text label beneath it.

    Call .set_state(True)  → green  (active / good)
         .set_state(False) → red    (inactive / bad)
         .reset()          → grey   (no data)
    """

    _SIZE   = 28   # canvas / oval outer dimension
    _INSET  = 3    # space between canvas edge and oval edge
    _GLOW   = 6    # extra spread used for the inner highlight dot

    def __init__(self, parent, label: str, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)

        # Canvas holds the oval
        self._canvas = tk.Canvas(
            self,
            width=self._SIZE, height=self._SIZE,
            bg=BG_DEEP, highlightthickness=0,
        )
        self._canvas.pack()

        i = self._INSET
        s = self._SIZE
        # Main oval
        self._oval = self._canvas.create_oval(
            i, i, s - i, s - i,
            fill=INDICATOR_IDLE,
            outline=BORDER,
            width=1,
        )
        # Small specular highlight (top-left corner)
        hi = i + 3
        self._highlight = self._canvas.create_oval(
            hi, hi, hi + 5, hi + 5,
            fill="#FFFFFF", outline="", stipple="gray50",
        )

        # Label
        tk.Label(
            self,
            text=label,
            bg=BG_DEEP, fg=FG_DIM,
            font=("Courier", 8),
            anchor="center",
            justify="center",
            wraplength=72,
        ).pack(pady=(3, 0))

    # ── public API ────────────────────────────────────────────────────────────

    def set_state(self, active: bool) -> None:
        color = INDICATOR_ON if active else INDICATOR_OFF
        self._canvas.itemconfig(self._oval, fill=color, outline=BORDER)

    def reset(self) -> None:
        self._canvas.itemconfig(self._oval, fill=INDICATOR_IDLE, outline=BORDER)


# ── Main application ───────────────────────────────────────────────────────────

class VacuumMonitorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Vacuum Telemetry Monitor")
        self.root.geometry("440x760")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DEEP)
        self.is_connected = False
        
        self.cmd_buttons = {}          # Store button references mapped by key name
        self._telemetry_timer = None   # Timer handle for timeout checks

        self.data_vars = {
            "BLDC Ammeter":             tk.StringVar(value="—"),
            "Compressor Valve Ammeter": tk.StringVar(value="—"),
            "Load Cell Value":          tk.StringVar(value="—"),
            "BLDC Temperature":         tk.StringVar(value="—"),
            "Vacuum Command":           tk.StringVar(value="—"),
            "Vacuum State":             tk.StringVar(value="—"),
            "App Error State":          tk.StringVar(value="—"),
        }
        self.status_var = tk.StringVar(value="Connecting…")

        self._build_telemetry_panel()
        self._build_timeout_panel()
        self._build_command_panel()
        self._build_hardware_panel()
        self._build_status_bar()
        self.setup_mqtt()

        # Initial pass enforces safety lock on all commands except TO_ABORT
        self.set_buttons_state(tk.DISABLED)

    # ── UI construction ───────────────────────────────────────────────────────

    def _lframe(self, title: str) -> tk.LabelFrame:
        """Helper: styled LabelFrame."""
        return tk.LabelFrame(
            self.root,
            text=f" {title} ",
            bg=BG_DEEP, fg=FG_MAIN,
            font=MONO_BOLD,
            bd=1, relief=tk.GROOVE,
            padx=10, pady=8,
        )

    def _build_telemetry_panel(self):
        outer = self._lframe("TELEMETRY")
        outer.pack(fill=tk.X, padx=14, pady=(14, 6))

        for label_text, string_var in self.data_vars.items():
            row = tk.Frame(outer, bg=BG_DEEP)
            row.pack(fill=tk.X, pady=2)

            tk.Label(
                row, text=f"{label_text}:", bg=BG_DEEP,
                fg=FG_DIM, font=MONO, anchor="w", width=26
            ).pack(side=tk.LEFT)

            tk.Label(
                row, textvariable=string_var, bg=BG_DEEP,
                fg=FG_MAIN, font=MONO_BOLD, anchor="w"
            ).pack(side=tk.LEFT)

    def _build_hardware_panel(self):
        outer = self._lframe("HARDWARE STATUS")
        outer.pack(fill=tk.X, padx=14, pady=6)

        # ── row 1: three running flags ────────────────────────────────────────
        row1 = tk.Frame(outer, bg=BG_DEEP)
        row1.pack(fill=tk.X, pady=(2, 4))
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        self._ind_vacuum = RoundIndicator(row1, "Vacuum")
        self._ind_drill  = RoundIndicator(row1, "Drill")
        self._ind_vibro  = RoundIndicator(row1, "Vibro")
        self._ind_lid   = RoundIndicator(row1, "Lid")

        self._ind_vacuum.grid(row=0, column=0)
        self._ind_drill .grid(row=0, column=1)
        self._ind_vibro .grid(row=0, column=2)
        self._ind_lid  .grid(row=0, column=3)
        

        # ── separator ─────────────────────────────────────────────────────────
        tk.Frame(outer, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 4))

        # ── row 2: lid state + computed is-ready ──────────────────────────────
        row2 = tk.Frame(outer, bg=BG_DEEP)
        row2.pack(fill=tk.X, pady=(0, 2))
        row2.columnconfigure((0), weight=1)

        self._ind_ready = RoundIndicator(row2, "Is Ready")

        self._ind_ready.grid(row=0, column=0)

    def _build_timeout_panel(self):
        outer = self._lframe("TIMEOUT PARAMETERS")
        outer.pack(fill=tk.X, padx=14, pady=6)

        fields_row = tk.Frame(outer, bg=BG_DEEP)
        fields_row.pack(fill=tk.X)
        fields_row.columnconfigure(0, weight=1)
        fields_row.columnconfigure(1, weight=1)

        self._collecting_entry = UIntEntry(
            fields_row,
            label="Collecting time (ms)",
            default=DEFAULT_COLLECTING_MS,
        )
        self._collecting_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self._dropping_entry = UIntEntry(
            fields_row,
            label="Dropping time (ms)",
            default=DEFAULT_DROPPING_MS,
        )
        self._dropping_entry.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _build_command_panel(self):
        outer = self._lframe("COMMANDS")
        outer.pack(fill=tk.X, padx=14, pady=6)

        for idx, (name, (value, color, hover_color)) in enumerate(VACUUM_COMMANDS.items()):
            btn = tk.Button(
                outer,
                text=name.replace("_", " "),
                bg=color,
                fg="#FFFFFF",
                activebackground=hover_color,
                activeforeground="#FFFFFF",
                font=MONO_BOLD,
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=6,
                cursor="hand2",
                command=lambda v=value, n=name: self.send_command(v, n),
                anchor="w",
                justify="left",
            )
            btn.grid(row=idx // 2, column=idx % 2, padx=6, pady=4, sticky="ew")
            self.cmd_buttons[name] = btn  # Map key string to button instance

        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BAR_BG, height=24)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(
            bar, textvariable=self.status_var,
            bg=BAR_BG, fg=FG_MUTED,
            font=("Courier", 8), anchor="w", padx=10,
        ).pack(fill=tk.X)

    # ── Interactive State Helpers ─────────────────────────────────────────────

    def set_buttons_state(self, state: str):
        """Sets the state of all command buttons, leaving TO_ABORT enabled at all times."""
        for name, btn in self.cmd_buttons.items():
            if "TO_ABORT" in name:
                btn.config(state=tk.NORMAL)
            else:
                btn.config(state=state)

    def _apply_button_states(self, is_ready: bool, vacuum_state: str):
        """
        Enable only the buttons permitted for the current vacuum state,
        and only when is_ready is True.  TO_ABORT bypasses both conditions.
        """
        allowed = STATE_ALLOWED_BUTTONS.get(vacuum_state, set())

        for name, btn in self.cmd_buttons.items():
            # TO_ABORT is always clickable, regardless of ready or state
            if "TO_ABORT" in name:
                btn.config(state=tk.NORMAL)
                continue

            # Derive the bare command token from the button label, e.g.
            # "[1] TO_COLLECTING" → "TO_COLLECTING"
            token = name.split("] ", 1)[-1]   # strip leading "[N] " prefix

            if is_ready and token in allowed:
                btn.config(state=tk.NORMAL)
            else:
                btn.config(state=tk.DISABLED)

    def reset_ui_to_idle(self):
        """Resets the UI fields when telemetry drops out."""
        for var in self.data_vars.values():
            var.set("—")
        self._ind_vacuum.reset()
        self._ind_drill.reset()
        self._ind_vibro.reset()
        self._ind_lid.reset()
        self._ind_ready.reset()
        self.set_buttons_state(tk.DISABLED)

    def _on_telemetry_timeout(self):
        """Called automatically if no message arrives within TELEMETRY_TIMEOUT_MS."""
        self.status_var.set("Telemetry timeout! Device disconnected or silent.")
        self.reset_ui_to_idle()

    def _reset_telemetry_timer(self):
        """Cancels the existing timeout timer and starts a fresh one."""
        if self._telemetry_timer is not None:
            self.root.after_cancel(self._telemetry_timer)
        self._telemetry_timer = self.root.after(TELEMETRY_TIMEOUT_MS, self._on_telemetry_timeout)

    # ── MQTT ──────────────────────────────────────────────────────────────────

    def setup_mqtt(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=CLIENT_ID)
        self.client.on_connect    = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message    = self.on_message
        try:
            self.client.connect(BROKER_ADDRESS, 1883, 60)
            self.client.loop_start()
            self.is_connected = True
        except Exception as e:
            self.is_connected = False
            self.status_var.set(f"Connection failed: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(TOPIC_ENC)
            self.root.after(0, self.status_var.set, f"Connected to {BROKER_ADDRESS}")
        else:
            self.root.after(0, self.status_var.set, f"Broker rejected connection (rc={rc})")

    def on_disconnect(self, client, userdata, rc):
        self.root.after(0, self.status_var.set, "Disconnected from broker")
        self.root.after(0, self.reset_ui_to_idle)

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            if isinstance(data, list) and len(data) >= 11:
                self.root.after(0, self.update_gui, data)
            else:
                print(f"Unexpected JSON format: {data}")
        except json.JSONDecodeError:
            print(msg.payload.decode("utf-8"))
            print("Error parsing JSON payload.")
        except Exception as e:
            print(f"Error processing message: {e}")

    def send_command(self, cmd_id: int, name: str):
        collecting_ms = self._collecting_entry.get_value()
        dropping_ms   = self._dropping_entry.get_value()

        # ── validate ──────────────────────────────────────────────────────────
        errors = []
        if collecting_ms is None:
            self._collecting_entry.mark_error()
            errors.append("collecting_time_ms")
        if dropping_ms is None:
            self._dropping_entry.mark_error()
            errors.append("dropping_time_ms")

        if errors:
            self.root.after(
                0, self.status_var.set,
                f"Invalid value(s): {', '.join(errors)} — must be unsigned integers"
            )
            return

        # ── build and publish ─────────────────────────────────────────────────
        payload = json.dumps([cmd_id, collecting_ms, dropping_ms])
        result  = self.client.publish(TOPIC_CMD, payload)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.root.after(
                0, self.status_var.set,
                f"Sent: {name}  →  {payload}  →  {TOPIC_CMD}"
            )
        else:
            self.root.after(
                0, self.status_var.set,
                f"Publish failed (rc={result.rc})"
            )

    # ── GUI update ────────────────────────────────────────────────────────────

    def update_gui(self, data: list):
        # We got valid data, refresh the timeout timer
        self._reset_telemetry_timer()

        # ── telemetry fields (indices 0-6) ────────────────────────────────────
        self.data_vars["BLDC Ammeter"].set(f"{data[0]:.2f} A")
        self.data_vars["Compressor Valve Ammeter"].set(f"{data[1]:.2f} A")
        self.data_vars["Load Cell Value"].set(f"{data[2]:.2f}")
        self.data_vars["BLDC Temperature"].set(f"{data[3]} °C")
        
        cmd_idx = data[4] if data[4] < len(VACUUM_COMMANDS_ENUM) else 0
        state_idx = data[5] if data[5] < len(VACUUM_STATES_ENUM) else 0
        err_idx = data[6] if data[6] < len(ERROR_STATES_ENUM) else 0
        
        self.data_vars["Vacuum Command"].set(VACUUM_COMMANDS_ENUM[cmd_idx])
        self.data_vars["Vacuum State"].set(VACUUM_STATES_ENUM[state_idx])
        self.data_vars["App Error State"].set(ERROR_STATES_ENUM[err_idx])

        # ── hardware status fields (indices 7-10) ─────────────────────────────
        lid_state       = int(data[7])
        is_running_vac  = bool(data[8])
        is_running_drl  = bool(data[9])
        is_running_vib  = bool(data[10])

        lid_is_open = (lid_state == LID_OPEN)

        # Ready = nothing running AND lid is closed
        is_ready = (
            not is_running_vac
            and not is_running_drl
            and not is_running_vib
            and not lid_is_open
        )

        self._ind_vacuum.set_state(is_running_vac)
        self._ind_drill .set_state(is_running_drl)
        self._ind_vibro .set_state(is_running_vib)
        self._ind_lid   .set_state(lid_is_open)
        self._ind_ready .set_state(is_ready)

        # Enable only the buttons valid for the current state (and only when ready)
        self._apply_button_states(is_ready, VACUUM_STATES_ENUM[state_idx])

    def on_closing(self):
        if self._telemetry_timer is not None:
            self.root.after_cancel(self._telemetry_timer)
        self.client.loop_stop()
        self.client.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app  = VacuumMonitorApp(root)
    #root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()