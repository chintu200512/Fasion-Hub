// Cart Management (Simplified for order system)

// Place Order Function
async function placeOrder(productId) {
    if (!productId) {
        showNotification('Invalid product', 'danger');
        return;
    }
    
    // Redirect to order form
    window.location.href = `/order-form/${productId}`;
}

// Submit Order Function
async function submitOrder(orderData) {
    try {
        const response = await axios.post('/api/place-order', orderData);
        
        if (response.data.success) {
            showNotification('Order placed successfully!', 'success');
            setTimeout(() => {
                window.location.href = '/my-orders';
            }, 2000);
            return true;
        } else {
            showNotification(response.data.message || 'Order failed', 'danger');
            return false;
        }
    } catch (error) {
        const message = error.response?.data?.message || 'Error placing order';
        showNotification(message, 'danger');
        return false;
    }
}

// Get Order Details
async function getOrderDetails(orderId) {
    try {
        const response = await axios.get(`/api/order/${orderId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching order:', error);
        return null;
    }
}

// Cancel Order (if pending)
async function cancelOrder(orderId) {
    if (!confirm('Are you sure you want to cancel this order?')) {
        return false;
    }
    
    try {
        const response = await axios.post(`/api/order/${orderId}/cancel`);
        if (response.data.success) {
            showNotification('Order cancelled successfully', 'success');
            setTimeout(() => location.reload(), 1500);
            return true;
        } else {
            showNotification(response.data.message, 'danger');
            return false;
        }
    } catch (error) {
        showNotification('Error cancelling order', 'danger');
        return false;
    }
}