from collections import deque
from pathlib import Path
import time

import threading
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, Response, jsonify, render_template

from cnn_perclos import (
    LEFT_EYE_INDEXES,
    RIGHT_EYE_INDEXES,
    calculate_ear,
    crop_face,
    extract_landmarks,
    load_metadata,
    play_alarm,
)
from config import ALARM_DURATION, ALARM_FREQUENCY, CAMERA_INDEX, EAR_THRESHOLD, SHOW_DEBUG_INFO

app = Flask(__name__)

# Global Variables
camera = None
is_running = False
detection_active = False
current_status = "-"
eye_aspect_ratio = 0.0
perclos_value = 0.0
cnn_confidence = 0.0
cnn_label = "unknown"
fps_counter = 0
start_time_fps = time.time()
last_alarm_time = 0.0
samples = deque()

# CNN + PERCLOS settings
MODEL_PATH = "drowsiness_cnn_hoangtung.keras"
DROWSY_LABEL = "Closed_Eyes"
PERCLOS_WINDOW = 120
PERCLOS_THRESHOLD = 0.40
ALARM_COOLDOWN = 2.0

# Model runtime state
cnn_model = None
class_names = []
image_size = (224, 224)
drowsy_index = None
model_ready = False

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def load_model_assets():
    global cnn_model, class_names, image_size, drowsy_index, model_ready

    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        print(f"Model tidak ditemukan: {MODEL_PATH}")
        model_ready = False
        return

    metadata = load_metadata(MODEL_PATH)
    if metadata is None:
        print("Metadata model (.json) tidak ditemukan.")
        model_ready = False
        return

    class_names = metadata.get("class_names", [])
    image_size = tuple(metadata.get("image_size", [224, 224]))

    if DROWSY_LABEL not in class_names:
        print(f"Label '{DROWSY_LABEL}' tidak ditemukan dalam class_names: {class_names}")
        model_ready = False
        return

    cnn_model = tf.keras.models.load_model(MODEL_PATH)
    drowsy_index = class_names.index(DROWSY_LABEL)
    model_ready = True

def generate_frames():
    global camera, is_running, detection_active, current_status
    global eye_aspect_ratio, perclos_value, cnn_confidence, cnn_label
    global fps_counter, start_time_fps, last_alarm_time, samples

    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)

    is_running = True
    fps_counter = 0
    start_time_fps = time.time()
    samples = deque()
    last_alarm_time = 0.0
    frame_count = 0

    def trigger_alarm():
            play_alarm(ALARM_FREQUENCY, ALARM_DURATION)
            
    while is_running and detection_active:
        ret, frame = camera.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        landmarks = extract_landmarks(face_mesh, frame)
        if landmarks is not None:
            left_eye = landmarks[LEFT_EYE_INDEXES]
            right_eye = landmarks[RIGHT_EYE_INDEXES]

            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)
            eye_aspect_ratio = (left_ear + right_ear) / 2.0
            eyes_closed = eye_aspect_ratio < EAR_THRESHOLD

            now = time.time()
            samples.append((now, eyes_closed))
            while samples and now - samples[0][0] > PERCLOS_WINDOW:
                samples.popleft()

            if samples:
                closed_count = sum(1 for _, closed in samples if closed)
                perclos_value = closed_count / len(samples)
            else:
                perclos_value = 0.0

            predicted_class = None
            face_crop = crop_face(frame, landmarks)
            if model_ready and face_crop is not None:
                resized = cv2.resize(face_crop, image_size)
                image_tensor = tf.expand_dims(resized, axis=0)
                prediction = cnn_model.predict(image_tensor, verbose=0)[0]
                predicted_class = int(np.argmax(prediction))
                cnn_label = class_names[predicted_class]
                cnn_confidence = float(prediction[predicted_class])
            else:
                cnn_label = "unknown"
                cnn_confidence = 0.0

            alert_condition = (
                model_ready
                and predicted_class == drowsy_index
                and perclos_value >= PERCLOS_THRESHOLD
            )
            current_status = "kantuk" if alert_condition else "normal"

            if alert_condition and now - last_alarm_time >= ALARM_COOLDOWN:
                threading.Thread(target=trigger_alarm, daemon=True).start()
                last_alarm_time = now
        else:
            current_status = "normal"
            perclos_value = 0.0
            cnn_label = "unknown"
            cnn_confidence = 0.0

        if SHOW_DEBUG_INFO:
            cv2.putText(frame, f"CNN: {cnn_label} ({cnn_confidence:.2f})", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"PERCLOS: {perclos_value:.2f}", (10, 55),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, f"EAR: {eye_aspect_ratio:.2f}", (10, 80),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Status: {current_status.upper()}", (10, 105),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255) if current_status == "kantuk" else (0, 255, 0), 2)

        frame_count += 1
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time_fps
            fps_counter = frame_count / elapsed if elapsed > 0 else 0

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    if camera:
        camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start', methods=['POST'])
def start_detection():
    global detection_active, current_status, eye_aspect_ratio, perclos_value, cnn_confidence, cnn_label
    if not model_ready:
        load_model_assets()
    detection_active = True
    current_status = "normal"
    eye_aspect_ratio = 0.0
    perclos_value = 0.0
    cnn_confidence = 0.0
    cnn_label = "unknown"
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_detection():
    global detection_active, is_running, camera, current_status
    global eye_aspect_ratio, perclos_value, cnn_confidence, cnn_label, fps_counter, samples
    detection_active = False
    is_running = False
    current_status = "normal"
    eye_aspect_ratio = 0.0
    perclos_value = 0.0
    cnn_confidence = 0.0
    cnn_label = "unknown"
    fps_counter = 0.0
    samples = deque()
    if camera:
        camera.release()
    return jsonify({'status': 'stopped'})

@app.route('/api/status')
def get_status():
    return jsonify({
        'status': current_status,
        'ear': round(eye_aspect_ratio, 2),
        'perclos': round(perclos_value, 3),
        'cnn_confidence': round(cnn_confidence, 3),
        'cnn_label': cnn_label,
        'fps': round(fps_counter, 1),
        'detection_active': detection_active
    })

@app.route('/api/config')
def get_config():
    return jsonify({
        'ear_threshold': EAR_THRESHOLD,
        'perclos_threshold': PERCLOS_THRESHOLD,
        'perclos_window': PERCLOS_WINDOW
    })

if __name__ == '__main__':
    load_model_assets()
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
