// Shared authentication utilities for SGP Costura frontend

const AUTH_CONFIG = {
    API_URL: "http://localhost:8001/api",
    TOKEN_KEY: "token",
    USERNAME_KEY: "username",
    ROLE_KEY: "role"
};

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem(AUTH_CONFIG.TOKEN_KEY) !== null;
}

// Get current user info
function getCurrentUser() {
    return {
        token: localStorage.getItem(AUTH_CONFIG.TOKEN_KEY),
        username: localStorage.getItem(AUTH_CONFIG.USERNAME_KEY),
        role: localStorage.getItem(AUTH_CONFIG.ROLE_KEY)
    };
}

// Logout function
function logout() {
    localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
    localStorage.removeItem(AUTH_CONFIG.USERNAME_KEY);
    localStorage.removeItem(AUTH_CONFIG.ROLE_KEY);
    window.location.href = '../login/login.html';
}

// Get default page based on user role
function getDefaultPageForRole(role) {
    const defaultPages = {
        'admin': '../page_03/page_03.html',
        'supervisor': '../page_03/page_03.html',
        'operator': '../page_01/page_01.html'
    };
    return defaultPages[role] || '../page_01/page_01.html';
}

// Protect page - redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '../login/login.html';
    }
}

// Make authenticated API request
async function authFetch(url, options = {}) {
    const user = getCurrentUser();

    if (!user.token) {
        throw new Error('Not authenticated');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${user.token}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        // Token expired or invalid
        logout();
    }

    return response;
}
