from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from starlette.config import Config
from bson import ObjectId

config = Config(".env")

MONGO_URI = config("MONGO_URI")
MONGO_DB_NAME = "linkedin_oauth_db"
MONGO_COLLECTION_NAME = "users"

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
users_collection = db[MONGO_COLLECTION_NAME]

async def upsert_user(user_data: dict):
    filter_query = {"linkedin_id": user_data["linkedin_id"]}
    update_data = {"$set": user_data}

    updated_user = await users_collection.find_one_and_update(
        filter_query,
        update_data,
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])  # Convert ObjectId to string
    
    return updated_user
