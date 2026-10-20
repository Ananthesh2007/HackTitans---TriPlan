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

# ------------------------------------------------------------------
# AI provider settings.
#
# The API key is read ONLY from the environment (or the .env file, which
# is never committed). Never hard-code a key in code and never send it
# to the frontend.
# ------------------------------------------------------------------

# "openai", "gemini" or "none" (forces the mock itinerary).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()

# The secret key. Leave empty to run in mock mode.
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()

# Which model to call.
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()


def _default_base_url() -> str:
    """Pick the API address that matches the chosen provider."""
    if LLM_PROVIDER == "gemini":
        return "https://generativelanguage.googleapis.com/v1beta/openai"
    return "https://api.openai.com/v1"


# The API base URL. Different providers use different addresses.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip() or _default_base_url()

# How long to wait for the provider before giving up (seconds).
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

# How many tokens the model may use for one answer.
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))

# Creativity. Lower values give more predictable JSON.
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Set to "true" to always use the mock itinerary, even with a valid key.
FORCE_MOCK_AI = os.getenv("FORCE_MOCK_AI", "false").strip().lower() in ("1", "true", "yes")


def is_ai_configured() -> bool:
    """True when the backend may call the real LLM.

    False means the backend uses the built-in mock itinerary instead.
    """
    if FORCE_MOCK_AI or LLM_PROVIDER == "none":
        return False
    return bool(LLM_API_KEY and LLM_MODEL and LLM_BASE_URL)
