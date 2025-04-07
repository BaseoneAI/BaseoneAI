import sys
import os
import asyncio
import openai
from starlette.config import Config
from database import comments_collection
from bson import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load config
config = Config(".env")
openai.api_key = config("OPENAI_API_KEY")

MONGO_URI = config("MONGO_URI")


async def send_to_openai(comment_text, user_name):
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are ARIA, a professional Business Development Manager replying to LinkedIn comments on behalf of BaseOne. Be warm, helpful, and subtly business-oriented."
            },
            {
                "role": "user",
                "content": f"Reply to this LinkedIn comment as ARIA from BaseOne, addressing a potential business opportunity:\n\nComment by {user_name}: '{comment_text}'"
            }
        ],
        max_tokens=200
    )
    return response["choices"][0]["message"]["content"].strip()

async def process_comment(comment_doc):
    comment_id = comment_doc.get("_id")
    comment_text = comment_doc.get("comment", "")
    user_name = comment_doc.get("user_name", "there")

    if not comment_text:
        print(f"No 'comment' field in document ID {comment_id}")
        return

    print(f"Processing new comment from {user_name}: {comment_text}")

    reply = await send_to_openai(comment_text, user_name)

    print(f"Generated reply:\n{reply}\n")

    # Save reply to the same document under a new field
    await comments_collection.update_one(
        {"_id": comment_id},
        {"$set": {"aria_reply": reply}}
    )
    print(f"Reply saved to comment document {_id}\n")

async def watch_comments():
    print("Watching MongoDB for new or updated comments...\n")
    async with comments_collection.watch() as stream:
        async for change in stream:
            if change["operationType"] in ["insert", "update", "replace"]:
                # Get full document
                doc_id = change["documentKey"]["_id"]
                full_doc = await comments_collection.find_one({"_id": doc_id})

                if full_doc:
                    await process_comment(full_doc)

if __name__ == "__main__":
    try:
        asyncio.run(watch_comments())
    except KeyboardInterrupt:
        print("Change stream listener stopped.")

