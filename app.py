from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from datetime import datetime
import bcrypt
import os
import requests
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from functools import wraps
from werkzeug.utils import secure_filename
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Upload configuration
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MongoDB Connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client[os.getenv('DB_NAME', 'fashionhub')]

# Collections
users_collection = db['users']
products_collection = db['products']
cart_collection = db['cart']
wishlist_collection = db['wishlist']
orders_collection = db['orders']

# Create unique index on product name to prevent duplicates
try:
    products_collection.create_index('name', unique=True)
except:
    pass

# Google OAuth Configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    }
)

# ============================================
# CONTEXT PROCESSOR - Inject cart count into all templates
# ============================================

@app.context_processor
def inject_cart_count():
    """Inject cart count into all templates"""
    if session.get("user_id"):
        count = cart_collection.count_documents({
            "user_id": session["user_id"]
        })
    else:
        count = 0
    return dict(cart_count=count)

# ============================================
# DECORATORS
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# GOOGLE OAUTH ROUTES
# ============================================

@app.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    session['next'] = request.args.get('next') or url_for('shop_page')
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
            flash('Could not retrieve email from Google', 'danger')
            return redirect(url_for('login_page'))
        
        user = users_collection.find_one({"email": email})
        
        if not user:
            user_id = users_collection.insert_one({
                "name": name,
                "email": email,
                "phone": "",
                "address": "",
                "created_at": datetime.now(),
                "last_login": datetime.now(),
                "total_orders": 0
            }).inserted_id
            session['user_id'] = str(user_id)
        else:
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            session['user_id'] = str(user["_id"])
        
        session["user_email"] = email
        session["user_name"] = name
        session['logged_in'] = True
        
        flash("Login successful", "success")
        
        next_page = session.pop('next', url_for('shop_page'))
        return redirect(next_page)
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        flash("Google login failed", "danger")
        return redirect(url_for("login_page"))

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('shop_page'))

# ============================================
# PROFILE ROUTES
# ============================================

@app.route('/profile')
@login_required
def profile_page():
    try:
        user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
        return render_template('profile.html', user=user)
    except Exception as e:
        flash('Error loading profile', 'danger')
        return redirect(url_for('shop_page'))

@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_update_profile():
    try:
        data = request.json
        users_collection.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {
                'phone': data.get('phone', ''),
                'address': data.get('address', '')
            }}
        )
        return jsonify({'success': True, 'message': 'Profile updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# PRODUCT ROUTES
# ============================================

@app.route('/')
@app.route('/shop')
def shop_page():
    try:
        products = list(products_collection.find().sort('created_at', -1).limit(20))
        for product in products:
            product['_id'] = str(product['_id'])
        return render_template('shop.html', products=products)
    except Exception as e:
        flash('Error loading products', 'danger')
        return render_template('shop.html', products=[])

@app.route('/product/<product_id>')
def product_detail(product_id):
    try:
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        if not product:
            flash('Product not found', 'danger')
            return redirect(url_for('shop_page'))
        
        product['_id'] = str(product['_id'])
        return render_template('product_detail.html', product=product)
    except Exception as e:
        flash('Product not found', 'danger')
        return redirect(url_for('shop_page'))

@app.route("/api/products/search")
def search_products():
    """Search products by name"""
    query = request.args.get("q", "")
    if query:
        products = list(products_collection.find({
            "name": {"$regex": query, "$options": "i"}
        }).limit(20))
    else:
        products = list(products_collection.find().limit(20))
    
    for p in products:
        p["_id"] = str(p["_id"])
    
    return jsonify(products)

# ============================================
# CART ROUTES
# ============================================

@app.route("/api/cart/add", methods=["POST"])
@login_required
def add_to_cart():
    """Add product to cart"""
    try:
        data = request.json
        product_id = data["product_id"]
        quantity = data.get("quantity", 1)

        product = products_collection.find_one({"_id": ObjectId(product_id)})

        if not product:
            return jsonify({"message": "Product not found"}), 404

        # Check if item already in cart
        existing_item = cart_collection.find_one({
            "user_id": session["user_id"],
            "product_id": product_id
        })

        if existing_item:
            # Update quantity
            cart_collection.update_one(
                {"_id": existing_item["_id"]},
                {"$inc": {"quantity": quantity}}
            )
        else:
            # Add new item
            cart_item = {
                "user_id": session["user_id"],
                "product_id": product_id,
                "name": product["name"],
                "price": product["price"],
                "image": product.get("image", "default.png"),
                "quantity": quantity,
                "added_at": datetime.now()
            }
            cart_collection.insert_one(cart_item)

        return jsonify({"message": "Added to cart", "success": True})
    
    except Exception as e:
        return jsonify({"message": str(e), "success": False}), 500

@app.route("/api/cart/remove/<product_id>", methods=["DELETE"])
@login_required
def remove_from_cart(product_id):
    """Remove product from cart"""
    try:
        cart_collection.delete_one({
            "user_id": session["user_id"],
            "product_id": product_id
        })
        return jsonify({"message": "Removed from cart", "success": True})
    except Exception as e:
        return jsonify({"message": str(e), "success": False}), 500

@app.route("/api/cart/update", methods=["POST"])
@login_required
def update_cart_quantity():
    """Update cart item quantity"""
    try:
        data = request.json
        product_id = data["product_id"]
        quantity = data.get("quantity", 1)
        
        if quantity <= 0:
            cart_collection.delete_one({
                "user_id": session["user_id"],
                "product_id": product_id
            })
        else:
            cart_collection.update_one(
                {"user_id": session["user_id"], "product_id": product_id},
                {"$set": {"quantity": quantity}}
            )
        
        return jsonify({"message": "Cart updated", "success": True})
    except Exception as e:
        return jsonify({"message": str(e), "success": False}), 500

@app.route("/api/cart", methods=["GET"])
@login_required
def get_cart():
    """Get user's cart"""
    try:
        cart_items = list(cart_collection.find({"user_id": session["user_id"]}))
        
        items = []
        total = 0
        
        for item in cart_items:
            item_data = {
                "product_id": item["product_id"],
                "name": item["name"],
                "price": item["price"],
                "image": item.get("image", "default.png"),
                "quantity": item["quantity"],
                "subtotal": item["price"] * item["quantity"]
            }
            items.append(item_data)
            total += item_data["subtotal"]
        
        return jsonify({"items": items, "total": total})
    except Exception as e:
        return jsonify({"items": [], "total": 0, "error": str(e)}), 500

@app.route("/cart")
@login_required
def cart_page():
    """Display cart page"""
    try:
        cart_items = list(cart_collection.find({"user_id": session["user_id"]}))
        
        items = []
        total = 0
        
        for item in cart_items:
            item_data = {
                "product_id": item["product_id"],
                "name": item["name"],
                "price": item["price"],
                "image": item.get("image", "default.png"),
                "quantity": item["quantity"],
                "subtotal": item["price"] * item["quantity"]
            }
            items.append(item_data)
            total += item_data["subtotal"]
        
        return render_template("cart.html", cart=items, total=total)
    except Exception as e:
        flash(f"Error loading cart: {str(e)}", "danger")
        return render_template("cart.html", cart=[], total=0)

# ============================================
# ORDER ROUTES
# ============================================

@app.route("/order/product/<product_id>")
@login_required
def order_page(product_id):
    """Show order page for a specific product"""
    try:
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            flash("Product not found", "danger")
            return redirect(url_for("shop_page"))
        
        product['_id'] = str(product['_id'])
        return render_template("order.html", product=product)
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("shop_page"))

@app.route("/place-order", methods=["POST"])
@login_required
def place_order():
    """Place an order"""
    try:
        product_id = request.form["product_id"]
        quantity = int(request.form["quantity"])
        mobile = request.form["mobile"]
        address = request.form["address"]
        
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        
        if not product:
            flash("Product not found", "danger")
            return redirect(url_for("shop_page"))
        
        if product.get('stock', 0) < quantity:
            flash("Insufficient stock available", "danger")
            return redirect(url_for("shop_page"))
        
        order = {
            "user_id": session["user_id"],
            "user_email": session["user_email"],
            "user_name": session["user_name"],
            "product_id": product_id,
            "product_name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "total_amount": product["price"] * quantity,
            "mobile": mobile,
            "address": address,
            "image": product.get("image", "default.png"),
            "order_status": "pending",
            "order_date": datetime.now(),
            "order_number": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        }
        
        orders_collection.insert_one(order)
        
        products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"stock": -quantity}}
        )
        
        users_collection.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$inc": {"total_orders": 1}}
        )
        
        flash("Order placed successfully!", "success")
        return redirect("/orders")
        
    except Exception as e:
        flash(f"Error placing order: {str(e)}", "danger")
        return redirect(url_for("shop_page"))

@app.route('/orders')
@login_required
def orders_page():
    """Show user's orders"""
    try:
        user_orders = list(orders_collection.find({
            'user_id': session['user_id']
        }).sort('order_date', -1))
        
        for order in user_orders:
            order['_id'] = str(order['_id'])
        
        return render_template('orders.html', orders=user_orders)
    except Exception as e:
        flash('Error loading orders', 'danger')
        return render_template('orders.html', orders=[])

@app.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    """Show order details"""
    try:
        order = orders_collection.find_one({
            '_id': ObjectId(order_id),
            'user_id': session['user_id']
        })
        if not order:
            flash('Order not found', 'danger')
            return redirect(url_for('orders_page'))
        
        order['_id'] = str(order['_id'])
        return render_template('order_detail.html', order=order)
    except Exception as e:
        flash('Order not found', 'danger')
        return redirect(url_for('orders_page'))

@app.route('/api/order/update-status/<order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Update order status (pending, confirmed, shipped, delivered)"""
    try:
        data = request.json
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        result = orders_collection.update_one(
            {'_id': ObjectId(order_id), 'user_id': session['user_id']},
            {'$set': {'order_status': new_status}}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Order status updated'})
        else:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# ADMIN PRODUCT CREATION WITH FILE UPLOAD
# ============================================

@app.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            price = float(request.form.get('price'))
            category = request.form.get('category')
            description = request.form.get('description')
            stock = int(request.form.get('stock', 0))
            
            existing = products_collection.find_one({"name": name})
            if existing:
                flash("Product already exists!", "danger")
                return redirect("/admin/add-product")
            
            image_file = request.files.get("image")
            image_filename = None
            
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                image_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                image_file.save(image_path)
                image_filename = unique_filename
            else:
                image_filename = "default.png"
            
            product = {
                "name": name,
                "price": price,
                "category": category,
                "description": description,
                "image": image_filename,
                "stock": stock,
                "rating": 4.5,
                "created_at": datetime.now()
            }
            
            products_collection.insert_one(product)
            flash("Product added successfully!", "success")
            return redirect("/admin/add-product")
            
        except DuplicateKeyError:
            flash("Product with this name already exists!", "danger")
            return redirect("/admin/add-product")
        except Exception as e:
            flash(f"Error adding product: {str(e)}", "danger")
            return redirect("/admin/add-product")
    
    return render_template('add_product.html')

# ============================================
# WISHLIST ROUTES
# ============================================

@app.route('/api/wishlist', methods=['GET'])
@login_required
def api_get_wishlist():
    """Get user's wishlist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify([])
        
        wishlist_items = list(wishlist_collection.find({'user_id': user_id}))
        items = []
        
        for item in wishlist_items:
            product = products_collection.find_one({'_id': ObjectId(item['product_id'])})
            if product:
                product['_id'] = str(product['_id'])
                items.append(product)
        
        return jsonify(items)
    except Exception as e:
        return jsonify([])

@app.route('/api/wishlist/toggle', methods=['POST'])
@login_required
def api_toggle_wishlist():
    """Toggle product in wishlist"""
    try:
        data = request.json
        user_id = session.get('user_id')
        product_id = data.get('product_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Please login'}), 401
        
        existing = wishlist_collection.find_one({
            'user_id': user_id,
            'product_id': product_id
        })
        
        if existing:
            wishlist_collection.delete_one({'_id': existing['_id']})
            return jsonify({'success': True, 'action': 'removed'})
        else:
            wishlist_collection.insert_one({
                'user_id': user_id,
                'product_id': product_id,
                'added_at': datetime.now()
            })
            return jsonify({'success': True, 'action': 'added'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# API SESSION ROUTE
# ============================================

@app.route('/api/session', methods=['GET'])
def api_get_session():
    if session.get('logged_in'):
        return jsonify({
            'logged_in': True,
            'user': {
                'id': session.get('user_id'),
                'name': session.get('user_name'),
                'email': session.get('user_email')
            }
        })
    return jsonify({'logged_in': False})

# ============================================
# PAGE ROUTES
# ============================================

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', 5000)))