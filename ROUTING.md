# Routing System Documentation

## Flask Routes (Backend)

### Authentication Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Redirect to login page |
| `/login` | GET | Display login page |
| `/register` | GET | Display registration page |

### Page Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/student` | GET | Student detection page (index.html) |
| `/admin` | GET | Admin monitoring dashboard |
| `/index.html` | GET | Fallback for direct index.html access |

### Video/Stream Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/video_feed` | GET | Real-time video stream (MJPEG) |

### API Routes
| Route | Method | Description | Response |
|-------|--------|-------------|----------|
| `/api/start` | POST | Start detection | `{'status': 'started'}` |
| `/api/stop` | POST | Stop detection | `{'status': 'stopped'}` |
| `/api/status` | GET | Get current status | JSON with detection data |
| `/api/config` | GET | Get configuration | JSON with thresholds |

## Frontend Routes (URL Paths)

### Access Flow

```
┌─────────────┐
│   127.0.0.1:5000/   │
│   (or any route)    │
└──────────┬──────────┘
           │
           ├─ Not Logged In?
           │  ↓
           ├─→ /login (login.html)
           │   ├─ Enter NIM + Password
           │   └─ Click "Daftar di sini" → /register
           │
           ├─ Admin Login (NIM="admin")?
           │  ↓
           │  → /admin (admin.html)
           │    ├─ Real-time monitoring
           │    ├─ Student table
           │    └─ Logout → /login
           │
           └─ Student Login (NIM≠"admin")?
              ↓
              → /student (index.html)
                 ├─ Camera detection
                 ├─ Stats display
                 └─ Logout → /login
```

## Route Details

### 1. `/login` - Login Page
**File:** `templates/login.html`

**Fields:**
- NIM (text input)
- Password (password input)

**Behavior:**
- Display login form
- On submit:
  - If NIM="admin" → Store as admin role
  - Otherwise → Store as student role
  - Save user to localStorage
  - Redirect to `/admin` or `/student`

**Link:**
- "Daftar di sini" → `/register`

---

### 2. `/register` - Registration Page
**File:** `templates/register.html`

**Fields:**
- Name (text input)
- NIM (text input)
- Email (email input)
- Password (password input)
- Confirm Password (password input)

**Behavior:**
- Display registration form
- Validate inputs
- On submit:
  - Save user to localStorage
  - Show success message (1 second)
  - Redirect to `/admin` or `/student`

**Link:**
- "Login di sini" → `/login`

---

### 3. `/student` - Student Detection Page
**File:** `templates/index.html`

**Components:**
- Header with navbar:
  - Title: "Deteksi Kantuk Mahasiswa"
  - User greeting: "Halo, [Nama]"
  - Logout button
- Video stream from `/video_feed`
- Control buttons: Start / Stop
- Stats cards: Status, CNN, Confidence, EAR, PERCLOS, FPS, Duration

**API Calls:**
- POST `/api/start` - Start detection
- POST `/api/stop` - Stop detection
- GET `/api/status` - Update stats (every 100ms)
- GET `/api/config` - Get thresholds (on load)

**Behavior:**
- User can see real-time camera feed
- Stats update automatically
- Audio alert on detection
- Logout clears session and goes to `/login`

---

### 4. `/admin` - Admin Dashboard
**File:** `templates/admin.html`

**Components:**
- Header with navbar:
  - Title: "Dashboard Dosen"
  - User greeting: "Halo, [Nama]"
  - Logout button
- Status display:
  - Mahasiswa Aktif (from `/api/status`)
  - Kamera (from `/api/status`)
- Student monitoring table:
  - Row 1: Real data from API
  - Rows 2-5: Dummy student data
  - Columns: No, Nama, NIM, Kamera, Status
- Toast notification system
- Audio alert system

**API Calls:**
- GET `/api/status` - Poll every 1 second
  - Updates table row 1
  - Triggers toast if status="kantuk"
  - Plays alert sound

**Behavior:**
- Real-time monitoring of active student
- Toast shows "PERINGATAN: Mahasiswa terdeteksi mengantuk!"
- Audio alert plays when drowsiness detected
- Dummy students shown as example
- Logout clears session and goes to `/login`

---

## Session Management

### localStorage Structure
```json
{
  "user": {
    "nim": "12345",
    "name": "Nama Mahasiswa",
    "email": "email@student.com",
    "role": "student"
  }
}
```

### Authentication Checks
1. **On page load:** `checkAuthentication()` from `auth.js`
   - If not logged in → redirect to `/login`
   - If admin accessing `/student` → redirect to `/admin`
   - If student accessing `/admin` → redirect to `/student`
   - Update navbar with user info

2. **On logout:** `logout()` from `auth.js`
   - Clear localStorage
   - Redirect to `/login`

---

## Testing URLs

### Login/Register
```
http://127.0.0.1:5000/login          # Login page
http://127.0.0.1:5000/register       # Register page
```

### Student User (NIM = "12345")
```
http://127.0.0.1:5000/student        # Student detection page
http://127.0.0.1:5000/               # Auto-redirects to /login
```

### Admin User (NIM = "admin")
```
http://127.0.0.1:5000/admin          # Admin dashboard
http://127.0.0.1:5000/               # Auto-redirects to /login
```

### API Endpoints
```
http://127.0.0.1:5000/api/status     # Get current status
http://127.0.0.1:5000/api/config     # Get configuration
http://127.0.0.1:5000/video_feed     # Video stream
```

---

## Code Flow

### 1. User Visits `/`
```
GET /
  ↓
Flask: render_template('login.html')
  ↓
Browser shows login page
```

### 2. User Submits Login Form
```
Form submit (client-side)
  ↓
JavaScript creates user object
  ↓
localStorage.setItem('user', JSON.stringify(user))
  ↓
window.location.href = '/admin' or '/student'
  ↓
Browser requests GET /admin or /student
  ↓
auth.js checkAuthentication() validates role
  ↓
If valid: Show page
  If invalid: redirect to correct page
```

### 3. User on `/admin` Page
```
GET /admin
  ↓
Flask: render_template('admin.html')
  ↓
Browser loads admin.js
  ↓
admin.js: startPolling() (every 1 second)
  ↓
Fetch GET /api/status
  ↓
Update table row 1
  ↓
Check if status changed to 'kantuk'
  ↓
If yes: Show toast + Play alert
```

### 4. User Clicks Logout
```
Click logout button
  ↓
JavaScript: logout()
  ↓
localStorage.removeItem('user')
  ↓
window.location.href = '/login'
  ↓
Browser requests GET /login
  ↓
auth.js: No user in localStorage
  ↓
Show login page
```

---

## Summary

| Component | Routes | Files |
|-----------|--------|-------|
| **Login** | `/login` | login.html |
| **Register** | `/register` | register.html |
| **Student** | `/student` | index.html |
| **Admin** | `/admin` | admin.html |
| **Video** | `/video_feed` | - |
| **API** | `/api/*` | - |
| **Auth** | - | auth.js |
| **Admin Logic** | - | admin.js |

All routes are now fully connected with proper Flask routing and frontend handling! 🎉
