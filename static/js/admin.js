// Admin dashboard JavaScript

let bookingsChart = null;
let currentForceBookingId = null;

// Helper function for authenticated fetch
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/auth/login';
        return null;
    }
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    
    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            window.location.href = '/auth/login';
            return null;
        }
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

// Load admin statistics
async function loadAdminStats() {
    const response = await authFetch('/dashboard/admin-stats');
    if (!response) return;
    
    const stats = await response.json();
    
    document.getElementById('totalUsers').textContent = stats.users?.total || 0;
    document.getElementById('customersCount').textContent = stats.users?.customers || 0;
    document.getElementById('providersCount').textContent = stats.users?.providers || 0;
    document.getElementById('totalServices').textContent = stats.services?.total || 0;
    document.getElementById('activeServices').textContent = stats.services?.active || 0;
    document.getElementById('inactiveServices').textContent = stats.services?.inactive || 0;
    document.getElementById('totalBookings').textContent = stats.bookings?.total || 0;
    document.getElementById('todayBookings').textContent = stats.bookings?.today || 0;
    document.getElementById('weeklyBookings').textContent = stats.bookings?.weekly || 0;
    document.getElementById('totalRevenue').textContent = `$${stats.revenue?.toLocaleString() || 0}`;
    
    // Update chart
    const ctx = document.getElementById('bookingsChart')?.getContext('2d');
    if (ctx && stats.bookings) {
        if (bookingsChart) bookingsChart.destroy();
        bookingsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Total', 'Today', 'This Week'],
                datasets: [{
                    label: 'Bookings',
                    data: [stats.bookings.total, stats.bookings.today, stats.bookings.weekly],
                    backgroundColor: '#3b82f6'
                }]
            },
            options: { responsive: true }
        });
    }
    
    // Display most booked services
    const container = document.getElementById('mostBookedList');
    if (container) {
        if (!stats.most_booked_services || stats.most_booked_services.length === 0) {
            container.innerHTML = '<p class="text-slate-400 text-center py-4 text-sm">No data available</p>';
        } else {
            container.innerHTML = stats.most_booked_services.map((service, index) => `
                <div class="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
                    <div class="flex items-center">
                        <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">${index + 1}</div>
                        <span class="ml-3 font-medium text-gray-800">${escapeHtml(service.name)}</span>
                    </div>
                    <span class="text-blue-600 font-semibold text-sm">${service.count} bookings</span>
                </div>
            `).join('');
        }
    }
}

// Load all users
async function loadAllUsers() {
    const response = await authFetch('/users/');
    if (!response) return;
    
    const users = await response.json();
    
    const tbody = document.getElementById('usersTableBody');
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-slate-400 text-sm">No users found</td</tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4">
                <div class="font-medium text-gray-900">${escapeHtml(user.full_name)}</div>
                <div class="text-sm text-gray-500">@${escapeHtml(user.username)}</div>
                ${user.phone ? `<div class="text-xs text-gray-400 mt-1">${escapeHtml(user.phone)}</div>` : ''}
             </td>
            <td class="px-6 py-4 text-gray-600">${escapeHtml(user.email)}</td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-semibold ${user.role === 'admin' ? 'bg-purple-100 text-purple-800' : user.role === 'provider' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}">
                    ${user.role}
                </span>
            </td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-semibold ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${user.is_active ? 'Active' : 'Deactive'}
                </span>
            </td>
            <td class="px-6 py-4">
                <button onclick="editUser(${user.id}, '${escapeHtml(user.full_name)}', '${escapeHtml(user.username)}', '${escapeHtml(user.email)}', '${escapeHtml(user.phone || '')}', '${user.role}', ${user.is_active})" 
                        class="text-blue-600 hover:text-blue-800 mr-2">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button onclick="deleteUser(${user.id})" class="text-red-600 hover:text-red-800">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </td>
    `).join('');
}

// Load all services for admin
async function loadAllServices() {
    const response = await authFetch('/services/all');
    if (!response) return;
    
    const services = await response.json();
    
    const tbody = document.getElementById('servicesTableBody');
    if (!services || services.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400 text-sm">No services found</td</tr>';
        return;
    }
    
    tbody.innerHTML = services.map(service => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 text-gray-600">#${service.id}</td>
            <td class="px-6 py-4 font-medium text-gray-800">${escapeHtml(service.name)}</td>
            <td class="px-6 py-4 text-gray-600">${escapeHtml(service.provider_name) || 'N/A'}</td>
            <td class="px-6 py-4 text-gray-600">${escapeHtml(service.category)}</td>
            <td class="px-6 py-4 text-gray-600">$${service.price}</td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-semibold ${service.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${service.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="px-6 py-4">
                <button onclick="editService(${service.id})" class="text-blue-600 hover:text-blue-800 mr-2">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button onclick="deleteService(${service.id})" class="text-red-600 hover:text-red-800">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
}

// Load all bookings with force actions
async function loadAllBookings() {
    const response = await authFetch('/bookings/all');
    if (!response) return;
    
    const bookings = await response.json();
    
    const tbody = document.getElementById('allBookingsBody');
    if (!bookings || bookings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-400 text-sm">No bookings found</td</tr>';
        return;
    }
    
    tbody.innerHTML = bookings.map(booking => {
        let paymentStatusClass = '';
        let paymentStatusText = '';
        
        if (booking.payment_status === 'paid') {
            paymentStatusClass = 'bg-green-100 text-green-800';
            paymentStatusText = 'Paid';
        } else if (booking.payment_status === 'unpaid') {
            paymentStatusClass = 'bg-yellow-100 text-yellow-800';
            paymentStatusText = 'Unpaid';
        } else {
            paymentStatusClass = 'bg-gray-100 text-gray-800';
            paymentStatusText = booking.payment_status || 'Unknown';
        }
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 text-gray-600">#${booking.id}</td>
                <td class="px-6 py-4 text-gray-600">${escapeHtml(booking.customer_name || 'Unknown')}</td>
                <td class="px-6 py-4 text-gray-600">${escapeHtml(booking.provider_name || 'Unknown')}</td>
                <td class="px-6 py-4 text-gray-600">${escapeHtml(booking.service_name || 'Unknown')}</td>
                <td class="px-6 py-4 text-gray-600">${booking.start_time ? new Date(booking.start_time).toLocaleDateString() : 'N/A'}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded-full text-xs font-semibold ${paymentStatusClass}">
                        <i class="fas ${booking.payment_status === 'paid' ? 'fa-check-circle' : 'fa-clock'} mr-1"></i>
                        ${paymentStatusText}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="status-badge status-${booking.status}">
                        ${booking.status}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <button onclick="showForceActionModal(${booking.id})" class="bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600 transition">
                        <i class="fas fa-bolt"></i> Force Action
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Load providers for dropdown
async function loadProvidersForDropdown() {
    const response = await authFetch('/users/providers');
    if (!response) return;
    
}

// Create User
document.getElementById('createUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    const response = await authFetch('/auth/signup', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    if (response && response.ok) {
        showToast('User created successfully!', 'success');
        closeCreateUserModal();
        loadAllUsers();
        loadAdminStats();
    } else {
        const error = await response?.json();
        showToast(error?.detail || 'Failed to create user', 'error');
    }
});

// Edit User
window.editUser = function(id, fullName, username, email, phone, role, isActive) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editFullName').value = fullName;
    document.getElementById('editUsername').value = username;
    document.getElementById('editEmail').value = email;
    document.getElementById('editPhone').value = phone || '';
    document.getElementById('editRole').value = role;
    document.getElementById('editStatus').value = isActive ? 'true' : 'false';
    document.getElementById('editUserModal').classList.remove('hidden');
    document.getElementById('editUserModal').classList.add('flex');
}

document.getElementById('editUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = document.getElementById('editUserId').value;
    const data = {
        full_name: document.getElementById('editFullName').value,
        username: document.getElementById('editUsername').value,
        email: document.getElementById('editEmail').value,
        phone: document.getElementById('editPhone').value || '',
        role: document.getElementById('editRole').value,
        is_active: document.getElementById('editStatus').value === 'true'
    };
    
    const response = await authFetch(`/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
    
    if (response && response.ok) {
        showToast('User updated successfully!', 'success');
        closeEditUserModal();
        loadAllUsers();
        loadAdminStats();
    } else {
        const error = await response?.json();
        showToast(error?.detail || 'Failed to update user', 'error');
    }
});

// Delete User
window.deleteUser = async function(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    
    const response = await authFetch(`/users/${userId}`, {
        method: 'DELETE'
    });
    
    if (response && response.ok) {
        showToast('User deleted successfully!', 'success');
        loadAllUsers();
        loadAdminStats();
    } else {
        showToast('Failed to delete user', 'error');
    }
}

// Create Service
document.getElementById('createServiceForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    const response = await authFetch('/services/', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    if (response && response.ok) {
        showToast('Service created successfully!', 'success');
        closeCreateServiceModal();
        loadAllServices();
        loadAdminStats();
    } else {
        const error = await response?.json();
        showToast(error?.detail || 'Failed to create service', 'error');
    }
});

// Edit Service
window.editService = async function(serviceId) {
    const response = await authFetch(`/services/${serviceId}`);
    if (!response) return;
    
    const service = await response.json();
    
    document.getElementById('editServiceId').value = service.id;
    document.getElementById('editServiceName').value = service.name;
    document.getElementById('editServiceDescription').value = service.description || '';
    document.getElementById('editServiceCategory').value = service.category;
    document.getElementById('editServicePrice').value = service.price;
    document.getElementById('editServiceDuration').value = service.duration_minutes;
    document.getElementById('editServiceStatus').value = service.is_active ? 'true' : 'false';
    
    document.getElementById('editServiceModal').classList.remove('hidden');
    document.getElementById('editServiceModal').classList.add('flex');
}

document.getElementById('editServiceForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const serviceId = document.getElementById('editServiceId').value;
    const data = {
        name: document.getElementById('editServiceName').value,
        description: document.getElementById('editServiceDescription').value,
        category: document.getElementById('editServiceCategory').value,
        price: parseFloat(document.getElementById('editServicePrice').value),
        duration_minutes: parseInt(document.getElementById('editServiceDuration').value),
        is_active: document.getElementById('editServiceStatus').value === 'true'
    };
    
    const response = await authFetch(`/services/${serviceId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
    
    if (response && response.ok) {
        showToast('Service updated successfully!', 'success');
        closeEditServiceModal();
        loadAllServices();
    } else {
        showToast('Failed to update service', 'error');
    }
});

// Delete Service
window.deleteService = async function(serviceId) {
    if (!confirm('Are you sure you want to delete this service? This will also delete all associated time slots and bookings.')) return;
    
    const response = await authFetch(`/services/${serviceId}`, {
        method: 'DELETE'
    });
    
    if (response && response.ok) {
        showToast('Service deleted successfully!', 'success');
        loadAllServices();
        loadAdminStats();
    } else {
        showToast('Failed to delete service', 'error');
    }
}

// Force Actions on Booking
window.showForceActionModal = function(bookingId) {
    currentForceBookingId = bookingId;
    document.getElementById('forceBookingId').textContent = `#${bookingId}`;
    document.getElementById('forceActionModal').classList.remove('hidden');
    document.getElementById('forceActionModal').classList.add('flex');
}

window.forceApproveBooking = async function() {
    const response = await authFetch(`/bookings/${currentForceBookingId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'confirmed' })
    });
    
    if (response && response.ok) {
        showToast('Booking force approved!', 'success');
        closeForceActionModal();
        loadAllBookings();
        loadAdminStats();
    } else {
        showToast('Failed to force approve booking', 'error');
    }
}

window.forceCancelBooking = async function() {
    const response = await authFetch(`/bookings/${currentForceBookingId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'cancelled' })
    });
    
    if (response && response.ok) {
        showToast('Booking force cancelled!', 'success');
        closeForceActionModal();
        loadAllBookings();
        loadAdminStats();
    } else {
        showToast('Failed to force cancel booking', 'error');
    }
}

// Modal functions
function showCreateUserModal() {
    document.getElementById('createUserModal').classList.remove('hidden');
    document.getElementById('createUserModal').classList.add('flex');
}

function closeCreateUserModal() {
    document.getElementById('createUserModal').classList.add('hidden');
    document.getElementById('createUserModal').classList.remove('flex');
    document.getElementById('createUserForm')?.reset();
}

function closeEditUserModal() {
    document.getElementById('editUserModal').classList.add('hidden');
    document.getElementById('editUserModal').classList.remove('flex');
}

function showCreateServiceModal() {
    loadProvidersForDropdown();
    document.getElementById('createServiceModal').classList.remove('hidden');
    document.getElementById('createServiceModal').classList.add('flex');
}

function closeCreateServiceModal() {
    document.getElementById('createServiceModal').classList.add('hidden');
    document.getElementById('createServiceModal').classList.remove('flex');
    document.getElementById('createServiceForm')?.reset();
}

function closeEditServiceModal() {
    document.getElementById('editServiceModal').classList.add('hidden');
    document.getElementById('editServiceModal').classList.remove('flex');
}

function closeForceActionModal() {
    document.getElementById('forceActionModal').classList.add('hidden');
    document.getElementById('forceActionModal').classList.remove('flex');
    currentForceBookingId = null;
}

// Download admin statistics report PDF
async function downloadAdminReport() {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        showToast('Please login first', 'error');
        window.location.href = '/auth/login';
        return;
    }
    
    showToast('Generating statistics report...', 'info');
    
    try {
        const response = await fetch('/pdf/admin-stats', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.status === 401) {
            showToast('Session expired. Please login again.', 'error');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            setTimeout(() => window.location.href = '/auth/login', 1500);
            return;
        }
        
        if (response.status === 403) {
            showToast('You are not authorized to view this report', 'error');
            return;
        }
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Extract filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `admin_statistics_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename=(.+)/);
                if (match) filename = match[1];
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Statistics report downloaded successfully!', 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to download report', 'error');
        }
    } catch (error) {
        console.error('Error downloading report:', error);
        showToast('Connection error. Please try again.', 'error');
    }
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show toast message
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-50 border-l-4 ${type === 'error' ? 'border-red-500' : 'border-green-500'}`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'error' ? 'fa-exclamation-circle text-red-500' : 'fa-check-circle text-green-500'} mr-2"></i>
            <span class="text-slate-700">${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Initialize admin page
function initAdminPage() {
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role');
    
    if (!token || role !== 'admin') {
        window.location.href = '/auth/login';
        return;
    }
    
    loadAdminStats();
    loadAllUsers();
    loadAllServices();
    loadAllBookings();
    loadProvidersForDropdown();
}

document.addEventListener('DOMContentLoaded', initAdminPage);