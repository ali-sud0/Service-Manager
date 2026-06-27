    // Update navbar based on localStorage
    function updateNavbar() {
        const token = localStorage.getItem('access_token');
        const userRole = localStorage.getItem('user_role');
        const userName = localStorage.getItem('user_name');
        const userEmail = localStorage.getItem('user_email');
        const userFullName = localStorage.getItem('user_full_name');
        
        if (token && userRole) {
            // Show logged in navbar
            document.getElementById('loggedOutNav').style.display = 'none';
            document.getElementById('loggedInNav').style.display = 'flex';
            
            // Update user info
            document.getElementById('userNameSpan').innerText = userName?.split(' ')[0] || 'User';
            document.getElementById('userFullNameSpan').innerText = userFullName || userName;
            document.getElementById('userEmailSpan').innerText = userEmail || '';
            document.getElementById('userRoleSpan').innerText = userRole.charAt(0).toUpperCase() + userRole.slice(1);
            
            // Set dashboard link based on role
            const dashboardLink = document.getElementById('dashboardLink');
            const editProfileMenuItem = document.getElementById('editProfileMenuItem');
            const myBookingsMenuItem = document.getElementById('myBookingsMenuItem');


            if (userRole === 'admin') {
                dashboardLink.href = '/dashboard/admin';
                if (dashboardLink) dashboardLink.style.display = 'block';
                if (editProfileMenuItem) editProfileMenuItem.style.display = 'none';
                if (myBookingsMenuItem) myBookingsMenuItem.style.display = 'none';
            } else if (userRole === 'provider') {
                dashboardLink.href = '/dashboard/provider';
                if (dashboardLink) dashboardLink.style.display = 'block';
                if (editProfileMenuItem) editProfileMenuItem.style.display = 'block';
                if (myBookingsMenuItem) myBookingsMenuItem.style.display = 'none';
            } else {
                if (dashboardLink) dashboardLink.style.display = 'none';
                if (editProfileMenuItem) editProfileMenuItem.style.display = 'block';
                if (myBookingsMenuItem) myBookingsMenuItem.style.display = 'block';
            }
        } else {
            // Show logged out navbar
            document.getElementById('loggedOutNav').style.display = 'flex';
            document.getElementById('loggedInNav').style.display = 'none';
        }
    }
    
    // Run on page load
    document.addEventListener('DOMContentLoaded', updateNavbar);
        
        // Run on page load
        document.addEventListener('DOMContentLoaded', updateNavbar);

        // Open edit profile modal and load current user data
async function openEditProfileModal() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const user = await response.json();
            
            document.getElementById('editFullName').value = user.full_name || '';
            document.getElementById('editUsername').value = user.username || '';
            document.getElementById('editEmail').value = user.email || '';
            document.getElementById('editPhone').value = user.phone || '';
            document.getElementById('editPassword').value = '';
            
            document.getElementById('editProfileModal').classList.remove('hidden');
            document.getElementById('editProfileModal').classList.add('flex');
        } else {
            showToast('Failed to load user data', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
}

// Close edit profile modal
function closeEditProfileModal() {
    document.getElementById('editProfileModal').classList.add('hidden');
    document.getElementById('editProfileModal').classList.remove('flex');
    document.getElementById('editProfileForm').reset();
}

// Save profile changes
document.getElementById('editProfileForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const token = localStorage.getItem('access_token');
    const formData = {
        full_name: document.getElementById('editFullName').value,
        username: document.getElementById('editUsername').value,
        email: document.getElementById('editEmail').value,
        phone: document.getElementById('editPhone').value
    };
    
    const password = document.getElementById('editPassword').value;
    if (password) {
        formData.password = password;
    }
    
    try {
        const response = await fetch('/users/me', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Profile updated successfully!', 'success');
            closeEditProfileModal();
            
            // Update stored user info
            localStorage.setItem('user_name', formData.full_name.split(' ')[0] || formData.username);
            localStorage.setItem('user_full_name', formData.full_name);
            localStorage.setItem('user_email', formData.email);
            
            // Update navbar display
            updateNavbar();
            
            // Reload page to reflect changes
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Connection error', 'error');
    }
});

// Helper function to show toast (if not already defined)
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
