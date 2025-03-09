import cv2
import threading

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
                self.active_cameras[camera_id] = {
                    'url': self.cameras[camera_id],
                    'thread': None,
                    'frame': None
                }
                self._start_capture_thread(camera_id)

    def remove_camera(self, camera_id):
        with self.lock:
            if camera_id in self.active_cameras:
                del self.active_cameras[camera_id]

    def get_active_cameras(self):
        return list(self.active_cameras.keys())

    def _start_capture_thread(self, camera_id):
        def capture():
            cap = cv2.VideoCapture(self.active_cameras[camera_id]['url'])
            while camera_id in self.active_cameras:
                ret, frame = cap.read()
                if ret:
                    _, jpeg = cv2.imencode('.jpg', frame)
                    self.active_cameras[camera_id]['frame'] = jpeg.tobytes()
            cap.release()

        thread = threading.Thread(target=capture)
        thread.start()
        self.active_cameras[camera_id]['thread'] = thread

    def gen_frames(self, camera_id):
        while True:
            if camera_id in self.active_cameras:
                frame = self.active_cameras[camera_id].get('frame')
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')