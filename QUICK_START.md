# 🎯 QUICK START - Sistem Deteksi Kantuk

## 📋 Persyaratan Awal
- ✅ Python 3.8+
- ✅ Virtual environment sudah aktif
- ✅ Webcam/Kamera tersedia

---

## 🚀 Langkah-Langkah Menjalankan

### 1️⃣ Aktivasi Virtual Environment
```powershell
cd "d:\Tugas\Semester 6\Viskom\Sistem_Deteksi_Kantuk_Mahasiswa"
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\.venv\Scripts\Activate.ps1")
```

### 2️⃣ Install Flask (jika belum ada)
```powershell
pip install Flask==3.0.0 Werkzeug==3.0.1
```

### 3️⃣ Jalankan Flask App
```powershell
python app.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### 4️⃣ Buka Browser
Ketik di address bar:
```
http://localhost:5000
```

---

## 🎮 Cara Menggunakan

### Mulai Deteksi
1. Klik button **"▶ Mulai"** atau tekan **Alt + S**
2. Video feed akan muncul dari webcam
3. Real-time metrics akan ter-update setiap 100ms

### Monitor Metrics
- **Status**: Normal / ⚠️ KANTUK
- **EAR**: Eye Aspect Ratio (threshold 0.25)
- **Head Tilt**: Kemiringan kepala (threshold 30°)
- **Drowsiness Time**: Durasi kantuk terdeteksi
- **FPS**: Performance monitoring
- **Duration**: Total waktu monitoring

### Hentikan Deteksi
1. Klik button **"⏹ Hentikan"** atau tekan **Alt + X**
2. Video feed akan stop
3. Semua metrics di-reset

---

## ⌨️ Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| **Alt + S** | Start detection |
| **Alt + X** | Stop detection |

---

## 🎨 Design Features
- **Color Palette**: Putih (dominan), Hitam, Biru Tua, Biru Muda
- **Responsive**: Desktop, Tablet, Mobile
- **Real-time**: Updates setiap 100ms
- **Modern UI**: Smooth animations & transitions

---

## 🔧 Konfigurasi (Optional)

Edit `config.py` untuk mengubah sensitivitas:

```python
EAR_THRESHOLD = 0.25              # Mata tertutup (lebih kecil = lebih sensitif)
HEAD_TILT_THRESHOLD = 30          # Kepala menunduk (lebih kecil = lebih sensitif)
ALERT_TIME = 30                   # Alarm setelah N detik
CAMERA_INDEX = 0                  # 0=default, 1=external camera
SHOW_EYE_LANDMARKS = True         # Tampilkan garis mata
SHOW_DEBUG_INFO = True            # Tampilkan info debug
```

---

## ❌ Troubleshooting

### Camera tidak terdeteksi
```
→ Edit config.py: CAMERA_INDEX = 1 (atau angka lain)
```

### Video feed blank/hitam
```
→ Refresh halaman (Ctrl+R)
→ Pastikan Flask app running
→ Periksa console browser (F12)
```

### Port 5000 sudah digunakan
```
→ Edit app.py baris terakhir: port=5001 (atau port lain)
```

### Alarm tidak berbunyi
```
→ Cek volume speaker
→ Refresh halaman
→ Cek permission browser
```

---

## 📊 File Structure
```
├── app.py                    # Flask backend
├── config.py                 # Configuration (jangan diubah)
├── drowsiness_detector.py    # Detection logic (jangan diubah)
├── templates/
│   └── index.html            # Frontend HTML
├── static/
│   ├── css/
│   │   └── style.css         # Styling
│   └── js/
│       └── script.js         # JavaScript logic
└── requirements.txt          # Dependencies
```

---

## ✅ Status
✅ Frontend created  
✅ Flask app ready  
✅ All files tested  
✅ No errors found  

**Ready to use!** 🎉
