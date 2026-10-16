from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config

app = FastAPI(title="TriPlan API", version="0.1.0")

# CORS lets the React frontend (a different address) call this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Quick check that the server is running."""
    return {
        "status": "ok",
        "service": "triplan-backend",
        "environment": config.APP_ENV,
    }