from flask import Blueprint, request, jsonify, render_template
from models.product import Product  # Changed from products to product
from config import Config

product_bp = Blueprint('product', __name__)

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