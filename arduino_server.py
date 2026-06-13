#!/usr/bin/env python3
"""
🤖 Robot Revery - Ultra Stable Arduino Server
• Handles all Arduino communication
• Never loses connection
• Continuous sensor monitoring
"""

from flask import Flask, jsonify, request
import serial
import threading
import time
import os
import logging
from datetime import datetime

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class UltraStableArduinoManager:
    def __init__(self):
        self.arduino = None
        self.connected = False
        self.port = None
        
        # Sensor data
        self.sensor_data = {
            "temp": 25.5,
            "hum": 60.0,
            "air": 350,
            "dist": 100
        }
        
        # Connection monitoring
        self.last_sensor_time = time.time()
        self.last_command_time = time.time()
        self.connection_attempts = 0
        self.max_attempts = 5
        
        # Thread control
        self.running = True
        self.command_lock = threading.Lock()
        
        # Start all threads
        self._start_threads()
        
        logger.info("🚀 Arduino Manager Started")
    
    def _start_threads(self):
        """Start all monitoring threads"""
        self.conn_thread = threading.Thread(target=self._connection_manager, daemon=True)
        self.conn_thread.start()
        
        self.sensor_thread = threading.Thread(target=self._sensor_reader, daemon=True)
        self.sensor_thread.start()
        
        self.health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        self.health_thread.start()
    
    def find_arduino_port(self):
        """Find Arduino port"""
        possible_ports = [
            "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2",
            "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2"
        ]
        
        for port in possible_ports:
            if os.path.exists(port):
                logger.info(f"🔍 Found Arduino port: {port}")
                return port
        return None
    
    def _connect_arduino(self):
        """Connect to Arduino"""
        try:
            port = self.find_arduino_port()
            if not port:
                return False
            
            # Close existing connection
            if self.arduino:
                try:
                    self.arduino.close()
                except:
                    pass
                time.sleep(2)
            
            logger.info(f"🔌 Connecting to {port}...")
            
            self.arduino = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=0.5,
                write_timeout=2
            )
            
            time.sleep(3)  # Wait for Arduino boot
            
            # Clear buffers
            self.arduino.reset_input_buffer()
            self.arduino.reset_output_buffer()
            time.sleep(0.5)
            
            # Send initialization
            self.arduino.write(b"\n\n")
            time.sleep(0.2)
            self.arduino.write(b"STATUS\n")
            time.sleep(1)
            
            # Read response
            response = self._read_arduino_response(timeout=3)
            
            if response and any(keyword in response for keyword in ["READY", "STATUS", "SENSOR_DATA", "MOVING"]):
                self.connected = True
                self.port = port
                self.connection_attempts = 0
                self.last_sensor_time = time.time()
                self.last_command_time = time.time()
                logger.info("✅ Arduino connected successfully!")
                return True
            else:
                logger.warning("⚠️ No clear response, but proceeding...")
                self.connected = True
                self.port = port
                return True
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def _read_arduino_response(self, timeout=2):
        """Read Arduino response"""
        response = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.arduino and self.arduino.in_waiting > 0:
                try:
                    line = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response += line + " "
                        logger.info(f"📨 Arduino: {line}")
                except:
                    break
            time.sleep(0.1)
        
        return response.strip()
    
    def _connection_manager(self):
        """Manage Arduino connection"""
        while self.running:
            if not self.connected:
                wait_time = min(2 ** self.connection_attempts, 30)
                logger.info(f"🔄 Reconnection in {wait_time}s...")
                time.sleep(wait_time)
                
                if self._connect_arduino():
                    self.connection_attempts = 0
                else:
                    self.connection_attempts += 1
            else:
                time.sleep(5)
    
    def _sensor_reader(self):
        """Continuous sensor reading"""
        buffer = ""
        
        while self.running:
            if self.connected and self.arduino and self.arduino.is_open:
                try:
                    # Read available bytes
                    bytes_to_read = self.arduino.in_waiting
                    if bytes_to_read > 0:
                        data = self.arduino.read(bytes_to_read).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if line:
                                self._process_sensor_line(line)
                    
                    # Prevent buffer overflow
                    if len(buffer) > 1000:
                        buffer = ""
                    
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"❌ Sensor read error: {e}")
                    self.connected = False
                    time.sleep(1)
            else:
                time.sleep(1)
    
    def _process_sensor_line(self, line):
        """Process sensor data"""
        try:
            # Format: "SENSOR_DATA,25.5,60.0,350,100"
            if line.startswith("SENSOR_DATA") and len(line.split(',')) >= 5:
                parts = line.split(',')
                self.sensor_data["temp"] = float(parts[1]) if parts[1] != "nan" else 25.5
                self.sensor_data["hum"] = float(parts[2]) if parts[2] != "nan" else 60.0
                self.sensor_data["air"] = int(parts[3])
                self.sensor_data["dist"] = int(parts[4])
                
                self.last_sensor_time = time.time()
                
        except Exception as e:
            logger.warning(f"⚠️ Sensor parse error: {e}")
    
    def _health_monitor(self):
        """Monitor Arduino health"""
        while self.running:
            if self.connected:
                current_time = time.time()
                
                # Check sensor data
                if current_time - self.last_sensor_time > 30:
                    logger.warning("⚠️ No sensor data for 30s")
                    
                # Force reconnect if no data for too long
                if current_time - self.last_sensor_time > 60:
                    logger.error("🚨 No sensor data for 60s, reconnecting...")
                    self.connected = False
                
                # Send keep-alive
                if current_time - self.last_command_time > 30:
                    try:
                        if self.arduino and self.arduino.is_open:
                            self.arduino.write(b"STATUS\n")
                            self.last_command_time = current_time
                    except:
                        self.connected = False
            
            time.sleep(10)
    
    def send_command(self, command, description=""):
        """Send command to Arduino"""
        with self.command_lock:
            if not self.connected:
                logger.warning("⚠️ Arduino not connected")
                return False
            
            try:
                # Clear buffer before sending
                if self.arduino.in_waiting > 0:
                    self.arduino.reset_input_buffer()
                
                # Send command
                full_command = f"{command}\n"
                self.arduino.write(full_command.encode())
                self.arduino.flush()
                
                self.last_command_time = time.time()
                logger.info(f"📤 Sent: {command} - {description}")
                
                time.sleep(0.2)
                return True
                
            except Exception as e:
                logger.error(f"❌ Command failed: {e}")
                self.connected = False
                return False
    
    def get_status(self):
        """Get status"""
        current_time = time.time()
        
        return {
            "connected": self.connected,
            "port": self.port,
            "sensor_data": self.sensor_data.copy(),
            "last_sensor_update": current_time - self.last_sensor_time,
            "connection_attempts": self.connection_attempts
        }
    
    def cleanup(self):
        """Cleanup"""
        self.running = False
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass

# Initialize Arduino manager
arduino_manager = UltraStableArduinoManager()

# ========== FLASK ROUTES ==========
@app.route('/')
def index():
    return {
        "status": "Ultra Stable Arduino Server",
        "arduino_connected": arduino_manager.connected,
        "endpoints": {
            "status": "/api/status",
            "sensors": "/api/sensors", 
            "command": "/api/command",
            "connect": "/api/connect"
        }
    }

@app.route('/api/status')
def status():
    return jsonify(arduino_manager.get_status())

@app.route('/api/sensors')
def get_sensors():
    return jsonify(arduino_manager.sensor_data)

@app.route('/api/command', methods=['POST'])
def send_command():
    data = request.json
    cmd = data.get("cmd")
    val = data.get("val", "")
    
    if not cmd:
        return jsonify({"status": "error", "message": "No command provided"})
    
    try:
        if cmd == "move":
            success = arduino_manager.send_command(f"MOVE {val}", f"Move {val}")
            message = f"Moving {val}"
            
        elif cmd == "servo":
            parts = val.split(',')
            if len(parts) == 2:
                servo_id = parts[0]
                angle = parts[1]
                success = arduino_manager.send_command(f"SERVO {servo_id},{angle}", f"Servo {servo_id} to {angle}°")
                message = f"Servo {servo_id} to {angle}°"
            else:
                return jsonify({"status": "error", "message": "Invalid servo command"})
                
        elif cmd == "mode":
            success = arduino_manager.send_command(f"MODE {val}", f"Mode {val}")
            message = f"Mode set to {val}"
            
        else:
            return jsonify({"status": "error", "message": f"Unknown command: {cmd}"})
        
        if success:
            return jsonify({
                "status": "success", 
                "message": message,
                "arduino_connected": arduino_manager.connected
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Command failed",
                "arduino_connected": arduino_manager.connected
            })
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/connect', methods=['POST'])
def connect_arduino():
    arduino_manager.connected = False
    time.sleep(1)
    return jsonify({"status": "success", "message": "Reconnection initiated"})

# Cleanup
import atexit
@atexit.register
def cleanup():
    arduino_manager.cleanup()

if __name__ == '__main__':
    logger.info("🚀 ARDUINO SERVER STARTING...")
    logger.info("📡 Port: 6000")
    
    try:
        app.run(host='0.0.0.0', port=6000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("👋 Server stopped")
    finally:
        arduino_manager.cleanup()