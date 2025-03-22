import asyncio
from database import org_collection
from bson import ObjectId
from pymongo import ReturnDocument


async def insert_organization_data():
    """Manually insert organization data into MongoDB."""
    data = {
        "_id": ObjectId("67d9490e596eeae3f070df8a"),  # Ensure correct ObjectId type
        "organization_id": "106406962",
        "organization_urn": "urn:li:organization:106406962",
        "user_email": "kamesh29kumar@gmail.com",
        "user_name": "Kamesh",
        "comment_id": "7467872827",
        "urn_id": "309e3098-1293-120938839-3909120912093",
        "comment": "great sam, how reliable are you for my company's marketing team queries and replies?",
        "post": "I'm Sam, a Marketing Analyst passionate about turning insights into actionable results. I analyze market trends and campaign data to maximize ROI."
    }

    # Insert or upsert logic
    result = await org_collection.find_one_and_update(
        {"_id": data["_id"]},
        {"$set": data},
        upsert=True,
        return_document=ReturnDocument.AFTER  # Ensures returning the updated document
    )

    if result:
        print("Inserted/Updated document:")
        print(result)
    else:
        print("Document insertion failed.")

async def main():
    """Run the async insert function."""
    await insert_organization_data()

# Run the event loop properly
if __name__ == "__main__":
    asyncio.run(main())
