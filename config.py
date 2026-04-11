import os

class Config:
    # Secret key for session management
    SECRET_KEY = 'dev-secret-key-change-in-production-12345'
    
    # MongoDB configuration
    MONGO_URI = 'mongodb://localhost:27017/'
    DATABASE_NAME = 'clothing_ecommerce'
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Pagination
    PRODUCTS_PER_PAGE = 12
    
    # Shipping rates
    FREE_SHIPPING_THRESHOLD = 5000  # ₹50 or equivalent
    SHIPPING_COST = 500  # ₹5 or equivalent
    
    # Server configuration
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    
    # Security
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Payment settings (for production)
    RAZORPAY_KEY_ID = ''
    RAZORPAY_KEY_SECRET = ''
    
    # Email settings (for production)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''


       # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/images/products'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Make sure upload directory exists
    @staticmethod
    def init_upload_folder():
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)