import os

from dotenv import load_dotenv

# Reads the .env file (if present) into environment variables.
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

# Websites allowed to call this backend. Separate several with commas.
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]