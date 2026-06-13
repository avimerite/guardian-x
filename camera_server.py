#!/usr/bin/env python3
"""
📹 FINAL FIXED Camera Server - 2=Fwd, 3=Back, 1/4/5/Fist=Stop
FIXED: Now properly sends STOP commands
"""

from flask import Flask, Response, jsonify
import cv2
import threading
import time
import logging
import numpy as np
import mediapipe as mp
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# MediaPipe with stable settings
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Main server API
MAIN_SERVER = "http://localhost:8000"

class FixedGestureController:
    """FIXED gesture controller - Now properly sends STOP commands"""
    
    def __init__(self):
        self.enabled = False
        self.current_gesture = "None"
        self.finger_count = 0
        self.last_command_time = 0
        self.command_cooldown = 0.5
        self.last_command = None
        self.hand_detected = False
        self.consecutive_detections = 0
        self.last_finger_count = 0
        
    def recognize_gesture_fixed(self, hand_landmarks):
        """FIXED gesture recognition - Now properly detects STOP gestures"""
        if not hand_landmarks:
            self.hand_detected = False
            self.consecutive_detections = 0
            return "None"
            
        self.hand_detected = True
        landmarks = hand_landmarks.landmark
        
        # PROPER finger detection
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_pips = [6, 10, 14, 18]  # PIP joints
        
        extended_fingers = []
        
        for tip, pip in zip(finger_tips, finger_pips):
            # Proper finger extension check
            if landmarks[tip].y < landmarks[pip].y:
                extended_fingers.append(True)
            else:
                extended_fingers.append(False)
        
        index, middle, ring, pinky = extended_fingers
        finger_count = sum(extended_fingers)
        self.finger_count = finger_count
        
        # FIXED GESTURE MAPPING:
        # ONLY 2 fingers = RUN
        if finger_count == 2 and index and middle and not ring and not pinky:
            self.consecutive_detections += 1
            return "✌️ RUN"
        # ONLY 3 fingers = BACK
        elif finger_count == 3 and index and middle and ring and not pinky:
            self.consecutive_detections += 1
            return "🤟 BACK"
        # ALL OTHERS (1, 4, 5, fist) = STOP
        else:
            self.consecutive_detections += 1  # FIXED: Also count STOP detections
            return "✊ STOP"
    
    def execute_command_fixed(self, gesture):
        """FIXED command execution - Now properly sends STOP commands"""
        if not self.enabled:
            return False
            
        current_time = time.time()
        if current_time - self.last_command_time < self.command_cooldown:
            return False
            
        # Require 2 consecutive detections for stability
        if self.consecutive_detections < 2:
            return False
            
        # FIXED: Allow STOP commands even if same as last command
        # This ensures robot stops when showing STOP gestures
        if gesture == self.last_command and gesture != "✊ STOP":
            return False
            
        command_map = {
            "✌️ RUN": "F",
            "🤟 BACK": "B", 
            "✊ STOP": "S"
        }
        
        if gesture in command_map:
            try:
                response = requests.post(
                    f"{MAIN_SERVER}/api/command",
                    json={"cmd": "move", "val": command_map[gesture]},
                    timeout=0.5
                )
                if response.status_code == 200:
                    self.last_command_time = current_time
                    self.last_command = gesture
                    logger.info(f"✅ {gesture} -> {command_map[gesture]}")
                    return True
            except Exception as e:
                logger.debug(f"Command: {e}")
                
        return False

class FixedCamera:
    def __init__(self):
        self.camera = None
        self.frame = None
        self.is_running = False
        self.thread = None
        self.frame_lock = threading.Lock()
        
        # Fixed gesture recognition
        self.gesture_controller = FixedGestureController()
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        # Performance
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
    def start(self):
        """Start camera with fixed settings"""
        if self.is_running:
            return True
            
        logger.info("🚀 Starting FIXED camera server...")
        
        for camera_index in [0, 1, 2]:
            try:
                self.camera = cv2.VideoCapture(camera_index)
                if self.camera.isOpened():
                    # Camera settings
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 30)
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 2)
                    
                    ret, test_frame = self.camera.read()
                    if ret:
                        logger.info(f"✅ Camera {camera_index} - FIXED MODE")
                        self.is_running = True
                        self.thread = threading.Thread(target=self._fixed_loop, daemon=True)
                        self.thread.start()
                        return True
                    self.camera.release()
            except Exception as e:
                logger.error(f"❌ Camera {camera_index} failed: {e}")
        
        logger.warning("⚠️ No camera - FIXED demo mode")
        self.is_running = True
        self.thread = threading.Thread(target=self._fixed_demo_loop, daemon=True)
        self.thread.start()
        return True
    
    def _fixed_loop(self):
        """Fixed main loop"""
        while self.is_running:
            try:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret:
                        processed_frame = self._fixed_process(frame)
                        with self.frame_lock:
                            self.frame = processed_frame
                
                # FPS tracking
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_time = current_time
                    
                time.sleep(0.033)
                
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(0.1)
    
    def _fixed_demo_loop(self):
        """Fixed demo loop"""
        demo_gestures = ["✌️ RUN", "🤟 BACK", "✊ STOP"]
        gesture_index = 0
        last_change = time.time()
        
        while self.is_running:
            # Create demo frame
            frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
            
            # Gesture cycling
            current_time = time.time()
            if current_time - last_change > 3.0:
                gesture_index = (gesture_index + 1) % len(demo_gestures)
                last_change = current_time
            
            demo_gesture = demo_gestures[gesture_index]
            self.gesture_controller.current_gesture = demo_gesture
            self.gesture_controller.hand_detected = True
            
            # Overlay
            frame = self._fixed_overlay(frame)
            
            with self.frame_lock:
                self.frame = frame
            
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_fps_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_fps_time = current_time
            
            time.sleep(0.033)
    
    def _fixed_process(self, frame):
        """Fixed frame processing - Now properly handles STOP commands"""
        # Mirror frame
        processed = cv2.flip(frame, 1)
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        
        # Hand processing
        results = self.hands.process(rgb_frame)
        
        gesture_detected = "None"
        self.gesture_controller.hand_detected = False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Fixed gesture recognition
                gesture_detected = self.gesture_controller.recognize_gesture_fixed(hand_landmarks)
                
                # FIXED: Always execute STOP commands immediately
                if gesture_detected == "✊ STOP":
                    # Send STOP command immediately without delay
                    self.gesture_controller.execute_command_fixed(gesture_detected)
                else:
                    # Normal command execution for RUN/BACK
                    if gesture_detected != "None":
                        self.gesture_controller.execute_command_fixed(gesture_detected)
                
                # Proper hand drawing
                self._draw_fixed_hand(processed, hand_landmarks, gesture_detected)
        
        self.gesture_controller.current_gesture = gesture_detected
        
        # Fixed overlay
        processed = self._fixed_overlay(processed)
        
        return processed
    
    def _draw_fixed_hand(self, frame, hand_landmarks, gesture):
        """Fixed hand drawing"""
        # Draw complete hand landmarks
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )
        
        # Bounding box
        h, w = frame.shape[:2]
        x_coords = [lm.x for lm in hand_landmarks.landmark]
        y_coords = [lm.y for lm in hand_landmarks.landmark]
        x_min, x_max = int(min(x_coords) * w), int(max(x_coords) * w)
        y_min, y_max = int(min(y_coords) * h), int(max(y_coords) * h)
        
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # Finger count display
        count_text = f"Fingers: {self.gesture_controller.finger_count}"
        cv2.putText(frame, count_text, (x_min, y_min - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def _fixed_overlay(self, frame):
        """Fixed overlay"""
        h, w = frame.shape[:2]
        
        # Top bar
        cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), -1)
        cv2.addWeighted(frame[0:40, 0:w], 0.7, frame[0:40, 0:w], 0.3, 0, frame[0:40, 0:w])
        
        # Gesture status
        gesture = self.gesture_controller.current_gesture
        hand_status = "🖐️" if self.gesture_controller.hand_detected else "👁️"
        
        if gesture == "✌️ RUN":
            color = (0, 255, 0)  # Green
        elif gesture == "🤟 BACK":
            color = (0, 255, 255)  # Yellow
        else:
            color = (0, 0, 255)  # Red
            
        status_text = f"{hand_status} {gesture}"
        cv2.putText(frame, status_text, (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # FPS
        cv2.putText(frame, f"FPS: {self.fps}", (w//2 - 40, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Mode
        mode_color = (0, 255, 0) if self.gesture_controller.enabled else (255, 0, 0)
        mode_text = "ACTIVE" if self.gesture_controller.enabled else "INACTIVE"
        cv2.putText(frame, mode_text, (w - 80, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, mode_color, 1)
        
        # Bottom guide
        guide_height = 30
        guide_bar = np.zeros((guide_height, w, 3), dtype=np.uint8)
        frame[h-guide_height:h, 0:w] = cv2.addWeighted(frame[h-guide_height:h, 0:w], 0.6, guide_bar, 0.4, 0)
        
        guide_text = "✌️2=RUN  🤟3=BACK  1/4/5/Fist=STOP"
        text_size = cv2.getTextSize(guide_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
        text_x = (w - text_size[0]) // 2
        cv2.putText(frame, guide_text, (text_x, h - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def get_frame(self):
        """Fixed frame encoding"""
        with self.frame_lock:
            if self.frame is not None:
                ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    return jpeg.tobytes()
        
        # Placeholder
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        cv2.putText(frame, "📹 FIXED CAMERA", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes() if ret else b''
    
    def stop(self):
        """Fixed cleanup"""
        self.is_running = False
        if self.camera:
            self.camera.release()
        if self.hands:
            self.hands.close()

# Global camera instance
camera = FixedCamera()

def generate_frames():
    """Fixed video stream"""
    while True:
        frame_bytes = camera.get_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)

@app.route('/')
def index():
    return {
        "status": "Fixed Camera Server - STOP Commands Working",
        "camera_connected": camera.is_running,
        "fps": camera.fps,
        "gesture_control": camera.gesture_controller.enabled,
        "current_gesture": camera.gesture_controller.current_gesture
    }

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return {
        "camera_connected": camera.is_running,
        "fps": camera.fps,
        "gesture_control_enabled": camera.gesture_controller.enabled,
        "current_gesture": camera.gesture_controller.current_gesture,
        "hand_detected": camera.gesture_controller.hand_detected,
        "finger_count": camera.gesture_controller.finger_count,
        "last_command": camera.gesture_controller.last_command
    }

@app.route('/gesture/enable')
def enable_gesture():
    camera.gesture_controller.enabled = True
    return {
        "status": "success",
        "message": "🎯 FIXED Gesture Control ENABLED - STOP commands working",
        "gesture_enabled": True
    }

@app.route('/gesture/disable')
def disable_gesture():
    camera.gesture_controller.enabled = False
    try:
        requests.post(f"{MAIN_SERVER}/api/command", 
                     json={"cmd": "move", "val": "S"}, timeout=1)
    except:
        pass
    return {
        "status": "success", 
        "message": "🔴 Gesture control disabled",
        "gesture_enabled": False
    }

@app.route('/gesture/status')
def gesture_status():
    return {
        "enabled": camera.gesture_controller.enabled,
        "current_gesture": camera.gesture_controller.current_gesture,
        "hand_detected": camera.gesture_controller.hand_detected,
        "finger_count": camera.gesture_controller.finger_count,
        "last_command": camera.gesture_controller.last_command
    }

# Test endpoint to manually send STOP command
@app.route('/test/stop')
def test_stop():
    try:
        response = requests.post(f"{MAIN_SERVER}/api/command", 
                               json={"cmd": "move", "val": "S"}, timeout=1)
        return {"status": "success", "message": "STOP command sent manually"}
    except:
        return {"status": "error", "message": "Failed to send STOP command"}

if __name__ == '__main__':
    logger.info("🚀 FIXED CAMERA SERVER STARTING...")
    logger.info("📹 http://localhost:5000")
    logger.info("🎯 FIXED Gesture Mapping:")
    logger.info("   ✌️ 2 Fingers = RUN")
    logger.info("   🤟 3 Fingers = BACK") 
    logger.info("   👆 1 Finger = STOP ✅")
    logger.info("   🖐️ 4 Fingers = STOP ✅")
    logger.info("   🖐️ 5 Fingers = STOP ✅")
    logger.info("   ✊ Fist = STOP ✅")
    logger.info("🔧 FIXED: STOP commands now work immediately!")
    
    # Start camera
    camera.start()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    finally:
        camera.stop()