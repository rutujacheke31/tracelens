from fastapi import FastAPI, File, Form, HTTPException, UploadFile

app = FastAPI(
    title="TraceLens API",
    description="Backend API for multimodal software bug investigation.",
    version="0.1.0",
)

MIN_DESCRIPTION_LENGTH = 10

ALLOWED_SCREENSHOT_TYPES = {
    "image/png",
    "image/jpg",
    "image/jpeg",
    "image/webp",
}

ALLOWED_SUPPORTING_FILE_EXTENSIONS = (
    ".log",
    ".txt",
    ".csv",
    ".json",
    ".pdf",
    ".doc",
    ".docx",
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
    supporting_file: UploadFile | None = File(default=None),
):
    cleaned_description = description.strip()
    validation_errors = []

    if len(cleaned_description) < MIN_DESCRIPTION_LENGTH:
        validation_errors.append(
            {
                "field": "description",
                "message": (
                    f"Description must contain at least "
                    f"{MIN_DESCRIPTION_LENGTH} characters."
                ),
            }
        )

    if screenshot and screenshot.content_type not in ALLOWED_SCREENSHOT_TYPES:
        validation_errors.append(
            {
                "field": "screenshot",
                "message": "Screenshot must be a PNG, JPG, JPEG, or WebP image.",
            }
        )

    if supporting_file:
        supporting_filename = (supporting_file.filename or "").lower()

        if not supporting_filename.endswith(
            ALLOWED_SUPPORTING_FILE_EXTENSIONS
        ):
            validation_errors.append(
                {
                    "field": "supporting_file",
                    "message": (
                        "Supporting file must use a .log, .txt, .csv, .json, "
                        ".pdf, .doc, or .docx extension."
                    ),
                }
            )

    if validation_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Validation failed.",
                "errors": validation_errors,
            },
        )   

    return {
        "message": "Bug report received successfully.",
        "description": cleaned_description,
        "screenshot_filename": screenshot.filename if screenshot else None,
        "supporting_file_filename": (
            supporting_file.filename if supporting_file else None
        ),
    }