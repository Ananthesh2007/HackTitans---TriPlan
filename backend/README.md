# TriPlan Backend

## Quick Start

1. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`.

## Environment Variables

See `.env.example` for all required variables. Key variables:

- `LLM_PROVIDER`: `"openai"`, `"gemini"`, or `"none"`
- `LLM_API_KEY`: Your API key (never commit this)
- `FRONTEND_ORIGINS`: Comma-separated list of allowed origins

## Development Notes

- The backend uses mock data when no LLM provider is configured
- All API keys are loaded from environment variables only
- Error responses follow a consistent format: `{"error": {"code": "...", "message": "..."}}`
- The API contract is defined in `docs/api-contract.md`
- System architecture is documented in `docs/architecture.md`

## Testing

Run the test suite:
```bash
pytest
```

## Deployment

See the project README for deployment instructions.