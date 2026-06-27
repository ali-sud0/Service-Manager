// WebSocket and Notifications

let notificationWs = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Decode JWT token to get user ID
function getUserIdFromToken() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    try {
        // JWT format: header.payload.signature
        const payload = token.split('.')[1];
        const decoded = JSON.parse(atob(payload));
        return decoded.sub;  // sub contains user ID
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
}

// Get token from localStorage
function getToken() {
    return localStorage.getItem('access_token');
}

// Connect to WebSocket with authentication
function connectNotificationWebSocket(userId) {
    const token = getToken();
    
    if (!userId || userId === 'None' || userId === 'null') {
        console.log('No valid user ID, skipping WebSocket connection');
        return;
    }
    
    if (!token) {
        console.log('No token, skipping WebSocket connection');
        return;
    }
    
    try {
        const wsUrl = `ws://localhost:8000/notifications/ws/${userId}?token=${encodeURIComponent(token)}`;
        
        notificationWs = new WebSocket(wsUrl);
        
        notificationWs.onopen = () => {
            reconnectAttempts = 0; // Reset reconnect attempts on successful connection
        };
        
        notificationWs.onmessage = (event) => {
            try {
                const notification = JSON.parse(event.data);
                
                // Show toast notification
                if (typeof showToast === 'function') {
                    showToast(notification.title + ': ' + notification.message);
                } else {
                    console.log('Notification:', notification);
                }
                
                // Update badge count
                updateNotificationBadge();
            } catch (e) {
                console.error('Error parsing notification:', e);
            }
        };
        
        notificationWs.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        notificationWs.onclose = (event) => {
            console.log('WebSocket closed - Code:', event.code, 'Reason:', event.reason);
            
            if (event.code === 1008) {
                console.error('Authentication failed for WebSocket. Please login again.');
                return;
            }
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                reconnectAttempts++;
                console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
                setTimeout(() => {
                    const newUserId = getUserIdFromToken();
                    if (newUserId) {
                        connectNotificationWebSocket(newUserId);
                    }
                }, delay);
            } else {
                console.error('Max reconnection attempts reached. Please refresh the page.');
            }
        };
    } catch (error) {
        console.error('Error creating WebSocket:', error);
    }
}

// Load notifications from server
async function loadNotifications() {
    const token = getToken();
    if (!token) return;
    
    try {
        const response = await fetch('/notifications/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateNotificationBadge(data.unread_count);
            displayNotifications(data.notifications);
        } else if (response.status === 401) {
            console.error('Unauthorized - please login again');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            window.location.href = '/auth/login';
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

// Mark notification as read
async function markNotificationAsRead(notificationId) {
    const token = getToken();
    if (!token) return;
    
    try {
        const response = await fetch(`/notifications/${notificationId}/read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            updateNotificationBadge();
            loadNotifications();
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Mark all notifications as read
async function markAllAsRead() {
    const token = getToken();
    if (!token) return;
    
    try {
        const response = await fetch('/notifications/read-all', {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            updateNotificationBadge();
            loadNotifications();
        }
    } catch (error) {
        console.error('Error marking all as read:', error);
    }
}

// Update notification badge count
async function updateNotificationBadge(unreadCount = null) {
    const token = getToken();
    if (!token) return;
    
    try {
        let count = unreadCount;
        if (count === null) {
            const response = await fetch('/notifications/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                count = data.unread_count;
            } else {
                return;
            }
        }
        
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error updating badge:', error);
    }
}

// Display notifications in panel
function displayNotifications(notifications) {
    const container = document.getElementById('notificationList');
    if (!container) return;
    
    if (!notifications || notifications.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i class="fas fa-bell-slash text-3xl mb-2"></i>
                <p class="text-sm">No notifications</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="p-2 border-b border-gray-100 flex justify-between items-center">
            <span class="text-xs text-gray-500">${notifications.length} notifications</span>
            <button onclick="markAllAsRead()" class="text-xs text-blue-500 hover:text-blue-700">
                Mark all as read
            </button>
        </div>
        ${notifications.map(notif => `
            <div class="p-4 border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer ${notif.is_read ? '' : 'bg-blue-50'}"
                 onclick="markNotificationAsRead(${notif.id})">
                <p class="font-semibold text-sm text-gray-800">${escapeHtmlStatic(notif.title)}</p>
                <p class="text-xs text-gray-500 mt-1">${escapeHtmlStatic(notif.message)}</p>
                <p class="text-xs text-gray-400 mt-2">${new Date(notif.created_at).toLocaleString()}</p>
            </div>
        `).join('')}
    `;
}

// Escape HTML to prevent XSS
function escapeHtmlStatic(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show toast message (fallback if not defined)
if (typeof showToast !== 'function') {
    window.showToast = function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 z-50 border-l-4 ${type === 'error' ? 'border-red-500' : 'border-green-500'}`;
        toast.innerHTML = `<span class="text-sm">${escapeHtmlStatic(message)}</span>`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    };
}

// Initialize notifications
function initNotifications() {
    
    const token = getToken();
    const userId = getUserIdFromToken();
    
    
    if (token && userId && userId !== 'None' && userId !== 'null') {
        connectNotificationWebSocket(userId);
        updateNotificationBadge();
    } else {
        console.log('No valid token or user ID, WebSocket not started');
    }
    
    // Setup notification button
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const panel = document.getElementById('notificationPanel');
            if (panel) {
                panel.classList.toggle('hidden');
                if (!panel.classList.contains('hidden')) {
                    loadNotifications();
                }
            }
        });
    }
    
    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
        const panel = document.getElementById('notificationPanel');
        const btn = document.getElementById('notificationBtn');
        if (panel && !panel.classList.contains('hidden') && 
            !panel.contains(e.target) && !btn?.contains(e.target)) {
            panel.classList.add('hidden');
        }
    });
}

// Make functions available globally
window.markNotificationAsRead = markNotificationAsRead;
window.markAllAsRead = markAllAsRead;
window.updateNotificationBadge = updateNotificationBadge;

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', initNotifications);