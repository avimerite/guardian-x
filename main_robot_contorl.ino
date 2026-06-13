#include <Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// ========== LCD ==========
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ========== DHT Sensor ==========
#define DHTPIN 13
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ========== MQ135 ==========
#define MQ135_PIN A0

// ========== Ultrasonic ==========
#define TRIG 11
#define ECHO 12

// ========== Motor Driver (L298N) ==========
#define IN1 7
#define IN2 6
#define IN3 5
#define IN4 4

// ========== Servos ==========
Servo servo1;  // Left Arm
Servo servo2;  // Left Elbow
Servo servo3;  // Right Arm
Servo servo4;  // Right Elbow
Servo servo5;  // Head

int servo1Pin = 2;
int servo2Pin = 3;
int servo3Pin = 8;
int servo4Pin = 9;
int servo5Pin = 10;

// ========== Variables ==========
bool obstacleMode = false;
bool gestureMode = false;
unsigned long lastSensorRead = 0;
unsigned long lastLCDUpdate = 0;
unsigned long lastDistanceRead = 0;
const unsigned long SENSOR_INTERVAL = 1000;    // 1 second
const unsigned long LCD_INTERVAL = 500;        // 500ms
const unsigned long DISTANCE_INTERVAL = 80;    // 80ms

int lastDistance = 0;
float lastTemp = 0;
float lastHum = 0;
int lastAir = 0;

// Obstacle avoidance variables
int searchState = 0; // 0=forward, 1=search left, 2=search right, 3=backward
unsigned long lastSearchChange = 0;
const unsigned long SEARCH_DELAY = 800; // Time to search in each direction

// ==============================================================
// SETUP - OPTIMIZED FOR SPEED
// ==============================================================
void setup() {
  Serial.begin(115200);
  
  // Fast LCD initialization
  Wire.begin();
  lcd.init();
  lcd.backlight();
  lcd.clear();
  
  // Fast pin setup
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(MQ135_PIN, INPUT);
  
  // Motor pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Initialize motors to STOP
  stopMotors();

  // Fast servo attachment
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  servo3.attach(servo3Pin);
  servo4.attach(servo4Pin);
  servo5.attach(servo5Pin);

  // Initialize servos to center
  servo1.write(90);
  servo2.write(90);
  servo3.write(90);
  servo4.write(90);
  servo5.write(90);

  // Initialize DHT
  dht.begin();

  // Quick startup
  lcd.setCursor(0, 0);
  lcd.print("Robot Revery");
  lcd.setCursor(0, 1);
  lcd.print("Ready!");
  delay(800);
  lcd.clear();
  
  Serial.println("READY: High Speed Mode");
}

// ==============================================================
// LOOP - MAXIMUM SPEED
// ==============================================================
void loop() {
  unsigned long currentTime = millis();
  
  // Ultra-fast distance reading
  if (currentTime - lastDistanceRead >= DISTANCE_INTERVAL) {
    lastDistance = getDistance();
    lastDistanceRead = currentTime;
  }

  // Fast sensor reading
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = currentTime;
  }

  // Fast LCD updates - SINGLE PAGE ONLY
  if (currentTime - lastLCDUpdate >= LCD_INTERVAL) {
    updateLCD();
    lastLCDUpdate = currentTime;
  }

  // Smart obstacle mode with search behavior
  if (obstacleMode) {
    handleSmartObstacleMode();
  }

  // Instant command processing
  if (Serial.available()) {
    serialEvent();
  }
  
  delay(10); // Minimal delay for maximum speed
}

// ==============================================================
// SINGLE LCD STATUS PAGE WITH HUMIDITY AND AIR QUALITY
// ==============================================================
void updateLCD() {
  // Clear and display single status page
  lcd.clear();
  
  // Line 1: Temperature and Humidity
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(lastTemp, 1);
  lcd.print("C H:");
  lcd.print(lastHum, 0);
  lcd.print("%");
  
  // Line 2: Air Quality and Distance
  lcd.setCursor(0, 1);
  lcd.print("A:");
  lcd.print(lastAir);
  lcd.print(" D:");
  lcd.print(lastDistance);
  lcd.print("cm");
  
  // Add mode indicator with symbols
  lcd.setCursor(14, 0);
  if (obstacleMode) {
    lcd.print("O");
  } else if (gestureMode) {
    lcd.print("G");
  } else {
    lcd.print("M");
  }
}

// ==============================================================
// SENSOR READING - MAXIMUM SPEED
// ==============================================================
void readSensors() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  int air = analogRead(MQ135_PIN);

  // Quick validation
  if (!isnan(t) && !isnan(h)) {
    lastTemp = t;
    lastHum = h;
  }
  lastAir = air;

  // Always send complete sensor data for low latency
  sendSensorData(lastTemp, lastHum, lastAir, lastDistance);
}

// ==============================================================
// SEND COMPLETE SENSOR DATA VIA SERIAL
// ==============================================================
void sendSensorData(float t, float h, int air, int dist) {
  Serial.print("SENSOR_DATA,");
  Serial.print(t);        // Temperature
  Serial.print(",");
  Serial.print(h);        // Humidity
  Serial.print(",");
  Serial.print(air);      // Air quality
  Serial.print(",");
  Serial.println(dist);   // Distance
}

// ==============================================================
// ULTRASONIC - MAXIMUM SPEED
// ==============================================================
int getDistance() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(5);  // Shorter pulse for speed
  digitalWrite(TRIG, LOW);
  
  long duration = pulseIn(ECHO, HIGH, 20000); // Shorter timeout: 20ms
  
  if (duration == 0) return 999;
  
  int distance = duration * 0.034 / 2;
  
  // Fast filtering
  static int lastValidDistance = 100;
  if (distance > 400 || distance < 2) {
    return lastValidDistance;
  }
  
  // Quick smoothing
  lastValidDistance = (lastValidDistance + distance) / 2;
  return lastValidDistance;
}

// ==============================================================
// SMART OBSTACLE AVOIDANCE WITH SEARCH BEHAVIOR
// ==============================================================
void handleSmartObstacleMode() {
  unsigned long currentTime = millis();
  
  // Define distance thresholds
  const int DANGER_DISTANCE = 15;    // Too close - immediate stop
  const int WARNING_DISTANCE = 37;   // Start searching at 37cm
  const int SAFE_DISTANCE = 60;      // All clear
  
  // Check for immediate danger
  if (lastDistance < DANGER_DISTANCE && lastDistance > 0) {
    stopMotors();
    searchState = 3; // Go to backward state
    lastSearchChange = currentTime;
    Serial.println("🚨 DANGER: Too close! Moving backward");
    return;
  }
  
  // State machine for obstacle avoidance
  switch (searchState) {
    case 0: // Moving forward
      if (lastDistance < WARNING_DISTANCE && lastDistance > 0) {
        // Obstacle detected at 37cm, start searching
        stopMotors();
        delay(200);
        searchState = 1; // Start searching left
        lastSearchChange = currentTime;
        Serial.println("⚠️ Obstacle at 37cm - Searching left");
      } else {
        moveForward(); // All clear, keep moving
      }
      break;
      
    case 1: // Searching left
      moveLeft();
      if (currentTime - lastSearchChange > SEARCH_DELAY) {
        // Check if path is clear after searching left
        if (lastDistance > SAFE_DISTANCE) {
          searchState = 0; // Path clear, resume forward
          Serial.println("✅ Left path clear - Moving forward");
        } else {
          searchState = 2; // Try searching right
          lastSearchChange = currentTime;
          Serial.println("❌ Left blocked - Searching right");
        }
      }
      break;
      
    case 2: // Searching right
      moveRight();
      if (currentTime - lastSearchChange > SEARCH_DELAY) {
        // Check if path is clear after searching right
        if (lastDistance > SAFE_DISTANCE) {
          searchState = 0; // Path clear, resume forward
          Serial.println("✅ Right path clear - Moving forward");
        } else {
          searchState = 3; // Both sides blocked, go backward
          lastSearchChange = currentTime;
          Serial.println("❌ Both sides blocked - Moving backward");
        }
      }
      break;
      
    case 3: // Moving backward
      moveBackward();
      if (currentTime - lastSearchChange > 1000) { // Back up for 1 second
        searchState = 1; // Try searching left again
        lastSearchChange = currentTime;
        Serial.println("🔄 Backed up - Searching left again");
      }
      break;
  }
}

// ==============================================================
// MOTOR CONTROL - HIGH SPEED
// ==============================================================
void moveForward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void moveBackward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void moveLeft() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void moveRight() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

// ==============================================================
// SERIAL COMMAND HANDLER - MINIMUM LATENCY
// ==============================================================
void serialEvent() {
  while (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();
    
    if (data.length() == 0) continue;

    // Ultra-fast command processing
    if (data.startsWith("MOVE")) {
      char direction = data.charAt(5);
      switch (direction) {
        case 'F': moveForward(); Serial.println("MOVING:F"); break;
        case 'B': moveBackward(); Serial.println("MOVING:B"); break;
        case 'L': moveLeft(); Serial.println("MOVING:L"); break;
        case 'R': moveRight(); Serial.println("MOVING:R"); break;
        case 'S': stopMotors(); Serial.println("MOVING:S"); break;
        default: Serial.println("ERROR:Bad direction"); break;
      }
    }
    else if (data.startsWith("SERVO")) {
      int commaIndex = data.indexOf(',');
      if (commaIndex > 0) {
        int id = data.substring(5, commaIndex).toInt();
        int angle = data.substring(commaIndex + 1).toInt();
        if (angle >= 0 && angle <= 180) {
          setServo(id, angle);
          Serial.print("SERVO:");
          Serial.print(id);
          Serial.print("=");
          Serial.println(angle);
        }
      }
    }
    else if (data.startsWith("MODE")) {
      if (data.indexOf("OBSTACLE") > 0) {
        obstacleMode = true;
        gestureMode = false;
        searchState = 0; // Reset search state
        Serial.println("MODE:OBSTACLE");
      } else if (data.indexOf("GESTURE") > 0) {
        gestureMode = true;
        obstacleMode = false;
        stopMotors();
        Serial.println("MODE:GESTURE");
      } else if (data.indexOf("MANUAL") > 0) {
        obstacleMode = false;
        gestureMode = false;
        stopMotors();
        Serial.println("MODE:MANUAL");
      }
    }
    else if (data == "TEST") {
      // Quick test
      moveForward(); delay(150); stopMotors(); 
      moveLeft(); delay(150); stopMotors();
      Serial.println("TEST:OK");
    }
    else if (data == "STATUS") {
      Serial.print("STATUS:READY MODE:");
      if (obstacleMode) Serial.print("OBSTACLE");
      else if (gestureMode) Serial.print("GESTURE");
      else Serial.print("MANUAL");
      Serial.print(" SEARCH:");
      Serial.println(searchState);
    }
    else if (data == "DISTANCE") {
      Serial.println(lastDistance);
    }
    else if (data == "GET_SENSORS") {
      // Send current sensor data on demand
      sendSensorData(lastTemp, lastHum, lastAir, lastDistance);
    }
    else if (data == "GET_HUMIDITY") {
      Serial.println(lastHum);
    }
    else if (data == "GET_TEMPERATURE") {
      Serial.println(lastTemp);
    }
    else if (data == "GET_AIR_QUALITY") {
      Serial.println(lastAir);
    }
    else {
      Serial.println("ERROR:Unknown");
    }
  }
}

// ==============================================================
// SERVO CONTROL - HIGH SPEED
// ==============================================================
void setServo(int id, int angle) {
  switch (id) {
    case 1: servo1.write(angle); break;
    case 2: servo2.write(angle); break;
    case 3: servo3.write(angle); break;
    case 4: servo4.write(angle); break;
    case 5: servo5.write(angle); break;
  }
  delay(5); // Minimal delay for maximum speed
}