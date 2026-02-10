# Sistem Deteksi Kantuk Karyawan

Sistem ini menggunakan computer vision untuk mendeteksi apakah karyawan mengantuk di depan komputer dengan mendeteksi:
- **Mata tertutup** (menggunakan Eye Aspect Ratio - EAR)
- **Kepala menunduk** (menggunakan head pose estimation)

## Fitur

✅ Deteksi real-time menggunakan webcam
✅ Alarm suara ketika kantuk terdeteksi lebih dari waktu yang ditentukan
✅ Visualisasi eye landmarks
✅ Display informasi EAR (Eye Aspect Ratio) dan sudut kepala
✅ Configurable threshold dan waktu alert

## Instalasi

1. **Install Python** (versi 3.8 atau lebih baru)

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Cara Menggunakan

### Menjalankan Program

```bash
python drowsiness_detector.py
```

### CNN + PERCLOS (Training dan Realtime)

Dataset perlu struktur folder seperti berikut:

```
train/
  drowsy/
  awake/
val/
  drowsy/
  awake/
test/
  drowsy/
  awake/
```

**Training model CNN:**

```bash
python cnn_perclos.py --mode train --train-dir train --val-dir val --test-dir test --image-size 224 --epochs 10
```

**Realtime (CNN + PERCLOS):**

```bash
python cnn_perclos.py --mode realtime --model-path drowsiness_cnn.keras --perclos-window 120 --perclos-threshold 0.4
```

### Kontrol Keyboard

- **`q`** - Keluar dari program
- **`r`** - Reset timer

### Konfigurasi

Anda dapat mengubah parameter di file `drowsiness_detector.py` pada fungsi `main()`:

```python
# Konfigurasi
EAR_THRESHOLD = 0.25  # Semakin kecil semakin sensitif (0.2 - 0.3 recommended)
HEAD_TILT_THRESHOLD = 30  # Sudut dalam derajat (20 - 40 recommended)
ALERT_TIME = 180  # Waktu dalam detik
```

**Waktu Alert:**
- 180 detik = 3 menit
- 300 detik = 5 menit

**Catatan:**
- `EAR_THRESHOLD`: Nilai 0.25 artinya jika EAR di bawah 0.25, mata dianggap tertutup
  - Nilai lebih kecil (0.2) = lebih sensitif
  - Nilai lebih besar (0.3) = kurang sensitif

- `HEAD_TILT_THRESHOLD`: Sudut kemiringan kepala dalam derajat
  - Nilai lebih kecil (20°) = lebih sensitif terhadap kepala menunduk
  - Nilai lebih besar (40°) = kurang sensitif

## Cara Kerja

1. **Face Detection**: Menggunakan MediaPipe Face Mesh untuk mendeteksi wajah dan landmark
2. **Eye Aspect Ratio (EAR)**: Menghitung rasio aspek mata untuk mendeteksi mata tertutup
3. **Head Pose**: Menghitung sudut kepala untuk mendeteksi kepala menunduk
4. **Timer**: Menghitung durasi kantuk
5. **Alarm**: Membunyikan alarm jika kantuk terdeteksi melebihi waktu yang ditentukan

## Tampilan Informasi

- **EAR**: Eye Aspect Ratio (nilai normal: 0.25-0.4, tertutup: <0.25)
- **Head Tilt**: Sudut kemiringan kepala dalam derajat
- **Status**: "Mata Tertutup" dan/atau "Kepala Menunduk"
- **Timer**: Countdown sebelum alarm berbunyi
- **Peringatan**: Alert merah ketika alarm aktif

## Troubleshooting

### Kamera tidak terdeteksi
- Pastikan webcam terhubung
- Coba ubah `cv2.VideoCapture(0)` menjadi `cv2.VideoCapture(1)` jika ada multiple camera

### Terlalu sensitif / Kurang sensitif
- Sesuaikan `EAR_THRESHOLD` dan `HEAD_TILT_THRESHOLD`
- Nilai yang lebih kecil = lebih sensitif
- Nilai yang lebih besar = kurang sensitif

### Alarm tidak berbunyi
- Pastikan speaker/audio output berfungsi
- Cek volume sistem

## Requirements

- Python 3.8+
- Webcam
- Windows/Linux/MacOS

## Library yang Digunakan

- **OpenCV**: Computer vision dan video capture
- **MediaPipe**: Face mesh detection
- **Pygame**: Audio/sound generation
- **NumPy**: Numerical computations
- **SciPy**: Distance calculations

## Lisensi

MIT License
