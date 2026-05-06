import cv2
import time
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

def generate_frames():
    global camera, is_running, detection_active
    global current_status, current_perclos, current_eye_state, current_yawn

    camera = cv2.VideoCapture(0) # Buka Web Kamera

    if not camera.isOpened():
        print("Error: Cannot open camera")
        return

    while is_running and detection_active:
        ret, frame = camera.read()
        if not ret:
            break

        # Balikkan frame (mirror effect) agar nyaman dilihat di layar
        frame = cv2.flip(frame, 1)

        # --- PROSES FRAME MENGGUNAKAN PIPELINE BARU ---
        result = pipeline.process(frame)

        # Update variabel global agar bisa dibaca oleh endpoint /api/status
        current_eye_state = result.get("eye_state", "-")
        current_yawn = result.get("yawn", "-")
        current_perclos = result.get("perclos", 0.0)
        current_status = result.get("status", "Normal")

        # Trigger Alarm
        if current_status == "Drowsy":
            alarm.play()
        else:
            alarm.stop()

        # --- VISUALISASI KE DALAM FRAME VIDEO ---
        cv2.putText(frame, f"Eye: {current_eye_state}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Yawn: {current_yawn}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"PERCLOS: {current_perclos:.2f}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Warna teks status: Merah jika ngantuk, Hijau jika normal
        color_status = (0, 0, 255) if current_status == "Drowsy" else (0, 255, 0)
        cv2.putText(frame, f"Status: {current_status}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_status, 2)

        # Encode frame ke format JPEG untuk dikirim ke HTML
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    # Jika stop ditekan, matikan kamera dan alarm
    if camera:
        camera.release()
        alarm.stop()


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
    global detection_active, is_running
    is_running = True
    detection_active = True
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_detection():
    global detection_active, is_running, current_status, current_perclos
    detection_active = False
    is_running = False
    current_status = "-"
    current_perclos = 0.0
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
