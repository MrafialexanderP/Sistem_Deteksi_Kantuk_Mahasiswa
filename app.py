import cv2
import time
import threading
from flask import Flask, Response, jsonify, render_template, request

# --- 1. IMPORT SESUAI CATATAN TEMAN ---
# Menambahkan "backend." di depan "src"
from backend.src.pipeline.drowsiness_pipeline import DrowsinessPipeline
from backend.src.utils.alarm import Alarm

app = Flask(__name__)

# --- 2. PATH MODEL & ALARM SESUAI CATATAN TEMAN ---
MODEL_PATH = "backend/models/drowsiness_cnn.keras"
ALARM_PATH = "backend/assets/alarm.wav"

# --- Global Variables ---
camera = None
is_running = False
detection_active = False
output_frame = None
frame_lock = threading.Lock()
capture_thread = None

# Yawn detection timer
yawn_start_time = None
yawn_duration_threshold = 2.0  # seconds

# Variabel untuk mengirim data ke Frontend (API)
current_status = "-"
current_perclos = 0.0
current_eye_state = "-"
current_yawn = "-"

# Data mahasiswa yang sedang login (dikirim dari halaman student)
current_student_info = {
    'name': '',
    'nim': ''
}

# Inisialisasi Pipeline & Alarm
pipeline = DrowsinessPipeline(MODEL_PATH)
alarm = Alarm(ALARM_PATH)

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None


def capture_loop():
    global camera, output_frame, is_running, detection_active
    global current_status, current_perclos, current_eye_state, current_yawn
    global yawn_start_time

    camera = cv2.VideoCapture(0)  # Buka Web Kamera
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)  # Naikkan resolusi untuk kualitas
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

    if not camera.isOpened():
        print("Error: Cannot open camera")
        return

    frame_count = 0
    while is_running and detection_active:
        ret, frame = camera.read()
        if not ret:
            break

        frame_count += 1
        # Kurangi skipping untuk smoothness
        if frame_count % 3 != 0:  # Process every 3rd frame instead of every 2nd
            continue

        frame = cv2.flip(frame, 1)

        # --- PROSES FRAME MENGGUNAKAN PIPELINE BARU ---
        result = pipeline.process(frame)

        current_eye_state = result.get("eye_state", "-")
        current_yawn = result.get("yawn", False)
        current_perclos = result.get("perclos", 0.0)

        # Yawn timer logic
        if current_yawn:
            if yawn_start_time is None:
                yawn_start_time = time.time()
            elif time.time() - yawn_start_time >= yawn_duration_threshold:
                current_status = "Drowsy"
                alarm.play()
            else:
                current_status = "Normal"
                alarm.stop()
        else:
            yawn_start_time = None
            current_status = "Normal"
            alarm.stop()

        # Override status if PERCLOS is high
        if current_perclos > 0.4:  # PERCLOS threshold
            current_status = "Drowsy"
            alarm.play()

        cv2.putText(frame, f"Eye: {current_eye_state}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Yawn: {current_yawn}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"PERCLOS: {current_perclos:.2f}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        color_status = (0, 0, 255) if current_status == "Drowsy" else (0, 255, 0)
        cv2.putText(frame, f"Status: {current_status}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_status, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        with frame_lock:
            output_frame = buffer.tobytes()

        time.sleep(0.05)  # Slightly slower to reduce CPU

    release_camera()
    alarm.stop()


def generate_frames():
    global output_frame

    while is_running and detection_active:
        with frame_lock:
            frame_bytes = output_frame

        if frame_bytes is None:
            time.sleep(0.05)
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.03)


# ==========================================
# ROUTES UNTUK FRONTEND (HTML)
# ==========================================
@app.route('/')
def root():
    return render_template('login.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/student')
def student():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# Endpoint untuk Streaming Video ke tag <img> HTML
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ==========================================
# ROUTES API (Tombol Start/Stop & Data JSON)
# ==========================================
@app.route('/api/start', methods=['POST'])
def start_detection():
    global detection_active, is_running, capture_thread
    if detection_active and capture_thread is not None and capture_thread.is_alive():
        return jsonify({'status': 'already_started'})

    is_running = True
    detection_active = True
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_detection():
    global detection_active, is_running, current_status, current_perclos, yawn_start_time
    detection_active = False
    is_running = False
    current_status = "-"
    current_perclos = 0.0
    yawn_start_time = None
    release_camera()
    alarm.stop() # Pastikan alarm mati saat distop
    return jsonify({'status': 'stopped'})

@app.route('/api/set_student', methods=['POST'])
def set_student():
    """Menerima data mahasiswa dari halaman student (dipanggil saat login)"""
    global current_student_info
    data = request.get_json()
    current_student_info['name'] = data.get('name', '')
    current_student_info['nim'] = data.get('nim', '')
    return jsonify({'status': 'ok'})

@app.route('/api/status')
def get_status():
    """Mengirim data text (Status, PERCLOS) ke Frontend JS secara realtime"""
    return jsonify({
        'status': current_status,
        'perclos': round(current_perclos, 3),
        'eye_state': current_eye_state,
        'yawn': current_yawn,
        'detection_active': detection_active,
        'student_name': current_student_info.get('name', ''),
        'student_nim': current_student_info.get('nim', '')
    })

if __name__ == '__main__':
    # Threaded=True agar video stream tidak terblokir oleh API request
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
