from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import secrets
from urllib.parse import urlencode
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse
from starlette.config import Config
import requests

# Load environment variables from .env
config = Config(".env")

# LinkedIn API Credentials from .env
LINKEDIN_CLIENT_ID = config("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")
LINKEDIN_AUTHORIZE_URL = config("LINKEDIN_AUTHORIZE_URL")
LINKEDIN_ACCESS_TOKEN_URL = config("LINKEDIN_ACCESS_TOKEN_URL")

# MongoDB Configuration (if needed)
MONGO_URI = config("MONGO_URI")
MONGO_DB_NAME = config("MONGO_DB_NAME", default="BaseoneAI")
MONGO_COLLECTION_NAME = config("MONGO_COLLECTION_NAME", default="BaseoneAI")

# OpenAI Key (if needed)
OPENAI_API_KEY = config("OPENAI_API_KEY")
ORGANIZATION_ID = config("TARGET_ORG_ID")
ORG_API_URL = f"https://api.linkedin.com/v2/organizations/{ORGANIZATION_ID}"

# Initialize FastAPI app
app = FastAPI()

# Add session middleware for storing state
app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"))

@app.get("/login")
async def login(request: Request):
    """ Redirect user to LinkedIn OAuth for login """
    state = secrets.token_urlsafe(16)  # Generate secure random state
    request.session["linkedin_state"] = state  # Store state in session

    auth_params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,  # Use LinkedIn client ID from .env
        "redirect_uri": LINKEDIN_REDIRECT_URI,  # Use redirect URI from .env
        "scope": "openid profile email w_member_social r_organization_social w_organization_social rw_organization_admin",  # Modify the required scope
        "state": state
    }
    auth_url = f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(auth_params)}"
    return HTMLResponse(f'<a href="{auth_url}">Login with LinkedIn</a>')

@app.get("/auth/callback/linkedin")
async def linkedin_callback(request: Request):
    """ Handle LinkedIn OAuth callback and exchange code for access token """
    code = request.query_params.get("code")
    received_state = request.query_params.get("state")
    stored_state = request.session.get("linkedin_state")

    if not code or not received_state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    if received_state != stored_state:
        raise HTTPException(status_code=403, detail="Invalid state. Possible CSRF attack.")

    # Exchange the authorization code for an access token
    access_token = await get_access_token(code)
    
    if access_token:
        return {"message": "Access token obtained successfully!", "access_token": access_token}
    else:
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

async def get_access_token(code: str):
    """
    Exchange the authorization code for an access token from LinkedIn.
    """
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }

    # Make the request to LinkedIn to obtain the access token
    response = requests.post(LINKEDIN_ACCESS_TOKEN_URL, data=token_data)
    token_info = response.json()

    if "access_token" in token_info:
        return token_info["access_token"]
    else:
        return None
@app.get("/organization/details")
async def get_organization_details(request: Request):
    """ Fetch details of the organization page by ID """
    access_token = request.query_params.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Missing access token")

    # Authorization headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"  # LinkedIn requires this header
    }

    # Make the request to the LinkedIn API
    response = requests.get(ORG_API_URL, headers=headers)

    if response.status_code == 200:
        # Organization data retrieved successfully
        org_data = response.json()
        return JSONResponse(content=org_data)
    else:
        # Handle errors (e.g., insufficient permissions, invalid organization ID)
        return JSONResponse({"error": response.json()}, status_code=response.status_code)