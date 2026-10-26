import logging
from pathlib import Path

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models import BugReport
from app.schemas.bug_report import BugReportResponse
from app.services.bug_analyzer import run_bug_analysis
from app.services.storage import (
    delete_report_uploads,
    save_upload_file,
)


logger = logging.getLogger(__name__)


app = FastAPI(
    title="TraceLens API",
    description="Backend API for multimodal software bug investigation.",
    version="0.1.0",
)

MIN_DESCRIPTION_LENGTH = 10

SCREENSHOT_EXTENSION_BY_CONTENT_TYPE = {
    "image/png": ".png",
    "image/jpg": ".jpg",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
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
    """Read an upload in chunks and calculate its size safely."""
    total_size = 0

    while True:
        chunk = await uploaded_file.read(
            FILE_READ_CHUNK_SIZE_BYTES
        )

        if not chunk:
            break

        total_size += len(chunk)

        if total_size > max_size_bytes:
            break

    # Reset the cursor so the file can be saved afterward.
    await uploaded_file.seek(0)

    return total_size


async def process_bug_report_analysis(
    report_id: int,
) -> None:
    """Analyze a saved report and store the result in PostgreSQL."""

    # The request database session closes after the response.
    # Therefore, the background task needs its own session.
    db = SessionLocal()

    try:
        bug_report = db.get(BugReport, report_id)

        if bug_report is None:
            return

        # Let clients know that Ollama has started processing.
        bug_report.status = "analyzing"
        db.commit()

        analysis_result = await run_bug_analysis(
            description=bug_report.description,
            screenshot_storage_key=(
                bug_report.screenshot_storage_key
            ),
            supporting_file_storage_key=(
                bug_report.supporting_file_storage_key
            ),
        )

        bug_report.analysis_result = analysis_result
        bug_report.status = "completed"

        db.commit()

    except Exception:
        # Log the full technical error in the server terminal.
        logger.exception(
            "Bug analysis failed for report ID %s.",
            report_id,
        )

        db.rollback()

        try:
            failed_report = db.get(BugReport, report_id)

            if failed_report is not None:
                failed_report.status = "failed"
                failed_report.analysis_result = {
                    "error": (
                        "TraceLens could not complete the analysis. "
                        "Check the backend terminal for details."
                    ),
                }

                db.commit()

        except SQLAlchemyError:
            db.rollback()

    finally:
        db.close()


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


@app.get(
    "/bug-reports/{report_id}",
    response_model=BugReportResponse,
)
async def get_bug_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    # Search the bug_reports table using its primary-key ID.
    bug_report = db.get(BugReport, report_id)

    if bug_report is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Bug report not found.",
            },
        )

    # FastAPI converts this database object using BugReportResponse.
    return bug_report


@app.post(
    "/analyze",
    status_code=202,
)
async def analyze_bug(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    screenshot: UploadFile | None = File(default=None),
    supporting_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    cleaned_description = description.strip()
    validation_errors = []

    screenshot_size = None
    screenshot_extension = None

    supporting_file_size = None
    supporting_file_extension = None

    # Validate the description.
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

    # Validate the optional screenshot.
    if screenshot:
        if (
            screenshot.content_type
            not in SCREENSHOT_EXTENSION_BY_CONTENT_TYPE
        ):
            validation_errors.append(
                {
                    "field": "screenshot",
                    "message": (
                        "Screenshot must be a PNG, JPG, "
                        "JPEG, or WebP image."
                    ),
                }
            )
        else:
            screenshot_extension = (
                SCREENSHOT_EXTENSION_BY_CONTENT_TYPE[
                    screenshot.content_type
                ]
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
                    "message": (
                        "Screenshot cannot exceed 5 MB."
                    ),
                }
            )

    # Validate the optional supporting file.
    if supporting_file:
        supporting_filename = supporting_file.filename or ""

        supporting_file_extension = Path(
            supporting_filename
        ).suffix.lower()

        if (
            supporting_file_extension
            not in ALLOWED_SUPPORTING_FILE_EXTENSIONS
        ):
            validation_errors.append(
                {
                    "field": "supporting_file",
                    "message": (
                        "Supporting file must use a .log, .txt, "
                        ".csv, .json, .pdf, .doc, or .docx "
                        "extension."
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
                    "message": (
                        "Supporting file cannot be empty."
                    ),
                }
            )
        elif (
            supporting_file_size
            > MAX_SUPPORTING_FILE_SIZE_BYTES
        ):
            validation_errors.append(
                {
                    "field": "supporting_file",
                    "message": (
                        "Supporting file cannot exceed 10 MB."
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

    # Create the database record before saving its uploaded files.
    bug_report = BugReport(
        description=cleaned_description,
        screenshot_filename=(
            screenshot.filename if screenshot else None
        ),
        screenshot_size_bytes=screenshot_size,
        supporting_file_filename=(
            supporting_file.filename
            if supporting_file
            else None
        ),
        supporting_file_size_bytes=supporting_file_size,
        status="queued",
    )

    report_id: int | None = None

    try:
        db.add(bug_report)
        db.flush()

        report_id = bug_report.id

        if screenshot and screenshot_extension:
            bug_report.screenshot_storage_key = (
                await save_upload_file(
                    uploaded_file=screenshot,
                    report_id=report_id,
                    file_category="screenshot",
                    extension=screenshot_extension,
                )
            )

        if supporting_file and supporting_file_extension:
            bug_report.supporting_file_storage_key = (
                await save_upload_file(
                    uploaded_file=supporting_file,
                    report_id=report_id,
                    file_category="supporting",
                    extension=supporting_file_extension,
                )
            )

        db.commit()

    except (SQLAlchemyError, OSError) as error:
        db.rollback()

        if report_id is not None:
            try:
                delete_report_uploads(report_id)
            except OSError:
                pass

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "The bug report could not be saved."
                ),
            },
        ) from error

    # Start AI processing only after the database and files are saved.
    background_tasks.add_task(
        process_bug_report_analysis,
        bug_report.id,
    )

    return {
        "message": (
            "Bug report saved. Analysis has been queued."
        ),
        "bug_report_id": bug_report.id,
        "status": bug_report.status,
        "description": bug_report.description,
        "screenshot_filename": (
            bug_report.screenshot_filename
        ),
        "screenshot_size_bytes": (
            bug_report.screenshot_size_bytes
        ),
        "supporting_file_filename": (
            bug_report.supporting_file_filename
        ),
        "supporting_file_size_bytes": (
            bug_report.supporting_file_size_bytes
        ),
    }