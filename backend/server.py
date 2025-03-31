from flask import Flask, jsonify, send_from_directory, Response
import cv2
import os
import sqlite3
import threading
import datetime
import time
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

camera = None
latest_frame = None
capture_active = False

# Load pre-trained Haar cascades for face and smile detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")


# Ensure save directory exists
SAVE_DIR = "smiles"
os.makedirs(SAVE_DIR, exist_ok=True)

# Database setup

DB_FILE = "smile_data.db"

def initialize_database():
    """Creates an empty database with a table for smile detections"""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)  # Delete the database if it exists (creates a fresh one)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create a table to store smile detections
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT UNIQUE,
        filename TEXT UNIQUE,
        x INTEGER,
        y INTEGER,
        w INTEGER,
        h INTEGER
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")

# Initialize database when the app starts


def get_db_connection():
    """Returns a new database connection"""
    return sqlite3.connect(DB_FILE, check_same_thread=False)



def capture_frame():
    """Continuously capture frames from the webcam."""
    global latest_frame, capture_active, camera
    while capture_active:
        success, frame = camera.read()
        if success:
            latest_frame = frame
        time.sleep(1)  # Capture a frame every second



initialize_database()


@app.route("/start-camera", methods=["POST"])
def start_camera():
    """Start the camera capture process."""
    global camera, capture_active
    if not capture_active:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print('CARMERA NOT OPENED')
            return jsonify({"error": "Failed to open camera"}), 500
        
        print('CARMERA OPENED')
        capture_active = True
        threading.Thread(target=capture_frame, daemon=True).start()
    return jsonify({"message": "Camera started"}), 200

@app.route("/stop-camera", methods=["POST"])
def stop_camera():
    """Stop the camera capture process."""
    global camera, capture_active
    capture_active = False
    if camera:
        camera.release()
        camera = None
    return jsonify({"message": "Camera stopped"}), 200

@app.route("/get-frame", methods=["GET"])
def get_frame():
    """Return the latest frame as a JPEG response."""
    global latest_frame
    if latest_frame is None:
        return jsonify({"error": "No frame captured yet"}), 500

    _, buffer = cv2.imencode(".jpg", latest_frame)


    return Response(buffer.tobytes(), mimetype="image/jpeg")

@app.route("/detect-smile", methods=["GET"])
def detect_smile():
    """Detect a smile in the current frame and return the result."""

    global latest_frame
    if latest_frame is None:
        return jsonify(smile_detected=False, coordinates="")
    else:
        print('WE HAVE A FRAME to SMILE-DETECT')

    # Convert frame to grayscale
    gray = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]  # Extract face region

        smiles = smile_cascade.detectMultiScale(face_roi, scaleFactor=1.5, minNeighbors=15, minSize=(20, 20))

        if len(smiles) > 0:
            print('SMILE DETECTED')

            sx, sy, sw, sh = smiles[0]
            sx, sy = sx + x, sy + y  # Adjust for full image coordinates

            # Draw rectangle
            cv2.rectangle(latest_frame, (sx, sy), (sx + sw, sy + sh), (0, 255, 0), 2)
  
            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("d%m-%d-%y_%H%M%S") + f"_{datetime.datetime.now().microsecond // 1000}"

            filename = f"{timestamp}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)

            cv2.imwrite(filepath, latest_frame)

            # Save image
            conn = get_db_connection()
            cursor = conn.cursor()

            # Store data in DB
            cursor.execute("INSERT INTO smiles (timestamp, filename, x, y, w, h) VALUES (?, ?, ?, ?, ?, ?)",
                            (timestamp, filename, sx, sy, sw, sh))
            conn.commit()

            coordinates = str(sx) + ',' + str(sy)

            return jsonify(smile_detected=True, coordinates=coordinates)
        
    return jsonify(smile_detected=False, coordinates="")



@app.route("/get-smiles", methods=["GET"])
def get_smiles():
    """Returns stored smile data for dropdown"""

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, filename FROM smiles ORDER BY id DESC")
    smiles = [{"timestamp": row[0], "filename": row[1]} for row in cursor.fetchall()]
    return jsonify(smiles)



@app.route("/get-image/<filename>", methods=["GET"])
def get_image(filename):
    """Returns a stored smile image"""
    return send_from_directory(SAVE_DIR, filename)



@app.route("/", methods=["GET"])
def home():
        return jsonify({"OK": "HOME"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
