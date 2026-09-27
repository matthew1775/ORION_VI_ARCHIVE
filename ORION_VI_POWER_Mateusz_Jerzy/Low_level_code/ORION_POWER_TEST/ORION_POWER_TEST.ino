#include <Arduino.h>

// Definicje pinów
constexpr uint8_t S_INNE_PIN  = GPIO_NUM_2; 
constexpr uint8_t S_SCI_PIN   = GPIO_NUM_0; 
constexpr uint8_t S_ELEK_PIN  = GPIO_NUM_16; 
constexpr uint8_t S_RAM_PIN   = GPIO_NUM_17; 
constexpr uint8_t S_W_R_PIN   = GPIO_NUM_21; 
constexpr uint8_t S_W_L_PIN   = GPIO_NUM_22; 

void setup() {
  // Inicjalizacja portu szeregowego
  Serial.begin(115200);
  
  // Konfiguracja pinów jako wyjścia
  pinMode(S_INNE_PIN, OUTPUT);
  pinMode(S_SCI_PIN, OUTPUT);
  pinMode(S_ELEK_PIN, OUTPUT);
  pinMode(S_RAM_PIN, OUTPUT);
  pinMode(S_W_R_PIN, OUTPUT);
  pinMode(S_W_L_PIN, OUTPUT);

  // Ustawienie początkowego stanu na LOW (niski)
  digitalWrite(S_INNE_PIN, LOW);
  digitalWrite(S_SCI_PIN, LOW);
  digitalWrite(S_ELEK_PIN, LOW);
  digitalWrite(S_RAM_PIN, LOW);
  digitalWrite(S_W_R_PIN, LOW);
  digitalWrite(S_W_L_PIN, LOW);

  Serial.println("System gotowy.");
  Serial.println("Dostepne komendy: S_INNE, S_SCI, S_ELEK, S_RAM, S_W_R, S_W_L");
}

void loop() {
  // Sprawdzenie, czy są nowe dane w buforze Serial
  if (Serial.available() > 0) {
    // Odczyt linii tekstu aż do znaku nowej linii
    String command = Serial.readStringUntil('\n');
    
    // Usunięcie ewentualnych białych znaków (np. \r, spacji), 
    // które mogą zepsuć porównanie
    command.trim(); 

    // Ignoruj puste wiadomości
    if (command.length() == 0) return;

    // Logika przełączania
    if (command == "S_INNE") {
      digitalWrite(S_INNE_PIN, !digitalRead(S_INNE_PIN));
      Serial.print("Stan S_INNE_PIN: ");
      Serial.println(digitalRead(S_INNE_PIN) ? "WYSOKI (HIGH)" : "NISKI (LOW)");
    } 
    else if (command == "S_SCI") {
      digitalWrite(S_SCI_PIN, !digitalRead(S_SCI_PIN));
      Serial.print("Stan S_SCI_PIN: ");
      Serial.println(digitalRead(S_SCI_PIN) ? "WYSOKI (HIGH)" : "NISKI (LOW)");
    } 
    else if (command == "S_ELEK") {
      digitalWrite(S_ELEK_PIN, !digitalRead(S_ELEK_PIN));
      Serial.print("Stan S_ELEK_PIN: ");
      Serial.println(digitalRead(S_ELEK_PIN) ? "WYSOKI (HIGH)" : "NISKI (LOW)");
    } 
    else if (command == "S_RAM") {
      digitalWrite(S_RAM_PIN, !digitalRead(S_RAM_PIN));
      Serial.print("Stan S_RAM_PIN: ");
      Serial.println(digitalRead(S_RAM_PIN) ? "WYSOKI (HIGH)" : "NISKI (LOW)");
    } 
    else if (command == "S_W_R") {
      digitalWrite(S_W_R_PIN, !digitalRead(S_W_R_PIN));
      Serial.print("Stan S_W_R_PIN: ");
      Serial.println(digitalRead(S_W_R_PIN) ? "WYSOKI (HIGH)" : "NISKI (LOW)");
    } 
    else if (command == "S_W_L") {
      digitalWrite(S_W_L_PIN, !digitalRead(S_W_L_PIN));
      Serial.print("Stan S_W_L_PIN: ");
      Serial.println(digitalRead(S_W_L_PIN) ? "WYSOKI (HIGH)" : "NISKI (LOW)");
    } 
    else {
      Serial.println("Nieznana komenda! Uzyj: S_INNE, S_SCI, S_ELEK, S_RAM, S_W_R, S_W_L");
    }
  }
}