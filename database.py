from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from starlette.config import Config

config = Config(".env")

# ✅ Connect to MongoDB
MONGO_URI = config("MONGO_URI")
MONGO_DB_NAME = "linkedin_oauth_db"
MONGO_COLLECTION_NAME = "organization"  # Make sure this matches your existing collection

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
org_collection = db[MONGO_COLLECTION_NAME]

# ✅ Function to Save LinkedIn Comments to `organization` Collection
async def save_linkedin_comments(org_id: str, comments: list):
    """Save LinkedIn comments for a specific organization."""
    if not comments:
        return

    for comment in comments:
        comment_id = comment.get("id")
        if not comment_id:
            continue 

        # Add `organization_id` to each comment doc
        comment["organization_id"] = org_id

        # Upsert each comment based on LinkedIn comment ID
        await org_collection.find_one_and_update(
            {"id": comment_id, "organization_id": org_id},
            {"$set": comment},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
