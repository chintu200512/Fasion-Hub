from flask import Flask, session, redirect, url_for, jsonify, request
from config import Config
from database.mongodb_connection import MongoDB, init_db
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.admin_routes import admin_bp
from models.user import User
from models.product import Product
from bson import ObjectId
import json
from datetime import datetime

# Custom JSON encoder for MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY
    app.json_encoder = JSONEncoder
    
    # Initialize database
    MongoDB.connect()
    init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)  # Register admin blueprint
    
    # Register context processors
    register_context_processors(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register before/after request handlers
    register_request_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app

def register_context_processors(app):
    from models.user import User
    from flask import session
    
    @app.context_processor
    def utility_processor():
        def cart_count():
            if 'user_id' in session:
                return len(User.get_cart(session['user_id']))
            return 0
        
        def is_authenticated():
            return 'user_id' in session
        
        def get_user():
            if 'user_id' in session:
                return User.get_user_by_id(session['user_id'])
            return None
        
        def is_admin():
            return session.get('is_admin', False)
        
        return dict(
            cart_count=cart_count,
            is_authenticated=is_authenticated,
            get_user=get_user,
            is_admin=is_admin
        )

def register_error_handlers(app):
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403

def register_request_handlers(app):
    from flask import session, request, redirect, url_for
    
    @app.before_request
    def before_request():
        session.permanent = True
        protected_routes = ['/cart', '/profile', '/order-confirmation']
        if any(request.path.startswith(route) for route in protected_routes):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
    
    @app.after_request
    def after_request(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

def register_cli_commands(app):
    from database.mongodb_connection import init_db
    from models.user import User
    from werkzeug.security import generate_password_hash
    import uuid
    from datetime import datetime
    
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database with sample data."""
        init_db()
        print('✅ Database initialized with sample data!')
    
    @app.cli.command('create-admin')
    def create_admin():
        """Create an admin user."""
        email = input('Enter admin email: ')
        password = input('Enter admin password: ')
        name = input('Enter admin name: ')
        
        admin_user = {
            "user_id": str(uuid.uuid4()),
            "email": email,
            "password_hash": generate_password_hash(password),
            "name": name,
            "address": None,
            "phone": None,
            "cart": [],
            "wishlist": [],
            "orders": [],
            "created_at": datetime.utcnow(),
            "is_admin": True
        }
        
        users_collection = User.get_collection()
        existing = users_collection.find_one({"email": email})
        
        if existing:
            print('❌ User with this email already exists!')
            return
        
        users_collection.insert_one(admin_user)
        print('=' * 50)
        print('✅ Admin user created successfully!')
        print('=' * 50)
        print(f'📧 Email: {email}')
        print(f'🔑 Password: {password}')
        print(f'👤 Name: {name}')
        print('=' * 50)

# Create app instance
app = create_app()

# Register additional routes after app creation
@app.route('/')
def home():
    return redirect(url_for('product.index'))

@app.route('/health')
def health_check():
    try:
        # Check database connection
        MongoDB.db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# API endpoint to get cart count
@app.route('/api/cart/count')
def api_cart_count():
    if 'user_id' in session:
        return jsonify({'count': len(User.get_cart(session['user_id']))})
    return jsonify({'count': 0})

# API endpoint to update cart item quantity
@app.route('/api/cart/update/<product_id>', methods=['PUT'])
def update_cart_item(product_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.json
    quantity = data.get('quantity', 1)
    
    user = User.get_user_by_id(session['user_id'])
    cart = user.get('cart', [])
    
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] = quantity
            break
    
    result = User.get_collection().update_one(
        {"user_id": session['user_id']},
        {"$set": {"cart": cart}}
    )
    
    if result.modified_count > 0:
        return jsonify({'success': True, 'message': 'Cart updated'})
    return jsonify({'success': False, 'message': 'Failed to update cart'}), 400

# API endpoint to remove item from cart
@app.route('/api/cart/remove', methods=['DELETE'])
def remove_cart_item():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.json
    product_id = data.get('product_id')
    size = data.get('size')
    color = data.get('color')
    
    user = User.get_user_by_id(session['user_id'])
    cart = user.get('cart', [])
    
    # Remove the specific item
    cart = [item for item in cart if not (
        item['product_id'] == product_id and 
        item.get('size') == size and 
        item.get('color') == color
    )]
    
    result = User.get_collection().update_one(
        {"user_id": session['user_id']},
        {"$set": {"cart": cart}}
    )
    
    if result.modified_count > 0:
        return jsonify({'success': True, 'message': 'Item removed from cart'})
    return jsonify({'success': False, 'message': 'Failed to remove item'}), 400

# API endpoint to apply coupon
@app.route('/api/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.json
    coupon_code = data.get('coupon', '').upper()
    
    # Define valid coupons
    coupons = {
        'SAVE10': {'discount': 0.10, 'min_amount': 1000},
        'SAVE20': {'discount': 0.20, 'min_amount': 2000},
        'FREESHIP': {'discount': 0, 'free_shipping': True}
    }
    
    if coupon_code in coupons:
        # Get cart total
        cart_items = User.get_cart(session['user_id'])
        total = 0
        for item in cart_items:
            product = Product.get_product_by_id(item['product_id'])
            if product:
                total += product['price'] * item['quantity']
        
        coupon_info = coupons[coupon_code]
        
        if 'min_amount' in coupon_info and total < coupon_info['min_amount']:
            return jsonify({
                'success': False, 
                'message': f'Minimum order amount of ₹{coupon_info["min_amount"]} required'
            }), 400
        
        # Store coupon in session
        session['applied_coupon'] = coupon_code
        
        return jsonify({
            'success': True,
            'message': 'Coupon applied successfully!',
            'coupon': coupon_info
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid coupon code'}), 400

# Order confirmation route
@app.route('/order-confirmation/<order_id>')
def order_confirmation(order_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from models.order import Order
    orders = Order.get_user_orders(session['user_id'])
    order = next((o for o in orders if o['order_id'] == order_id), None)
    
    if not order:
        return render_template('404.html'), 404
    
    return render_template('order_confirmation.html', order=order)

# Search suggestions API
@app.route('/api/search/suggestions')
def search_suggestions():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    products, _ = Product.get_all_products(page=1, per_page=5, search=query)
    suggestions = [{'name': p['name'], 'id': p['_id']} for p in products]
    return jsonify(suggestions)

if __name__ == '__main__':
    host = getattr(Config, 'HOST', '0.0.0.0')
    port = getattr(Config, 'PORT', 5000)
    debug = getattr(Config, 'DEBUG', True)
    
    print('=' * 50)
    print('🚀 Starting FashionHub E-Commerce Application')
    print('=' * 50)
    print(f'📍 Server running at: http://{host}:{port}')
    print(f'🔧 Debug mode: {debug}')
    print('=' * 50)
    
    app.run(host=host, port=port, debug=debug)