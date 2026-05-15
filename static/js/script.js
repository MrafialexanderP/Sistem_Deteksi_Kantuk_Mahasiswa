/**
 * Student Drowsiness Detection - Frontend Script
 * Polls /api/status and updates stat cards to match backend response.
 *
 * Backend API response format:
 *   { status: "Normal"|"Drowsy", perclos: float, eye_state: string, yawn: bool|string, detection_active: bool }
 */

let detectionActive = false;
let startTime = null;
let updateInterval = null;
let durationInterval = null;
let previousStatus = null; // Track status transitions for alert

async function startDetection() {
    try {
        const response = await fetch('/api/start', { method: 'POST' });
        if (response.ok) {
            detectionActive = true;
            startTime = Date.now();
            previousStatus = null;
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('recordingIndicator').classList.remove('hidden');
            
            const feed = document.getElementById('videoFeed');
            feed.src = '/video_feed?' + Date.now();
            
            startUpdates();
            startDuration();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function stopDetection() {
    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        if (response.ok) {
            detectionActive = false;
            previousStatus = null;
            
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('recordingIndicator').classList.add('hidden');
            
            document.getElementById('videoFeed').src = '';
            
            clearInterval(updateInterval);
            clearInterval(durationInterval);
            
            // Reset all stat values
            document.getElementById('statusValue').textContent = '-';
            document.getElementById('statusValue').className = 'stat-value';
            document.getElementById('eyeStateValue').textContent = '-';
            document.getElementById('yawnValue').textContent = '-';
            document.getElementById('perclosValue').textContent = '0.00';
            document.getElementById('durationValue').textContent = '00:00';

            document.getElementById('statusBar').style.width = '0%';
            document.getElementById('eyeStateBar').style.width = '0%';
            document.getElementById('yawnBar').style.width = '0%';
            document.getElementById('perclosBar').style.width = '0%';
            document.getElementById('durationBar').style.width = '0%';

            // Reset bar colors
            document.getElementById('statusBar').className = 'stat-bar-fill';
            document.getElementById('eyeStateBar').className = 'stat-bar-fill';
            document.getElementById('yawnBar').className = 'stat-bar-fill';
            document.getElementById('perclosBar').className = 'stat-bar-fill';

            // Reset status card highlight
            const statusCard = document.getElementById('statusCard');
            if (statusCard) {
                statusCard.classList.remove('stat-card-danger', 'stat-card-safe');
            }

            // Hide drowsy alert
            hideDrowsyAlert();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function startUpdates() {
    updateInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            updateStatus(data);
        } catch (error) {
            console.error('Error:', error);
        }
    }, 250);
}

/**
 * Updates all stat cards from the API response.
 * Maps backend fields to the correct UI elements.
 */
function updateStatus(data) {
    const status = data.status;         // "Normal" or "Drowsy"
    const eyeState = data.eye_state;    // "Open_Eyes", "Closed_Eyes", "-", or null
    const yawn = data.yawn;             // true, false, or "-"
    const perclos = data.perclos;       // float 0.0 - 1.0

    // ---- Status Card ----
    const statusEl = document.getElementById('statusValue');
    const statusBar = document.getElementById('statusBar');
    const statusCard = document.getElementById('statusCard');

    const isDrowsy = (status === 'Drowsy');
    statusEl.textContent = isDrowsy ? 'Mengantuk' : 'Normal';
    statusEl.className = 'stat-value ' + (isDrowsy ? 'text-danger' : 'text-success');
    statusBar.style.width = isDrowsy ? '100%' : '30%';
    statusBar.className = 'stat-bar-fill ' + (isDrowsy ? 'bar-danger' : 'bar-success');

    if (statusCard) {
        statusCard.classList.toggle('stat-card-danger', isDrowsy);
        statusCard.classList.toggle('stat-card-safe', !isDrowsy);
    }

    // Drowsy alert overlay
    if (isDrowsy) {
        showDrowsyAlert();
    } else {
        hideDrowsyAlert();
    }

    // ---- Eye State Card ----
    const eyeEl = document.getElementById('eyeStateValue');
    const eyeBar = document.getElementById('eyeStateBar');

    let eyeDisplay = '-';
    let eyeClosed = false;
    if (eyeState === 'Closed_Eyes') {
        eyeDisplay = 'Tertutup';
        eyeClosed = true;
    } else if (eyeState === 'Open_Eyes') {
        eyeDisplay = 'Terbuka';
    }
    eyeEl.textContent = eyeDisplay;
    eyeEl.className = 'stat-value ' + (eyeClosed ? 'text-warning' : '');
    eyeBar.style.width = eyeClosed ? '100%' : (eyeState === 'Open_Eyes' ? '30%' : '0%');
    eyeBar.className = 'stat-bar-fill ' + (eyeClosed ? 'bar-warning' : 'bar-success');

    // ---- Yawn Card ----
    const yawnEl = document.getElementById('yawnValue');
    const yawnBar = document.getElementById('yawnBar');

    let isYawning = false;
    let yawnDisplay = '-';
    if (yawn === true || yawn === 'True' || yawn === 'true') {
        yawnDisplay = 'Ya';
        isYawning = true;
    } else if (yawn === false || yawn === 'False' || yawn === 'false') {
        yawnDisplay = 'Tidak';
    }
    yawnEl.textContent = yawnDisplay;
    yawnEl.className = 'stat-value ' + (isYawning ? 'text-danger' : '');
    yawnBar.style.width = isYawning ? '100%' : '15%';
    yawnBar.className = 'stat-bar-fill ' + (isYawning ? 'bar-danger' : 'bar-success');

    // ---- PERCLOS Card ----
    const perclosEl = document.getElementById('perclosValue');
    const perclosBar = document.getElementById('perclosBar');
    const perclosVal = typeof perclos === 'number' ? perclos : 0;
    
    perclosEl.textContent = perclosVal.toFixed(2);
    const perclosPercent = Math.min(perclosVal * 100, 100);
    perclosBar.style.width = perclosPercent + '%';

    const perclosHigh = perclosVal > 0.4;
    perclosEl.className = 'stat-value ' + (perclosHigh ? 'text-danger' : '');
    perclosBar.className = 'stat-bar-fill ' + (perclosHigh ? 'bar-danger' : '');

    // Track status transition
    previousStatus = status;
}

// ---- Drowsy Alert Overlay ----
function showDrowsyAlert() {
    const alert = document.getElementById('drowsyAlert');
    if (alert) alert.classList.remove('hidden');
}

function hideDrowsyAlert() {
    const alert = document.getElementById('drowsyAlert');
    if (alert) alert.classList.add('hidden');
}

function startDuration() {
    let seconds = 0;
    durationInterval = setInterval(() => {
        seconds++;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        document.getElementById('durationValue').textContent = 
            `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        
        const durationPercent = Math.min((seconds / 1800) * 100, 100);
        document.getElementById('durationBar').style.width = durationPercent + '%';
    }, 1000);
}

// ====== REGISTER STUDENT INFO TO BACKEND ======
// Sends logged-in student's name & NIM so admin dashboard can display them
function registerStudentToBackend() {
    const userStr = localStorage.getItem('user');
    if (!userStr) return;

    const user = JSON.parse(userStr);
    fetch('/api/set_student', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: user.name || 'Mahasiswa',
            nim: user.nim || '-'
        })
    }).catch(err => console.warn('Failed to register student:', err));
}

document.addEventListener('DOMContentLoaded', registerStudentToBackend);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key === 's') {
        e.preventDefault();
        if (!detectionActive) startDetection();
    }
    if (e.altKey && e.key === 'x') {
        e.preventDefault();
        if (detectionActive) stopDetection();
    }
});

// Cleanup on unload
window.addEventListener('beforeunload', () => {
    if (detectionActive) stopDetection();
});
