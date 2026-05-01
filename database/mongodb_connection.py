from pymongo import MongoClient
from datetime import datetime

class MongoDBAtlas:
    _client = None
    _db = None
    
    # Update these with your actual Atlas credentials
    MONGO_URI = "mongodb+srv://narendra200512_db_user:<chintu>@fasion-hub.bxrcrnb.mongodb.net/?appName=fasion-hub"
    DB_NAME = "fasion-hub"
    
    @classmethod
    def connect(cls):
        if cls._client is None:
            try:
                cls._client = MongoClient(
                    cls.MONGO_URI,
                    serverSelectionTimeoutMS=5000,
                    retryWrites=True,
                    retryReads=True,
                    tls=True
                )
                cls._client.admin.command('ping')
                print("✅ MongoDB Atlas Connected")
            except Exception as e:
                print(f"❌ Connection Error: {e}")
                raise
        return cls._client
    
    @classmethod
    def get_db(cls):
        if cls._db is None:
            cls._db = cls.connect()[cls.DB_NAME]
        return cls._db
    
    @classmethod
    def get_products_collection(cls):
        """Get products collection specifically"""
        return cls.get_db()["products"]
    
    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            print("🔌 Disconnected from Atlas")

# ========== USAGE EXAMPLES ==========

# Initialize connection
db = MongoDBAtlas()
products = db.get_products_collection()

# 1. INSERT a product
new_product = {
    "name": "Premium Leather Jacket",
    "price": 4999,
    "category": "Jackets",
    "sizes": ["S", "M", "L", "XL"],
    "colors": ["Black", "Brown"],
    "in_stock": True,
    "created_at": datetime.now()
}

result = products.insert_one(new_product)
print(f"✅ Product inserted with ID: {result.inserted_id}")

# 2. INSERT multiple products
multiple_products = [
    {
        "name": "Cotton T-Shirt",
        "price": 599,
        "category": "T-Shirts",
        "sizes": ["S", "M", "L"],
        "in_stock": True
    },
    {
        "name": "Slim Fit Jeans",
        "price": 1299,
        "category": "Denim",
        "sizes": ["28", "30", "32", "34"],
        "in_stock": True
    }
]

result = products.insert_many(multiple_products)
print(f"✅ Inserted {len(result.inserted_ids)} products")

# 3. FIND all products
print("\n📦 All Products:")
for product in products.find():
    print(f"  - {product['name']}: ₹{product['price']}")

# 4. FIND products with filter
cheap_products = products.find({"price": {"$lt": 1000}})
print("\n💰 Products under ₹1000:")
for product in cheap_products:
    print(f"  - {product['name']}: ₹{product['price']}")

# 5. FIND one specific product
leather_jacket = products.find_one({"name": "Premium Leather Jacket"})
if leather_jacket:
    print(f"\n🎯 Found: {leather_jacket['name']}")

# 6. UPDATE a product
result = products.update_one(
    {"name": "Cotton T-Shirt"},
    {"$set": {"price": 499, "on_sale": True}}
)
print(f"\n✅ Updated {result.modified_count} product")

# 7. UPDATE multiple products
result = products.update_many(
    {"category": "T-Shirts"},
    {"$set": {"discount": 10}}
)
print(f"✅ Applied discount to {result.modified_count} products")

# 8. DELETE a product
result = products.delete_one({"name": "Slim Fit Jeans"})
print(f"✅ Deleted {result.deleted_count} product")

# 9. Check product count
count = products.count_documents({})
print(f"\n📊 Total products in collection: {count}")

# 10. CLOSE connection when done
# MongoDBAtlas.close()