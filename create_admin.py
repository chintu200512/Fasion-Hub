from app import app
from models.user import User
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime

with app.app_context():
    # Check if admin exists
    admin = User.get_collection().find_one({"email": "admin@example.com"})
    
    if not admin:
        admin_user = {
            "user_id": str(uuid.uuid4()),
            "email": "admin@example.com",
            "password_hash": generate_password_hash("admin123"),
            "name": "Admin User",
            "address": "Admin Address",
            "phone": "1234567890",
            "cart": [],
            "wishlist": [],
            "orders": [],
            "created_at": datetime.utcnow(),
            "is_admin": True
        }
        User.get_collection().insert_one(admin_user)
        print("=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print(f"📧 Email: admin@example.com")
        print(f"🔑 Password: admin123")
        print("=" * 50)
    else:
        print("⚠️ Admin user already exists!")
        print(f"📧 Email: admin@example.com")