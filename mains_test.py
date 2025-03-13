from fastapi import FastAPI, Request
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from pymongo import MongoClient
import os
import logging
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"), session_cookie="session", same_site="lax")

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client[os.getenv("MONGO_DB_NAME", "BaseoneAI")]
users_collection = db[os.getenv("MONGO_COLLECTION_NAME", "BaseoneAI")]

oauth = OAuth()
linkedin = oauth.register(
    name="linkedin",
    client_id=os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
    authorize_url=os.getenv("LINKEDIN_AUTHORIZE_URL"),
    access_token_url=os.getenv("LINKEDIN_ACCESS_TOKEN_URL"),
    userinfo_endpoint=os.getenv("LINKEDIN_USERINFO_ENDPOINT"),
    client_kwargs={"scope": "openid profile email"}
)

@app.get('/login/linkedin')
async def login_linkedin(request: Request):
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")
    return await linkedin.authorize_redirect(request, redirect_uri)
@app.get('/auth/callback/linkedin')
async def linkedin_auth_callback(request: Request):
    try:
        # 🔍 Exchange Code for Access Token
        token = await linkedin.authorize_access_token(request)
        user_response = await linkedin.get("me", token=token)
        email_response = await linkedin.get(os.getenv("LINKEDIN_EMAIL_ENDPOINT"), token=token)
        user_data = {
            "linkedin_id": user_response.json().get("id"),
            "name": user_response.json().get("localizedFirstName") + " " + user_response.json().get("localizedLastName"),
            "email": email_response.json()["elements"][0]["handle~"]["emailAddress"],
            "access_token": token["access_token"],}
        users_collection.update_one(
            {"linkedin_id": user_data["linkedin_id"]},
            {"$set": user_data},
            upsert=True
        )
        return {"message": "LinkedIn authentication successful", "user": user_data}
    except Exception as e:
        logger.error(f"Error in LinkedIn OAuth: {str(e)}")
        return {"error": "Authentication failed."}