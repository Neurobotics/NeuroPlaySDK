// (C) 2024 Neurobotics LLC
// Authors: Dmitry Konyshev <d.konyshev@neurobotics.ru>

// THIS IS AN EXAMPLE OF RICH COMMAND PARSING
// To use this example NeuroPlayPro app should be installed
// This app has capability to answer to queries via COM-port
// This example shows rich exchange - the full output of commands (see NeuroPlayPro API)
// To enable exchange see NeuroPlayPro -> Settings (activate Advanced) -> Exchange -> Enable COM-port
// Use the 'Server-like' mode


// (C) 2024 Нейроботикс
// Автор: Дмитрий Конышев <d.konyshev@neurobotics.ru>

// ЭТОТ ПРИМЕР ИСПОЛЬЗУЕТ РАЗБОР ПОЛНЫХ КОМАНД
// Для использвания этого примера необходимо установить приложение NeuroPlayPro
// Это приложение имеет возможность отвечать на запросы посредством COM-порта.
// Этот пример показывает полноценный способ связи - обработку всего содержимого команд (см. NeuroPlayPro API)
// Для включения общения см. NeuroPlayPro -> Настройки (включите Расширенные) -> Обмен -> Включить COM-порт
// Используйте режим 'Как сервер'

#include <Servo.h>

const uint8_t LED_PIN = LED_BUILTIN;

// Change SERVO_PIN and MIN/MAX to actual values
const uint8_t SERVO_PIN = 6;
const int SERVO_MIN_VALUE = 1000;
const int SERVO_MAX_VALUE = 1800;
Servo servo1;

// Incoming message container
String message = "";

void setup() {
  Serial.begin(115200);

  // Enable LED pin
  pinMode(LED_PIN, OUTPUT);

  // Enable servo
  servo1.attach(SERVO_PIN);
}

long long timestamp = 0;

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    // Skip special symbols
    if (c == '\r' || c == '\n' || c == '{' || c == '"' || c == ' ') continue;
    
    // Wait for the ending bracket
    if (c == '}') {
      int meditationPos = message.indexOf("meditation");
      if (meditationPos >= 0) {
          // Parse the JSON
          meditationPos += 11;
          int commaPos = message.indexOf(",", meditationPos);
          String num = message.substring(meditationPos, commaPos);
          
          // The 'meditation' value
          int meditation = num.toInt();
          if (meditation < 0) meditation = 0;
          else if (meditation > 100) meditation = 100;

          // Activate the LED if meditation is above 50%
          digitalWrite(LED_BUILTIN, meditation > 50 ? HIGH : LOW);

          int pulse = SERVO_MIN_VALUE + 100 * (SERVO_MAX_VALUE - SERVO_MIN_VALUE) / (100 - meditation);
          // Activate the servo
          if (servo1.attached()) {            
            servo1.writeMicroseconds(pulse);
          }
      }
      
      message = "";
    } else {
      // Append next character
      message += c;
    }
  }
  
  long long ts = millis();

  // Ask NeuroPlayPro for values every second
  if (ts - timestamp > 250) {
    timestamp = ts;
    Serial.print("meditation?less");
    // In this example only 'meditation' is required
    // Use 'bci' which gives { meditation: X, concentration: X, attention: X, mental_state: X }
    // Or use any other command from NeuroPlayPro API
    // NOTE: Strings are a bit messy in Arduino
  }  
  delay(10); 
}
