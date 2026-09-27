import cv2
import os
from onvif import ONVIFCamera

# Wymuszenie TCP dla płynnego obrazu
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# --- KONFIGURACJA ONVIF ---
IP = "192.168.1.82"
PORT_ONVIF = 554  # Jeśli nie zadziała, spróbuj: 80, 8000 lub 5000
USER = "admin"
PASSWORD = "orion"
# --------------------------

print("Połączenie z urządzeniem przez ONVIF...")
try:
    # Inicjalizacja połączenia ONVIF
    mycam = ONVIFCamera(IP, PORT_ONVIF, USER, PASSWORD)
    
    # Tworzenie usługi medialnej
    media_service = mycam.create_media_service()
    
    # Pobranie wszystkich dostępnych profili wideo (kanałów/strumieni)
    profiles = media_service.GetProfiles()
    
    if not profiles:
        print("Błąd: Nie znaleziono żadnych profili wideo w urządzeniu.")
        exit()

    # Wyświetlenie znalezionych profili, abyś wiedział co rejestrator udostępnia
    print("\nZnalezione profile ONVIF:")
    for i, profile in enumerate(profiles):
        print(f"[{i}] Nazwa profilu: {profile.Name} (Token: {profile.token})")

    # Wybieramy profil. Zazwyczaj rejestrator ma po 2 profile na kamerę (główny i pomocniczy).
    # Jeśli szukasz kanału 4, metodą prób i błędów wybierz odpowiedni indeks z listy (np. 6 lub 7).
    # Na start wybieramy profil o indeksie 0:
    wybrany_indeks = 0 
    target_profile = profiles[wybrany_indeks]
    print(f"\nPobieranie strumienia dla profilu: {target_profile.Name}")

    # Pobranie dokładnego linku RTSP dla wybranego profilu
    stream_setup = {
        'Stream': 'RTP-Unicast',
        'Transport': {'Protocol': 'RTSP'}
    }
    uri_response = media_service.GetStreamUri({'StreamSetup': stream_setup, 'ProfileToken': target_profile.token})
    
    # Wyciągnięcie czystego adresu URL
    rtsp_url = uri_response.Uri
    
    # Często ONVIF zwraca link bez loginu i hasła w środku, musimy je wstrzyknąć dla OpenCV:
    if "://" in rtsp_url:
        protokol, reszta = rtsp_url.split("://", 1)
        rtsp_url = f"{protokol}://{USER}:{PASSWORD}@{reszta}"

    print(f"Wygenerowany dynamicznie link RTSP: {rtsp_url}\n")

except Exception as e:
    print(f"Błąd ONVIF: Nie można połączyć się z portem {PORT_ONVIF}. Sprawdź czy port jest poprawny.")
    print(f"Szczegóły błędu: {e}")
    exit()

# --- URUCHOMIENIE OPENCV Z WYCIĄGNIĘTYM LINKIEM ---
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Błąd OpenCV: Nie można otworzyć pobranego strumienia RTSP.")
    exit()

print("Strumień uruchomiony pomyślnie! Naciśnij 'q' aby wyjść.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Utracono połączenie.")
        break
    
    cv2.imshow("ONVIF Stream", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()