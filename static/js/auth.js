// Auth related JavaScript functions

const API_BASE = '';
const token = localStorage.getItem('access_token');

// Login handler

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_role', data.role);
            localStorage.setItem('user_id', data.user_id);

            
            // Get user info for navbar
            const userResponse = await fetch('/users/me', {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            });
            if (userResponse.ok) {
                const userData = await userResponse.json();
                localStorage.setItem('user_name', userData.full_name.split(' ')[0] || userData.username);
                localStorage.setItem('user_full_name', userData.full_name);
                localStorage.setItem('user_email', userData.email);
            }

            if (data.role === 'admin') {
                window.location.href = '/dashboard/admin';
            } else if (data.role === 'provider') {
                window.location.href = '/dashboard/provider';
            } else {
                window.location.href = '/services';
            }
        } else {
            const error = await response.json();
            alert(error.detail || 'Login failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Connection error');
    }
}

async function handleSignup(event) {
    event.preventDefault(); 
    
    const fullName = document.querySelector('input[name="first_name"]').value + ' ' + 
                     document.querySelector('input[name="last_name"]').value;
    
    const data = {
        full_name: fullName,
        username: document.querySelector('input[name="username"]').value,
        email: document.querySelector('input[name="email"]').value,
        phone: document.querySelector('input[name="phone"]').value || '',
        password: document.querySelector('input[name="password"]').value,
        role: document.querySelector('input[name="role"]:checked').value
    };
    
    
    try {
        const response = await fetch('/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        
        if (response.ok) {
            const result = await response.json();
            localStorage.setItem('access_token', result.access_token);
            localStorage.setItem('user_role', result.role);
            alert('Account created successfully! Please Login');
            window.location.href = '/auth/login';
        } else {
            const error = await response.json();
            alert(error.detail || 'Registration failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Connection error. Please make sure the server is running.');
    }
}

function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    window.location.href = '/auth/login';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-50 border-l-4 ${type === 'error' ? 'border-red-500' : 'border-blue-500'}`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'error' ? 'fa-exclamation-circle text-red-500' : 'fa-check-circle text-blue-500'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Check if user is authenticated
function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

// Get user role
function getUserRole() {
    return localStorage.getItem('user_role');
}

// Require auth redirect
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/auth/login';
        return false;
    }
    return true;
}

// Require role redirect
function requireRole(role) {
    if (!requireAuth()) return false;
    if (getUserRole() !== role && getUserRole() !== 'admin') {
        window.location.href = '/';
        return false;
    }
    return true;
}