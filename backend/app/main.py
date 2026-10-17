from fastapi import FastAPI

app = FastAPI(
    title="TraceLens API",
    description="Backend API for multimodal software bug investigation.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "TraceLens API",
        "message": "TraceLens backend is running.",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }