import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection string (Make sure this is correct)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = "linkedin_oauth_db"

async def test_mongo_connection():
    try:
        # Initialize MongoDB client
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB_NAME]

        # Run a simple command to check connection
        server_info = await db.command("ping")
        print("✅ MongoDB Connection Successful:", server_info)

        # List databases
        databases = await client.list_database_names()
        print("📂 Available Databases:", databases)

    except Exception as e:
        print("❌ MongoDB Connection Failed:", str(e))

# Run the test
asyncio.run(test_mongo_connection())
