#include <Arduino.h> 
#include "config.h" 
#include "ODriveCAN.h" 
#include "Network.h" 
#include <Adafruit_NeoPixel.h>
#include <ESP32Servo.h> // <--- Dodana biblioteka

volatile float targetVelocityFront = 0.0f; 
volatile float targetVelocityRear = 0.0f; 
volatile float targetSteeringFront = 0.0f; 
volatile float targetSteeringRear = 0.0f;    

float servoVoltageA = 0.0f; 
float servoVoltageB = 0.0f; 
float servoCurrentA = 0.0f; 
float servoCurrentB = 0.0f; 
float measuredPosFront = 0.0f; 
float measuredVelFront = 0.0f; 
float measuredPosRear = 0.0f; 
float measuredVelRear = 0.0f; 
uint32_t activeErrorsFront = 0;      
uint32_t activeErrorsRear = 0;      
const unsigned long SAFETY_TIMEOUT = 1000; 
unsigned long lastMqttCmdTime = 0; 
bool lastMqttState = false; 
bool isFirstLoop = true; 

// --- DEKLARACJA OBIEKTÓW SERWO ---
Servo servoA;
Servo servoB;
// --- KLASA REGULATORA PID ---
class SteerPID {
  private:
    float kp, ki, kd;
    float integral, prevError;
    unsigned long lastTime;
    float maxVelocity;

  public:
    SteerPID(float p, float i, float d, float maxV) {
      kp = p; ki = i; kd = d; maxVelocity = maxV;
      integral = 0; prevError = 0; lastTime = 0;
    }

    float compute(float target, float current) {
      unsigned long now = millis();
      
      // Przy pierwszym przebiegu tylko inicjalizujemy czas, żeby uniknąć skoków
      if (lastTime == 0) { 
        lastTime = now; 
        return 0.0f; 
      }
      
      float dt = (now - lastTime) / 1000.0f; // Różnica czasu w sekundach
      lastTime = now;
      if (dt <= 0.0f) return 0.0f;

      float error = target - current;

      // 1. Człon Całkujący (z zabezpieczeniem Anti-windup)
      integral += error * dt;
      integral = constrain(integral, -1.0f, 1.0f); 

      // 2. Człon Różniczkujący
      float derivative = (error - prevError) / dt;
      prevError = error;

      // 3. Wyjście PID (żądana PRĘDKOŚĆ skrętu w radianach/s)
      float velocity = (kp * error) + (ki * integral) + (kd * derivative);

      // ZABEZPIECZENIE: Ucinamy prędkość do bezpiecznego limitu z configu
      velocity = constrain(velocity, -maxVelocity, maxVelocity);

      // Zwracamy o ile radianów powinniśmy się przesunąć w tej pojedynczej klatce programu
      return velocity * dt;
    }
};


void setup() {   
  Serial.begin(115200);   
  delay(1000);       
  Serial.println("\n\n>>> SYSTEM BOOT START <<<");   
  
  pinMode(SV_VFB_A, INPUT);   
  pinMode(SV_VFB_B, INPUT);   
  pinMode(SV_CFB_A, INPUT);   
  pinMode(SV_CFB_B, INPUT);   

  // --- INICJALIZACJA SERW ZAMIAST LEDC ---
  // Dobra praktyka: przypisanie timerów dla ESP32Servo
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

// ... (poprzedni kod setupu)
  servoA.setPeriodHertz(50);
  servoA.attach(SV_A_PIN, FRONT_MIN_PULSE, FRONT_MAX_PULSE); // Użyj limitów przodu
  
  servoB.setPeriodHertz(50);
  servoB.attach(SV_B_PIN, REAR_MIN_PULSE, REAR_MAX_PULSE);   // Użyj limitów tyłu
  
  // Ustawienie na pozycję środkową przy starcie
  servoA.writeMicroseconds(FRONT_MID_PULSE);
  servoB.writeMicroseconds(REAR_MID_PULSE);
  // ... (reszta setupu)

  initNetwork();   
  initCAN();   
  Serial.println(">>> SETUP COMPLETE <<<"); 
} // <--- Brakująca klamra zamykająca setup

// --- DEKLARACJA OBIEKTÓW SERWO ---


// Zmienne trzymające faktyczną (wyliczoną) pozycję kół w radianach
float currentSteerRadFront = 0.0f;
float currentSteerRadRear = 0.0f;



// Tworzymy dwa niezależne regulatory (Przód i Tył)
SteerPID pidFront(STEER_KP, STEER_KI, STEER_KD, STEER_MAX_VEL);
SteerPID pidRear(STEER_KP, STEER_KI, STEER_KD, STEER_MAX_VEL);


// --- NOWA FUNKCJA STERUJĄCA ---
void updateServoPID(float targetRad, float &currentRad, SteerPID &pid, Servo &servo, int minPulse, int midPulse, int maxPulse) {
  // 1. Zabezpieczenie celu
  float safeTarget = constrain(targetRad, -MAX_STEER_RAD, MAX_STEER_RAD);
  
  // 2. PID wylicza łagodny przyrost pozycji
  float deltaRad = pid.compute(safeTarget, currentRad);
  currentRad += deltaRad;
  
  // 3. Mapowanie: ułamek maksymalnego wychylenia (od -1.0 do 1.0)
  float normalized = currentRad / MAX_STEER_RAD;
  
  // 4. Konwersja na impulsy z uwzględnieniem asymetrycznego środka (ważne dla przodu!)
  float targetPulse;
  if (normalized >= 0) {
    // Wychylenie w jedną stronę (np. od 1976 do 2643)
    targetPulse = midPulse + (normalized * (maxPulse - midPulse));
  } else {
    // Wychylenie w drugą stronę (np. od 1976 do 1309)
    // Zmienna 'normalized' jest tu ujemna, więc znak sam się dopasuje
    targetPulse = midPulse + (normalized * (midPulse - minPulse)); 
  }
  
  // Zabezpieczenie ostateczne dla serwa
  targetPulse = constrain(targetPulse, minPulse, maxPulse);
  servo.writeMicroseconds((int)targetPulse);
}

void readSensors() {   
  servoVoltageA = (analogRead(SV_VFB_A) * ADC_VREF) / ADC_RES;   
  servoVoltageB = (analogRead(SV_VFB_B) * ADC_VREF) / ADC_RES;   
  
  float rawVoltageCFB_A = (analogRead(SV_CFB_A) * ADC_VREF) / ADC_RES;   
  float rawVoltageCFB_B = (analogRead(SV_CFB_B) * ADC_VREF) / ADC_RES;   
  
  servoCurrentA = (rawVoltageCFB_A - ACS712_OFFSET) / ACS712_SENS;   
  servoCurrentB = (rawVoltageCFB_B - ACS712_OFFSET) / ACS712_SENS; 
} // <--- Brakująca klamra

void loop() {   
  unsigned long now = millis();   
  bool currentMqttState = isMqttConnected();   
  
  if (currentMqttState != lastMqttState || isFirstLoop) {       
      lastMqttState = currentMqttState;       
      isFirstLoop = false;   
  } // <--- Brakująca klamra
  
  if (now - lastMqttCmdTime > SAFETY_TIMEOUT) {     
    if (targetVelocityFront != 0.0f || targetVelocityRear != 0.0f) {       
      Serial.println("!!! WATCHDOG: Utrata polaczenia - STOP !!!");       
      targetVelocityFront = 0.0f;       
      targetVelocityRear = 0.0f;       
      targetSteeringFront = 0.0f;       
      targetSteeringRear = 0.0f;     
    }   
  } // <--- Brakująca klamra
  
  handleNetwork();   
  
// Wewnątrz loop():
  updateServoPID(targetSteeringFront, currentSteerRadFront, pidFront, servoA, FRONT_MIN_PULSE, FRONT_MID_PULSE, FRONT_MAX_PULSE);
  
  updateServoPID(targetSteeringRear, currentSteerRadRear, pidRear, servoB, REAR_MIN_PULSE, REAR_MID_PULSE, REAR_MAX_PULSE);
  
  readSensors();   
  
  static unsigned long lastCanCycle = 0;   
  if (now - lastCanCycle > 50) {     
    lastCanCycle = now;     
    sendVelocity(ODRIVE_FRONT_ID, targetVelocityFront * DIR_FRONT);     
    sendVelocity(ODRIVE_REAR_ID, targetVelocityRear * DIR_REAR);     
    requestEncoderData(ODRIVE_FRONT_ID);     
    requestEncoderData(ODRIVE_REAR_ID);   
  } // <--- Brakująca klamra
  
  handleCANMessages();   
  
  static unsigned long lastMqttPub = 0;   
  if (now - lastMqttPub > MQTT_PUB_INTERVAL) {      
    lastMqttPub = now;     
    sendFeedbackMessage();
  } // <--- Brakująca klamra
} // <--- Brakująca klamra pętli loop