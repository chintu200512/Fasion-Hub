from flask import Blueprint, request, jsonify, session, render_template
from models.user import User
from models.product import Product
from models.order import Order
from config import Config

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/cart')
def view_cart():
    if 'user_id' not in session:
        return render_template('cart.html', cart_items=[], total=0, shipping_cost=0, grand_total=0)
    
    cart_items = User.get_cart(session['user_id'])
    items_with_details = []
    total = 0
    
    for item in cart_items:
        product = Product.get_product_by_id(item['product_id'])
        if product:
            item_total = product['price'] * item['quantity']
            total += item_total
            items_with_details.append({
                **item,
                'product': product,
                'item_total': item_total
            })
    
    shipping_cost = 0 if total >= Config.FREE_SHIPPING_THRESHOLD else Config.SHIPPING_COST
    grand_total = total + shipping_cost
    
    return render_template('cart.html', 
                         cart_items=items_with_details,
                         total=total,
                         shipping_cost=shipping_cost,
                         grand_total=grand_total,
                         free_shipping_threshold=Config.FREE_SHIPPING_THRESHOLD)

@cart_bp.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.json
    product_id = data.get('product_id')
    size = data.get('size')
    color = data.get('color')
    quantity = data.get('quantity', 1)
    
    success = User.add_to_cart(session['user_id'], product_id, size, color, quantity)
    
    if success:
        return jsonify({'success': True, 'message': 'Added to cart'})
    return jsonify({'success': False, 'message': 'Failed to add to cart'}), 400

@cart_bp.route('/api/cart/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.json
    shipping_address = data.get('shipping_address')
    payment_method = data.get('payment_method')
    
    cart_items = User.get_cart(session['user_id'])
    items_with_details = []
    total = 0
    
    for item in cart_items:
        product = Product.get_product_by_id(item['product_id'])
        if product and product['stock'] >= item['quantity']:
            items_with_details.append({
                'product_id': item['product_id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': item['quantity'],
                'size': item['size'],
                'color': item['color']
            })
            total += product['price'] * item['quantity']
            Product.update_stock(item['product_id'], item['quantity'])
    
    shipping_cost = 0 if total >= Config.FREE_SHIPPING_THRESHOLD else Config.SHIPPING_COST
    grand_total = total + shipping_cost
    
    order_id = Order.create_order(
        session['user_id'],
        items_with_details,
        grand_total,
        shipping_address,
        payment_method
    )
    
    return jsonify({'success': True, 'order_id': order_id, 'redirect': url_for('order_confirmation', order_id=order_id)})

def url_for(endpoint, **values):
    from flask import url_for as flask_url_for
    return flask_url_for(endpoint, **values)