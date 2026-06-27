let currentServiceId = null;

// Load categories for filter
async function loadCategories() {
    try {
        const response = await fetch('/services/categories');
        const categories = await response.json();
        const select = document.getElementById('categorySelect');
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
        showToast('Error loading categories', 'error');
    }
}

// Load providers for filter
async function loadProviders() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/users/providers', {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        
        if (response.ok) {
            const providers = await response.json();
            const select = document.getElementById('providerSelect');
            
            select.innerHTML = '<option value="">All Providers</option>';
            providers.forEach(provider => {
                const option = document.createElement('option');
                option.value = provider.id;
                option.textContent = provider.full_name || provider.username;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading providers:', error);
    }
}

// Load services with filters
async function loadServices() {
    const search = document.getElementById('searchInput')?.value || '';
    const category = document.getElementById('categorySelect')?.value || '';
    const provider = document.getElementById('providerSelect')?.value || '';
    const minPrice = document.getElementById('minPrice')?.value || '';
    const maxPrice = document.getElementById('maxPrice')?.value || '';
    
    let url = `/services/search?q=${encodeURIComponent(search)}`;

    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (minPrice) url += `&min_price=${minPrice}`;
    if (provider) url += `&provider_id=${provider}`;
    if (maxPrice) url += `&max_price=${maxPrice}`;
    
    try {
        const response = await fetch(url);
        const services = await response.json();
        displayServices(services);
    } catch (error) {
        console.error('Error loading services:', error);
        showToast('Error loading services', 'error');
    }
}

// Display services in grid
function displayServices(services) {
    const grid = document.getElementById('servicesGrid');
    
    if (!services || services.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i class="fas fa-search text-6xl text-gray-300 mb-4"></i>
                <p class="text-xl text-gray-500">No services found</p>
                <p class="text-gray-400 mt-2">Try adjusting your search filters</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = services.map(service => `
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden card-hover group">
            <div class="h-56 overflow-hidden relative">
                <img src="/static/uploads/${service.image_url || 'default-service.jpg'}" 
                     alt="${service.name}"
                     class="w-full h-full object-cover group-hover:scale-110 transition duration-500">
                <div class="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-full px-2 py-1 text-sm font-semibold text-primary-600">
                    ★ ${service.average_rating ? service.average_rating.toFixed(1) : 'New'}
                </div>
            </div>
            <div class="p-6">
                <h3 class="text-xl font-bold text-gray-900 mb-2">${escapeHtml(service.name)}</h3>
                <p class="text-gray-600 mb-4 line-clamp-2">${escapeHtml(service.description || 'No description available')}</p>
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <span class="text-2xl font-bold text-primary-600">$${service.price}</span>
                        <span class="text-gray-500 text-sm">/service</span>
                    </div>
                    <div class="flex items-center text-gray-500">
                        <i class="fas fa-clock mr-1"></i>
                        <span class="text-sm">${service.duration_minutes} min</span>
                    </div>
                </div>
                <div class="text-sm text-gray-500 mb-4">
                    <i class="fas fa-user mr-1"></i> ${escapeHtml(service.provider_name || 'Service Provider')}
                </div>
                <button onclick="showSchedules(${service.id})" 
                        class="w-full bg-blue-600 text-white py-2 rounded-xl font-semibold hover:shadow-lg transition transform hover:scale-[1.02]">
                    <i class="fas fa-calendar-check mr-2"></i>
                    Book Now
                </button>
            </div>
        </div>
    `).join('');
}

// Show available schedules
async function showSchedules(serviceId) {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        window.location.href = '/auth/login';
        return;
    }
    
    currentServiceId = serviceId;
    
    try {
        const response = await fetch(`/schedules/service/${serviceId}`);
        const schedules = await response.json();
        
        const modal = document.getElementById('bookingModal');
        const modalContent = document.getElementById('modalContent');
        
        if (!schedules || schedules.length === 0) {
            modalContent.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-calendar-times text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">No available time slots</p>
                    <button onclick="closeModal()" class="mt-4 gradient-bg text-white px-6 py-2 rounded-xl">Close</button>
                </div>
            `;
        } else {
            modalContent.innerHTML = `
                <div class="max-h-96 overflow-y-auto space-y-2">
                    ${schedules.map(schedule => `
                        <div class="border rounded-xl p-4 flex justify-between items-center hover:bg-gray-50 transition">
                            <div>
                                <i class="fas fa-calendar-alt text-primary-600 mr-2"></i>
                                <strong>${new Date(schedule.start_time).toLocaleDateString()}</strong>
                                <span class="mx-2">•</span>
                                <i class="fas fa-clock text-primary-600 mr-1"></i>
                                ${new Date(schedule.start_time).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                            </div>
                            <button onclick="bookService(${schedule.id})" 
                                    class="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition">
                                Book
                            </button>
                        </div>
                    `).join('')}
                </div>
                <button onclick="closeModal()" class="mt-4 w-full bg-gray-200 text-gray-700 py-2 rounded-xl hover:bg-gray-300 transition">
                    Cancel
                </button>
            `;
        }
        
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } catch (error) {
        console.error('Error loading schedules:', error);
        showToast('Error loading available times', 'error');
    }
}

// Book a service
async function bookService(scheduleId) {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/bookings/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                service_id: currentServiceId,
                schedule_id: scheduleId
            })
        });
        
        if (response.ok) {
            showToast('Booking request sent successfully!', 'success');
            closeModal();
            loadServices();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Booking failed', 'error');
        }
    } catch (error) {
        console.error('Error booking:', error);
        showToast('Connection error', 'error');
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('bookingModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize customer page
function initPage() {
    if (document.getElementById('searchInput')) {
        document.getElementById('searchInput').addEventListener('input', loadServices);
        document.getElementById('categorySelect')?.addEventListener('change', loadServices);
        document.getElementById('providerSelect')?.addEventListener('change', loadServices);
        document.getElementById('minPrice')?.addEventListener('input', loadServices);
        document.getElementById('maxPrice')?.addEventListener('input', loadServices);
        
        // Close modal on outside click
        document.getElementById('bookingModal')?.addEventListener('click', (e) => {
            if (e.target === document.getElementById('bookingModal')) {
                closeModal();
            }
        });
        
        loadCategories();
        loadProviders();
        loadServices();
    }
}

function displaySchedules(schedules) {
    const container = document.getElementById('schedulesList');
    
    if (schedules.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No available time slots</p>';
        return;
    }
    
    container.innerHTML = schedules.map(schedule => {
        const isPassed = schedule.is_passed;
        const date = new Date(schedule.start_time);
        const isPast = date < new Date();
        
        return `
            <div class="border rounded-lg p-3 flex justify-between items-center ${isPassed ? 'bg-red-50 border-red-300' : 'hover:bg-gray-50'}">
                <div class="${isPassed ? 'text-red-500' : 'text-gray-700'}">
                    <i class="fas fa-calendar-alt mr-2"></i>
                    ${date.toLocaleDateString()}
                    <i class="fas fa-clock mr-2 ml-2"></i>
                    ${date.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                    ${isPassed ? '<span class="ml-2 text-xs text-red-500"><i class="fas fa-hourglass-end"></i> Passed</span>' : ''}
                </div>
                ${!isPassed ? 
                    `<button onclick="bookService(${schedule.id})" 
                        class="bg-green-600 text-white px-4 py-1 rounded-lg hover:bg-green-700 transition">
                        Book
                    </button>` :
                    `<button disabled class="bg-gray-300 text-gray-500 px-4 py-1 rounded-lg cursor-not-allowed">
                        Passed
                    </button>`
                }
            </div>
        `;
    }).join('');
}


initPage();
