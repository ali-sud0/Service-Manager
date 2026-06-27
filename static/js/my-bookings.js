let currentFilter = 'all';
let currentBookingId = null;

// Load bookings
async function loadBookings(filter = 'all') {
    currentFilter = filter;
    
    // Update active tab style
    document.querySelectorAll('[id^="tab"]').forEach(tab => {
        tab.classList.remove('border-slate-800', 'text-slate-800');
        tab.classList.add('border-transparent', 'text-slate-600');
    });
    const activeTab = document.getElementById(`tab${filter.charAt(0).toUpperCase() + filter.slice(1)}`);
    if (activeTab) {
        activeTab.classList.add('border-slate-800', 'text-slate-800');
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/auth/login';
        return;
    }
    
    try {
        const response = await fetch('/bookings/my-bookings', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/auth/login';
            return;
        }
        
        let bookings = await response.json();
        
        // Filter bookings
        if (filter !== 'all') {
            bookings = bookings.filter(b => b.status === filter);
        }
        
        displayBookings(bookings);
    } catch (error) {
        console.error('Error loading bookings:', error);
        showToast('Error loading bookings', 'error');
    }
}

// Display bookings
function displayBookings(bookings) {
    const container = document.getElementById('bookingsList');
    
    if (!bookings || bookings.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 bg-white rounded-xl border border-slate-200">
                <i class="fas fa-calendar-times text-5xl text-slate-300 mb-3"></i>
                <p class="text-slate-500">No bookings found</p>
                <a href="/services" class="inline-block mt-4 text-slate-700 underline">Browse Services</a>
            </div>
        `;
        return;
    }
    
    container.innerHTML = bookings.map(booking => {
        const startTime = booking.start_time ? new Date(booking.start_time) : null;
        const canCancel = booking.can_cancel;
        const cancellationTimeLeft = booking.cancellation_time_left;
        const isPaid = booking.payment_status === 'paid';
        const isPending = booking.status === 'pending';
        const isConfirmed = booking.status === 'confirmed';
        
        return `
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition">
                <div class="p-5">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <h3 class="text-lg font-semibold text-slate-800">${escapeHtml(booking.service_name)}</h3>
                                <span class="status-badge status-${booking.status} text-xs">
                                    ${booking.status}
                                </span>
                            </div>
                            <p class="text-slate-600 text-sm mb-3">
                                <i class="fas fa-user mr-1 text-slate-400"></i> ${escapeHtml(booking.provider_name)}
                            </p>
                            <div class="flex flex-wrap gap-4 text-sm text-slate-500">
                                <div>
                                    <i class="fas fa-calendar-alt mr-1"></i>
                                    ${startTime ? startTime.toLocaleDateString() : 'Date TBD'}
                                </div>
                                <div>
                                    <i class="fas fa-clock mr-1"></i>
                                    ${startTime ? startTime.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : 'Time TBD'}
                                </div>
                                <div>
                                    <i class="fas fa-tag mr-1"></i>
                                    $${booking.total_price}
                                </div>
                                <div>
                                    <i class="fas fa-credit-card mr-1"></i>
                                    ${isPaid ? '<span class="text-green-600">Paid</span>' : '<span class="text-orange-600">Unpaid</span>'}
                                </div>
                            </div>
                            ${cancellationTimeLeft ? `
                                <p class="text-xs text-orange-500 mt-2">
                                    <i class="fas fa-hourglass-half mr-1"></i>
                                    Cancel available for: ${cancellationTimeLeft}
                                </p>
                            ` : ''}
                            
                            ${isPaid ? `
                                <button onclick="viewPaymentDetails(${booking.id})" 
                                        class="mt-3 text-xs text-blue-600 hover:text-blue-800 transition">
                                    <i class="fas fa-receipt mr-1"></i> View Payment Details
                                </button>
                            ` : ''}
                        </div>
                        <div class="flex flex-col gap-2 ml-4">
                            ${!isPaid && isConfirmed ? `
                                <button onclick="openPaymentModal(${booking.id}, '${escapeHtml(booking.service_name)}', ${booking.total_price})" 
                                        class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition">
                                    <i class="fas fa-credit-card mr-1"></i> Pay Now
                                </button>
                            ` : isPaid ? `
                                <button disabled class="bg-gray-300 text-gray-500 px-4 py-2 rounded-lg text-sm cursor-not-allowed">
                                    <i class="fas fa-check-circle mr-1"></i> Paid
                                </button>
                            ` : isPending ? `
                                <button disabled class="bg-gray-300 text-gray-500 px-4 py-2 rounded-lg text-sm cursor-not-allowed">
                                    <i class="fas fa-clock mr-1"></i> Waiting for confirmation
                                </button>
                            ` : ''}
                            
                            ${canCancel && !isPaid ? `
                                <button onclick="cancelBooking(${booking.id})" 
                                        class="border border-red-500 text-red-500 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50 transition">
                                    <i class="fas fa-times mr-1"></i> Cancel
                                </button>
                            ` : ''}
                            ${isPaid ? `
                                    <button onclick="downloadInvoice(${booking.id})" 
                                    class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                                        <i class="fas fa-download mr-1"></i> Receipt
                                    </a>
                                ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// View payment details
async function viewPaymentDetails(bookingId) {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/payments/status/${bookingId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const payment = await response.json();
            showPaymentInfoModal(payment);
        } else {
            showToast('Failed to load payment details', 'error');
        }
    } catch (error) {
        console.error('Error loading payment details:', error);
        showToast('Error loading payment details', 'error');
    }
}

// Show payment info modal
function showPaymentInfoModal(payment) {
    const modal = document.getElementById('paymentInfoModal');
    const content = document.getElementById('paymentInfoContent');
    
    const paidDate = payment.paid_at ? new Date(payment.paid_at).toLocaleString() : 'N/A';
    
    content.innerHTML = `
        <div class="space-y-4">
            <div class="bg-green-50 rounded-lg p-4 text-center">
                <i class="fas fa-check-circle text-green-500 text-4xl mb-2"></i>
                <p class="text-green-700 font-semibold">Payment Successful</p>
            </div>
            
            <div class="border border-slate-200 rounded-lg p-4 space-y-3">
                <div class="flex justify-between">
                    <span class="text-slate-500">Transaction ID:</span>
                    <span class="font-mono text-sm text-slate-700">${escapeHtml(payment.transaction_id || 'N/A')}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Amount Paid:</span>
                    <span class="font-bold text-green-600">$${payment.amount || 0}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Payment Status:</span>
                    <span class="text-green-600">${payment.payment_status || 'Paid'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Payment Date:</span>
                    <span class="text-slate-700">${paidDate}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Booking ID:</span>
                    <span class="text-slate-700">#${payment.booking_id}</span>
                </div>
            </div>
            
            <button onclick="closePaymentInfoModal()" 
                    class="w-full bg-slate-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition">
                Close
            </button>
        </div>
    `;
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// Close payment info modal
function closePaymentInfoModal() {
    const modal = document.getElementById('paymentInfoModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Open payment modal
async function openPaymentModal(bookingId, serviceName, amount) {
    currentBookingId = bookingId;
    const modal = document.getElementById('paymentModal');
    const content = document.getElementById('paymentContent');
    
    content.innerHTML = `
        <div class="space-y-4">
            <div class="bg-slate-50 rounded-lg p-4">
                <p class="text-sm text-slate-600">Service</p>
                <p class="font-medium text-slate-800">${escapeHtml(serviceName)}</p>
                <p class="text-sm text-slate-600 mt-2">Amount</p>
                <p class="text-2xl font-bold text-slate-800">$${amount}</p>
            </div>
            
            <div class="space-y-3">
                <label class="block text-sm font-medium text-slate-700">Payment Method</label>
                <select id="paymentMethod" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm">
                    <option value="credit_card">Credit Card</option>
                    <option value="debit_card">Debit Card</option>
                    <option value="paypal">PayPal</option>
                </select>
            </div>
            
            <div class="bg-blue-50 rounded-lg p-3 text-sm text-blue-700">
                <i class="fas fa-shield-alt mr-2"></i>
                Your payment is secure and encrypted.
            </div>
            
            <div class="flex gap-3 pt-3">
                <button onclick="processPayment()" class="flex-1 bg-slate-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition">
                    <i class="fas fa-lock mr-1"></i> Pay $${amount}
                </button>
                <button onclick="closePaymentModal()" class="flex-1 border border-slate-200 py-2 rounded-lg text-sm hover:bg-slate-50 transition">
                    Cancel
                </button>
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// Process payment
async function processPayment() {
    const token = localStorage.getItem('access_token');
    const paymentMethod = document.getElementById('paymentMethod')?.value;
    
    if (!currentBookingId) return;
    
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Processing...';
    btn.disabled = true;
    
    try {
        const response = await fetch(`/payments/process/${currentBookingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                payment_method: paymentMethod 
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Show success with transaction info
            showPaymentSuccessModal(data);
            closePaymentModal();
            loadBookings(currentFilter);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Payment failed', 'error');
        }
    } catch (error) {
        console.error('Error processing payment:', error);
        showToast('Connection error', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Show payment success modal
function showPaymentSuccessModal(paymentData) {
    const modal = document.getElementById('paymentSuccessModal');
    const content = document.getElementById('paymentSuccessContent');
    
    content.innerHTML = `
        <div class="space-y-4">
            <div class="bg-green-50 rounded-lg p-4 text-center">
                <i class="fas fa-check-circle text-green-500 text-5xl mb-3"></i>
                <h3 class="text-lg font-semibold text-green-700">Payment Successful!</h3>
                <p class="text-green-600 text-sm mt-1">Your payment has been processed successfully.</p>
            </div>
            
            <div class="border border-slate-200 rounded-lg p-4 space-y-3">
                <div class="flex justify-between">
                    <span class="text-slate-500">Transaction ID:</span>
                    <span class="font-mono text-sm text-slate-700">${escapeHtml(paymentData.transaction_id)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Amount Paid:</span>
                    <span class="font-bold text-green-600">$${paymentData.amount}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Payment Date:</span>
                    <span class="text-slate-700">${new Date().toLocaleString()}</span>
                </div>
            </div>
            
            <div class="flex gap-3">
                <button onclick="closePaymentSuccessModal()" 
                        class="flex-1 bg-slate-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition">
                    Close
                </button>
                <button onclick="window.location.href='/my/bookings'" 
                        class="flex-1 border border-slate-200 py-2 rounded-lg text-sm hover:bg-slate-50 transition">
                    View My Bookings
                </button>
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// Close payment success modal
function closePaymentSuccessModal() {
    const modal = document.getElementById('paymentSuccessModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Cancel booking
async function cancelBooking(bookingId) {
    if (!confirm('Are you sure you want to cancel this booking?')) return;
    
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/bookings/${bookingId}/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            showToast('Booking cancelled successfully', 'success');
            loadBookings(currentFilter);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to cancel booking', 'error');
        }
    } catch (error) {
        console.error('Error cancelling booking:', error);
        showToast('Connection error', 'error');
    }
}

// Close payment modal
function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    currentBookingId = null;
}

// Download invoice PDF
async function downloadInvoice(bookingId) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showToast('Please login first', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/pdf/invoice/${bookingId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.status === 401) {
            showToast('Session expired. Please login again.', 'error');
            localStorage.removeItem('access_token');
            setTimeout(() => window.location.href = '/auth/login', 1500);
            return;
        }
        
        if (response.ok) {
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `invoice_${bookingId}.pdf`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename=(.+)/);
                if (match) filename = match[1];
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Invoice downloaded successfully!', 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to download invoice', 'error');
        }
    } catch (error) {
        console.error('Error downloading invoice:', error);
        showToast('Connection error', 'error');
    }
}

// Download customer report PDF
async function downloadCustomerReport() {
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    
    if (!token) {
        showToast('Please login first', 'error');
        window.location.href = '/auth/login';
        return;
    }
    
    let customerId = userId;
    if (!customerId) {
        try {
            const response = await fetch('/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const user = await response.json();
                customerId = user.id;
                localStorage.setItem('user_id', customerId);
            }
        } catch (error) {
            console.error('Error fetching user info:', error);
        }
    }
    
    if (!customerId) {
        showToast('Unable to identify user', 'error');
        return;
    }
    
    showToast('Generating report...', 'info');
    
    try {
        const response = await fetch(`/pdf/customer-bookings/${customerId}`, {
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
            showToast('No bookings found for this customer', 'error');
            return;
        }
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Extract filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `my_bookings_${new Date().toISOString().slice(0, 10)}.pdf`;
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

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show toast
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 z-50 border-l-4 ${type === 'error' ? 'border-red-500' : 'border-emerald-500'}`;
    toast.innerHTML = `
        <div class="flex items-center gap-2">
            <i class="fas ${type === 'error' ? 'fa-exclamation-circle text-red-500' : 'fa-check-circle text-emerald-500'}"></i>
            <span class="text-slate-700 text-sm">${escapeHtml(message)}</span>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Initialize page
function initBookingsPage() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/auth/login';
        return;
    }
    loadBookings('all');
}

document.addEventListener('DOMContentLoaded', initBookingsPage);