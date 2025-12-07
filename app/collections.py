from app.database import get_db

class CollectionWrapper:
    def __init__(self, collection_name):
        self.collection_name = collection_name
        self._collection = None
    
    def _get_collection(self):
        if self._collection is None:
            self._collection = get_db()[self.collection_name]
        return self._collection
    
    def __getattr__(self, name):
        return getattr(self._get_collection(), name)

users_collection = CollectionWrapper("users")
products_collection = CollectionWrapper("products")
carts_collection = CollectionWrapper("carts")
orders_collection = CollectionWrapper("orders")
