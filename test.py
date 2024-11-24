import cv2
import time
import os
from datetime import datetime
import base64
from openai import OpenAI
import io
from PIL import Image

def encode_image_to_base64(image_path):
  """Encode an image file to base64 string."""
  with open(image_path, "rb") as image_file:
      return base64.b64encode(image_file.read()).decode('utf-8')

def initialize_camera():
  """Initialize and configure the webcam."""
  cap = cv2.VideoCapture(0)
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
  cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
  cap.set(cv2.CAP_PROP_CONTRAST, 32)
  time.sleep(2)  # Wait for camera to initialize

  if not cap.isOpened():
      raise RuntimeError("Error: Could not open webcam")

  return cap

def capture_images(cap, base_dir, num_images=3):
  """Capture multiple images from the webcam."""
  image_paths = []

  for i in range(num_images):
      # Skip first few frames for proper exposure
      for _ in range(5):
          ret, frame = cap.read()

      if not ret or frame is None:
          print("Error: Could not read frame")
          continue

      if frame.mean() < 10:
          print("Warning: Frame appears to be too dark")
          continue

      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
      filename = f"{base_dir}/frame_{timestamp}.jpg"

      if cv2.imwrite(filename, frame):
          image_paths.append(filename)
          print(f"Successfully saved image: {filename}")
      else:
          print(f"Failed to save image: {filename}")

      time.sleep(2)

  return image_paths

def analyze_images_with_llm(client, image_paths):
  """Analyze images using OpenAI's API."""
  if not image_paths:
      print("No valid images captured, skipping API request")
      return None

  messages = [
      {
          "role": "user",
          "content": [
              {"type": "text", "text": "Describe the images in a very detailed manner"}
          ]
      }
  ]

  # Add images to the message
  for image_path in image_paths:
      base64_image = encode_image_to_base64(image_path)
      messages[0]["content"].append({
          "type": "image_url",
          "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
          }
      })

  print("API Request to an llm")
  response = client.chat.completions.create(
      model="gpt-4o",
      messages=messages,
      max_tokens=300,
  )

  return response.choices[0].message.content

def cleanup_images(image_paths):
  """Delete captured images."""
  for path in image_paths:
      try:
          os.remove(path)
      except Exception as e:
          print(f"Error deleting {path}: {e}")

def initialize_openai_client(api_key):
  """Initialize OpenAI client."""
  return OpenAI(api_key=api_key)

def analyze_for_security_threat(client, image_description):
  """
  Analyze the image description to determine if it indicates kidnapping/abduction.
  Returns a tuple of (boolean, explanation)
  """
  messages = [
      {
          "role": "system",
          "content": """You are a security threat analyzer. Your task is to determine if the image 
          shows a video/content of kidnapping being played on a phone, screen, or display device.

          Specifically look for:
          - Presence of phone/screen/display showing video content
          - Any kidnapping or abduction scenes being played/shown
          - People watching or recording kidnapping-related content
          - Mentions of video playback or media viewing of suspicious activity

          Note: For testing purposes, if the description mentions any video/content of kidnapping 
          being shown on a device, consider it as a confirmed threat.

          Respond with a clear YES or NO followed by a brief explanation."""
      },
      {
          "role": "user",
          "content": f"""Based on this image description, is there any video/content of kidnapping 
          being shown on a phone or screen? Description {image_description}

          Respond in this format:
          THREAT: [YES/NO]
          EXPLANATION: [Your brief analysis]"""
      }
  ]

  try:
      response = client.chat.completions.create(
          model="gpt-4",  # Using GPT-4 for better analysis
          messages=messages,
          max_tokens=150,
          temperature=0.3  # Lower temperature for more focused responses
      )

      analysis = response.choices[0].message.content

      # Parse the response
      threat_detected = "YES" in analysis.split("THREAT:")[1].split("EXPLANATION:")[0].strip().upper()
      explanation = analysis.split("EXPLANATION:")[1].strip()

      return threat_detected, explanation

  except Exception as e:
      print(f"Error in security threat analysis: {e}")
      return None, str(e)

def capture_and_analyze():
  """Main function to coordinate the surveillance process."""
  # Initialize OpenAI client
  api_key = ""
  client = initialize_openai_client(api_key)

  # Create directory for saving images
  base_dir = "surveillance_images"
  os.makedirs(base_dir, exist_ok=True)

  # Initialize camera
  cap = initialize_camera()

  try:
      while True:
          # Capture images
          image_paths = capture_images(cap, base_dir)

          try:
              # Analyze images
              image_description = analyze_images_with_llm(client, image_paths)
              if image_description:
                  print(f"Scene Description: {image_description}")
                  print("\n" + "="*50 + "\n")

                  # Analyze for security threats
                  threat_detected, explanation = analyze_for_security_threat(client, image_description)

                  if threat_detected is not None:
                      print(f"""
                        🚨 Security Analysis Results 🚨
                        {'⚠️ THREAT DETECTED ⚠️' if threat_detected else '✅ No Threat Detected'}
                        Analysis: {explanation}
                        {"🔴 ALERT: Potential kidnapping/abduction scenario detected!" if threat_detected else "🟢 Scene appears normal."}
                        """)
                  print("="*50 + "\n")

          except Exception as e:
              print(f"Error in analysis pipeline: {e}")

          finally:
              # Clean up images
              cleanup_images(image_paths)

  except KeyboardInterrupt:
      print("\nStopping surveillance...")
  finally:
      cap.release()


if __name__ == "__main__":
  capture_and_analyze()
