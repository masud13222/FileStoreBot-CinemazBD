from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def connect_db():
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('DB_NAME', 'file_sharing_bot')]
        print("MongoDB connected successfully!")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return None 