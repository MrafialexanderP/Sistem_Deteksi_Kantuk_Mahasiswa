/**
 * Authentication & Session Management
 * Handles user login, logout, and session persistence
 */

// Get user from localStorage
function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Check if user is logged in
function isLoggedIn() {
    return getUser() !== null;
}

// Get user role
function getUserRole() {
    const user = getUser();
    return user ? user.role : null;
}

// Logout user
function logout() {
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// Check authentication on page load
function checkAuthentication() {
    // Get current path
    const currentPath = window.location.pathname;
    
    // Don't check on login/register routes
    if (currentPath === '/login' || currentPath === '/register' || currentPath === '/') {
        return;
    }

    // Check if user is logged in
    if (!isLoggedIn()) {
        window.location.href = '/login';
        return;
    }

    // Check role-based routing
    const user = getUser();
    
    // Prevent students from accessing admin
    if (currentPath === '/admin' && user.role !== 'admin') {
        window.location.href = '/student';
        return;
    }

    // Prevent admins from accessing student page
    if ((currentPath === '/student' || currentPath === '/index.html') && user.role === 'admin') {
        window.location.href = '/admin';
        return;
    }

    // Update navbar if elements exist
    updateNavbar();
    setupLogoutButton();
}

// Update navbar with user info
function updateNavbar() {
    const user = getUser();
    if (user) {
        const userNameElement = document.getElementById('userName');
        if (userNameElement) {
            const displayName = user.name || 'User';
            userNameElement.textContent = `Halo, ${displayName}`;
        }
    }
}

// Setup logout button
function setupLogoutButton() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
}

// Run check on page load
document.addEventListener('DOMContentLoaded', checkAuthentication);
