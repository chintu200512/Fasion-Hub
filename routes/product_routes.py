from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from models.product import Product
from models.user import User
from config import Config
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database.mongodb_connection import MongoDB

product_bp = Blueprint('product', __name__)

# Configure upload settings
UPLOAD_FOLDER = "static/images/products"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@product_bp.route("/add-product", methods=["GET", "POST"])
def add_product():
    """Add new product to database (Admin only)"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Check if user is admin
    user = User.get_user_by_id(session['user_id'])
    if not user or not user.get('is_admin', False):
        return "Access denied. Admin only.", 403
    
    if request.method == "POST":
        try:
            # Get form data
            name = request.form.get("name")
            price = request.form.get("price")
            category = request.form.get("category")
            subcategory = request.form.get("subcategory", "")
            description = request.form.get("description", "")
            stock = request.form.get("stock", 10)
            rating = request.form.get("rating", 4)
            
            # Handle size and color (multiple selections)
            sizes = request.form.getlist("sizes")
            colors = request.form.getlist("colors")
            
            # Handle image upload
            image = request.files.get("image")
            filename = None
            
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                # Create unique filename with timestamp
                name_parts = filename.rsplit('.', 1)
                filename = f"{name_parts[0]}_{int(datetime.now().timestamp())}.{name_parts[1]}"
                
                # Ensure upload directory exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Save image
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)
                print(f"Image saved: {image_path}")
            else:
                # Use default image if no image uploaded
                filename = "placeholder.jpg"
            
            # Create product document
            product_data = {
                "name": name,
                "price": int(price),
                "category": category,
                "subcategory": subcategory,
                "description": description,
                "image": filename,
                "stock": int(stock),
                "rating": float(rating),
                "size": sizes if sizes else ["S", "M", "L", "XL"],
                "color": colors if colors else ["Black", "White", "Blue"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert into database
            db = MongoDB.get_collection('products')
            result = db.insert_one(product_data)
            
            if result.inserted_id:
                print(f"Product added successfully: {name}")
                return redirect(url_for('product.shop'))
            else:
                error = "Failed to add product"
                return render_template("add_product.html", error=error)
                
        except Exception as e:
            print(f"Error adding product: {e}")
            return render_template("add_product.html", error=str(e))
    
    # GET request - show form
    return render_template("add_product.html")

@product_bp.route('/')
def index():
    """Homepage with featured products"""
    try:
        featured_products, total = Product.get_all_products(page=1, per_page=8)
        return render_template('index.html', products=featured_products)
    except Exception as e:
        print(f"Error in index: {e}")
        return render_template('index.html', products=[])

@product_bp.route('/shop')
def shop():
    """Shop page with filters"""
    try:
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category', 'all')
        search = request.args.get('search', '')
        sort = request.args.get('sort', '')
        
        products, total = Product.get_all_products(
            page=page,
            per_page=Config.PRODUCTS_PER_PAGE,
            category=category,
            search=search,
            sort=sort
        )
        
        categories = Product.get_categories()
        
        total_pages = (total + Config.PRODUCTS_PER_PAGE - 1) // Config.PRODUCTS_PER_PAGE if total > 0 else 0
        
        return render_template('shop.html',
                             products=products,
                             categories=categories,
                             current_category=category,
                             current_page=page,
                             total_pages=total_pages,
                             search=search,
                             sort=sort)
    except Exception as e:
        print(f"Error in shop: {e}")
        return render_template('shop.html', products=[], categories=[])

@product_bp.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
        product = Product.get_product_by_id(product_id)
        if not product:
            return render_template('404.html'), 404
        
        # Get related products from same category
        related, _ = Product.get_all_products(page=1, per_page=4, category=product.get('category', ''))
        
        return render_template('product_detail.html', product=product, related=related)
    except Exception as e:
        print(f"Error in product_detail: {e}")
        return render_template('404.html'), 404

@product_bp.route('/api/products/search')
def search_products():
    """API search endpoint"""
    try:
        query = request.args.get('q', '')
        products, _ = Product.get_all_products(page=1, per_page=10, search=query)
        return jsonify(products)
    except Exception as e:
        print(f"Error in search_products: {e}")
        return jsonify([])