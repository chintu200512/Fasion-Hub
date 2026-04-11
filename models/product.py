from database.mongodb_connection import MongoDB
from bson import ObjectId

class Product:
    collection = MongoDB.get_collection('product')
    
    @classmethod
    def get_all_product(cls, page=1, per_page=12, category=None, search=None, sort=None):
        """Get all product with pagination, filtering, and sorting"""
        query = {}
        
        # Apply category filter
        if category and category != 'all':
            query['category'] = category
        
        # Apply search filter
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}}
            ]
        
        # Determine sorting
        sort_option = [('created_at', -1)]  # default: newest first
        if sort == 'price_asc':
            sort_option = [('price', 1)]
        elif sort == 'price_desc':
            sort_option = [('price', -1)]
        elif sort == 'rating':
            sort_option = [('rating', -1)]
        
        try:
            # Get total count
            total = cls.collection.count_documents(query)
            
            # Get paginated products
            cursor = cls.collection.find(query).sort(sort_option).skip((page-1) * per_page).limit(per_page)
            product = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for product in products:
                product['_id'] = str(product['_id'])
            
            return product, total
        except Exception as e:
            print(f"Error in get_all_products: {e}")
            return [], 0  # Return empty list and 0 instead of None
    
    @classmethod
    def get_product_by_id(cls, product_id):
        """Get a single product by ID"""
        try:
            # Try to convert string ID to ObjectId
            if isinstance(product_id, str):
                product_id = ObjectId(product_id)
            
            product = cls.collection.find_one({"_id": product_id})
            if product:
                product['_id'] = str(product['_id'])
                return product
            return None
        except Exception as e:
            print(f"Error in get_product_by_id: {e}")
            return None
    
    @classmethod
    def get_product_by_ids(cls, product_ids):
        """Get multiple product by their IDs"""
        try:
            object_ids = []
            for pid in product_ids:
                try:
                    object_ids.append(ObjectId(pid))
                except:
                    pass
            
            if not object_ids:
                return []
            
            product = list(cls.collection.find({"_id": {"$in": object_ids}}))
            for product in product:
                product['_id'] = str(product['_id'])
            return product
        except Exception as e:
            print(f"Error in get_product_by_ids: {e}")
            return []
    
    @classmethod
    def get_categories(cls):
        """Get all unique categories"""
        try:
            categories = cls.collection.distinct('category')
            return categories
        except Exception as e:
            print(f"Error in get_categories: {e}")
            return []
    
    @classmethod
    def update_stock(cls, product_id, quantity):
        """Update product stock"""
        try:
            if isinstance(product_id, str):
                product_id = ObjectId(product_id)
            
            result = cls.collection.update_one(
                {"_id": product_id},
                {"$inc": {"stock": -quantity}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error in update_stock: {e}")
            return False
    
    @classmethod
    def create_product(cls, product_data):
        """Create a new product"""
        try:
            result = cls.collection.insert_one(product_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error in create_product: {e}")
            return None