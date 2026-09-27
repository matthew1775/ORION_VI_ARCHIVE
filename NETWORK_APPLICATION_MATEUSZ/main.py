import sys
import os

# --- OPTYMALIZACJA ROZMIARU EXE ---
# Wymuszamy backend TkAgg. Dzięki temu PyInstaller nie musi pakować 
# gigantycznych bibliotek Qt5/Qt6/PySide, co zaoszczędzi ok. 20-30 MB.
import matplotlib
matplotlib.use('TkAgg') 
# ----------------------------------

import paramiko
import json
import time
import threading
import collections
import csv
import re
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime

# --- KONFIGURACJA DANYCH LOGOWANIA ---
UBNT_USERNAME = "orion"       
UBNT_PASSWORD = "OrionOrion!" 

DEVICES = [
    {"name": "BAZA",  "ip": "192.168.1.101", "color": "blue"},
    {"name": "ROVER", "ip": "192.168.1.102", "color": "orange"}
]

UPDATE_INTERVAL = 0.1
HISTORY_LEN = 100

data_store = {
    "BAZA": {
        "signal": collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN),
        "rate":   collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN),
        "latency": collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN),
        "freq":   collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN)
    },
    "ROVER": {
        "signal": collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN),
        "rate":   collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN),
        "latency": collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN),
        "freq":   collections.deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN)
    }
}

running = True
file_lock = threading.Lock()

TIME_FMT_LOG = "%H.%M.%S_%d.%m.%Y"
START_TIME = datetime.now()
TEMP_FILENAME = f"TEMP_LOGS_{START_TIME.strftime(TIME_FMT_LOG)}.csv"

def init_csv():
    headers = ["Timestamp", "Device", "IP", "Signal_dBm", "Noise_dBm", "Tx_Latency_ms", "TX_Rate_Mbps", "RX_Rate_Mbps", "Frequency_MHz"]
    try:
        with open(TEMP_FILENAME, mode='w', newline='') as f:
            csv.writer(f).writerow(headers)
        print(f"--> Plik tymczasowy: {TEMP_FILENAME}")
    except Exception as e:
        print(f"Błąd pliku: {e}")
        sys.exit(1)

def save_to_csv(dev_name, ip, data):
    wlan = data.get('wlan', {})
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        dev_name, ip,
        wlan.get('signal', ''),
        wlan.get('noise', ''),
        wlan.get('wlanTxLatency', ''),
        wlan.get('wlanTxRate', ''),
        wlan.get('wlanRxRate', ''),
        wlan.get('freq', '')
    ]
    with file_lock:
        with open(TEMP_FILENAME, mode='a', newline='') as f:
            csv.writer(f).writerow(row)

def parse_ubnt_output(raw_output):
    parsed = {'wlan': {}}
    try:
        return json.loads(raw_output)
    except:
        pass
    for line in raw_output.splitlines():
        if "=" in line:
            parts = line.split("=", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if k == "signal": parsed['wlan']['signal'] = int(v)
            elif k == "noise": parsed['wlan']['noise'] = int(v)
            elif k == "wlanTxLatency": parsed['wlan']['wlanTxLatency'] = int(v)
            elif k == "wlanTxRate": 
                try: parsed['wlan']['wlanTxRate'] = float(v)
                except: parsed['wlan']['wlanTxRate'] = 0
            elif k == "freq": parsed['wlan']['freq'] = int(v)
    return parsed

def ssh_worker(dev):
    global running
    name = dev["name"]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while running:
        try:
            client.connect(dev["ip"], username=UBNT_USERNAME, password=UBNT_PASSWORD, timeout=3)
            while running:
                t_start = time.time()
                try:
                    stdin, stdout, stderr = client.exec_command('mca-status')
                    output = stdout.read().decode('utf-8', errors='ignore')
                    data = parse_ubnt_output(output)
                    wlan = data.get('wlan', {})
                    sig = int(wlan.get('signal', -96))
                    if sig == 0: sig = -96
                    lat_val = int(wlan.get('wlanTxLatency', 0))
                    rate_val = float(wlan.get('wlanTxRate', 0))
                    freq_val = int(wlan.get('freq', 0))
                    data_store[name]['signal'].append(sig)
                    data_store[name]['latency'].append(lat_val)
                    data_store[name]['rate'].append(rate_val)
                    data_store[name]['freq'].append(freq_val)
                    save_to_csv(name, dev["ip"], data)
                except Exception:
                    if len(data_store[name]['signal']) > 0:
                        for k in ['signal', 'latency', 'rate', 'freq']:
                            data_store[name][k].append(data_store[name][k][-1])
                    break
                elapsed = time.time() - t_start
                time.sleep(max(0, UPDATE_INTERVAL - elapsed))
        except:
            time.sleep(2)
        finally:
            try: client.close()
            except: pass

def finalize_filename():
    end_time = datetime.now()
    final_name = f"LOGS_{START_TIME.strftime(TIME_FMT_LOG)}_TO_{end_time.strftime(TIME_FMT_LOG)}.csv"
    try:
        if os.path.exists(TEMP_FILENAME):
            os.rename(TEMP_FILENAME, final_name)
            print(f"\n✅ Zapisano plik jako: {final_name}")
    except Exception as e:
        print(f"❌ Błąd zmiany nazwy: {e}")

def run_gui():
    global running
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.canvas.manager.set_window_title('Ubiquiti Monitor')
    ax_sig, ax_spd = axs[0, 0], axs[0, 1]
    ax_lat, ax_frq = axs[1, 0], axs[1, 1]
    xs = list(range(HISTORY_LEN))
    lines = { "signal": {}, "rate": {}, "latency": {}, "freq": {} }
    for dev in DEVICES:
        nm, c = dev["name"], dev["color"]
        lines["signal"][nm], = ax_sig.plot(xs, data_store[nm]['signal'], label=nm, color=c)
        lines["rate"][nm],   = ax_spd.plot(xs, data_store[nm]['rate'],   label=nm, color=c)
        lines["latency"][nm],= ax_lat.plot(xs, data_store[nm]['latency'],label=nm, color=c)
        lines["freq"][nm],   = ax_frq.plot(xs, data_store[nm]['freq'],   label=nm, color=c)

    ax_sig.set_title("1. Siła Sygnału (dBm)"); ax_sig.set_ylim(-100, -30); ax_sig.grid(True)
    ax_spd.set_title("2. Prędkość TX (Mbps)"); ax_spd.set_ylim(0, 150); ax_spd.grid(True)
    ax_lat.set_title("3. Latency (ms)"); ax_lat.grid(True); ax_lat.set_ylim(0, 10)
    ax_frq.set_title("4. Częstotliwość (MHz)"); ax_frq.grid(True)
    
    def animate(i):
        if not running: return []
        updated_lines = []
        all_lats = list(data_store["BAZA"]["latency"]) + list(data_store["ROVER"]["latency"])
        ax_lat.set_ylim(0, 10 if (mx:=max(all_lats) if all_lats else 0) < 5 else mx * 1.5)
        all_freqs = [x for x in list(data_store["BAZA"]["freq"]) + list(data_store["ROVER"]["freq"]) if x > 0]
        if all_freqs:
            mn, mx = min(all_freqs), max(all_freqs)
            ax_frq.set_ylim(mn - 50 if mn == mx else mn - 20, mx + 50 if mn == mx else mx + 20)
        for dev in DEVICES:
            nm = dev["name"]
            lines["signal"][nm].set_data(xs, list(data_store[nm]['signal']))
            lines["rate"][nm].set_data(xs, list(data_store[nm]['rate']))
            lines["latency"][nm].set_data(xs, list(data_store[nm]['latency']))
            lines["freq"][nm].set_data(xs, list(data_store[nm]['freq']))
            lines["signal"][nm].set_label(f"{nm}: {data_store[nm]['signal'][-1] if data_store[nm]['signal'] else 'N/A'} dBm")
            lines["rate"][nm].set_label(f"{nm}: {data_store[nm]['rate'][-1] if data_store[nm]['rate'] else 'N/A'} Mbps")
            lines["latency"][nm].set_label(f"{nm}: {data_store[nm]['latency'][-1] if data_store[nm]['latency'] else 'N/A'} ms")
            lines["freq"][nm].set_label(f"{nm}: {data_store[nm]['freq'][-1] if data_store[nm]['freq'] else 'N/A'} MHz")
            updated_lines.extend([lines["signal"][nm], lines["rate"][nm], lines["latency"][nm], lines["freq"][nm]])
        ax_sig.legend(loc='upper right'); ax_spd.legend(loc='upper right'); ax_lat.legend(loc='upper right'); ax_frq.legend(loc='upper right')
        return updated_lines

    def on_close(event):
        global running
        running = False
    fig.canvas.mpl_connect('close_event', on_close)
    ani = animation.FuncAnimation(fig, animate, interval=100, blit=False)
    plt.tight_layout(); plt.show()

if __name__ == "__main__":
    init_csv()
    threads = []
    for dev in DEVICES:
        t = threading.Thread(target=ssh_worker, args=(dev,)); t.daemon = True; t.start(); threads.append(t)
    try: run_gui()
    except KeyboardInterrupt: running = False
    for t in threads: t.join(timeout=1.0)
    finalize_filename()