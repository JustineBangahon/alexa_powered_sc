from flask import Flask, render_template, request, jsonify, Response
import cv2

app = Flask(__name__)

# Map each camera ID to its RTSP URL.
CAMERA_STREAMS = {
    "camera1": "rtsp://camera1:camera1@192.168.43.67/stream1",
    "camera2": "rtsp://camera2:camera2@192.168.43.68/stream1",
    "camera3": "rtsp://camera3:camera3@192.168.43.69/stream1"
}

def gen_frames(rtsp_url):
    """Capture frames from the RTSP stream and yield them as JPEG."""
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = cap.read()
        if not success:
            break  # Stop if there's an issue.
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release()

@app.route('/')
def index():
    # Render the index template, which will show the camera streams.
    return render_template('index.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    try:
        command = request.json.get('command', "").lower()
        cameras_to_show = []
        
        # If the command says "remove all cameras", we want to clear everything.
        if "remove all cameras" in command:
            cameras_to_show = []
        # If the command is to show all cameras, return all of them.
        elif "show all cameras" in command:
            cameras_to_show = list(CAMERA_STREAMS.keys())
        else:
            # Check for individual cameras.
            if "camera 1" in command or "camera one" in command:
                cameras_to_show.append("camera1")
            if "camera 2" in command or "camera two" in command:
                cameras_to_show.append("camera2")
            if "camera 3" in command or "camera three" in command:
                cameras_to_show.append("camera3")
        
        # If no camera is recognized and the command wasn't to remove cameras,
        # return an error.
        if not cameras_to_show and "remove all cameras" not in command:
            return jsonify({"error": "No cameras recognized in the command"}), 400
        
        return jsonify({"cameras": cameras_to_show})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    rtsp_url = CAMERA_STREAMS.get(camera_id)
    if not rtsp_url:
        return "Camera not found", 404
    # Stream the video feed from the given RTSP URL.
    return Response(gen_frames(rtsp_url), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
