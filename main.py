import cv2
from flask import Flask, Response
import threading
from ultralytics import YOLO
from twilio.rest import Client
from collections import deque

# Initialize a counter for kidnapping detections
kidnapping_counter = 0
# Use a deque to keep track of the last N frames
detection_history = deque(maxlen=10)  # Adjust the number as needed
# Threshold for triggering an alert
ALERT_THRESHOLD = 10  # Adjust as needed


def alert():

    # Your Account SID and Auth Token from twilio.com/console
    account_sid = ''
    auth_token = ''  # Replace with your actual auth token
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body='Hello! This is a test message from your kidnapping detection system.',
        from_='whatsapp:+14155238886',
        to='whatsapp:+917795348927'
    )

    print(message.sid)

app = Flask(__name__)

# Global variables
camera = None
output_frame = None
lock = threading.Lock()
model = YOLO("last.pt")  # Load the YOLOv8 model

def initialize_camera():
    global camera
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)

def capture_frames():
  global output_frame, camera, lock, model, kidnapping_counter
  
  while True:
      if camera is None or not camera.isOpened():
          continue

      success, frame = camera.read()
      if not success:
          continue

      # Perform object detection
      results = model(frame)
      annotated_frame = results[0].plot()

      with lock:
          output_frame = annotated_frame.copy()

      # Check for kidnapping detections
      kidnapping_detected = False
      for r in results:
          detections = r.boxes.cls.tolist()
          if 0 in detections:  # Assuming 0 is the class index for kidnapping
              kidnapping_detected = True
              break

      # Update detection history
      detection_history.append(kidnapping_detected)

      # Count kidnapping detections in recent frames
      kidnapping_counter = sum(detection_history)

      print(f"Kidnapping detections in last {len(detection_history)} frames: {kidnapping_counter}")

      # Check if alert threshold is exceeded
      if kidnapping_counter >= ALERT_THRESHOLD:
          alert()
          # Reset the counter after alerting
          kidnapping_counter = 0
          detection_history.clear()

      # Optional: Print all detection results
      for r in results:
          print(f"Detected objects: {r.boxes.cls.tolist()}")


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
        <h1>Webcam Stream with Object Detection</h1>
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


