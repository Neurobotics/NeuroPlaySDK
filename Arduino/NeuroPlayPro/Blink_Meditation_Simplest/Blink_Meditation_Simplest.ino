// (C) 2024 Neurobotics LLC
// Author: Dmitry Konyshev <d.konyshev@neurobotics.ru>

// THIS IS AN EXAMPLE WHERE NEUROPLAYPRO PUSHES DATA TO COM-PORT
// To use this example NeuroPlayPro app should be installed
// This app has capability push meditation/concentration values and mental state index via COM-port
// In this example exchange consists of listening to COM-port input.
// To enable exchange see NeuroPlayPro -> Settings (activate Advanced) -> Exchange -> Enable COM-port
// Use the 'Send as number' mode.
// All values emitted from NeuroPlayPro consist of one byte.


// (C) 2024 Нейроботикс
// Автор: Дмитрий Конышев <d.konyshev@neurobotics.ru>

// В ЭТОМ ПРИМЕРЕ РАССМОТРЕН СЛУЧАЙ, КОГДА NEUROPLAYPRO САМ ОТПРАВЛЯЕТ ЗНАЧЕНИЯ В COM-ПОРТ
// Для использвания этого примера необходимо установить приложение NeuroPlayPro
// Это приложение имеет возможность отправлять значения медитации, концентрации и ментальных состояний в COM-порт.
// Этот пример показывает способ связи, когда необходимо лишь считывать значения, поступающие в COM-порт.
// Для включения общения см. NeuroPlayPro -> Настройки (включите Расширенные) -> Обмен -> Включить COM-порт
// Используйте режим 'Отправлять числа'.
// Все отправляемые из NeuroPlayPro числа умещяются в один байт.

#include <Servo.h>

const uint8_t LED_PIN = LED_BUILTIN;

// Change SERVO_PIN and MIN/MAX to actual values
const uint8_t SERVO_PIN = 6;
const int SERVO_MIN_VALUE = 1000;
const int SERVO_MAX_VALUE = 1800;
Servo servo1;

void setup() {
  Serial.begin(115200);

  // Enable LED pin
  pinMode(LED_PIN, OUTPUT);

  // Enable servo
  servo1.attach(SERVO_PIN);
}

void loop() {
  if (Serial.available() > 0) {
    int c = Serial.read();

    // The value is a number 0-100% in case of meditation/concentration or 0-8 in case of mental states
    // Considering that the value is meditation (see Value output)
          
    // The 'meditation' value 
    int meditation = c;
    if (meditation < 0) meditation = 0;
    else if (meditation > 100) meditation = 100;

    // Activate the LED if meditation is above 50%
    digitalWrite(LED_BUILTIN, meditation > 50 ? HIGH : LOW);

    int pulse = SERVO_MIN_VALUE;
    if (meditation != 0) pulse += 100 * (SERVO_MAX_VALUE - SERVO_MIN_VALUE) / (meditation);
    // Activate the servo
    if (servo1.attached()) servo1.writeMicroseconds(pulse);
  }   
  
  delay(10); 
}
