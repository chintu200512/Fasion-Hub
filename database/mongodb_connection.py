from pymongo import MongoClient
from config import Config
from datetime import datetime

class MongoDB:
    client = None
    db = None
    
    @classmethod
    def connect(cls):
        if cls.client is None:
            try:
                cls.client = MongoClient(Config.MONGO_URI)
                cls.db = cls.client[Config.DATABASE_NAME]
                # Test connection
                cls.client.admin.command('ping')
                print(f"Successfully connected to MongoDB database: {Config.DATABASE_NAME}")
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                raise
        return cls.db
    
    @classmethod
    def get_collection(cls, collection_name):
        db = cls.connect()
        return db[collection_name]
    
    @classmethod
    def close(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
            print("MongoDB connection closed")

# Initialize collections
def init_db():
    db = MongoDB.connect()
    
    # Create indexes
    db.users.create_index("email", unique=True)
    db.products.create_index("name")
    db.products.create_index("category")
    db.products.create_index("price")
    
    # Check if products collection is empty
    if db.products.count_documents({}) == 0:
        sample_products = [
            {
                "name": "Classic Cotton T-Shirt",
                "price": 999,
                "category": "men",
                "subcategory": "tshirts",
                "size": ["S", "M", "L", "XL"],
                "color": ["White", "Black", "Navy"],
                "description": "Premium cotton t-shirt for everyday comfort",
                "image": "tshirt1.jpg",
                "stock": 50,
                "rating": 4.5,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Slim Fit Jeans",
                "price": 2499,
                "category": "men",
                "subcategory": "jeans",
                "size": ["28", "30", "32", "34", "36"],
                "color": ["Blue", "Black"],
                "description": "Comfortable stretch denim jeans",
                "image": "jeans1.jpg",
                "stock": 30,
                "rating": 4.3,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Floral Summer Dress",
                "price": 1899,
                "category": "women",
                "subcategory": "dresses",
                "size": ["XS", "S", "M", "L"],
                "color": ["Floral Print"],
                "description": "Light and breezy summer dress",
                "image": "dress1.jpg",
                "stock": 25,
                "rating": 4.7,
                "created_at": datetime.utcnow()
            }
        ]
        db.products.insert_many(sample_products)
        print(f"Added {len(sample_products)} sample products to database")
    
    print("Database initialization complete")