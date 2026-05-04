# 🚀 Quick Start Routing Guide

## Akses Aplikasi

### Port
```
http://127.0.0.1:5000
```

## Routes Utama

### 1. **LOGIN** 
```
GET http://127.0.0.1:5000/login
```
- Masukkan NIM dan Password
- Pilihan 1: NIM = `admin` → masuk sebagai Admin
- Pilihan 2: NIM = `12345` (atau apapun) → masuk sebagai Student

### 2. **REGISTER**
```
GET http://127.0.0.1:5000/register
```
- Isi form: Nama, NIM, Email, Password, Konfirmasi Password
- Auto-redirect ke `/admin` atau `/student` setelah register

### 3. **STUDENT PAGE** (Halaman Deteksi Kamera)
```
GET http://127.0.0.1:5000/student
```
- Akses hanya untuk user student
- Tombol: Mulai / Hentikan
- Lihat real-time: Status, CNN, Confidence, EAR, PERCLOS, FPS, Duration

### 4. **ADMIN DASHBOARD** (Halaman Monitoring)
```
GET http://127.0.0.1:5000/admin
```
- Akses hanya untuk user admin
- Real-time monitoring mahasiswa
- Tabel daftar mahasiswa
- Toast notification saat ada yang mengantuk
- Alert sound otomatis

---

## Test Scenarios

### Scenario 1: Login Sebagai Student
```
1. Buka http://127.0.0.1:5000/login
2. NIM: 12345
3. Password: (apa saja, misal: password123)
4. Click Login
5. Auto-redirect ke /student
6. Lihat camera detection page
```

### Scenario 2: Login Sebagai Admin
```
1. Buka http://127.0.0.1:5000/login
2. NIM: admin
3. Password: (apa saja, misal: admin123)
4. Click Login
5. Auto-redirect ke /admin
6. Lihat monitoring dashboard
```

### Scenario 3: Register Baru
```
1. Buka http://127.0.0.1:5000/register
2. Isi semua field:
   - Nama: Budi Santoso
   - NIM: 12346
   - Email: budi@student.com
   - Password: password123
   - Konfirmasi: password123
3. Click Daftar
4. Auto-redirect ke /student (atau /admin jika NIM=admin)
```

### Scenario 4: Logout
```
1. Click tombol "Logout" di top-right
2. Session dihapus dari localStorage
3. Auto-redirect ke /login
```

---

## API Endpoints

### Status Real-time
```
GET /api/status
Response:
{
  "status": "normal" atau "kantuk",
  "ear": 0.25,
  "perclos": 0.40,
  "cnn_confidence": 0.95,
  "cnn_label": "Open_Eyes",
  "fps": 30.0,
  "detection_active": true
}
```

### Start Detection
```
POST /api/start
Response: {"status": "started"}
```

### Stop Detection
```
POST /api/stop
Response: {"status": "stopped"}
```

### Config Thresholds
```
GET /api/config
Response:
{
  "ear_threshold": 0.25,
  "perclos_threshold": 0.40,
  "perclos_window": 120
}
```

### Video Stream
```
GET /video_feed
Response: MJPEG stream (untuk img tag)
```

---

## File Structure

```
templates/
├── login.html          # Login page
├── register.html       # Register page
├── index.html          # Student detection page
└── admin.html          # Admin monitoring page

static/
├── css/
│   └── style.css       # All styling (auth, student, admin)
└── js/
    ├── auth.js         # Session management & routing
    ├── admin.js        # Admin polling & notifications
    └── script.js       # Student page detection controls
```

---

## Session Management

### localStorage Keys
```javascript
// User object stored in localStorage
user = {
  "nim": "12345",
  "name": "Nama Mahasiswa",
  "email": "email@student.com",
  "role": "student" // atau "admin"
}
```

### Check Session (Client-side)
```javascript
const user = JSON.parse(localStorage.getItem('user'));
if (user && user.role === 'admin') {
  console.log('Admin:', user.name);
}
```

### Clear Session (Logout)
```javascript
localStorage.removeItem('user');
window.location.href = '/login';
```

---

## Troubleshooting

### Masalah: "Halaman tidak ditemukan"
**Solusi:** Pastikan Flask server running di port 5000
```bash
python app.py
```

### Masalah: Login tapi tidak redirect
**Solusi:** Buka Developer Console (F12) → Console tab
```javascript
// Cek localStorage
console.log(localStorage.getItem('user'));

// Cek current path
console.log(window.location.pathname);
```

### Masalah: Admin tidak bisa akses monitoring
**Solusi:** Pastikan NIM = "admin" saat login
```javascript
// Cek role di console
const user = JSON.parse(localStorage.getItem('user'));
console.log(user.role); // harus "admin"
```

### Masalah: Toast notification tidak muncul
**Solusi:** 
1. Buka /admin (bukan /student)
2. Start detection di student page
3. Status harus berubah ke "kantuk"
4. Toast akan muncul di admin page

---

## Notes

✅ **Sudah Jalan:**
- Login/Register dengan role detection
- Role-based page access
- Real-time /api/status polling
- Toast notifications
- Audio alert element
- Logout functionality

⚠️ **Perhatian:**
- Audio file `/static/alarm.mp3` harus ada untuk alert sound
- Gunakan format MP3 untuk kompatibilitas browser
- Session hanya di localStorage (tidak di backend)

---

**Ready to test?** 🎉

```bash
# Start server
python app.py

# Open browser
http://127.0.0.1:5000
```
