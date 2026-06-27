// Provider dashboard JavaScript

let bookingsChart = null;
let currentServiceForSchedule = null;

// Load dashboard stats
async function loadProviderStats() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/dashboard/provider-stats', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const stats = await response.json();
        
        document.getElementById('servicesCount').textContent = stats.services_count;
        document.getElementById('totalBookings').textContent = stats.bookings.total;
        document.getElementById('pendingBookings').textContent = stats.bookings.pending;
        document.getElementById('revenue').textContent = `$${stats.revenue.toLocaleString()}`;
        
        // Update chart
        if (bookingsChart) bookingsChart.destroy();
        const ctx = document.getElementById('bookingsChart')?.getContext('2d');
        if (ctx) {
            bookingsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Pending', 'Confirmed', 'Completed', 'Cancelled'],
                    datasets: [{
                        data: [stats.bookings.pending, stats.bookings.confirmed, stats.bookings.completed, stats.bookings.cancelled],
                        backgroundColor: ['#f59e0b', '#10b981', '#3b82f6', '#ef4444']
                    }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showToast('Error loading dashboard data', 'error');
    }
}

// Load provider services
async function loadProviderServices() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/services/my-services', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const services = await response.json();
        
        const container = document.getElementById('servicesList');
        if (!services || services.length === 0) {
            container.innerHTML = '<p class="text-slate-400 text-center py-4 text-sm">No services added yet</p>';
            return;
        }
        
        container.innerHTML = services.map(service => `
            <div class="border border-slate-200 rounded-xl p-4 flex justify-between items-center hover:shadow-md transition">
                <div class="flex-1">
                    <p class="font-semibold text-slate-800">${escapeHtml(service.name)}</p>
                    <p class="text-sm text-slate-500">$${service.price} • ${service.duration_minutes} min</p>
                    <span class="text-xs px-2 py-1 rounded-full ${service.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                        ${service.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
                <div class="flex gap-2">
                    <button onclick="viewTimeSlots(${service.id}, '${escapeHtml(service.name)}')" class="bg-blue-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-blue-600 transition">
                        <i class="fas fa-calendar-alt mr-1"></i> Slots
                    </button>
                    <button onclick="showAddScheduleModal(${service.id})" class="bg-green-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-green-600 transition">
                        <i class="fas fa-calendar-plus mr-1"></i> Add Slot
                    </button>
                    <button onclick="deleteService(${service.id})" class="bg-red-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-red-600 transition">
                        <i class="fas fa-trash mr-1"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading services:', error);
        showToast('Error loading services', 'error');
    }
}

// View time slots for a service
async function viewTimeSlots(serviceId, serviceName) {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/schedules/service/${serviceId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const slots = await response.json();
            const now = new Date();
            
            let slotsHtml = `
                <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" id="slotsModal" onclick="if(event.target===this) closeSlotsModal()">
                    <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
                        <div class="p-5">
                            <div class="flex justify-between items-center mb-4">
                                <h3 class="text-lg font-semibold text-slate-800">Time Slots for ${escapeHtml(serviceName)}</h3>
                                <div class="flex gap-2">
                                    <button onclick="refreshSlots(${serviceId}, '${escapeHtml(serviceName)}')" class="text-slate-400 hover:text-slate-600">
                                        <i class="fas fa-sync-alt text-lg"></i>
                                    </button>
                                    <button onclick="closeSlotsModal()" class="text-slate-400 hover:text-slate-600">
                                        <i class="fas fa-times text-xl"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="space-y-2">
            `;
            
            if (!slots || slots.length === 0) {
                slotsHtml += '<p class="text-slate-400 text-center py-4">No time slots available for this service.</p>';
            } else {
                slotsHtml += slots.map(slot => {
                    const startTime = new Date(slot.start_time);
                    const endTime = new Date(slot.end_time);
                    const isPassed = endTime < now;
                    const isBooked = slot.has_booking === true;
                    const isAvailable = slot.is_available === true && !isBooked;
                    
                    return `
                        <div class="border border-slate-200 rounded-lg p-3 ${isPassed ? 'bg-gray-100' : ''}">
                            <div class="flex justify-between items-center">
                                <div class="flex-1">
                                    <p class="font-medium text-slate-700">
                                        <i class="fas fa-calendar-day text-slate-400 mr-2"></i>
                                        ${startTime.toLocaleDateString()}
                                    </p>
                                    <p class="text-sm text-slate-500 mt-1">
                                        <i class="fas fa-clock text-slate-400 mr-2"></i>
                                        ${startTime.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})} - 
                                        ${endTime.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                                    </p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="px-2 py-1 rounded-full text-xs font-semibold ${isPassed ? 'bg-gray-300 text-gray-600' : (isBooked ? 'bg-red-100 text-red-700' : (isAvailable ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'))}">
                                        ${isPassed ? 'Passed' : (isBooked ? 'Booked' : (isAvailable ? 'Available' : 'Disabled'))}
                                    </span>
                                    ${!isPassed && !isBooked ? `
                                        <button onclick="toggleScheduleStatus(${slot.id}, ${serviceId}, '${escapeHtml(serviceName)}', ${!isAvailable})" 
                                            class="${isAvailable ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-green-500 hover:bg-green-600'} text-white px-2 py-1 rounded text-xs transition">
                                            <i class="fas ${isAvailable ? 'fa-ban' : 'fa-check'} mr-1"></i>
                                            ${isAvailable ? 'Disable' : 'Enable'}
                                        </button>
                                    ` : ''}
                                    ${!isPassed && !isBooked ? `
                                        <button onclick="deleteScheduleSlot(${slot.id}, ${serviceId}, '${escapeHtml(serviceName)}')" 
                                            class="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600 transition">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            slotsHtml += `
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('slotsModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            document.body.insertAdjacentHTML('beforeend', slotsHtml);
        } else {
            showToast('Failed to load time slots', 'error');
        }
    } catch (error) {
        console.error('Error loading time slots:', error);
        showToast('Error loading time slots', 'error');
    }
}

// Toggle schedule status (Enable/Disable)
async function toggleScheduleStatus(scheduleId, serviceId, serviceName, makeAvailable) {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/schedules/${scheduleId}/toggle-status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ is_available: makeAvailable })
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(result.message, 'success');
            // Refresh the modal
            closeSlotsModal();
            viewTimeSlots(serviceId, serviceName);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to toggle schedule status', 'error');
        }
    } catch (error) {
        console.error('Error toggling schedule status:', error);
        showToast('Connection error', 'error');
    }
}

// Refresh slots modal
async function refreshSlots(serviceId, serviceName) {
    closeSlotsModal();
    viewTimeSlots(serviceId, serviceName);
}

// Delete schedule slot
async function deleteScheduleSlot(scheduleId, serviceId, serviceName) {
    if (!confirm(`Are you sure you want to delete this time slot for "${serviceName}"?`)) return;
    
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/schedules/${scheduleId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            showToast('Time slot deleted successfully!', 'success');
            // Close current modal and refresh
            closeSlotsModal();
            // Refresh the slots view
            viewTimeSlots(serviceId, serviceName);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to delete time slot', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
}

// Close slots modal
function closeSlotsModal() {
    const modal = document.getElementById('slotsModal');
    if (modal) {
        modal.remove();
    }
}

// Load provider bookings
async function loadProviderBookings() {
    const token = localStorage.getItem('access_token');
    
    
    try {
        const response = await fetch('/bookings/provider-bookings', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        
        if (response.status === 401) {
            console.error('Unauthorized');
            window.location.href = '/auth/login';
            return;
        }
        
        const bookings = await response.json();
        
        const tbody = document.getElementById('bookingsTableBody');
        if (!tbody) {
            console.error('bookingsTableBody not found');
            return;
        }
        
        if (!bookings || bookings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-400 text-sm">No bookings yet</td</tr>';
            return;
        }
        
        tbody.innerHTML = bookings.map(booking => {
            const startTime = booking.start_time ? new Date(booking.start_time) : null;
            const formattedDate = startTime ? startTime.toLocaleString() : 'N/A';
            
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
                    <td class="px-6 py-4 text-slate-600">${escapeHtml(booking.customer_name || 'Unknown')}</td>
                    <td class="px-6 py-4 text-slate-600">${escapeHtml(booking.service_name || 'Unknown')}</td>
                    <td class="px-6 py-4 text-slate-600">${formattedDate}</td>
                    <td class="px-6 py-4">
                        <span class="status-badge status-${booking.status}">
                            ${booking.status}
                        </span>
                    </td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 rounded-full text-xs font-semibold ${paymentStatusClass}">
                            <i class="fas ${booking.payment_status === 'paid' ? 'fa-check-circle' : 'fa-clock'} mr-1"></i>
                            ${paymentStatusText}
                        </span>
                    </td>
                    <td class="px-6 py-4">
                        ${booking.status === 'pending' ? `
                            <button onclick="updateBookingStatus(${booking.id}, 'confirmed')" class="bg-green-500 text-white px-3 py-1 rounded text-sm mr-1 hover:bg-green-600 transition">Approve</button>
                            <button onclick="updateBookingStatus(${booking.id}, 'rejected')" class="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition">Reject</button>
                        ` : booking.status === 'confirmed' ? `
                            <button onclick="updateBookingStatus(${booking.id}, 'completed')" class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition">Complete</button>
                        ` : ''}
                    </td>
                </table>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading bookings:', error);
        showToast('Error loading bookings', 'error');
    }
}


// Add new service
async function addService(event) {
    event.preventDefault();
    const token = localStorage.getItem('access_token');
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/services/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Service added successfully!', 'success');
            closeAddServiceModal();
            loadProviderServices();
            loadProviderStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add service', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
}

// Add schedule time slot
async function addSchedule(event) {
    event.preventDefault();
    const token = localStorage.getItem('access_token');
    const data = {
        service_id: currentServiceForSchedule,
        start_time: document.getElementById('startTime').value,
        end_time: document.getElementById('endTime').value
    };
    
    try {
        const response = await fetch('/schedules/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Time slot added successfully!', 'success');
            closeAddScheduleModal();
            // Refresh slots view if open
            if (document.getElementById('slotsModal')) {
                closeSlotsModal();
            }
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add time slot', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
}

// Update booking status
async function updateBookingStatus(bookingId, status) {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/bookings/${bookingId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status: status })
        });
        
        if (response.ok) {
            showToast(`Booking ${status} successfully!`, 'success');
            loadProviderBookings();
            loadProviderStats();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update status', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
}

// Delete service
async function deleteService(serviceId) {
    if (!confirm('Are you sure you want to delete this service? This will also delete all associated time slots and affect existing bookings.')) return;
    
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/services/${serviceId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            showToast('Service deleted successfully!', 'success');
            loadProviderServices();
            loadProviderStats();
        } else {
            showToast('Failed to delete service', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
}

// Modal functions
function showAddServiceModal() {
    const modal = document.getElementById('addServiceModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeAddServiceModal() {
    const modal = document.getElementById('addServiceModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    const form = document.getElementById('addServiceForm');
    if (form) form.reset();
}

function showAddScheduleModal(serviceId) {
    currentServiceForSchedule = serviceId;
    const modal = document.getElementById('addScheduleModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeAddScheduleModal() {
    const modal = document.getElementById('addScheduleModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    const form = document.getElementById('addScheduleForm');
    if (form) form.reset();
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

// Initialize provider page
function initProviderPage() {
    // Check authentication and role
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role');
    
    if (!token || role !== 'provider') {
        window.location.href = '/auth/login';
        return;
    }
    
    // Load data
    loadProviderStats();
    loadProviderServices();
    loadProviderBookings();
    
    // Setup form handlers
    const addServiceForm = document.getElementById('addServiceForm');
    if (addServiceForm) {
        addServiceForm.addEventListener('submit', addService);
    }
    
    const addScheduleForm = document.getElementById('addScheduleForm');
    if (addScheduleForm) {
        addScheduleForm.addEventListener('submit', addSchedule);
    }
    
    // Setup modal close on outside click
    const addServiceModal = document.getElementById('addServiceModal');
    if (addServiceModal) {
        addServiceModal.addEventListener('click', (e) => {
            if (e.target === addServiceModal) closeAddServiceModal();
        });
    }
    
    const addScheduleModal = document.getElementById('addScheduleModal');
    if (addScheduleModal) {
        addScheduleModal.addEventListener('click', (e) => {
            if (e.target === addScheduleModal) closeAddScheduleModal();
        });
    }
}

function displayTimeSlots(slots) {
    const container = document.getElementById('slotsList');
    const now = new Date();
    
    if (slots.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">No time slots available</p>';
        return;
    }
    
    container.innerHTML = slots.map(slot => {
        const startTime = new Date(slot.start_time);
        const isPassed = startTime < now;
        
        return `
            <div class="border rounded-lg p-3 flex justify-between items-center ${isPassed ? 'bg-red-50 border-red-300' : 'hover:bg-gray-50'}">
                <div>
                    <p class="font-medium ${isPassed ? 'text-red-500' : 'text-gray-700'}">
                        <i class="fas fa-calendar-day mr-2"></i>
                        ${startTime.toLocaleDateString()}
                    </p>
                    <p class="text-sm ${isPassed ? 'text-red-400' : 'text-gray-500'} mt-1">
                        <i class="fas fa-clock mr-2"></i>
                        ${startTime.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})} - 
                        ${new Date(slot.end_time).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                    </p>
                </div>
                <div>
                    <span class="px-2 py-1 rounded-full text-xs font-semibold ${isPassed ? 'bg-red-100 text-red-700' : (slot.is_available ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700')}">
                        ${isPassed ? 'Passed' : (slot.is_available ? 'Available' : 'Booked')}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}


// Download provider report PDF
async function downloadProviderReport() {
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    
    if (!token) {
        showToast('Please login first', 'error');
        window.location.href = '/auth/login';
        return;
    }
    
    // اگر user_id در localStorage ذخیره نشده، از API بگیر
    let providerId = userId;
    if (!providerId) {
        try {
            const response = await fetch('/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const user = await response.json();
                providerId = user.id;
                localStorage.setItem('user_id', providerId);
            }
        } catch (error) {
            console.error('Error fetching user info:', error);
        }
    }
    
    if (!providerId) {
        showToast('Unable to identify provider', 'error');
        return;
    }
    
    showToast('Generating report...', 'info');
    
    try {
        const response = await fetch(`/pdf/provider-bookings/${providerId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.status === 401) {
            showToast('Session expired. Please login again.', 'error');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            localStorage.removeItem('user_id');
            setTimeout(() => window.location.href = '/auth/login', 1500);
            return;
        }
        
        if (response.status === 403) {
            showToast('You are not authorized to view this report', 'error');
            return;
        }
        
        if (response.status === 404) {
            showToast('No bookings found for this provider', 'error');
            return;
        }
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Extract filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `provider_bookings_${new Date().toISOString().slice(0, 10)}.pdf`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename=(.+)/);
                if (match) filename = match[1];
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Report downloaded successfully!', 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to download report', 'error');
        }
    } catch (error) {
        console.error('Error downloading report:', error);
        showToast('Connection error. Please try again.', 'error');
    }
}

// Run initialization
document.addEventListener('DOMContentLoaded', initProviderPage);