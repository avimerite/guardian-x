#!/usr/bin/env python3
"""
Simple Web Controller - No logs, just reliable controls
"""

from flask import Flask, render_template_string, jsonify
import subprocess
import threading
import time
import os
import webbrowser

app = Flask(__name__)

# Track running processes
processes = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Simple HTML interface
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Simple Robot Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { 
            text-align: center; 
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .service {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
        }
        .service.camera { border-left-color: #28a745; }
        .service.main { border-left-color: #dc3545; }
        .service h3 { margin-bottom: 10px; color: #333; }
        .status { 
            padding: 5px 10px; 
            border-radius: 15px; 
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .running { background: #d4edda; color: #155724; }
        .stopped { background: #f8d7da; color: #721c24; }
        .buttons { margin-top: 15px; }
        button {
            padding: 12px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
        }
        .start { background: #28a745; color: white; }
        .stop { background: #dc3545; color: white; }
        .open { background: #007bff; color: white; }
        .bulk { 
            background: #6f42c1; 
            color: white;
            padding: 15px 25px;
            font-size: 16px;
            margin: 10px 5px;
        }
        .links { text-align: center; margin-top: 20px; }
        .links a {
            display: inline-block;
            margin: 10px;
            padding: 10px 20px;
            background: #17a2b8;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        #message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            text-align: center;
            display: none;
        }
        .success { background: #d4edda; color: #155724; display: block; }
        .error { background: #f8d7da; color: #721c24; display: block; }
        .tip {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-size: 14px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Simple Robot Controller</h1>
        <div class="subtitle">One-click control • No complications</div>
        
        <div class="tip">
            💡 <strong>New reliable camera server!</strong> No more mjpg-streamer issues.
        </div>
        
        <div id="message"></div>
        
        <div class="service camera">
            <h3>📹 Camera Server 
                <span id="cameraStatus" class="status stopped">Stopped</span>
            </h3>
            <p><strong>NEW:</strong> Simple & reliable Flask+OpenCV server</p>
            <div class="buttons">
                <button class="start" onclick="controlService('camera', 'start')">Start Camera</button>
                <button class="stop" onclick="controlService('camera', 'stop')">Stop Camera</button>
                <button class="open" onclick="openLink('http://localhost:5000/video_feed')">View Camera</button>
            </div>
        </div>
        
        <div class="service main">
            <h3>🤖 Main Robot Server 
                <span id="mainStatus" class="status stopped">Stopped</span>
            </h3>
            <p>Full robot control dashboard</p>
            <div class="buttons">
                <button class="start" onclick="controlService('main', 'start')">Start Main</button>
                <button class="stop" onclick="controlService('main', 'stop')">Stop Main</button>
                <button class="open" onclick="openLink('http://localhost:8000')">Open Dashboard</button>
            </div>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <button class="bulk" onclick="controlService('all', 'start')">🚀 START EVERYTHING</button>
            <button class="bulk" onclick="controlService('all', 'stop')">🛑 STOP EVERYTHING</button>
        </div>
        
        <div class="links">
            <a href="http://localhost:8000" target="_blank">🎮 Robot Dashboard</a>
            <a href="http://localhost:5000/video_feed" target="_blank">📹 Camera Feed</a>
        </div>
    </div>

    <script>
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = type;
            setTimeout(() => {
                msg.style.display = 'none';
                msg.className = '';
            }, 3000);
        }

        function controlService(service, action) {
            showMessage(`${action === 'start' ? 'Starting' : 'Stopping'} ${service} server...`, 'info');
            
            fetch(`/api/${action}/${service}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message, 'success');
                        setTimeout(updateStatus, 2000);
                        
                        // Auto-open dashboard when starting everything
                        if (action === 'start' && service === 'all') {
                            setTimeout(() => {
                                openLink('http://localhost:8000');
                            }, 3000);
                        }
                    } else {
                        showMessage(data.message, 'error');
                    }
                })
                .catch(err => {
                    showMessage('Network error - check if servers are running', 'error');
                });
        }

        function openLink(url) {
            window.open(url, '_blank');
        }

        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    updateServiceStatus('camera', data.camera_running);
                    updateServiceStatus('main', data.main_running);
                })
                .catch(err => {
                    console.log('Status check failed');
                });
        }

        function updateServiceStatus(service, isRunning) {
            const element = document.getElementById(service + 'Status');
            if (element) {
                element.textContent = isRunning ? 'Running' : 'Stopped';
                element.className = `status ${isRunning ? 'running' : 'stopped'}`;
            }
        }

        // Update status every 5 seconds
        setInterval(updateStatus, 5000);
        updateStatus(); // Initial update
    </script>
</body>
</html>
"""

def is_process_running(process_name):
    """Check if process is running"""
    try:
        result = subprocess.run(
            f"pgrep -f '{process_name}'", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0
    except:
        return False

def start_service(service):
    """Start a service"""
    try:
        if service == 'camera':
            cmd = f"cd {BASE_DIR} && python3 camera_server.py"
            processes['camera'] = subprocess.Popen(cmd, shell=True)
            return True, "📹 Camera server starting... (Uses reliable Flask+OpenCV)"
        elif service == 'main':
            cmd = f"cd {BASE_DIR} && python3 app.py"
            processes['main'] = subprocess.Popen(cmd, shell=True)
            return True, "🤖 Main server starting..."
    except Exception as e:
        return False, f"Error: {str(e)}"
    return False, "Unknown service"

def stop_service(service):
    """Stop a service"""
    try:
        if service == 'camera':
            subprocess.run(f"pkill -f 'camera_server.py'", shell=True)
            if 'camera' in processes:
                processes['camera'] = None
            return True, "📹 Camera server stopped"
        elif service == 'main':
            subprocess.run(f"pkill -f 'app.py'", shell=True)
            if 'main' in processes:
                processes['main'] = None
            return True, "🤖 Main server stopped"
    except Exception as e:
        return False, f"Error: {str(e)}"
    return False, "Unknown service"

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/status')
def status():
    return jsonify({
        'camera_running': is_process_running('camera_server.py'),
        'main_running': is_process_running('app.py')
    })

@app.route('/api/start/<service>')
def start(service):
    if service == 'all':
        success1, msg1 = start_service('camera')
        time.sleep(3)  # Give camera time to start
        success2, msg2 = start_service('main')
        return jsonify({
            'success': success1 and success2,
            'message': f"Camera: {msg1}, Main: {msg2}"
        })
    else:
        success, message = start_service(service)
        return jsonify({'success': success, 'message': message})

@app.route('/api/stop/<service>')
def stop(service):
    if service == 'all':
        success1, msg1 = stop_service('camera')
        success2, msg2 = stop_service('main')
        return jsonify({
            'success': success1 and success2,
            'message': f"Camera: {msg1}, Main: {msg2}"
        })
    else:
        success, message = stop_service(service)
        return jsonify({'success': success, 'message': message})

def open_browser():
    """Open browser automatically"""
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

if __name__ == '__main__':
    print("🚀 SIMPLE ROBOT CONTROLLER")
    print("=" * 50)
    print("📊 Control Panel: http://localhost:8080")
    print("🤖 Robot Dashboard: http://192.168.1.174:8000") 
    print("📹 Camera Feed: http://localhost:5000/video_feed")
    print("=" * 50)
    print("💡 Features:")
    print("   • Ultimate robot ever)")
    print("   • One-click start/stop")
    print("   • Auto-recovery for camera disconnections")
    print("   • Simple and stable")
    print("=" * 50)
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 50)
    
    # Open browser automatically
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the web controller
    app.run(host='0.0.0.0', port=8080, debug=False)