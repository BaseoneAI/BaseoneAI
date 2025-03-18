import requests
from urllib.parse import urlencode
from starlette.config import Config
import os

# Load config from .env
config = Config(".env")

# Configuration from your .env
CLIENT_ID = config("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

def get_access_token(auth_code):
    """
    Exchange the authorization code for an access token.
    """
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    # Make the request to LinkedIn to obtain the access token
    response = requests.post(TOKEN_URL, data=token_data)
    token_info = response.json()

    if "access_token" in token_info:
        access_token = token_info["access_token"]
        return access_token
    else:
        return None, token_info.get("error_description", "Unknown error")

