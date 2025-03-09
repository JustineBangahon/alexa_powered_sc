from flask import Flask, render_template, Response, jsonify
from camera_manager import CameraManager
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize camera manager
camera_manager = CameraManager()

# Alexa Skill Handler
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speech = "Welcome to Surveillance System. You can show or hide cameras."
        return handler_input.response_builder.speak(speech).response

class DisplayCameraIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DisplayCameraIntent")(handler_input)

    def handle(self, handler_input):
        camera = handler_input.request_envelope.request.intent.slots["camera"].value
        camera_manager.add_camera(camera)
        speech = f"Showing {camera}"
        return handler_input.response_builder.speak(speech).response

class RemoveCameraIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("RemoveCameraIntent")(handler_input)

    def handle(self, handler_input):
        camera = handler_input.request_envelope.request.intent.slots["camera"].value
        camera_manager.remove_camera(camera)
        speech = f"Removing {camera}"
        return handler_input.response_builder.speak(speech).response

skill_builder = SkillBuilder()
skill_builder.add_request_handler(LaunchRequestHandler())
skill_builder.add_request_handler(DisplayCameraIntentHandler())
skill_builder.add_request_handler(RemoveCameraIntentHandler())

skill_adapter = SkillAdapter(
    skill=skill_builder.create(),
    skill_id="your_skill_id",
    app=app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/active_cameras')
def active_cameras():
    return jsonify(camera_manager.get_active_cameras())

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    return Response(camera_manager.gen_frames(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)