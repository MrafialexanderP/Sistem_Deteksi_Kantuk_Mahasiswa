let detectionActive = false;
let startTime = null;
let updateInterval = null;
let durationInterval = null;

async function startDetection() {
    try {
        const response = await fetch('/api/start', { method: 'POST' });
        if (response.ok) {
            detectionActive = true;
            startTime = Date.now();
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('recordingIndicator').classList.remove('hidden');
            document.getElementById('statusDot').classList.add('active');
            document.getElementById('statusText').textContent = 'Online';
            
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
            
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('recordingIndicator').classList.add('hidden');
            document.getElementById('statusDot').classList.remove('active');
            document.getElementById('statusText').textContent = 'Offline';
            
            document.getElementById('videoFeed').src = '';
            
            clearInterval(updateInterval);
            clearInterval(durationInterval);
            
            document.getElementById('statusValue').textContent = '-';
            document.getElementById('cnnLabelValue').textContent = 'unknown';
            document.getElementById('confidenceValue').textContent = '0.00';
            document.getElementById('earValue').textContent = '0.00';
            document.getElementById('perclosValue').textContent = '0.00';
            document.getElementById('fpsValue').textContent = '0.0';
            document.getElementById('durationValue').textContent = '00:00';
            document.getElementById('statusBar').style.width = '0%';
            document.getElementById('confidenceBar').style.width = '0%';
            document.getElementById('earBar').style.width = '0%';
            document.getElementById('perclosBar').style.width = '0%';
            document.getElementById('fpsBar').style.width = '0%';
            document.getElementById('durationBar').style.width = '0%';
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
    }, 100);
}

function updateStatus(data) {
    const status = data.status;
    const ear = data.ear;
    const perclos = data.perclos;
    const confidence = data.cnn_confidence;
    const cnnLabel = data.cnn_label;
    const fps = data.fps;
    
    // Update status
    document.getElementById('statusValue').textContent = 
        status === 'kantuk' ? 'Mengantuk' : 'Normal';
    document.getElementById('statusValue').style.color = 
        status === 'kantuk' ? 'var(--danger)' : 'var(--success)';
    
    const statusPercent = status === 'kantuk' ? 100 : 30;
    document.getElementById('statusBar').style.width = statusPercent + '%';

    // Update CNN label
    document.getElementById('cnnLabelValue').textContent = cnnLabel;

    // Update confidence
    document.getElementById('confidenceValue').textContent = confidence.toFixed(2);
    const confidencePercent = Math.min(confidence * 100, 100);
    document.getElementById('confidenceBar').style.width = confidencePercent + '%';

    // Update EAR
    document.getElementById('earValue').textContent = ear.toFixed(2);
    const earPercent = Math.min((ear / 0.5) * 100, 100);
    document.getElementById('earBar').style.width = earPercent + '%';
    
    // Update PERCLOS
    document.getElementById('perclosValue').textContent = perclos.toFixed(2);
    const perclosPercent = Math.min(perclos * 100, 100);
    document.getElementById('perclosBar').style.width = perclosPercent + '%';
    
    // Update FPS
    document.getElementById('fpsValue').textContent = fps.toFixed(1);
    const fpsPercent = Math.min((fps / 30) * 100, 100);
    document.getElementById('fpsBar').style.width = fpsPercent + '%';
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
