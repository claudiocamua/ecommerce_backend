from pymongo import MongoClient
from pymongo.server_api import ServerApi
from app.config import settings
from fastapi import HTTPException

client = None
db = None

def get_client():
    global client, db
    
    if client is None:
        try:
            client = MongoClient(
                settings.MONGODB_URI,
                server_api=ServerApi('1'),
                serverSelectionTimeoutMS=10000,
                tls=True, 
            )

            client.admin.command('ping')
            db = client[settings.DB_NAME]
            print("Conectado ao MongoDB com sucesso!")

        except Exception as e:
            print(f"Falha na conexão com MongoDB: {e}")
            client = None
            db = None
    
    return client, db

def get_db():
    _, database = get_client()
    if database is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponível."
        )
    return database

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

def init_collections():
    try:
        get_db()
        print("Collections prontas.")
        return True
    except:
        print("Não foi possível carregar as collections.")
        return False

def test_connection():
    try:
        cli, _ = get_client()
        if cli:
            print("Ping OK")
            return True
        return False
    except:
        return False
