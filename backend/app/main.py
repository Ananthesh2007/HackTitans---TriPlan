from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.errors import register_error_handlers
from app.routes import flights, hotels, transport, trips, weather

app = FastAPI(title="TriPlan API", version="0.2.0")

# CORS lets the React frontend (a different address) call this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Every error (validation, 404, crashes) leaves in the same JSON format.
register_error_handlers(app)

app.include_router(trips.router)
app.include_router(flights.router)
app.include_router(hotels.router)
app.include_router(transport.router)
# Date: 21-10-2026 — Added weather endpoint (optional feature)
app.include_router(weather.router)


@app.get("/health")
def health():
    """Quick check that the server is running."""
    return {
        "status": "ok",
        "service": "triplan-backend",
        "environment": config.APP_ENV,
    }