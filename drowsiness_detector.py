import argparse
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
from scipy.spatial import distance as dist

pygame.mixer.init()

_SOUND_CACHE = {}
_ALARM_CHANNEL = None

LEFT_EYE_INDEXES = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDEXES = [33, 160, 158, 133, 153, 144]

def calculate_ear(eye_landmarks):
    """
    Menghitung Eye Aspect Ratio untuk mendeteksi mata tertutup
    """
    # Vertical eye landmarks
    A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
    B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
    
    # Horizontal eye landmarks
    C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
    
    # EAR formula
    ear = (A + B) / (2.0 * C)
    return ear

def calculate_head_tilt(nose_tip, chin):
    """
    Menghitung kemiringan kepala berdasarkan posisi hidung dan dagu
    """
    angle = np.degrees(np.arctan2(chin[1] - nose_tip[1], chin[0] - nose_tip[0]))
    # Deviasi dari arah vertikal (90 derajat = posisi tegak)
    return abs(90.0 - abs(angle))

# Fungsi untuk membunyikan alarm
def play_alarm(audio_path=None, loop=False):
    """
    Membunyikan alarm suara
    """
    global _ALARM_CHANNEL
    if audio_path:
        audio_path = str(Path(audio_path))
        sound = _SOUND_CACHE.get(audio_path)
        if sound is None:
            if not Path(audio_path).exists():
                print(f"File audio tidak ditemukan: {audio_path}")
                return
            sound = pygame.mixer.Sound(audio_path)
            _SOUND_CACHE[audio_path] = sound
        if loop:
            if _ALARM_CHANNEL is None or not _ALARM_CHANNEL.get_busy():
                _ALARM_CHANNEL = sound.play(loops=-1)
        else:
            sound.play()
        return

    # Membuat suara beep menggunakan pygame
    frequency = 1000  # Hz
    duration = 500  # milliseconds

    # Generate beep sound
    sample_rate = 22050
    n_samples = int(round(duration * sample_rate / 1000))

    # Generate square wave
    buf = np.sin(2 * np.pi * np.arange(n_samples) * frequency / sample_rate)
    buf = (buf * 32767).astype(np.int16)

    # Convert to stereo
    stereo_buf = np.column_stack((buf, buf))

    sound = pygame.sndarray.make_sound(stereo_buf)
    if loop:
        if _ALARM_CHANNEL is None or not _ALARM_CHANNEL.get_busy():
            _ALARM_CHANNEL = sound.play(loops=-1)
    else:
        sound.play()

def stop_alarm():
    """
    Menghentikan alarm yang sedang diputar.
    """
    global _ALARM_CHANNEL
    if _ALARM_CHANNEL is not None:
        _ALARM_CHANNEL.stop()
        _ALARM_CHANNEL = None

def download_kaggle_dataset(dataset, file_path):
    """
    Mengunduh dataset Kaggle dan mengembalikan path lokal.
    """
    import kagglehub

    base_dir = Path(kagglehub.dataset_download(dataset))
    return base_dir / file_path if file_path else base_dir

def iter_image_files(root_path):
    """
    Mengiterasi file gambar dalam folder (rekursif) atau file tunggal.
    """
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    root = Path(root_path)

    if root.is_file():
        if root.suffix.lower() in image_exts:
            yield root
        return

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in image_exts:
            yield path

def extract_landmarks(face_mesh, image_bgr):
    """
    Ekstrak landmark wajah pertama dari gambar.
    """
    rgb_frame = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if not results.multi_face_landmarks:
        return None

    h, w, _ = image_bgr.shape
    face_landmarks = results.multi_face_landmarks[0]
    landmarks = []

    for landmark in face_landmarks.landmark:
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        landmarks.append([x, y])

    return np.array(landmarks)

def calibrate_ear_threshold_from_images(dataset_path, positive_labels, negative_labels=None):
    """
    Mengkalibrasi ambang EAR berdasarkan dataset gambar berlabel.
    """
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    positive_set = {label.strip().lower() for label in positive_labels if label.strip()}
    negative_set = None
    if negative_labels is not None:
        negative_set = {label.strip().lower() for label in negative_labels if label.strip()}

    pos_ear_values = []
    neg_ear_values = []

    for image_path in iter_image_files(dataset_path):
        label_name = image_path.parent.name.lower()

        if negative_set is not None:
            if label_name in positive_set:
                is_drowsy = True
            elif label_name in negative_set:
                is_drowsy = False
            else:
                continue
        else:
            is_drowsy = label_name in positive_set

        image = cv2.imread(str(image_path))
        if image is None:
            continue

        landmarks = extract_landmarks(face_mesh, image)
        if landmarks is None:
            continue

        left_eye = landmarks[LEFT_EYE_INDEXES]
        right_eye = landmarks[RIGHT_EYE_INDEXES]
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0

        if is_drowsy:
            pos_ear_values.append(avg_ear)
        else:
            neg_ear_values.append(avg_ear)

    if not pos_ear_values or not neg_ear_values:
        print("Kalibrasi gagal: label drowsy/awake tidak cukup.")
        return None

    pos_mean = float(np.mean(pos_ear_values))
    neg_mean = float(np.mean(neg_ear_values))
    threshold = (pos_mean + neg_mean) / 2.0

    print("=== Hasil Kalibrasi EAR ===")
    print(f"Jumlah drowsy: {len(pos_ear_values)}")
    print(f"Jumlah awake: {len(neg_ear_values)}")
    print(f"Rata-rata EAR drowsy: {pos_mean:.4f}")
    print(f"Rata-rata EAR awake: {neg_mean:.4f}")
    print(f"Rekomendasi EAR_THRESHOLD: {threshold:.4f}")

    return threshold

class DrowsinessDetector:
    def __init__(self, ear_threshold=0.25, head_tilt_threshold=30, alert_time=180, alarm_audio=None, alarm_interval=2.0):
        """
        Inisialisasi Drowsiness Detector
        
        Parameters:
        - ear_threshold: Batas EAR untuk mendeteksi mata tertutup (default: 0.25)
        - head_tilt_threshold: Batas sudut kepala menunduk dalam derajat (default: 30)
        - alert_time: Waktu dalam detik sebelum alarm berbunyi (default: 180 = 3 menit)
        """
        self.ear_threshold = ear_threshold
        self.head_tilt_threshold = head_tilt_threshold
        self.alert_time = alert_time
        self.alarm_audio = alarm_audio
        self.alarm_interval = alarm_interval
        
        # MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Status tracking
        self.drowsy_start_time = None
        self.is_drowsy = False
        self.alarm_on = False
        self.last_alarm_time = 0.0
        
        # Landmark indices untuk kepala
        self.NOSE_TIP = 1
        self.CHIN = 152
        
    def process_frame(self, frame):
        """
        Memproses setiap frame untuk deteksi kantuk
        """
        # Konversi BGR ke RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        h, w, _ = frame.shape
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Ekstrak koordinat landmark
                landmarks = []
                for landmark in face_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    landmarks.append([x, y])
                
                landmarks = np.array(landmarks)
                
                # Hitung EAR untuk kedua mata
                left_eye = landmarks[LEFT_EYE_INDEXES]
                right_eye = landmarks[RIGHT_EYE_INDEXES]
                
                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Hitung kemiringan kepala
                nose_tip = landmarks[self.NOSE_TIP]
                chin = landmarks[self.CHIN]
                head_tilt = calculate_head_tilt(nose_tip, chin)
                
                # Deteksi kantuk
                eyes_closed = avg_ear < self.ear_threshold
                head_down = head_tilt > self.head_tilt_threshold
                
                # Status kantuk
                current_drowsy = eyes_closed or head_down
                
                if current_drowsy:
                    if self.drowsy_start_time is None:
                        self.drowsy_start_time = time.time()
                    
                    elapsed_time = time.time() - self.drowsy_start_time

                    # Jika sudah melebihi waktu alert
                    if elapsed_time >= self.alert_time:
                        if not self.alarm_on:
                            self.alarm_on = True
                            self.last_alarm_time = 0.0

                        now = time.time()
                        if self.alarm_interval <= 0:
                            play_alarm(self.alarm_audio, loop=True)
                        elif now - self.last_alarm_time >= self.alarm_interval:
                            play_alarm(self.alarm_audio, loop=False)
                            self.last_alarm_time = now
                        # Tampilkan peringatan
                        cv2.putText(frame, "PERINGATAN: KANTUK TERDETEKSI!", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        # Tampilkan countdown
                        remaining_time = self.alert_time - elapsed_time
                        cv2.putText(frame, f"Waktu: {remaining_time:.1f}s", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    # Reset jika tidak mengantuk
                    self.drowsy_start_time = None
                    self.alarm_on = False
                    self.last_alarm_time = 0.0
                    stop_alarm()
                
                # Tampilkan informasi
                status_text = []
                if eyes_closed:
                    status_text.append("Mata Tertutup")
                if head_down:
                    status_text.append("Kepala Menunduk")
                
                cv2.putText(frame, f"EAR: {avg_ear:.2f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"Head Tilt: {head_tilt:.1f}", (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                if status_text:
                    cv2.putText(frame, " | ".join(status_text), (10, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Gambar landmark mata
                for point in left_eye:
                    cv2.circle(frame, tuple(point), 2, (0, 255, 0), -1)
                for point in right_eye:
                    cv2.circle(frame, tuple(point), 2, (0, 255, 0), -1)
        
        return frame
    
    def run(self):
        """
        Menjalankan detector dengan webcam
        """
        cap = cv2.VideoCapture(0)
        
        print("=== Drowsiness Detection System ===")
        print(f"EAR Threshold: {self.ear_threshold}")
        print(f"Head Tilt Threshold: {self.head_tilt_threshold}°")
        print(f"Alert Time: {self.alert_time} detik ({self.alert_time/60:.1f} menit)")
        print("\nTekan 'q' untuk keluar")
        print("Tekan 'r' untuk reset timer")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Gagal membaca frame dari kamera")
                break
            
            # Flip horizontal agar seperti cermin
            frame = cv2.flip(frame, 1)
            
            # Proses frame
            processed_frame = self.process_frame(frame)
            
            # Tampilkan frame
            cv2.imshow('Drowsiness Detection', processed_frame)
            
            # Keyboard controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.drowsy_start_time = None
                self.alarm_on = False
                print("Timer direset")
        
        cap.release()
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="Sistem deteksi kantuk")
    parser.add_argument("--kaggle-dataset", default="", help="ID dataset Kaggle, contoh: nexuswho/drowsiness-detection")
    parser.add_argument("--kaggle-path", default="", help="Subpath di dalam dataset, contoh: test/images")
    parser.add_argument("--dataset-dir", default="", help="Path dataset lokal (folder atau file gambar)")
    parser.add_argument("--calibrate-ear", action="store_true", help="Kalibrasi EAR dari dataset gambar")
    parser.add_argument("--positive-labels", default="drowsy,sleepy,closed", help="Label drowsy, dipisah koma")
    parser.add_argument("--negative-labels", default="", help="Label non-drowsy, dipisah koma (opsional)")
    parser.add_argument("--alarm-audio", default="", help="Path file audio wav/mp3 untuk alarm")
    parser.add_argument("--alarm-interval", type=float, default=0.0, help="Jeda alarm berulang (detik). 0 = loop tanpa jeda")
    args = parser.parse_args()

    # Konfigurasi
    EAR_THRESHOLD = 0.20  # Semakin kecil semakin sensitif untuk mata tertutup
    HEAD_TILT_THRESHOLD = 20  # Sudut dalam derajat
    ALERT_TIME = 60  # Waktu dalam detik (60 = 1 menit)

    if args.calibrate_ear:
        dataset_path = None

        if args.dataset_dir:
            dataset_path = Path(args.dataset_dir)
        elif args.kaggle_dataset:
            dataset_path = download_kaggle_dataset(args.kaggle_dataset, args.kaggle_path)

        if dataset_path is None or not dataset_path.exists():
            print("Dataset tidak ditemukan. Kalibrasi dilewati.")
        else:
            positive_labels = args.positive_labels.split(",") if args.positive_labels else []
            negative_labels = args.negative_labels.split(",") if args.negative_labels else None
            calibrated_threshold = calibrate_ear_threshold_from_images(
                dataset_path,
                positive_labels,
                negative_labels
            )
            if calibrated_threshold is not None:
                EAR_THRESHOLD = calibrated_threshold

    # Membuat dan menjalankan detector
    detector = DrowsinessDetector(
        ear_threshold=EAR_THRESHOLD,
        head_tilt_threshold=HEAD_TILT_THRESHOLD,
        alert_time=ALERT_TIME,
        alarm_audio=args.alarm_audio,
        alarm_interval=args.alarm_interval
    )

    detector.run()

if __name__ == "__main__":
    main()
