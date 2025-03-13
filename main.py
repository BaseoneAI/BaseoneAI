from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import logging
import jwt
import os
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

app = FastAPI()

# Load environment variables
config = Config(".env")

# Middleware for session management
app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"), session_cookie="session")

# LinkedIn OAuth Config
LINKEDIN_CLIENT_ID = config("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# LinkedIn OAuth 2.0 URLs
AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/me"
EMAIL_URL = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"

@app.get("/login/linkedin")
async def linkedin_login(request: Request):
    """Step 1: Redirect user to LinkedIn for authentication"""
    
    # Generate authorization URL
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email",
        "state": "random_csrf_token_1234",  # Generate securely in production
    }
    request.session["oauth_state"] = params["state"]  # Store state in session
    auth_url = f"{AUTHORIZE_URL}?{'&'.join([f'{k}={v}' for k,v in params.items()])}"

    logger.debug(f"Redirecting user to LinkedIn: {auth_url}")
    return RedirectResponse(auth_url)

@app.get("/auth/callback/linkedin")
async def linkedin_callback(request: Request):
    """Handle LinkedIn OpenID Connect callback."""
    try:
        code = request.query_params.get("code")
        received_state = request.query_params.get("state")
        stored_state = request.session.get("oauth_state")

        logger.debug(f"Received state: {received_state}, Stored state: {stored_state}")

        if stored_state != received_state:
            return JSONResponse({"error": "CSRF Warning! State mismatch"}, status_code=400)

        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": LINKEDIN_REDIRECT_URI,
                    "client_id": LINKEDIN_CLIENT_ID,
                    "client_secret": LINKEDIN_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        id_token = token_data.get("id_token")  # OpenID JWT Token

        if not access_token or not id_token:
            return JSONResponse({"error": "Failed to retrieve tokens", "response": token_data}, status_code=400)

        logger.debug(f"Access Token: {access_token}")
        logger.debug(f"ID Token: {id_token}")

        # Decode JWT (LinkedIn OpenID Connect uses JWT)
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})  # Skip verification for now
        logger.debug(f"Decoded ID Token: {decoded_token}")

        # Extract user info from the ID token
        user_profile = {
            "linkedin_id": decoded_token.get("sub"),
            "first_name": decoded_token.get("given_name"),
            "last_name": decoded_token.get("family_name"),
            "email": decoded_token.get("email"),  # Email comes from ID Token
        }

        logger.info(f"User authenticated: {user_profile}")
        return JSONResponse({"message": "Authentication successful", "user": user_profile})

    except Exception as e:
        logger.error(f"Error in LinkedIn OpenID Connect: {str(e)}")
        return JSONResponse({"error": "Authentication failed", "details": str(e)}, status_code=400)