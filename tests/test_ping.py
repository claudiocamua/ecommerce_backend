from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")

if not uri:
    raise Exception("MONGODB_URI não encontrada no .env")

client = MongoClient(
    uri,
    tls=True,
    tlsCAFile=certifi.where()
)

def test_mongo_ping():
    result = client.admin.command("ping")
    assert result["ok"] == 1
