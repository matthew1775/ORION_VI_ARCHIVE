import cv2
import threading
import numpy as np
import time
import os
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

class VideoStream:
    """Klasa do asynchronicznego odczytu i zarządzania strumieniem RTSP."""
    def __init__(self, src=0, name="Camera"):
        self.src = src
        self.name = name
        self.stopped = False
        self.frame = None

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        cap = cv2.VideoCapture(self.src)
        while not self.stopped:
            grabbed, frame = cap.read()
            if not grabbed:
                self.frame = None
                time.sleep(0.1) 
                continue
            self.frame = frame
        cap.release()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True

def main():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # --- KONFIGURACJA KAMER ---
    IP = "192.168.11.150"  
    USER = "orion"
    PASS = "orion"

    current_resolution = "960x540"

    def get_stream_url(cam_id, resolution):
        return f"rtsp://{USER}:{PASS}@{IP}/axis-media/media.amp?camera={cam_id}&resolution={resolution}"

    active_streams = {
        0: VideoStream(get_stream_url(1, current_resolution), "Cam 1").start(),
        1: VideoStream(get_stream_url(2, current_resolution), "Cam 2").start(),
        2: VideoStream(get_stream_url(3, current_resolution), "Cam 3").start(),
        3: VideoStream(get_stream_url(4, current_resolution), "Cam 4").start()
    }

    window_name = "Axis F34 - Multiview (ArUco & QR)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    is_fullscreen = True

    # --- ZMIENNE DO NAGRYWANIA ---
    is_recording = False
    video_writer = None
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    fps = 30.0  
    resolution_video = (1920, 1080)

    # --- ZMIENNA DO WDR ---
    wdr_enabled = False

    # --- KONFIGURACJA ARUCO ---
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_250)
    aruco_params = cv2.aruco.DetectorParameters()
    MARKER_SIZE = 0.05  
    camera_matrix = np.array([[1000, 0, 960], 
                              [0, 1000, 540], 
                              [0, 0, 1]], dtype=np.float32)
    dist_coeffs = np.zeros((4,1))
    marker_3d_points = np.array([
        [-MARKER_SIZE / 2, MARKER_SIZE / 2, 0],
        [MARKER_SIZE / 2, MARKER_SIZE / 2, 0],
        [MARKER_SIZE / 2, -MARKER_SIZE / 2, 0],
        [-MARKER_SIZE / 2, -MARKER_SIZE / 2, 0]
    ], dtype=np.float32)

    # --- INICJALIZACJA DETEKTORA KODÓW QR ---
    qr_detector = cv2.QRCodeDetector()

    print(f"Katalog roboczy ustawiony na: {SCRIPT_DIR}")
    print("--- SKRÓTY KLAWISZOWE ---")
    print("1, 2, 3, 4 - Wł/Wył konkretne strumienie")
    print("6, 7, 8    - Zmiana rozdzielczości (6: 720p, 7: 450p, 8: 270p)")
    print("s          - Zrób zrzut ekranu (Screenshot)")
    print("d / f      - Start / Stop nagrywania wideo")
    print("w          - Wł/Wył tryb WDR")
    print("m          - Wł/Wył tryb pełnoekranowy")
    print("q / ESC    - Wyjście z programu\n")

    while True:
        frames_to_show = []
        for i in range(4):
            if active_streams[i] is not None:
                frm = active_streams[i].read()
                name = active_streams[i].name
                
                if frm is not None:
                    frm_display = frm.copy()
                    gray = cv2.cvtColor(frm_display, cv2.COLOR_BGR2GRAY)
                    
                    # --- 1. WYKRYWANIE ARUCO ---
                    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
                    if ids is not None:
                        cv2.aruco.drawDetectedMarkers(frm_display, corners, ids)
                        for j in range(len(ids)):
                            marker_id = ids[j][0]
                            marker_corners = corners[j][0]
                            success, rvec, tvec = cv2.solvePnP(marker_3d_points, marker_corners, camera_matrix, dist_coeffs)
                            
                            if success:
                                cv2.drawFrameAxes(frm_display, camera_matrix, dist_coeffs, rvec, tvec, 0.03)
                                x, y, z = tvec[0][0], tvec[1][0], tvec[2][0]
                                text = f"ID: {marker_id}  X: {x:.2f} Y: {y:.2f} Z: {z:.2f}"
                                text_pos = (int(marker_corners[0][0]), int(marker_corners[0][1]) - 15)
                                cv2.putText(frm_display, text, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
                                cv2.putText(frm_display, text, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    # --- 2. WYKRYWANIE KODÓW QR ---
                    retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frm_display)
                    if retval:
                        for info, pts in zip(decoded_info, points):
                            if info: # Jeśli udało się odczytać tekst z QR
                                pts = np.int32(pts)
                                # Rysowanie fioletowego kwadratu dookoła kodu QR
                                cv2.polylines(frm_display, [pts], isClosed=True, color=(255, 0, 255), thickness=3)
                                
                                # Wyświetlanie odczytanego tekstu nad kodem QR
                                qr_text = f"QR: {info}"
                                text_pos = (int(pts[0][0]), int(pts[0][1]) - 10)
                                cv2.putText(frm_display, qr_text, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
                                cv2.putText(frm_display, qr_text, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

                else:
                    frm_display = np.zeros((1080, 1920, 3), dtype=np.uint8)
                    cv2.putText(frm_display, f"{name} - Ladowanie...", (800, 540), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 165, 255), 3)
                
                frames_to_show.append((name, frm_display))

        # --- DYNAMICZNY UKŁAD (LAYOUT 16:9) ---
        num_cams = len(frames_to_show)
        display_grid = None

        if num_cams == 0:
            display_grid = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(display_grid, "Wszystkie strumienie wylaczone. Wcisnij 1, 2, 3 lub 4.", (350, 540), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        elif num_cams == 1:
            name, frm = frames_to_show[0]
            display_grid = cv2.resize(frm, (1920, 1080))
            cv2.putText(display_grid, name, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        elif num_cams == 2:
            name1, frm1 = frames_to_show[0]
            name2, frm2 = frames_to_show[1]
            f1 = cv2.resize(frm1, (960, 540))
            cv2.putText(f1, name1, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            f2 = cv2.resize(frm2, (960, 540))
            cv2.putText(f2, name2, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            middle_row = np.hstack((f1, f2))
            black_pad = np.zeros((270, 1920, 3), dtype=np.uint8)
            display_grid = np.vstack((black_pad, middle_row, black_pad))
        else:
            grid_frames = []
            for i in range(4):
                if i < num_cams:
                    name, frm = frames_to_show[i]
                    f = cv2.resize(frm, (960, 540))
                    cv2.putText(f, name, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    grid_frames.append(f)
                else:
                    grid_frames.append(np.zeros((540, 960, 3), dtype=np.uint8))
            top_row = np.hstack((grid_frames[0], grid_frames[1]))
            bottom_row = np.hstack((grid_frames[2], grid_frames[3]))
            display_grid = np.vstack((top_row, bottom_row))

        # --- INFORMACJE WIZUALNE NA EKRANIE ---
        wdr_text = "WDR: ON" if wdr_enabled else "WDR: OFF"
        wdr_color = (0, 255, 0) if wdr_enabled else (0, 0, 255)
        cv2.putText(display_grid, wdr_text, (20, 1000), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
        cv2.putText(display_grid, wdr_text, (20, 1000), cv2.FONT_HERSHEY_SIMPLEX, 1, wdr_color, 2)
        
        res_text = f"RES: {current_resolution}"
        cv2.putText(display_grid, res_text, (20, 1050), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
        cv2.putText(display_grid, res_text, (20, 1050), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        if is_recording:
            if int(time.time() * 2) % 2 == 0:
                cv2.circle(display_grid, (1850, 50), 15, (0, 0, 255), -1)
                cv2.putText(display_grid, "REC", (1760, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if video_writer is not None:
                video_writer.write(display_grid)

        cv2.imshow(window_name, display_grid)

        # --- OBSŁUGA KLAWIATURY ---
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('q') or key == 27:
            break
        elif key == ord('m'):
            is_fullscreen = not is_fullscreen
            if is_fullscreen:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        elif key in [ord('6'), ord('7'), ord('8')]:
            if key == ord('6'):
                new_resolution = "1280x720"
            elif key == ord('7'):
                new_resolution = "800x450"
            elif key == ord('8'):
                new_resolution = "480x270"
            
            if new_resolution != current_resolution:
                print(f"Zmieniam rozdzielczosc sieciowa na: {new_resolution}...")
                current_resolution = new_resolution
                for i in range(4):
                    if active_streams[i] is not None:
                        active_streams[i].stop()
                        new_url = get_stream_url(i+1, current_resolution)
                        active_streams[i] = VideoStream(new_url, f"Cam {i+1}").start()

        elif key == ord('w'):
            wdr_enabled = not wdr_enabled
            state_str = "on" if wdr_enabled else "off"
            print(f"Wysylanie komendy: WDR {state_str.upper()}...")
            
            def toggle_wdr_api():
                for i in range(4):
                    url = f"http://{IP}/axis-cgi/param.cgi?action=update&ImageSource.{i}.Sensor.WDR={state_str}"
                    try:
                        resp = requests.get(url, auth=HTTPDigestAuth(USER, PASS), timeout=3)
                        if resp.status_code == 200:
                            print(f"Kamera {i+1}: WDR {state_str.upper()} OK")
                        else:
                            print(f"Kamera {i+1}: Blad WDR (Kod {resp.status_code})")
                    except Exception as e:
                        print(f"Kamera {i+1}: Blad sieci przy ustawianiu WDR - {e}")
                        
            threading.Thread(target=toggle_wdr_api, daemon=True).start()

        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(SCRIPT_DIR, filename)
            cv2.imwrite(filepath, display_grid)
            print(f"[{timestamp}] Zrobiono zrzut ekranu: {filepath}")
        elif key == ord('d'):
            if not is_recording:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"nagranie_{timestamp}.mp4"
                filepath = os.path.join(SCRIPT_DIR, filename)
                video_writer = cv2.VideoWriter(filepath, fourcc, fps, resolution_video)
                is_recording = True
                print(f"[{timestamp}] Rozpoczeto nagrywanie wideo: {filepath}")
        elif key == ord('f'):
            if is_recording:
                is_recording = False
                if video_writer is not None:
                    video_writer.release()
                    video_writer = None
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Zakonczono nagrywanie wideo.")
        elif key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            idx = key - ord('1')
            if active_streams[idx] is not None:
                print(f"Zamykanie kamery {idx+1}...")
                active_streams[idx].stop()
                active_streams[idx] = None
            else:
                print(f"Otwieranie kamery {idx+1}...")
                new_url = get_stream_url(idx+1, current_resolution)
                active_streams[idx] = VideoStream(new_url, f"Cam {idx+1}").start()

    print("Zamykanie programu...")
    if is_recording and video_writer is not None:
        video_writer.release()
    for i in range(4):
        if active_streams[i] is not None:
            active_streams[i].stop()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()