#ifndef ID4_CAN_H
#define ID4_CAN_H

#include <Arduino.h>

// Deklaracje funkcji
void initCanAndServos();
void handleCanAndServos();
// Nowa funkcja do pobierania pozycji pierwszego serwa
int16_t getServo1Position();
// Funkcja zwracająca status połączenia dla głównego pliku (do obsługi LED)
bool isReceivingCommands();

#endif