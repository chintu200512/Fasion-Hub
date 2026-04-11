from flask import Flask, session, redirect, url_for, jsonify, request
from config import Config
from database.mongodb_connection import MongoDB, init_db
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from models.user import User
from models.product import Product
from bson import ObjectId
import json
from datetime import datetime

# Rest of your app.py code remains the same...

# Custom JSON encoder
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
        
        return dict(
            cart_count=cart_count,
            is_authenticated=is_authenticated,
            get_user=get_user
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
        init_db()
        print('Database initialized with sample data!')
    
    @app.cli.command('create-admin')
    def create_admin():
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
        
        users_collection = User.collection
        existing = users_collection.find_one({"email": email})
        
        if existing:
            print('User with this email already exists!')
            return
        
        users_collection.insert_one(admin_user)
        print(f'Admin user {email} created successfully!')

# Create app instance
app = create_app()

# Import routes after app creation to avoid circular imports
from routes import auth_routes, product_routes, cart_routes

# Register additional routes
@app.route('/')
def home():
    from flask import redirect, url_for
    return redirect(url_for('product.index'))

@app.route('/health')
def health_check():
    from flask import jsonify
    from database.mongodb_connection import MongoDB
    from datetime import datetime
    
    try:
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

if __name__ == '__main__':
    host = getattr(Config, 'HOST', '0.0.0.0')
    port = getattr(Config, 'PORT', 5000)
    debug = getattr(Config, 'DEBUG', True)
    app.run(host=host, port=port, debug=debug)