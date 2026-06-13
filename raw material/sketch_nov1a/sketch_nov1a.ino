/*
  Cartoon Eyes v4 – Emotion Engine Edition 👁️💫
  For ESP32 + 2x 0.96" I2C OLEDs (SSD1306)
  Author: Custom made for Avinash’s robot
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
  float px, py;      // pupil position
  float tx, ty;      // target
  float size, tsize; // pupil size
  bool blink;
  int blinkPos;
  unsigned long lastBlink;
  unsigned long lastMove;
  unsigned long lastMood;
  int mood; // 0=normal,1=happy,2=sleepy,3=surprised,4=curious
};

Eye eye;

// ===== Helper: draw single cartoon eye =====
void drawEye(Adafruit_SSD1306 &d, int cx, int cy, float px, float py, float ps, int blink, int mood) {
  d.clearDisplay();

  // Base eye white
  d.fillCircle(cx, cy, 32, SSD1306_WHITE);
  d.drawCircle(cx, cy, 32, SSD1306_BLACK);

  // Blink effect
  int cover = map(blink, 0, 100, 0, 32);
  if (cover > 0) {
    d.fillRect(0, 0, SCREEN_W, cover, SSD1306_BLACK);
    d.fillRect(0, SCREEN_H - cover, SCREEN_W, cover, SSD1306_BLACK);
  }

  // Adjust based on mood
  int offsetY = 0;
  if (mood == 1) offsetY = 3;         // happy - pupil lower
  if (mood == 2) offsetY = -5;        // sleepy - pupil higher
  if (mood == 3) ps = ps - 3;         // surprised - small pupil
  if (mood == 4) ps = ps + 1.5;       // curious - slightly bigger

  // Pupil
  d.fillCircle(cx + px, cy + py + offsetY, ps, SSD1306_BLACK);

  // Shine dot
  static int twinkle = 0;
  twinkle = (twinkle + 1) % 40;
  int shineR = (twinkle < 20) ? 3 : 2;
  d.fillCircle(cx + px - 5, cy + py - 5, shineR, SSD1306_WHITE);

  // Happy smile (simple line)
  if (mood == 1 && blink < 50) {
    d.drawLine(cx - 12, cy + 20, cx + 12, cy + 20, SSD1306_BLACK);
  }

  // Sleepy eyelid
  if (mood == 2 && !eye.blink) {
    d.fillRect(0, 0, SCREEN_W, 12, SSD1306_BLACK);
  }

  d.display();
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

  eye.px = eye.py = 0;
  eye.tx = eye.ty = 0;
  eye.size = 11;
  eye.tsize = 11;
  eye.blink = false;
  eye.blinkPos = 0;
  eye.lastBlink = millis();
  eye.lastMove = millis();
  eye.lastMood = millis();
  eye.mood = 0;
}

// ===== Loop =====
void loop() {
  unsigned long now = millis();

  // Random pupil movement
  if (now - eye.lastMove > random(1500, 3000)) {
    eye.lastMove = now;
    eye.tx = random(-10, 10);
    eye.ty = random(-6, 6);
  }

  // Random pupil dilation
  if (random(0, 100) < 2) eye.tsize = random(8, 14);

  // Random mood change
  if (now - eye.lastMood > random(6000, 12000)) {
    eye.lastMood = now;
    eye.mood = random(0, 5);
  }

  // Random blink
  if (!eye.blink && now - eye.lastBlink > random(2500, 6000)) {
    eye.blink = true;
    eye.blinkPos = 0;
  }

  if (eye.blink) {
    eye.blinkPos += 8;
    if (eye.blinkPos >= 200) {
      eye.blink = false;
      eye.blinkPos = 0;
      eye.lastBlink = now;
    }
  }

  int blinkAmt = eye.blinkPos <= 100 ? eye.blinkPos : 200 - eye.blinkPos;

  // Smooth movement
  eye.px += (eye.tx - eye.px) * 0.15;
  eye.py += (eye.ty - eye.py) * 0.15;
  eye.size += (eye.tsize - eye.size) * 0.1;

  // Render both eyes (mirrored)
  drawEye(leftEye, SCREEN_W/2, SCREEN_H/2, eye.px, eye.py, eye.size, blinkAmt, eye.mood);
  drawEye(rightEye, SCREEN_W/2, SCREEN_H/2, -eye.px, eye.py, eye.size, blinkAmt, eye.mood);

  delay(25);
}
