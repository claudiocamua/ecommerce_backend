from pymongo import MongoClient
from app.config import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.DB_NAME]

# Collections principais do sistema
users_collection = db.get_collection("users")
products_collection = db.get_collection("products")
carts_collection = db.get_collection("carts")
orders_collection = db.get_collection("orders")


def get_db():
    """Fornece acesso ao banco (usado nas rotas e serviços)"""
    return db


def test_connection():
    """Testa a conexão com o MongoDB e exibe informações úteis"""
    try:
        client.admin.command("ping")
        print("Conexão estabelecida com o MongoDB Atlas!")
        print(f"Banco conectado: {settings.DB_NAME}")
        
        print("Collections:")
        for name in db.list_collection_names():
            print(f" - {name}")

    except Exception as error:
        print(f"Falha ao conectar: {error}")
