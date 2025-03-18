from starlette.config import Config

config = Config(".env")  # Loads environment variables

MONGO_URI = config("MONGO_URI")
MONGO_DB_NAME = config("MONGO_DB_NAME", default="BaseoneAI")
MONGO_COLLECTION_NAME = config("MONGO_COLLECTION_NAME", default="BaseoneAI")

LINKEDIN_CLIENT_ID = config("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = config("LINKEDIN_CLIENT_SECRET")
LINKEDIN_AUTHORIZE_URL = config("LINKEDIN_AUTHORIZE_URL")
LINKEDIN_ACCESS_TOKEN_URL = config("LINKEDIN_ACCESS_TOKEN_URL")
LINKEDIN_USERINFO_ENDPOINT = config("LINKEDIN_USERINFO_ENDPOINT")
LINKEDIN_EMAIL_ENDPOINT = config("LINKEDIN_EMAIL_ENDPOINT")
LINKEDIN_REDIRECT_URI = config("LINKEDIN_REDIRECT_URI")
TARGET_ORG_ID = config("TARGET_ORG_ID")

OPENAI_API_KEY = config("OPENAI_API_KEY")
CHROMA_DB_PATH = config("CHROMA_DB_PATH")
