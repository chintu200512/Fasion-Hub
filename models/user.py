from database.mongodb_connection import MongoDB
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

class User:
    collection = None
    
    @classmethod
    def get_collection(cls):
        if cls.collection is None:
            cls.collection = MongoDB.get_collection('users')
        return cls.collection
    
    @classmethod
    def create_user(cls, email, password, name, address=None, phone=None):
        collection = cls.get_collection()
        existing = collection.find_one({"email": email})
        if existing:
            return None, "Email already exists"
        
        user = {
            "user_id": str(uuid.uuid4()),
            "email": email,
            "password_hash": generate_password_hash(password),
            "name": name,
            "address": address,
            "phone": phone,
            "cart": [],
            "wishlist": [],
            "orders": [],
            "created_at": datetime.utcnow(),
            "is_admin": False
        }
        
        collection.insert_one(user)
        return user, "User created successfully"
    
    @classmethod
    def authenticate(cls, email, password):
        collection = cls.get_collection()
        user = collection.find_one({"email": email})
        if user and check_password_hash(user["password_hash"], password):
            return user
        return None
    
    @classmethod
    def get_user_by_id(cls, user_id):
        collection = cls.get_collection()
        return collection.find_one({"user_id": user_id})
    
    @classmethod
    def add_to_cart(cls, user_id, product_id, size, color, quantity=1):
        collection = cls.get_collection()
        user = cls.get_user_by_id(user_id)
        if not user:
            return False
        
        cart = user.get('cart', [])
        found = False
        for item in cart:
            if (item.get('product_id') == product_id and 
                item.get('size') == size and 
                item.get('color') == color):
                item['quantity'] = item.get('quantity', 0) + quantity
                found = True
                break
        
        if not found:
            cart.append({
                'product_id': product_id,
                'size': size,
                'color': color,
                'quantity': quantity
            })
        
        result = collection.update_one(
            {"user_id": user_id},
            {"$set": {"cart": cart}}
        )
        return result.modified_count > 0
    
    @classmethod
    def get_cart(cls, user_id):
        user = cls.get_user_by_id(user_id)
        return user.get('cart', []) if user else []