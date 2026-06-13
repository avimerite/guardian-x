/*
  EMO Robot Eyes - Smooth & Curved Edition 🤖👁️
  For ESP32 + 2x 0.96" I2C OLEDs (SSD1306)
  Smooth animations + Rounded curves
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_W 128
#define SCREEN_H 64

TwoWire I2C_L = TwoWire(0);
TwoWire I2C_R = TwoWire(1);

Adafruit_SSD1306 leftEye(SCREEN_W, SCREEN_H, &I2C_L, -1);
Adafruit_SSD1306 rightEye(SCREEN_W, SCREEN_H, &I2C_R, -1);

struct Eye {
  // Smooth movement variables
  float px, py;           // current pupil position
  float tx, ty;           // target pupil position  
  float vx, vy;           // velocity for smooth movement
  float size;             // current pupil size
  float targetSize;       // target pupil size
  
  // Animation states
  bool blinking;
  float blinkProgress;    // 0.0 to 1.0 for smooth blink
  unsigned long lastBlink;
  
  // Emotional state
  int emotion;            // 0=normal, 1=happy, 2=sleepy, 3=surprised, 4=curious, 5=angry
  unsigned long lastEmotionChange;
  unsigned long lastMove;
  
  // Smooth transitions
  float emotionBlend;     // smooth emotion transitions
};

Eye eye;

// EMO Style Constants with rounded curves
const int EMO_EYE_WIDTH = 100;
const int EMO_EYE_HEIGHT = 50;
const int EMO_CORNER_RADIUS = 12;  // Rounded corners!
const int EMO_PUPIL_BASE_SIZE = 12;
const int EMO_PUPIL_MAX_MOVE = 20;

// ===== Smooth EMO Robot Eye =====
void drawSmoothEMOEye(Adafruit_SSD1306 &d, int cx, int cy, bool isLeft) {
  d.clearDisplay();
  
  // Draw EMO rounded screen
  drawRoundedEMOScreen(d, cx, cy);
  
  // Calculate smooth pupil position
  int pupilX = cx + eye.px;
  int pupilY = cy + eye.py;
  
  // Draw smooth EMO pupil
  d.fillCircle(pupilX, pupilY, eye.size, SSD1306_BLACK);
  
  // Smooth reflection dot
  d.fillCircle(pupilX - 3, pupilY - 3, 3, SSD1306_WHITE);
  
  // Smooth blinking
  if (eye.blinkProgress > 0.0) {
    drawSmoothBlink(d, cx, cy);
  }
  
  // Draw emotion effects
  drawSmoothEmotion(d, cx, cy, isLeft);
  
  d.display();
}

void drawRoundedEMOScreen(Adafruit_SSD1306 &d, int cx, int cy) {
  // EMO-style rounded rectangular screen
  int screenLeft = cx - EMO_EYE_WIDTH/2;
  int screenTop = cy - EMO_EYE_HEIGHT/2;
  
  // Main screen with rounded corners
  d.fillRoundRect(screenLeft, screenTop, EMO_EYE_WIDTH, EMO_EYE_HEIGHT, EMO_CORNER_RADIUS, SSD1306_WHITE);
  
  // Smooth border
  d.drawRoundRect(screenLeft, screenTop, EMO_EYE_WIDTH, EMO_EYE_HEIGHT, EMO_CORNER_RADIUS, SSD1306_BLACK);
  d.drawRoundRect(screenLeft+1, screenTop+1, EMO_EYE_WIDTH-2, EMO_EYE_HEIGHT-2, EMO_CORNER_RADIUS, SSD1306_BLACK);
  
  // Inner bezel with rounded corners
  d.drawRoundRect(screenLeft+3, screenTop+3, EMO_EYE_WIDTH-6, EMO_EYE_HEIGHT-6, EMO_CORNER_RADIUS-2, SSD1306_BLACK);
}

void drawSmoothBlink(Adafruit_SSD1306 &d, int cx, int cy) {
  int screenLeft = cx - EMO_EYE_WIDTH/2;
  int screenTop = cy - EMO_EYE_HEIGHT/2;
  
  // Smooth blink animation using progress
  float blinkHeight = EMO_EYE_HEIGHT * eye.blinkProgress;
  
  // Top eyelid (rounded)
  d.fillRoundRect(screenLeft, screenTop, EMO_EYE_WIDTH, blinkHeight/2, EMO_CORNER_RADIUS/2, SSD1306_BLACK);
  
  // Bottom eyelid (rounded)
  d.fillRoundRect(screenLeft, cy + EMO_EYE_HEIGHT/2 - blinkHeight/2, EMO_EYE_WIDTH, blinkHeight/2, EMO_CORNER_RADIUS/2, SSD1306_BLACK);
}

void drawSmoothEmotion(Adafruit_SSD1306 &d, int cx, int cy, bool isLeft) {
  int screenTop = cy - EMO_EYE_HEIGHT/2 - 8;
  
  // Smooth emotion transitions
  float blend = eye.emotionBlend;
  
  switch(eye.emotion) {
    case 1: // Happy - smooth ^^ eyebrows
      {
        int startY = screenTop;
        int endY = screenTop - 3;
        for(int x = -25; x <= -10; x++) {
          float t = (x + 25) / 15.0;
          int y = startY + (endY - startY) * t;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
        for(int x = 10; x <= 25; x++) {
          float t = (x - 10) / 15.0;
          int y = startY + (endY - startY) * t;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
      }
      break;
      
    case 2: // Sleepy - smooth eyelids
      if (!eye.blinking) {
        float closeAmount = 0.3 + 0.4 * sin(millis() * 0.002); // breathing effect
        d.fillRoundRect(cx-EMO_EYE_WIDTH/2, cy-EMO_EYE_HEIGHT/2, EMO_EYE_WIDTH, EMO_EYE_HEIGHT * closeAmount, EMO_CORNER_RADIUS/2, SSD1306_BLACK);
      }
      break;
      
    case 3: // Surprised - smooth OO
      {
        int startY = screenTop - 5;
        int endY = screenTop - 8;
        for(int x = -30; x <= -15; x++) {
          float t = (x + 30) / 15.0;
          int y = startY + (endY - startY) * t;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
        for(int x = 15; x <= 30; x++) {
          float t = (x - 15) / 15.0;
          int y = startY + (endY - startY) * t;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
      }
      break;
      
    case 4: // Curious - smooth ><
      {
        // Left eyebrow - downward slope
        for(int x = -30; x <= -15; x++) {
          int y = screenTop + (x + 30) * 0.13;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
        // Right eyebrow - downward slope
        for(int x = 15; x <= 30; x++) {
          int y = screenTop + (30 - x) * 0.13;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
      }
      break;
      
    case 5: // Angry - smooth VV
      {
        // Left eyebrow - V shape
        for(int x = -28; x <= -12; x++) {
          int y = screenTop + 2 - abs(x + 20) * 0.3;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
        // Right eyebrow - V shape
        for(int x = 12; x <= 28; x++) {
          int y = screenTop + 2 - abs(x - 20) * 0.3;
          d.drawPixel(cx + x, y, SSD1306_BLACK);
        }
      }
      break;
  }
  
  // Smooth Zzz animation for sleepy
  if (eye.emotion == 2 && random(0, 100) < 8) {
    float wave = sin(millis() * 0.005) * 2;
    d.setCursor(cx-8 + wave, cy+EMO_EYE_HEIGHT/2+5);
    d.setTextSize(1);
    d.print("zZz");
  }
}

// ===== Setup =====
void setup() {
  Serial.begin(115200);
  I2C_L.begin(21, 22);
  I2C_R.begin(17, 16);

  leftEye.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  rightEye.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  leftEye.clearDisplay();
  rightEye.clearDisplay();
  leftEye.display();
  rightEye.display();

  // Initialize smooth EMO robot eye
  eye.px = eye.py = 0;
  eye.tx = eye.ty = 0;
  eye.vx = eye.vy = 0;
  eye.size = EMO_PUPIL_BASE_SIZE;
  eye.targetSize = EMO_PUPIL_BASE_SIZE;
  eye.blinking = false;
  eye.blinkProgress = 0.0;
  eye.lastBlink = millis();
  eye.emotion = 0;
  eye.lastEmotionChange = millis();
  eye.lastMove = millis();
  eye.emotionBlend = 1.0;

  Serial.println("Smooth EMO Robot Eyes Ready! 🤖");
  Serial.println("Commands: 0-5 emotions, b=blink");
  Serial.println("0=Normal, 1=Happy, 2=Sleepy, 3=Surprised, 4=Curious, 5=Angry");
}

// ===== Main Loop =====
void loop() {
  unsigned long now = millis();
  
  checkSerialCommands();
  updateSmoothBehavior(now);

  // Draw both smooth EMO eyes
  drawSmoothEMOEye(leftEye, SCREEN_W/2, SCREEN_H/2, true);
  drawSmoothEMOEye(rightEye, SCREEN_W/2, SCREEN_H/2, false);

  delay(33); // ~30fps for smooth animations
}

void updateSmoothBehavior(unsigned long now) {
  // === Smooth Pupil Movement ===
  if (now - eye.lastMove > random(2500, 6000)) {
    eye.lastMove = now;
    
    // Smooth target changes
    eye.tx = random(-EMO_PUPIL_MAX_MOVE, EMO_PUPIL_MAX_MOVE);
    eye.ty = random(-EMO_PUPIL_MAX_MOVE/2, EMO_PUPIL_MAX_MOVE/2);
  }

  // Smooth acceleration toward target
  float ax = (eye.tx - eye.px) * 0.1;
  float ay = (eye.ty - eye.py) * 0.1;
  
  eye.vx += ax;
  eye.vy += ay;
  
  // Smooth damping
  eye.vx *= 0.85;
  eye.vy *= 0.85;
  
  // Update position
  eye.px += eye.vx;
  eye.py += eye.vy;

  // Soft constraints
  if (abs(eye.px) > EMO_PUPIL_MAX_MOVE) {
    eye.px = constrain(eye.px, -EMO_PUPIL_MAX_MOVE, EMO_PUPIL_MAX_MOVE);
    eye.vx *= -0.3; // gentle bounce
  }
  if (abs(eye.py) > EMO_PUPIL_MAX_MOVE/2) {
    eye.py = constrain(eye.py, -EMO_PUPIL_MAX_MOVE/2, EMO_PUPIL_MAX_MOVE/2);
    eye.vy *= -0.3; // gentle bounce
  }

  // === Smooth Emotion Transitions ===
  if (now - eye.lastEmotionChange > random(10000, 20000)) {
    eye.lastEmotionChange = now;
    int newEmotion = random(0, 6);
    if (newEmotion != eye.emotion) {
      eye.emotion = newEmotion;
      eye.emotionBlend = 0.0; // start blend
    }
  }

  // Smooth emotion blending
  if (eye.emotionBlend < 1.0) {
    eye.emotionBlend += 0.02;
    if (eye.emotionBlend > 1.0) eye.emotionBlend = 1.0;
  }

  // === Smooth Pupil Size Changes ===
  switch(eye.emotion) {
    case 0: eye.targetSize = EMO_PUPIL_BASE_SIZE; break;
    case 1: eye.targetSize = EMO_PUPIL_BASE_SIZE - 2; break;
    case 2: eye.targetSize = EMO_PUPIL_BASE_SIZE - 4; break;
    case 3: eye.targetSize = EMO_PUPIL_BASE_SIZE + 4; break;
    case 4: eye.targetSize = EMO_PUPIL_BASE_SIZE + 2; break;
    case 5: eye.targetSize = EMO_PUPIL_BASE_SIZE - 3; break;
  }
  
  // Smooth size interpolation
  eye.size += (eye.targetSize - eye.size) * 0.1;

  // === Smooth Blinking ===
  if (!eye.blinking && now - eye.lastBlink > random(4000, 8000)) {
    eye.blinking = true;
    eye.blinkProgress = 0.0;
    eye.lastBlink = now;
  }

  // Smooth blink animation
  if (eye.blinking) {
    eye.blinkProgress += 0.08;
    
    if (eye.blinkProgress >= 1.0) {
      eye.blinking = false;
      eye.blinkProgress = 0.0;
    }
  }

  // === Micro-expressions ===
  if (random(0, 200) == 0) {
    // Quick glance around
    eye.tx += random(-5, 6);
    eye.ty += random(-3, 4);
  }
}

void checkSerialCommands() {
  if (Serial.available()) {
    char cmd = Serial.read();
    
    // Emotion commands 0-5
    if (cmd >= '0' && cmd <= '5') {
      int newEmotion = cmd - '0';
      if (newEmotion != eye.emotion) {
        eye.emotion = newEmotion;
        eye.emotionBlend = 0.0; // start smooth transition
      }
      Serial.print("EMO Emotion: ");
      switch(eye.emotion) {
        case 0: Serial.println("Normal"); break;
        case 1: Serial.println("Happy ^^"); break;
        case 2: Serial.println("Sleepy zZz"); break;
        case 3: Serial.println("Surprised OO"); break;
        case 4: Serial.println("Curious ><"); break;
        case 5: Serial.println("Angry VV"); break;
      }
    }
    
    // Manual smooth blink
    if (cmd == 'b' || cmd == 'B') {
      eye.blinking = true;
      eye.blinkProgress = 0.0;
      eye.lastBlink = millis();
      Serial.println("Smooth blink!");
    }
    
    // Look directions with smooth movement
    if (cmd == 'w' || cmd == 'W') { 
      eye.tx = 0; 
      eye.ty = -15; 
      Serial.println("Look up"); 
    }
    if (cmd == 's' || cmd == 'S') { 
      eye.tx = 0; 
      eye.ty = 15; 
      Serial.println("Look down"); 
    }
    if (cmd == 'a' || cmd == 'A') { 
      eye.tx = -15; 
      eye.ty = 0; 
      Serial.println("Look left"); 
    }
    if (cmd == 'd' || cmd == 'D') { 
      eye.tx = 15; 
      eye.ty = 0; 
      Serial.println("Look right"); 
    }
    if (cmd == 'c' || cmd == 'C') { 
      eye.tx = 0; 
      eye.ty = 0; 
      Serial.println("Center"); 
    }
  }
}