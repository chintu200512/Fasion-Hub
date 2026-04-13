// Main JavaScript for FashionHub

// Session Management
async function checkSession() {
    try {
        const response = await axios.get('/api/session');
        return response.data.logged_in;
    } catch (error) {
        console.error('Session check error:', error);
        return false;
    }
}

// Notification System
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 250px;
        animation: slideIn 0.3s ease;
    `;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Format Price
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN').format(price);
}

// Validate Mobile Number
function isValidMobile(mobile) {
    return /^\d{10}$/.test(mobile);
}

// Validate Email
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Loading State
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="spinner"></div>';
    }
}

function hideLoading(containerId, content) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = content;
    }
}

// Image Preview
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 200px; border-radius: 10px;">`;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Logout Function
async function logout() {
    try {
        await axios.post('/api/logout');
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
        showNotification('Error logging out', 'danger');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});