from fastapi import FastAPI

app = FastAPI(
    title="Intelligent Travel Companion API"
)

@app.get("/api/health")
def read_health():
    """
    Health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}