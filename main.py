import cv2
from flask import Flask, Response
import threading

app = Flask(__name__)

# Global variables
camera = None
output_frame = None
lock = threading.Lock()

def initialize_camera():
  global camera
  camera = cv2.VideoCapture(0)
  camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
  camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
  camera.set(cv2.CAP_PROP_FPS, 30)

def capture_frames():
  global output_frame, camera, lock
  
  while True:
      if camera is None or not camera.isOpened():
          continue

      success, frame = camera.read()
      if not success:
          continue

      with lock:
          output_frame = frame.copy()

def generate_frames():
  global output_frame, lock
  
  while True:
      with lock:
          if output_frame is None:
              continue
          
          (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
          if not flag:
              continue

      yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encodedImage) + b'\r\n')

@app.route('/')
def index():
  return """
  <html>
    <body>
      <h1>Webcam Stream</h1>
      <img src="/video_feed" width="640" height="480" />
    </body>
  </html>
  """

@app.route('/video_feed')
def video_feed():
  return Response(generate_frames(),
                  mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
  initialize_camera()
  
  # Start the frame capture thread
  capture_thread = threading.Thread(target=capture_frames)
  capture_thread.daemon = True
  capture_thread.start()
  
  # Run the Flask app
  app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)

  # Release the camera when the app is closed
  if camera is not None:
      camera.release()
