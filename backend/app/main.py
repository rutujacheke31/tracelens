from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import BugReport


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

BYTES_PER_MEGABYTE = 1024 * 1024

MAX_SCREENSHOT_SIZE_BYTES = 5 * BYTES_PER_MEGABYTE
MAX_SUPPORTING_FILE_SIZE_BYTES = 10 * BYTES_PER_MEGABYTE

FILE_READ_CHUNK_SIZE_BYTES = 1 * BYTES_PER_MEGABYTE


async def get_upload_size(
    uploaded_file: UploadFile,
    max_size_bytes: int,
) -> int:
    total_size = 0

    while True:
        chunk = await uploaded_file.read(FILE_READ_CHUNK_SIZE_BYTES)

        if not chunk:
            break

        total_size += len(chunk)

        if total_size > max_size_bytes:
            break

    await uploaded_file.seek(0)

    return total_size


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
    db: Session = Depends(get_db),
):
    cleaned_description = description.strip()
    validation_errors = []

    screenshot_size = None
    supporting_file_size = None

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

    if screenshot:
        if screenshot.content_type not in ALLOWED_SCREENSHOT_TYPES:
            validation_errors.append(
                {
                    "field": "screenshot",
                    "message": "Screenshot must be a PNG, JPG, JPEG, or WebP image.",
                }
            )

        screenshot_size = await get_upload_size(
            screenshot,
            MAX_SCREENSHOT_SIZE_BYTES,
        )

        if screenshot_size == 0:
            validation_errors.append(
                {
                    "field": "screenshot",
                    "message": "Screenshot cannot be empty.",
                }
            )
        elif screenshot_size > MAX_SCREENSHOT_SIZE_BYTES:
            validation_errors.append(
                {
                    "field": "screenshot",
                    "message": "Screenshot cannot exceed 5 MB.",
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

        supporting_file_size = await get_upload_size(
            supporting_file,
            MAX_SUPPORTING_FILE_SIZE_BYTES,
        )

        if supporting_file_size == 0:
            validation_errors.append(
                {
                    "field": "supporting_file",
                    "message": "Supporting file cannot be empty.",
                }
            )
        elif supporting_file_size > MAX_SUPPORTING_FILE_SIZE_BYTES:
            validation_errors.append(
                {
                    "field": "supporting_file",
                    "message": "Supporting file cannot exceed 10 MB.",
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

    bug_report = BugReport(
        description=cleaned_description,
        screenshot_filename=screenshot.filename if screenshot else None,
        supporting_file_filename=(
            supporting_file.filename if supporting_file else None
        ),
    )

    try:
        db.add(bug_report)
        db.commit()
        db.refresh(bug_report)
    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                "message": "The bug report could not be saved.",
            },
        ) from error

    return {
        "message": "Bug report received successfully.",
        "bug_report_id": bug_report.id,
        "status": bug_report.status,
        "description": bug_report.description,
        "screenshot_filename": bug_report.screenshot_filename,
        "screenshot_size_bytes": screenshot_size,
        "supporting_file_filename": bug_report.supporting_file_filename,
        "supporting_file_size_bytes": supporting_file_size,
    }