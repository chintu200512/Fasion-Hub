// Cart page specific functionality

// Remove item from cart
function removeFromCart(productId, size, color) {
    if (confirm('Remove this item from cart?')) {
        fetch('/api/cart/remove', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                size: size,
                color: color
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
}

// Apply coupon code
function applyCoupon() {
    const couponCode = document.getElementById('coupon-code').value;
    
    fetch('/api/cart/apply-coupon', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ coupon: couponCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Coupon applied successfully!', 'success');
            location.reload();
        } else {
            showNotification(data.message, 'error');
        }
    });
}

// Proceed to checkout
function proceedToCheckout() {
    const shippingAddress = document.getElementById('shipping-address').value;
    const paymentMethod = document.querySelector('input[name="payment"]:checked').value;
    
    if (!shippingAddress) {
        showNotification('Please enter shipping address', 'error');
        return;
    }
    
    fetch('/api/cart/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            shipping_address: shippingAddress,
            payment_method: paymentMethod
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            showNotification(data.message, 'error');
        }
    });
}