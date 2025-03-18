from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from starlette.config import Config
from bson import ObjectId

config = Config(".env")

MONGO_URI = config("MONGO_URI")
MONGO_DB_NAME = "linkedin_oauth_db"
MONGO_COLLECTION_NAME = "organizations"
MONGO_COMMENTS_COLLECTION = "comments"

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
org_collection = db[MONGO_COLLECTION_NAME]
comments_collection = db[MONGO_COMMENTS_COLLECTION]

async def upsert_organization(org_data: dict):
    filter_query = {"organization_id": org_data["organization_id"]}
    update_data = {"$set": org_data}

    updated_org = await org_collection.find_one_and_update(
        filter_query,
        update_data,
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    if updated_org:
        updated_org["_id"] = str(updated_org["_id"])  # Convert ObjectId to string
    
    return updated_org

async def save_linkedin_comments(org_id: str, comments: list):
    if not comments:
        return

    for comment in comments:
        comment_id = comment.get("id")
        if not comment_id:
            continue  # skip if no id present

        # Add organization_id to comment doc
        comment["organization_id"] = org_id

        # Upsert each comment based on LinkedIn comment ID
        await comments_collection.find_one_and_update(
            {"id": comment_id, "organization_id": org_id},
            {"$set": comment},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
