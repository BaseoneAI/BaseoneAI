from pymongo import MongoClient

MONGO_URI = "your_mongo_uri_here"
client = MongoClient(MONGO_URI)

try:
    client.server_info()  # Ping the server
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
