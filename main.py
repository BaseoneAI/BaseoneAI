import secrets
import requests
import httpx
import logging
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(
    filename="app_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
config = Config(".env")

# LinkedIn API Credentials from .env
LINKEDIN_CLIENT_ID = config("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")
LINKEDIN_AUTHORIZE_URL = config("LINKEDIN_AUTHORIZE_URL")
LINKEDIN_ACCESS_TOKEN_URL = config("LINKEDIN_ACCESS_TOKEN_URL")

# Initialize FastAPI app
app = FastAPI()

# Add session middleware for state management (CSRF protection)
app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"))

@app.get("/login")
async def login(request: Request):
    """Redirect user to LinkedIn OAuth authorization URL."""
    state = secrets.token_urlsafe(16)
    request.session["linkedin_state"] = state

    auth_params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email w_member_social r_organization_social w_organization_social rw_organization_admin",
        "state": state
    }
    auth_url = f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(auth_params)}"
    logger.info("Redirecting user to LinkedIn login page")
    return HTMLResponse(f'<a href="{auth_url}">Login with LinkedIn</a>')

@app.get("/auth/callback/linkedin")
async def linkedin_callback(request: Request):
    """Handle LinkedIn OAuth callback and retrieve access token."""
    code = request.query_params.get("code")
    received_state = request.query_params.get("state")
    stored_state = request.session.get("linkedin_state")

    if not code or not received_state:
        logger.error("Missing code or state in callback")
        raise HTTPException(status_code=400, detail="Missing code or state")

    if received_state != stored_state:
        logger.error("Invalid state. Possible CSRF attack.")
        raise HTTPException(status_code=403, detail="Invalid state. Possible CSRF attack.")

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }

    response = requests.post(LINKEDIN_ACCESS_TOKEN_URL, data=token_data)
    token_info = response.json()

    if "access_token" in token_info:
        logger.info("Access token obtained successfully")
        return {"access_token": token_info["access_token"]}
    else:
        logger.error(f"Failed to obtain access token: {token_info}")
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

@app.get("/organization/latest-post")
async def fetch_latest_post(authorization: str = Header(...)):
    """Fetch the latest post from your organization's LinkedIn page."""
    if not authorization:
        logger.warning("Missing authorization header")
        raise HTTPException(status_code=400, detail="Authorization header is required")
    
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format")
        raise HTTPException(status_code=400, detail="Authorization header must be a Bearer token")
    
    access_token = authorization.split(" ")[1]
    logger.info("Fetching latest organization post")

    headers = {
        "authorization": authorization,
        "X-Restli-Protocol-Version": "2.0.0"
    }

    print(headers)

    