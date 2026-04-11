from database.mongodb_connection import MongoDB
from datetime import datetime
import uuid

class Order:
    collection = MongoDB.get_collection('orders')
    
    @classmethod
    def create_order(cls, user_id, items, total_amount, shipping_address, payment_method):
        order = {
            "order_id": str(uuid.uuid4()),
            "user_id": user_id,
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = cls.collection.insert_one(order)
        
        # Update user's orders
        users_collection = MongoDB.get_collection('users')
        users_collection.update_one(
            {"user_id": user_id},
            {"$push": {"orders": order["order_id"]}, "$set": {"cart": []}}
        )
        
        return str(result.inserted_id)
    
    @classmethod
    def get_user_orders(cls, user_id):
        orders = list(cls.collection.find({"user_id": user_id}).sort("created_at", -1))
        for order in orders:
            order['_id'] = str(order['_id'])
        return orders
    
    @classmethod
    def update_order_status(cls, order_id, status):
        result = cls.collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0