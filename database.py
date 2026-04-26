from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

client = None
db = None

def connect_db():
    global client, db
    client = MongoClient(
        os.getenv("MONGODB_URL"),
        tlsCAFile=certifi.where()
    )
    db = client[os.getenv("DATABASE_NAME")]
    print("✅ MongoDB Connected Successfully")

def get_db():
    return db