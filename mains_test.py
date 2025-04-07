import requests
import logging
import secrets
import httpx
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from urllib.parse import urlencode
from pathlib import Path

# Setup logging directory and file
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist

logging.basicConfig(
    filename=LOG_DIR / "app_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
config = Config(".env")

# LinkedIn API Credentials (validate presence)
REQUIRED_ENV_VARS = [
    "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", 
    "LINKEDIN_REDIRECT_URI", "LINKEDIN_AUTHORIZE_URL", 
    "LINKEDIN_ACCESS_TOKEN_URL", "TARGET_ORG_ID", "SECRET_KEY"
]

for var in REQUIRED_ENV_VARS:
    if not config(var, default=None):
        raise ValueError(f"Missing required environment variable: {var}")

LINKEDIN_CLIENT_ID = config("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")
LINKEDIN_AUTHORIZE_URL = config("LINKEDIN_AUTHORIZE_URL")
LINKEDIN_ACCESS_TOKEN_URL = config("LINKEDIN_ACCESS_TOKEN_URL")
TARGET_ORG_ID = config("TARGET_ORG_ID")

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"))

@app.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["linkedin_state"] = state
    auth_params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": "r_dma_admin_pages_content",
        "state": state
    }
    auth_url = f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(auth_params)}"
    logger.info("Redirecting user to LinkedIn login page")
    return HTMLResponse(f'<a href="{auth_url}">Login with LinkedIn</a>')

@app.get("/auth/callback/linkedin")
async def linkedin_callback(request: Request, code: str = None, state: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    
    # Exchange authorization code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,  # This must match the one in LinkedIn App settings
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
    
    if response.status_code != 200:
        logger.error(f"Failed to exchange token: {response.text}")
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve access token")

    token_response = response.json()
    access_token = token_response.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token not received")

    logger.info("Successfully retrieved access token")
    return {"access_token": access_token}


LINKEDIN_API_BASE = "https://api.linkedin.com/rest"

@app.get("/organization/posts")
async def fetch_organization_posts(authorization: str = Header(...)):
    """Fetch LinkedIn posts for the organization page."""
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format")
        raise HTTPException(status_code=400, detail="Authorization header must be a Bearer token")

    access_token = authorization.split(" ")[1]
    logger.info("Fetching LinkedIn posts")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202401",  # Ensure API versioning
        "X-Restli-Protocol-Version": "2.0.0"
    }

    organization_id = "urn:li:organization:106406962"
    api_url = f"{LINKEDIN_API_BASE}/dmaPosts?q=entity&entity={organization_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch posts: {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content={"error": "Failed to fetch LinkedIn posts", "details": response.text}
            )

        posts_data = response.json()
        post_count = len(posts_data.get("elements", []))
        logger.info(f"Successfully retrieved {post_count} LinkedIn posts")

        return JSONResponse(content=posts_data)

    except httpx.RequestError as e:
        logger.error(f"HTTP Request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")