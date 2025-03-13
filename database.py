from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from starlette.config import Config

# Load environment variables
config = Config(".env")

# MongoDB Config
MONGO_URI = config("MONGO_URI")
MONGO_DB_NAME = "linkedin_oauth_db"
MONGO_COLLECTION_NAME = "users"

# Initialize MongoDB Connection
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
users_collection = db[MONGO_COLLECTION_NAME]

async def save_user(user_data: dict):
    try:
        await users_collection.insert_one(user_data)
        return {"message": "User saved", "user": user_data}
    except DuplicateKeyError:
        return {"message": "User already exists", "user": user_data}

async def get_user_by_id(user_id: str):
    return await users_collection.find_one({"_id": user_id})
