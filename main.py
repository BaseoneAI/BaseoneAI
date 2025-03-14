from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import logging
import jwt
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from database import upsert_user

app = FastAPI()

config = Config(".env")

app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"), session_cookie="session")

LINKEDIN_CLIENT_ID = config("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

@app.get("/login/linkedin")
async def linkedin_login(request: Request):
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email",
        "state": "random_csrf_token_1234",
    }
    request.session["oauth_state"] = params["state"]
    auth_url = f"{AUTHORIZE_URL}?{'&'.join([f'{k}={v}' for k,v in params.items()])}"

    logger.debug(f"Redirecting user to LinkedIn: {auth_url}")
    return RedirectResponse(auth_url)

@app.get("/auth/callback/linkedin")
async def linkedin_callback(request: Request):
    try:
        code = request.query_params.get("code")
        received_state = request.query_params.get("state")
        stored_state = request.session.get("oauth_state")

        if stored_state != received_state:
            return JSONResponse({"error": "CSRF Warning! State mismatch"}, status_code=400)

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
        id_token = token_data.get("id_token")

        if not access_token or not id_token:
            return JSONResponse({"error": "Failed to retrieve tokens", "response": token_data}, status_code=400)

        decoded_token = jwt.decode(id_token, options={"verify_signature": False})

        user_data = {
            "linkedin_id": decoded_token.get("sub"),
            "first_name": decoded_token.get("given_name"),
            "last_name": decoded_token.get("family_name"),
            "email": decoded_token.get("email"),
        }

        updated_user = await upsert_user(user_data)

        logger.info(f"User saved/updated in MongoDB: {updated_user}")
        return JSONResponse({"message": "Authentication successful", "user": updated_user})

    except Exception as e:
        logger.error(f"Error in LinkedIn OAuth: {str(e)}")
        return JSONResponse({"error": "Authentication failed", "details": str(e)}, status_code=400)
