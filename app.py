from flask import Flask, render_template_string, Response, jsonify, request
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from flask_ask_sdk.skill_adapter import SkillAdapter
import cv2
import threading
import numpy as np

app = Flask(__name__)
app.secret_key = 'itm4finalproject'

class CameraManager:
    def __init__(self):
        self.cameras = {
            "camera1": "rtsp://camera1:camera1@192.168.43.67/stream1",
            "camera2": "rtsp://camera2:camera2@192.168.43.68/stream1",
            "camera3": "rtsp://camera3:camera3@192.168.43.69/stream1"
        }
        self.active_cameras = {}
        self.lock = threading.Lock()

    def add_camera(self, camera_id):
        with self.lock:
            if camera_id in self.cameras and camera_id not in self.active_cameras:
                print(f"Starting camera: {camera_id}")
                self.active_cameras[camera_id] = {
                    'url': self.cameras[camera_id],
                    'thread': None,
                    'frame': None
                }
                self._start_capture_thread(camera_id)

    def remove_camera(self, camera_id):
        with self.lock:
            if camera_id in self.active_cameras:
                print(f"Stopping camera: {camera_id}")
                del self.active_cameras[camera_id]

    def get_active_cameras(self):
        return list(self.active_cameras.keys())

    def _start_capture_thread(self, camera_id):
        def capture():
            cap = cv2.VideoCapture(self.active_cameras[camera_id]['url'])
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            while camera_id in self.active_cameras:
                ret, frame = cap.read()
                if not ret:
                    print(f"Error reading frame from {camera_id}")
                    break
                
                _, jpeg = cv2.imencode('.jpg', frame)
                with self.lock:
                    self.active_cameras[camera_id]['frame'] = jpeg.tobytes()
            
            cap.release()
            print(f"Camera {camera_id} thread exited")

        thread = threading.Thread(target=capture, daemon=True)
        thread.start()
        self.active_cameras[camera_id]['thread'] = thread

# Initialize camera manager
camera_manager = CameraManager()

# Alexa Skill Handlers
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak(
            "Welcome to Surveillance System. You can show or hide cameras."
        ).response

class DisplayCameraIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DisplayCameraIntent")(handler_input)

    def handle(self, handler_input):
        camera = handler_input.request_envelope.request.intent.slots["camera"].value
        camera_manager.add_camera(camera)
        return handler_input.response_builder.speak(
            f"Showing {camera}"
        ).response

class RemoveCameraIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("RemoveCameraIntent")(handler_input)

    def handle(self, handler_input):
        camera = handler_input.request_envelope.request.intent.slots["camera"].value
        camera_manager.remove_camera(camera)
        return handler_input.response_builder.speak(
            f"Removing {camera}"
        ).response

# Build Alexa Skill
skill_builder = SkillBuilder()
skill_builder.add_request_handler(LaunchRequestHandler())
skill_builder.add_request_handler(DisplayCameraIntentHandler())
skill_builder.add_request_handler(RemoveCameraIntentHandler())

skill_adapter = SkillAdapter(
    skill=skill_builder.create(),
    skill_id="your_skill_id",
    app=app
)

# Web Interface Routes
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Surveillance System</title>
        <style>
            .video-container { display: flex; flex-wrap: wrap; gap: 10px; }
            .video-box { width: 640px; height: 480px; border: 2px solid #333; }
        </style>
    </head>
    <body>
        <h1>Surveillance Cameras</h1>
        <div class="video-container" id="container"></div>
        <script>
            function updateCameras() {
                fetch('/active_cameras')
                    .then(r => r.json())
                    .then(cameras => {
                        const container = document.getElementById('container');
                        container.innerHTML = cameras.map(cam => `
                            <img class="video-box" src="/video_feed/${cam}" />
                        `).join('');
                    });
            }
            setInterval(updateCameras, 1000);
        </script>
    </body>
    </html>
    ''')

@app.route('/active_cameras')
def get_active_cameras():
    return jsonify(camera_manager.get_active_cameras())

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    def generate():
        while True:
            frame = None
            with camera_manager.lock:
                if camera_id in camera_manager.active_cameras:
                    frame = camera_manager.active_cameras[camera_id].get('frame')
            
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Generate black frame if no stream
                black_frame = np.zeros((480, 640, 3), np.uint8)
                _, jpeg = cv2.imencode('.jpg', black_frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Test endpoints (remove in production)
@app.route('/test/add/<camera_id>')
def test_add(camera_id):
    camera_manager.add_camera(camera_id)
    return f"Added {camera_id}"

@app.route('/test/remove/<camera_id>')
def test_remove(camera_id):
    camera_manager.remove_camera(camera_id)
    return f"Removed {camera_id}"

if __name__ == '__main__':
    skill_adapter.register(app=app, route="/alexa")
    app.run(host='0.0.0.0', port=5000, threaded=True)