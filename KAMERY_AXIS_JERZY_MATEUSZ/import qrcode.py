import qrcode
import os

def stworz_kod_qr(tekst, nazwa_pliku="moj_kod_qr.png"):
    """
    Funkcja generująca kod QR i zapisująca go w tym samym folderze co skrypt.
    """
    
    # ==========================================
    # NOWOŚĆ: Ustalanie dokładnej ścieżki
    # ==========================================
    # Pobiera ścieżkę do folderu, w którym znajduje się ten konkretny plik .py
    folder_skryptu = os.path.dirname(os.path.abspath(__file__))
    
    # Łączy ścieżkę folderu z nazwą pliku (tworzy pełną ścieżkę zapisu)
    pelna_sciezka = os.path.join(folder_skryptu, nazwa_pliku)

    # Konfiguracja kodu QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2,
    )

    # Dodanie tekstu do zakodowania
    qr.add_data(tekst)
    qr.make(fit=True)

    # Wygenerowanie obrazu
    img = qr.make_image(fill_color="black", back_color="white")

    # Zapisanie obrazu z użyciem pełnej ścieżki
    img.save(pelna_sciezka)
    print(f"Sukces! Kod QR został wygenerowany i zapisany w:\n{pelna_sciezka}")

# ==========================================
# Użycie generatora
# ==========================================

twoj_tekst = "PROBKA_101"

# Możesz zmienić nazwę pliku wyjściowego w drugim argumencie
stworz_kod_qr(twoj_tekst, "kod_qr_w_tym_samym_folderze.png")