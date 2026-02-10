import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
from scipy.spatial import distance as dist

pygame.mixer.init()

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
    return abs(angle)

# Fungsi untuk membunyikan alarm
def play_alarm():
    """
    Membunyikan alarm suara
    """
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
    sound.play()

class DrowsinessDetector:
    def __init__(self, ear_threshold=0.25, head_tilt_threshold=30, alert_time=180):
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
        
        # Landmark indices untuk mata
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
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
                left_eye = landmarks[self.LEFT_EYE]
                right_eye = landmarks[self.RIGHT_EYE]
                
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
                            play_alarm()
                            self.alarm_on = True
                        
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
    # Konfigurasi
    EAR_THRESHOLD = 0.25  # Semakin kecil semakin sensitif untuk mata tertutup
    HEAD_TILT_THRESHOLD = 30  # Sudut dalam derajat
    ALERT_TIME = 180  # Waktu dalam detik (180 = 3 menit, 300 = 5 menit)
    
    # Membuat dan menjalankan detector
    detector = DrowsinessDetector(
        ear_threshold=EAR_THRESHOLD,
        head_tilt_threshold=HEAD_TILT_THRESHOLD,
        alert_time=ALERT_TIME
    )
    
    detector.run()

if __name__ == "__main__":
    main()
