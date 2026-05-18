/**
 * Admin Dashboard - Priority-Based Real-time Monitoring
 * Polls /api/status every 1 second.
 * Sorts students by urgency: kantuk (3) > offline (2) > normal (1)
 */

// ====== CONSTANTS ======
const POLL_INTERVAL_MS = 1000;

// ====== STATE ======
let pollingInterval = null;
let previousDisplayStatus = null; // tracks the real student's previous display status

// ====== DUMMY STUDENTS ======
// These represent other students in the class.
// id is a fixed internal reference — NOT used for row numbering.
const dummyStudents = [
    { id: 2, name: 'Siti Nurhaliza', nim: '12345002', active: true, status: 'kantuk' },
    { id: 5, name: 'Ratna Wijaya', nim: '12345005', active: true, status: 'normal' },
    { id: 3, name: 'Ahmad Hidayat', nim: '12345001', active: true, status: 'kantuk' },
    { id: 7, name: 'Dewi Lestari', nim: '12345007', active: true, status: 'normal' },
    { id: 4, name: 'Budi Santoso', nim: '12345003', active: true, status: 'normal' },
    { id: 6, name: 'Eka Prasetyo', nim: '12345004', active: false, status: 'normal' },
    { id: 8, name: 'Fajar Ramadan', nim: '12345006', active: false, status: 'normal' },
];

// ====== REAL STUDENT (updated from /api/status) ======
let activeStudent = {
    id: 1,
    name: 'Mahasiswa Aktif',
    nim: '-',
    active: true,
    status: 'kantuk',
};

// ====== HELPER: DOM shortcut ======
function el(id) {
    return document.getElementById(id);
}

// ====== STATUS LOGIC ======
/**
 * Returns the effective display status for a student:
 *   - 'offline'  → when active === false (camera off)
 *   - 'kantuk'   → when active === true AND status === 'kantuk'
 *   - 'normal'   → when active === true AND status === 'normal'
 */
function getDisplayStatus(student) {
    if (!student.active) return 'offline';
    return student.status === 'kantuk' ? 'kantuk' : 'normal';
}

// ====== PRIORITY SCORING ======
/**
 * Returns a priority score used for descending sort:
 *   kantuk  → 3  (CRITICAL — needs immediate attention)
 *   offline → 2  (WARNING  — ask student to turn on camera)
 *   normal  → 1  (SAFE     — no action needed)
 */
function getPriority(student) {
    const ds = getDisplayStatus(student);
    if (ds === 'kantuk') return 3;
    if (ds === 'offline') return 2;
    return 1; // normal
}

// ====== RENDER: SUMMARY BAR ======
function updateSummaryBar() {
    const all = [activeStudent, ...dummyStudents];
    const total = all.length;
    const aktivCount = all.filter(s => s.active).length;
    const kantukCount = all.filter(s => getDisplayStatus(s) === 'kantuk').length;

    if (el('totalMahasiswa')) el('totalMahasiswa').textContent = total;
    if (el('aktivCount')) el('aktivCount').textContent = aktivCount;
    if (el('mengantukCount')) el('mengantukCount').textContent = kantukCount;
}

// ====== RENDER: STUDENT TABLE ======
/**
 * Merges real + dummy students, sorts by priority (descending),
 * and re-renders the entire tbody.
 * Row numbers reflect sorted order (idx + 1), NOT fixed IDs.
 */
function renderStudentTable() {
    const tbody = el('studentTableBody');
    if (!tbody) return;

    // Merge and sort — re-run on every poll
    const all = [activeStudent, ...dummyStudents];
    const sorted = all.slice().sort((a, b) => getPriority(b) - getPriority(a));

    tbody.innerHTML = '';

    sorted.forEach((s, idx) => {
        const display = getDisplayStatus(s);

        let badgeClass = 'badge-normal';
        let statusText = 'Normal';
        let rowClass = '';

        if (display === 'kantuk') {
            badgeClass = 'badge-kantuk';
            statusText = 'Mengantuk';
            rowClass = 'danger-row';
        } else if (display === 'offline') {
            badgeClass = 'badge-offline';
            statusText = 'Offline';
            rowClass = 'warning-row';
        }

        const tr = document.createElement('tr');
        if (rowClass) tr.classList.add(rowClass);

        // "No" column = sorted position (idx + 1), NOT the student's id
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${s.name}</td>
            <td>${s.nim}</td>
            <td><span class="camera-badge ${s.active ? 'online' : 'offline'}">${s.active ? 'Online' : 'Offline'}</span></td>
            <td><span class="badge ${badgeClass}">${statusText}</span></td>
        `;

        tbody.appendChild(tr);
    });

    updateAlertList();
}

// ====== RENDER: ALERT LIST ======
function updateAlertList() {
    const alertSection = el('alertSection');
    const alertList = el('alertList');
    if (!alertSection || !alertList) return;

    const all = [activeStudent, ...dummyStudents];
    const kantukStudents = all.filter(s => getDisplayStatus(s) === 'kantuk');

    if (kantukStudents.length === 0) {
        alertSection.classList.add('hidden');
        return;
    }

    alertSection.classList.remove('hidden');
    alertList.innerHTML = '';

    kantukStudents.forEach(s => {
        const p = document.createElement('p');
        p.textContent = s.name + (s.id === activeStudent.id ? ' (Aktif)' : '');
        alertList.appendChild(p);
    });
}

// ====== ALERTS / TOAST / SOUND ======
/**
 * Only triggers when the real student transitions from non-kantuk → kantuk.
 * Uses previousDisplayStatus to prevent repeated alerts on the same state.
 */
function checkAlertTrigger(prev, current) {
    if (prev !== 'kantuk' && current === 'kantuk') {
        onKantukDetected();
    }
}

function onKantukDetected() {
    playAlertSound();
    showToast('Mahasiswa mengantuk terdeteksi!');
}

function playAlertSound() {
    const audio = el('alertSound');
    if (!audio) return;
    audio.currentTime = 0;
    audio.play().catch(e => console.warn('Audio play failed:', e));
}

function showToast(message, duration = 4000) {
    const toast = el('toast');
    const msg = el('toastMessage');
    if (!toast || !msg) return;

    msg.textContent = message;
    toast.classList.remove('hidden');
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hidden');
    }, duration);
}

// ====== POLLING / API ======
async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        // Update ONLY the real (active) student from API response
        activeStudent.active = !!data.detection_active;
        activeStudent.status = data.status === 'Drowsy' ? 'kantuk' : 'normal';

        // Update student identity from backend (set by student page on login)
        if (data.student_name) activeStudent.name = data.student_name;
        if (data.student_nim)  activeStudent.nim  = data.student_nim;

        const currentDisplay = getDisplayStatus(activeStudent);

        // Check if alert should fire (normal → kantuk transition)
        checkAlertTrigger(previousDisplayStatus, currentDisplay);

        // Re-render everything
        updateSummaryBar();
        renderStudentTable();

        // Save for next comparison
        previousDisplayStatus = currentDisplay;

    } catch (err) {
        console.error('Error fetching /api/status:', err);
        // On network error → treat real student as offline
        activeStudent.active = false;
        const currentDisplay = getDisplayStatus(activeStudent);
        updateSummaryBar();
        renderStudentTable();
        previousDisplayStatus = currentDisplay;
    }
}

// ====== POLLING CONTROL ======
function startPolling() {
    fetchStatus(); // immediate first fetch
    pollingInterval = setInterval(fetchStatus, POLL_INTERVAL_MS);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// ====== INIT ======
function initAdminDashboard() {
    // Render initial state before first API response arrives
    previousDisplayStatus = getDisplayStatus(activeStudent);
    updateSummaryBar();
    renderStudentTable();

    // Start 1-second polling loop
    startPolling();
}

document.addEventListener('DOMContentLoaded', initAdminDashboard);
window.addEventListener('beforeunload', stopPolling);
