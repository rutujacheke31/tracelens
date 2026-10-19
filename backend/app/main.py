from fastapi import FastAPI, File, Form, UploadFile

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


@app.post("/analyze")
async def analyze_bug(
    description: str = Form(...),
    screenshot: UploadFile | None = File(default=None),
    log_file: UploadFile | None = File(default=None),
):
    return {
        "message": "Bug report received successfully.",
        "description": description,
        "screenshot_filename": screenshot.filename if screenshot else None,
        "log_filename": log_file.filename if log_file else None,
    }