# Configuration file untuk Drowsiness Detection System

# ===== THRESHOLD SETTINGS =====

# Eye Aspect Ratio Threshold
# Semakin kecil nilai ini, semakin sensitif deteksi mata tertutup
# Range yang disarankan: 0.20 - 0.30
EAR_THRESHOLD = 0.25

# Head Tilt Threshold (dalam derajat)
# Semakin kecil nilai ini, semakin sensitif deteksi kepala menunduk
# Range yang disarankan: 20 - 40
HEAD_TILT_THRESHOLD = 30

# ===== TIMING SETTINGS =====

# Waktu sebelum alarm berbunyi (dalam detik)
# 180 detik = 3 menit
# 300 detik = 5 menit
ALERT_TIME = 180  # Ubah ke 300 untuk 5 menit

# ===== CAMERA SETTINGS =====

# Camera Index (0 = default camera, 1 = external camera)
CAMERA_INDEX = 0

# ===== ALARM SETTINGS =====

# Frekuensi alarm dalam Hz
ALARM_FREQUENCY = 1000

# Durasi alarm dalam milliseconds
ALARM_DURATION = 500

# ===== DISPLAY SETTINGS =====

# Tampilkan landmark mata
SHOW_EYE_LANDMARKS = True

# Tampilkan informasi debug
SHOW_DEBUG_INFO = True
