from fastapi import FastAPI, Request
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from pymongo import MongoClient
import logging

app = FastAPI(docs_url="/docs", redoc_url="/redoc")
config = Config('E:/Baseone/Comment_bot/.env')  # Ensure your environment variables are stored in a .env file
oauth = OAuth(config)
app.add_middleware(SessionMiddleware, secret_key=config('SECRET_KEY'))
logger = logging.getLogger(__name__)

# MongoDB Connection
MONGO_URI = config("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client[config("MONGO_DB_NAME", default="BaseoneAI")]
users_collection = db[config("MONGO_COLLECTION_NAME", default="BaseoneAI")]

# LinkedIn OAuth Registration
linkedin = oauth.register(
    name='linkedin',
    client_id=config('LINKEDIN_CLIENT_ID'),
    client_secret=config('LINKEDIN_CLIENT_SECRET'),
    authorize_url=config('LINKEDIN_AUTHORIZE_URL'),
    access_token_url=config('LINKEDIN_ACCESS_TOKEN_URL'),
    userinfo_endpoint=config('LINKEDIN_USERINFO_ENDPOINT'),
    client_kwargs={"scope": "r_liteprofile r_emailaddress w_member_social"},
)

# Login Route
@app.get('/login/linkedin')
async def login_linkedin(request: Request):
    redirect_uri = config('LINKEDIN_REDIRECT_URI')
    return await linkedin.authorize_redirect(request, redirect_uri)

# LinkedIn OAuth Callback
@app.get('/auth/callback/linkedin')
async def linkedin_auth_callback(request: Request):
    try:
        token = await linkedin.authorize_access_token(request)
        user_response = await linkedin.get('me', token=token)
        email_response = await linkedin.get("emailAddress?q=members&projection=(elements*(handle~))", token=token)
        
        return {"message": "LinkedIn authentication successful", "user": user_response.json()}
    except Exception as e:
        logger.error(f"Error in LinkedIn OAuth: {str(e)}")
        return {"error": "Authentication failed."}